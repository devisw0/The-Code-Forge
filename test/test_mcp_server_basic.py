from fastmcp import FastMCP
from fastapi import FastAPI  # Import the "Mall"

# 1. Create the main "Mall" app
app = FastAPI(title="My Test App")

# 2. Create the "Store" (your mcp object)
mcp = FastMCP("My Server")

@mcp.tool
def process_data(input: str) -> str:
    """Process data on the server"""
    return f"Processed: {input}"

# 3. "Mount" the store inside the mall at the /mcp path
app.mount("/mcp", mcp)

# 4. We no longer use mcp.run(). The file ends here.
# Uvicorn will run the 'app' object.