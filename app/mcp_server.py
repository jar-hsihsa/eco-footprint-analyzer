import asyncio
import csv
import json
import os

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("eco-footprint-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="read_utility_data",
            description="Reads utility data from a local file or generates dummy data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to CSV or TXT file, or 'dummy'"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="get_emission_factors",
            description="Retrieves standard carbon emission factors for a given category and region.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "The category of emission (e.g., 'electricity', 'transport')"
                    },
                    "region": {
                        "type": "string",
                        "description": "The geographical region (default: 'India')",
                        "default": "India"
                    }
                },
                "required": ["category"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if not arguments:
        arguments = {}

    if name == "read_utility_data":
        file_path = arguments.get("file_path", "dummy")
        if file_path.lower() == "dummy":
            dummy_data = {
                "electricity_kwh": 350,
                "petrol_liters": 45,
                "lpg_cylinders": 1,
                "flights_short_haul": 2,
                "public_transport_km": 150
            }
            return [types.TextContent(type="text", text=json.dumps(dummy_data, indent=2))]

        if not os.path.exists(file_path):
            return [types.TextContent(type="text", text=f"Error: File {file_path} not found.")]

        try:
            if file_path.endswith('.csv'):
                with open(file_path) as f:
                    reader = csv.DictReader(f)
                    return [types.TextContent(type="text", text=json.dumps(list(reader), indent=2))]
            else:
                with open(file_path) as f:
                    return [types.TextContent(type="text", text=f.read())]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error reading file: {e!s}")]

    elif name == "get_emission_factors":
        category = arguments.get("category", "")
        region = arguments.get("region", "India")

        db_path = os.path.join(os.path.dirname(__file__), "emission_factors.json")
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                database = json.load(f)
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error loading database: {e!s}")]

        factors = database.get(region, database.get("Global_Average", {}))

        if category.lower() in factors:
            result = factors[category.lower()]
        elif category.lower() in database.get("Global_Average", {}):
            result = database["Global_Average"][category.lower()]
        else:
            result = {"error": f"Category {category} not found."}

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
