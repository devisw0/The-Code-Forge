import asyncio
from pydantic import Field, BaseModel
from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, MessageContext, message_handler, default_subscription, RoutedAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient, BedrockInfo, AnthropicBedrockChatCompletionClient
from autogen_core.models import ModelInfo
from autogen_agentchat.messages import TextMessage
import boto3
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from fastmcp import Client
import json
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat

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

# system_prompt = f""" You are a helpful assistant which can be use tools specified to answer/fulfill user requests.

# When the user asks a question plese first check if there is an available tool to help with it. The only way to access the tools listed
# in DOG_MCP_MENU is by using our client funciton called 'dog_mcp'

# Here is the DOG_MCP_MENU I spoke of:
# Here is the JSON "menu" of all tools available on the remote server:
# <tools>
# {DOG_MCP_MENU}
# </tools>

# If you would like another way to view the tools, please execute the get_dog_mcp_tools function

# To call a tool, you have to respond with a JSON object representing the call to the *local* 'call_dog_mcp' function. The arguments for 'call_dog_mcp' are 'tool_name' (the name of the *remote* tool from the menu) and any arguments required by that remote tool (like 'dog_breed').

# For example, to get a random image of a hound, you would respond with:
# {
#   "tool_name": "call_dog_mcp",
#   "tool_args": {
#     "tool_name": "get_breed_image_random",
#     "dog_breed": "hound"
#   }
# }

# If no tool is needed, just answer the user's question directly.
# """

system_prompt = """You are a helpful assistant with access to Dog API tools via an MCP server.

You have access to:
- get_dog_mcp_tools(): Lists available tools on the server
- call_dog_mcp(tool_name, **kwargs): Calls a remote tool

Remote tools available via call_dog_mcp:
- tool_name="get_all_dog_breeds": Gets dictionary of all breeds/sub-breeds
- tool_name="get_breed_sub_breeds", dog_breed="<breed>": Gets sub-breeds for a breed  
- tool_name="get_breed_image_random", dog_breed="<breed>": Gets random image URL

Use call_dog_mcp to access these remote tools.
"""

async def get_dog_mcp_tools():
    """
    Tool used to get information about the tools available in dog_mcp
    
    Args:
      None

    Return:
      List of available tools"""
    try:
      SERVER_URL = "http://127.0.0.1:8000/mcp"
      async with Client(SERVER_URL) as client:
      
        tools = await client.list_tools()

        return tools
    
    except Exception as e:
        print(f"... [Tool Error: {e}] ...")
        return f"Error connecting to server or listing tools: {e}"
  


async def call_dog_mcp(tool_name: str, dog_breed:str) -> str:
    """
    A gateway to the Dog API server.
    
    Args:
        tool_name (str): The specific tool to call (example: 'get_breed_image_random').
        **kwargs: The arguments for that specific tool (example: dog_breed='hound').
    """

    SERVER_URL = "http://127.0.0.1:8000/mcp"

    kwargs = {}
    if dog_breed:
        kwargs['dog_breed'] = dog_breed

    print(f"\n [Gateway: Calling tool '{tool_name}' with args {kwargs}]")
    
    try:
        async with Client(SERVER_URL) as client:
            
            await client.ping()

            #** to unpack dictionary 
            result = await client.call_tool(tool_name, **kwargs)

            return json.dumps(result)
           
    except Exception as e:
        return f"Error in Dog API gateway: {e}"
    

async def main():
    dog_history_agent = AssistantAgent(
        name='Dog_History_Agent',
        description='Provides historical information about dog breeds and sub-breeds',
        system_message="You are a helpful assistant that gives information about dog breeds and their history.",
        model_client=bedrock_client
    )

    dog_mcp_agent = AssistantAgent(
        name='dog_mcp_agent',
        description='Uses Dog API tools to fetch breed data, sub-breeds, and images',
        system_message=system_prompt,
        model_client=bedrock_client,
        tools=[get_dog_mcp_tools, call_dog_mcp]
    )

    selector_prompt = """
    Select the appropriate agent:
    - Dog_History_Agent: For questions about breed history and characteristics
    - dog_mcp_agent: For fetching breed lists, sub-breeds, or images using the Dog API
    """

    selectorgc = SelectorGroupChat(
        participants=[dog_history_agent, dog_mcp_agent],
        model_client=bedrock_client,
        selector_prompt=selector_prompt
    )

    user_question = await asyncio.to_thread(input, 'What do you want to ask about a dog breed? ')
    result = await selectorgc.run(task=user_question)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())

