from fastmcp import FastMCP
import httpx
import json

weather_mcp = FastMCP("Weather MCP Server for weather tools")

main_mcp = FastMCP("The main MCP Server with not one specific type of tools")

#prefix basically, when the mcp server is used it adds that prefix to your tools
#in our case mounting our weather_mcp turns forcast_tool to weather_forecast_tool
main_mcp = main_mcp.mount(server = weather_mcp, prefix= "weather")

@main_mcp.tool
def save_text_to_file(filename: str, content: str) -> str:
    """Saves a string of text content to a file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved file: {filename}"
    except Exception as e:
        return f"Error saving file: {e}"
    


