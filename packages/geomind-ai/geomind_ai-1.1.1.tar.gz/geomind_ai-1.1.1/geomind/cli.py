"""
Command-line interface for GeoMind.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional
import subprocess
import platform
import threading
import time

from .agent import GeoMindAgent


# Config file path for storing API key
CONFIG_DIR = Path.home() / ".geomind"
CONFIG_FILE = CONFIG_DIR / "config"


def get_saved_api_key() -> Optional[str]:
    """Get API key saved on user's PC."""
    if CONFIG_FILE.exists():
        try:
            return CONFIG_FILE.read_text().strip()
        except Exception:
            return None
    return None


def save_api_key(api_key: str) -> bool:
    """Save API key to user's PC."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(api_key)
        return True
    except Exception:
        return False


def display_recent_images():
    """Display recently created images if any exist."""
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        return
    
    # Get recent image files (created in last few seconds)
    import time
    recent_threshold = time.time() - 30  # 30 seconds ago
    
    recent_images = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.tiff']:
        for img_file in outputs_dir.glob(ext):
            if img_file.stat().st_mtime > recent_threshold:
                recent_images.append(img_file)
    
    if recent_images:
        print("\n" + "="*60)
        print("Generated Images:")
        for img in recent_images:
            print(f"   • {img.name} ({img.stat().st_size // 1024}KB)")
        
        # Try to open the most recent image
        if recent_images:
            latest_image = max(recent_images, key=lambda x: x.stat().st_mtime)
            open_image_viewer(latest_image)
        print("="*60)


def open_image_viewer(image_path: Path):
    """Open image in default viewer."""
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(str(image_path))
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(image_path)], check=False)
        else:  # Linux
            subprocess.run(["xdg-open", str(image_path)], check=False)
        print(f"   -> Opened {image_path.name} in default viewer")
    except Exception:
        print(f"   -> Saved to: {image_path}")


def format_response_box(title: str, content: str, color_code: str = "\033[94m") -> str:
    """Format response in an attractive box."""
    RESET = "\033[0m"
    lines = content.split('\n')
    max_width = max(len(line) for line in lines) if lines else 0
    max_width = max(max_width, len(title) + 4)
    width = min(max_width + 4, 80)
    
    box = f"{color_code}"
    box += "┌" + "─" * (width - 2) + "┐\n"
    box += f"│ {title:<{width-4}} │\n"
    box += "├" + "─" * (width - 2) + "┤\n"
    
    for line in lines:
        if line.strip():
            box += f"│ {line:<{width-4}} │\n"
        else:
            box += f"│{' ' * (width-2)}│\n"
    
    box += "└" + "─" * (width - 2) + "┘"
    box += RESET
    return box


class ThinkingIndicator:
    """Claude Code style thinking animation."""
    
    def __init__(self):
        self.is_thinking = False
        self.thread = None
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.thinking_messages = [
            "Thinking",
            "Analyzing satellite data",
            "Processing request",
            "Searching imagery"
        ]
    
    def start(self):
        """Start the thinking animation."""
        self.is_thinking = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the thinking animation."""
        self.is_thinking = False
        if self.thread:
            self.thread.join(timeout=0.1)
        # Clear the line
        print("\r" + " " * 60 + "\r", end="", flush=True)
    
    def _animate(self):
        """Run the thinking animation."""
        frame_idx = 0
        message_idx = 0
        message_counter = 0
        
        # Colors like Claude Code
        DIM = '\033[2m'
        RESET = '\033[0m'
        
        while self.is_thinking:
            spinner = self.frames[frame_idx % len(self.frames)]
            
            # Cycle through thinking messages every 30 frames (3 seconds)
            if message_counter % 30 == 0:
                message_idx = (message_idx + 1) % len(self.thinking_messages)
            
            message = self.thinking_messages[message_idx]
            
            # Show thinking with shimmer effect like Claude Code
            print(f"\r{DIM}{spinner} {message}...{RESET}", end="", flush=True)
            
            time.sleep(0.1)
            frame_idx += 1
            message_counter += 1


