"""
GeoMind Agent - Main agent class powered by OpenRouter.

This module implements the AI agent that can understand natural language
queries about satellite imagery and execute the appropriate tools.
"""

import json
import re
from typing import Optional, Callable, Any
from datetime import datetime

from openai import OpenAI

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    OPENROUTER_MODEL,
)
from .tools import (
    geocode_location,
    get_bbox_from_location,
    search_imagery,
    get_item_details,
    list_recent_imagery,
    create_rgb_composite,
    calculate_ndvi,
    get_band_statistics,
)


# Map tool names to functions
TOOL_FUNCTIONS = {
    "geocode_location": geocode_location,
    "get_bbox_from_location": get_bbox_from_location,
    "search_imagery": search_imagery,
    "list_recent_imagery": list_recent_imagery,
    "get_item_details": get_item_details,
    "create_rgb_composite": create_rgb_composite,
    "calculate_ndvi": calculate_ndvi,
    "get_band_statistics": get_band_statistics,
}

# Tool definitions for the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "geocode_location",
            "description": "Convert a place name to geographic coordinates (latitude, longitude). Use this when you need to find coordinates for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "The name of the place to geocode (e.g., 'New York City', 'Paris, France')",
                    }
                },
                "required": ["place_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_bbox_from_location",
            "description": "Get a bounding box for a location, suitable for searching satellite imagery.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {
                        "type": "string",
                        "description": "The name of the place",
                    },
                    "buffer_km": {
                        "type": "number",
                        "description": "Buffer distance in kilometers (default: 10)",
                    },
                },
                "required": ["place_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_imagery",
            "description": "Search for Sentinel-2 satellite imagery in the EOPF catalog. Returns available scenes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Bounding box as [min_lon, min_lat, max_lon, max_lat]",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                    },
                    "max_cloud_cover": {
                        "type": "number",
                        "description": "Maximum cloud cover percentage (0-100)",
                    },
                    "max_items": {
                        "type": "integer",
                        "description": "Maximum number of results",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_recent_imagery",
            "description": "List recent Sentinel-2 imagery for a location. Combines geocoding and search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {
                        "type": "string",
                        "description": "Name of the location to search",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 7)",
                    },
                    "max_cloud_cover": {
                        "type": "number",
                        "description": "Maximum cloud cover percentage",
                    },
                    "max_items": {
                        "type": "integer",
                        "description": "Maximum number of results",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_item_details",
            "description": "Get detailed information about a specific Sentinel-2 scene by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "description": "The STAC item ID"}
                },
                "required": ["item_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_rgb_composite",
            "description": "Create an RGB true-color composite image from Sentinel-2 data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zarr_url": {
                        "type": "string",
                        "description": "URL to the SR_10m Zarr asset from a STAC item",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path to save the output image",
                    },
                    "subset_size": {
                        "type": "integer",
                        "description": "Size to subset the image (default: 1000 pixels)",
                    },
                },
                "required": ["zarr_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_ndvi",
            "description": "Calculate NDVI (vegetation index) from Sentinel-2 data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zarr_url": {
                        "type": "string",
                        "description": "URL to the SR_10m Zarr asset",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path to save the NDVI image",
                    },
                    "subset_size": {
                        "type": "integer",
                        "description": "Size to subset the image",
                    },
                },
                "required": ["zarr_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_band_statistics",
            "description": "Get statistics (min, max, mean) for spectral bands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zarr_url": {
                        "type": "string",
                        "description": "URL to the Zarr asset",
                    },
                    "bands": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of band names to analyze",
                    },
                },
                "required": ["zarr_url"],
            },
        },
    },
]


