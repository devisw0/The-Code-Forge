import asyncio
from pydantic import Field, BaseModel
from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, MessageContext, message_handler, default_subscription, RoutedAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient, BedrockInfo, AnthropicBedrockChatCompletionClient
from autogen_core.models import ModelInfo
from autogen_agentchat.messages import TextMessage 
import boto3
from autogen_agentchat.agents import AssistantAgent
from fastmcp import Client
import json


session = boto3.Session(profile_name='devan2')
credentials = session.get_credentials()


bedrock_client = AnthropicBedrockChatCompletionClient(
    model="anthropic.claude-3-5-sonnet-20240620-v1:0",
    temperature=0.7,
    model_info=ModelInfo(
        vision=False,
        function_calling=True,
        json_output=False,
        family="unknown",
        structured_output=True
    ),
    bedrock_info=BedrockInfo(
        aws_region="us-east-1",
        aws_access_key=credentials.access_key,
        aws_secret_key=credentials.secret_key,
        aws_session_token=credentials.token,
    )
)

DOG_MCP_MENU = """
[
  {
    "name": "get_all_dog_breeds",
    "description": "Gets a dictionary of all dog breeds and their sub-breeds."
  },
  {
    "name": "get_breed_sub_breeds",
    "description": "This tool will be used to get a dog breed's sub-breeds.",
    "parameters": {
      "properties": {
        "dog_breed": { "type": "string" }
      },
      "required": ["dog_breed"]
    }
  },
  {
    "name": "get_breed_image_random",
    "description": "This tool will be used to get a random image of a specified dog breed.",
    "parameters": {
      "properties": {
        "dog_breed": { "type": "string" }
      },
      "required": ["dog_breed"]
    }
  }
]
"""

system_prompt = f""" You are a helpful assistant which can be use tools specified to answer/fulfill user requests.

When the user asks a question plese first check if there is an available tool to help with it. The only way to access the tools listed
in DOG_MCP_MENU is by using our client funciton called 'dog_mcp'

Here is the DOG_MCP_MENU I spoke of:
Here is the JSON "menu" of all tools available on the remote server:
<tools>
{DOG_MCP_MENU}
</tools>

To call a tool, you have to respond with a JSON object in the following format:
{{
  "tool_name": "call_dog_api",
  "tool_args": {{
    "tool_name": "THE_REMOTE_TOOL_NAME_FROM_THE_MENU",
    "dog_breed": "THE_BREED_NAME_IF_NEEDED"
  }}
}}

For example, to get a random image of a hound, you would respond with:
{{
  "tool_name": "call_dog_api",
  "tool_args": {{
    "tool_name": "get_breed_image_random",
    "dog_breed": "hound"
  }}
}}

If no tool is needed, just answer the user's question directly.
"""

async def call_dog_mcp(tool_name: str, **kwargs) -> str:
    """
    A gateway to the Dog API server.
    
    Args:
        tool_name (str): The specific tool to call (example: 'get_breed_image_random').
        **kwargs: The arguments for that specific tool (example: dog_breed='hound').
    """
    SERVER_URL = "http://127.0.0.1:8000/mcp"
    print(f"\n [Gateway: Calling tool '{tool_name}' with args {kwargs}]")
    
    try:
        async with Client(SERVER_URL) as client:

            result = await client.call_tool(tool_name, **kwargs)

            return json.dumps(result)
            
    except Exception as e:
        return f"Error in Dog API gateway: {e}"