def main():
    """Main CLI entry point for the geomind package."""
    parser = argparse.ArgumentParser(
        description="GeoMind - AI agent for geospatial analysis with Sentinel-2 imagery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  geomind

  # Single query
  geomind --query "Find recent imagery of Paris"

  # With custom model
  geomind --model "anthropic/claude-3.5-sonnet"

  # With API key
  geomind --api-key "your-openrouter-api-key"

  # Clear saved API key
  geomind --clear-key

Environment Variables:
  OPENROUTER_API_KEY    Your OpenRouter API key
  OPENROUTER_MODEL      Model to use (default: nvidia/nemotron-3-nano-30b-a3b:free)
  OPENROUTER_API_URL    API endpoint (default: https://openrouter.ai/api/v1)
        """,
    )

    parser.add_argument(
        "--query",
        "-q",
        type=str,
        help="Single query to run (if not provided, starts interactive mode)",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        help="Model name to use (e.g., 'anthropic/claude-3.5-sonnet')",
    )
    parser.add_argument(
        "--api-key",
        "-k",
        type=str,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env variable)",
    )
    parser.add_argument(
        "--version", "-v", action="store_true", help="Show version and exit"
    )
    parser.add_argument("--clear-key", action="store_true", help="Clear saved API key")

    args = parser.parse_args()

    if args.clear_key:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            print("Saved API key cleared.")
        else:
            print("No saved API key found.")
        sys.exit(0)

    if args.version:
        from . import __version__

        print(f"GeoMind version {__version__}")
        sys.exit(0)

    # Start interactive or single-query mode
    try:
        if args.query:
            # Single query mode - check API key in order: argument > env > saved file
            from .config import OPENROUTER_API_KEY
            
            api_key = args.api_key or OPENROUTER_API_KEY or get_saved_api_key()
            if not api_key:
                print("Error: No API key found. Run 'geomind' first to set up.")
                sys.exit(1)
            agent = GeoMindAgent(model=args.model, api_key=api_key)
            agent.chat(args.query)
        else:
            # Interactive mode
            run_interactive(model=args.model, api_key=args.api_key)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


def print_banner():
    from . import __version__
    
    # ANSI color codes
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    
    banner = f"""
┌──────────────────────────────────────────────────────────────────────┐
│ {BOLD}>_ GeoMind{RESET} (v{__version__})                                                  │
│                                                                      │
│ model:     nvidia/nemotron-3-nano-30b-a3b:free                       │
│ docs:      https://harshshinde0.github.io/GeoMind                    │
│ authors:   Harsh Shinde, Rajat Shinde                                │
│ official:  https://harshshinde0.github.io/GeoMind                    │
│                                                                      │
│ Type "?" for help, "quit" to exit.                                   │
└──────────────────────────────────────────────────────────────────────┘
"""
    print(banner)
    print()


def print_help():
    """Print interactive session help."""
    help_text = """
Interactive Commands:
  help, ?          Show this help
  reset            Reset conversation
  exit, quit, q    Exit GeoMind

Query Examples:
  > Find recent Sentinel-2 imagery of Paris
  > Show me NDVI data for the Amazon rainforest  
  > Search for images with less than 10% cloud cover in London
  > Get satellite data for coordinates 40.7128, -74.0060

For CLI options, run: geomind --help
    """
    print(help_text)


def run_interactive(model: Optional[str] = None, api_key: Optional[str] = None):
    """Run interactive CLI mode."""
    from . import __version__

    print_banner()

    # Check for API key in order: argument > env > saved file
    from .config import OPENROUTER_API_KEY

    # Priority: command line arg > env variable > saved file
    if api_key:
        # Use provided argument
        pass
    elif OPENROUTER_API_KEY:
        api_key = OPENROUTER_API_KEY
    else:
        api_key = get_saved_api_key()

    if not api_key:
        print("\nOpenRouter API key required (FREE)")
        print("   Get yours at: https://openrouter.ai/settings/keys\n")
        api_key = input("   Enter your API key: ").strip()

        if not api_key:
            print("\nNo API key provided. Exiting.")
            return

        # Save the key for future use
        if save_api_key(api_key):
            print("   API key saved! You won't need to enter it again.\n")
        else:
            print("   Warning: Could not save API key. You'll need to enter it next time.\n")

    agent = GeoMindAgent(model=model, api_key=api_key)

    # Claude Code style color scheme
    CYAN = '\033[96m'
    DIM = '\033[2m' 
    BOLD = '\033[1m'
    RESET = '\033[0m'

    while True:
        try:
            # Simple prompt like Claude Code
            user_input = input(f"\n{CYAN}>{RESET} ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print(f"\n{DIM}Goodbye!{RESET}")
                break

            if user_input.lower() == "reset":
                agent.reset()
                print(f"{DIM}Started new conversation{RESET}")
                continue

            if user_input.lower() in ["help", "?"]:
                print_help()
                continue

            # Start thinking animation
            thinking = ThinkingIndicator()
            thinking.start()
            
            try:
                # Get response from agent
                response = agent.chat(user_input, verbose=False)
                
                # Stop thinking animation
                thinking.stop()
                
                # Display response cleanly like Claude Code
                print(f"\n{response}")
                
            except Exception as chat_error:
                thinking.stop()
                raise chat_error

        except KeyboardInterrupt:
            print(f"\n\n{DIM}Goodbye!{RESET}")
            break
        except Exception as e:
            print(f"\n{DIM}Error: {e}{RESET}")


if __name__ == "__main__":
    main()
