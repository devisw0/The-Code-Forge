from fastmcp import FastMCP
import httpx  # Replace requests with httpx for async support
import json

mcp_server = FastMCP(name='My MCP Server', instructions='This MCP Server will host tools to get dog breed data')

@mcp_server.tool
async def get_all_dog_breeds():
    
    """Gets a dictionary of all dog breeds and their sub-breeds."""

    url = 'https://dog.ceo/api/breeds/list/all'
    async with httpx.AsyncClient() as client:

        response = await client.get(url)

        formatted_request = response.json()

        formatted_request = formatted_request.get('message', 'not available')

        return formatted_request

@mcp_server.tool
async def get_breed_sub_breeds(dog_breed: str):
    """
    This tool will be used to get a dog breed's sub-breeds.
    
    Args:
        dog_breed (str): The dog breed to get sub-breeds for
         
    Return: 
        subbreeds (list): List of the subbreeds for this dog breed
    """
    url = f'https://dog.ceo/api/breed/{dog_breed}/list'

    async with httpx.AsyncClient() as client:

        response = await client.get(url)

        subbreeds = response.json()

        subbreeds = subbreeds.get('message', 'not available')

        return subbreeds

@mcp_server.tool
async def get_breed_image_random(dog_breed: str):
    """
    This tool will be used to get a random image of a specified dog breed
    
    Args:
        dog_breed (str): The dog breed to get an image for
        
    Return: 
        Image URL for the specified breed
    """
    url = f'https://dog.ceo/api/breed/{dog_breed}/images/random'
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        image_data = response.json()
        image_url = image_data.get('message', 'not found')
        return image_url

if __name__ == "__main__":
    mcp_server.run(transport="http", host="0.0.0.0", port=8000)