class GeoMindAgent:
    """
    GeoMind - An AI agent for geospatial analysis with Sentinel-2 imagery.

    Uses OpenRouter API for access to multiple AI models.
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the GeoMind agent.

        Args:
            model: Model name (default: nvidia/nemotron-3-nano-30b-a3b:free)
            api_key: OpenRouter API key (required).
        """
        self.provider = "openrouter"
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model_name = model or OPENROUTER_MODEL
        self.base_url = OPENROUTER_API_URL

        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required.\n"
                "Get your FREE API key at: https://openrouter.ai/settings/keys\n\n"
                "Then provide it in one of these ways:\n"
                "1. Run: geomind --api-key YOUR_KEY\n"
                "2. Set environment variable: OPENROUTER_API_KEY=YOUR_KEY\n"
                "3. Create .env file with: OPENROUTER_API_KEY=YOUR_KEY"
            )

        print(f"GeoMind Agent initialized with {self.model_name}")

        # Create OpenAI-compatible client
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        # Chat history
        self.history = []

        # Add system message
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return f"""You are GeoMind, an expert AI assistant specialized in geospatial analysis 
and satellite imagery. You help users find, analyze, and visualize Sentinel-2 satellite data 
from the EOPF (ESA Earth Observation Processing Framework) catalog.

Your capabilities include:
1. **Search**: Find Sentinel-2 L2A imagery by location, date, and cloud cover
2. **Geocoding**: Convert place names to coordinates for searching
3. **Visualization**: Create RGB composites and NDVI maps from imagery
4. **Analysis**: Calculate spectral indices and band statistics

Key information:
- Data source: EOPF STAC API (https://stac.core.eopf.eodc.eu)
- Satellite: Sentinel-2 (L2A surface reflectance products)
- Bands available: B01-B12 at 10m, 20m, or 60m resolution
- Current date: {datetime.now().strftime('%Y-%m-%d')}

IMPORTANT - Zarr URL usage:
- STAC search results include both SR_10m (base URL) and individual band assets (B02_10m, B03_10m, B04_10m, B08_10m)
- EITHER type of URL works for create_rgb_composite and calculate_ndvi:
  * SR_10m URL: Points to .../measurements/reflectance/r10m (contains all bands as subdirectories)
  * Individual band URLs: Point directly to specific bands like .../r10m/b02
- Prefer using SR_10m URL as it's simpler and works for all bands
- The processing functions automatically handle the correct path structure

When users ask for imagery:
1. First use get_bbox_from_location or list_recent_imagery to search
2. Present the results clearly with key metadata (ID, date, cloud cover)
3. Offer to create visualizations if data is found
4. For visualizations, use the SR_10m asset URL from search results

Always explain what you're doing and interpret results in a helpful way."""

    def _call_llm(self, messages: list, tools: list) -> dict:
        """Call LLM via OpenAI-compatible client."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096,
        )
        return response.model_dump()

    def _execute_function(self, name: str, args: dict) -> dict:
        """Execute a function call and return the result."""
        print(f"  Executing: {name}({args})")

        if name not in TOOL_FUNCTIONS:
            return {"error": f"Unknown function: {name}"}

        try:
            result = TOOL_FUNCTIONS[name](**args)
            return result
        except Exception as e:
            return {"error": str(e)}

    def chat(self, message: str, verbose: bool = True) -> str:
        """
        Send a message to the agent and get a response.
        """
        if verbose:
            print(f"\nUser: {message}")
            print("Processing...")

        # Add user message to history
        self.history.append({"role": "user", "content": message})

        # Build messages with system prompt
        messages = [{"role": "system", "content": self.system_prompt}] + self.history

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call the model (via proxy or direct)
            response_data = self._call_llm(messages, TOOLS)

            # Extract assistant message from response
            choice = response_data["choices"][0]
            assistant_message = choice["message"]

            # Check if there are tool calls
            tool_calls = assistant_message.get("tool_calls", [])
            if tool_calls:
                # Add assistant message with tool calls to messages
                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_message.get("content") or "",
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["function"]["name"],
                                    "arguments": tc["function"]["arguments"],
                                },
                            }
                            for tc in tool_calls
                        ],
                    }
                )

                # Execute each tool call
                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])

                    result = self._execute_function(func_name, func_args)

                    # Add tool result to messages
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(result, default=str),
                        }
                    )
            else:
                # No tool calls, we have a final response
                final_text = assistant_message.get("content") or ""

                # Add to history
                self.history.append({"role": "assistant", "content": final_text})

                if verbose:
                    print(f"\nGeoMind: {final_text}")

                return final_text

        return "Max iterations reached."

    def reset(self):
        """Reset the chat session."""
        self.history = []
        print("Chat session reset")


def main(model: Optional[str] = None):
    """Main entry point for CLI usage."""
    import sys

    print("=" * 60)
    print("GeoMind - Geospatial AI Agent")
    print("=" * 60)
    print("Powered by OpenRouter | Sentinel-2 Imagery")
    print("Type 'quit' or 'exit' to end the session")
    print("Type 'reset' to start a new conversation")
    print("=" * 60)

    try:
        agent = GeoMindAgent(model=model)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nPlease check your API key and internet connection.")
        sys.exit(1)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if user_input.lower() == "reset":
                agent.reset()
                continue

            agent.chat(user_input)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
