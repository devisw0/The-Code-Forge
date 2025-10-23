from fastmcp import FastMCP
import requests
import json

mcp_server = FastMCP(name = 'My MCP Server', instructions='This MCP Server will host tools to get financial data')

@mcp_server.tool
def get_all_dog_breeds():
    url = 'https://dog.ceo/api/breeds/list/all'
    request = requests.get(url = url)
    formatted_request = request.json()
    formatted_request = formatted_request.get('message', 'not available')
    
    return formatted_request

@mcp_server.tool
def get_breed_sub_breeds(dog_breed:str):
    """
    This tool will be used to get a dog breed's sub-breeds. For example Bulldog is a breed but a French, English and 
    Boston bull dogs are all sub-breed of bulldog.
    
    Args:
        dog_breed (str) this is the dog breed that we want to see if it has subbreeds
         
    Return: 
        subbreeds (list) this is a list of the subbreeds a specific dogbreed has. It may also have no subbreeds """
    url = f'https://dog.ceo/api/breed/{dog_breed}/list'
    request = requests.get(url = url)
    subbreeds = request.json()
    subbreeds = subbreeds.get('message','not available')
    return subbreeds


@mcp_server.tool
def get_breed_image_random(dog_breed:str):
   """
   This tool will be used to get a random image of a specified dog breed
   
   Args:
        dog_breed (str) this argument is used in the api request to get the image of the dog breed
    Return: 
        We will return the image url which will be under vaue of the message key in the response """
   
   url = f'https://dog.ceo/api/breed/{dog_breed}/images/random'

   image_request = requests.get(url=url)
   image_request = image_request.json()

   image_url = image_request.get('message', 'not found')

   return image_url


    
if __name__ == "__main__":
    mcp_server.run(transport="http", host="0.0.0.0", port=8000)
