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

dog_mcp_agent_prompt = f"""You handle requests for dog images and breed data using the Dog API.

  You have access to these local functions:
  - get_dog_mcp_tools(): Lists available tools on the server
  - call_dog_mcp(tool_name, dog_breed): Gateway function to call remote MCP server tools

  Here are the remote tools available on the MCP server (accessed via call_dog_mcp):
  {DOG_MCP_MENU}

  CRITICAL RULES:
  1. Only call the EXACT tool the user requests
  2. Do not call multiple tools unless explicitly asked
  3. If user asks for an image, use call_dog_mcp with tool_name="get_breed_image_random"
  4. If user asks for sub-breeds, use call_dog_mcp with tool_name="get_breed_sub_breeds"
  5. If user asks for all breeds, use call_dog_mcp with tool_name="get_all_dog_breeds"

  Remember: You must use call_dog_mcp() to access the MCP server tools. Pass the tool_name and any required parameters like dog_breed.

  After getting results, present them clearly to the user.
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
  


async def call_dog_mcp(tool_name: str, dog_breed:str | None = None) -> str:
    """
    A gateway to the Dog API server.
    
    Args:
        tool_name (str): The specific tool to call (example: 'get_breed_image_random').
        dog_breed (str | None): The dog breed parameter (optional).
    """

    SERVER_URL = "http://127.0.0.1:8000/mcp"

    kwargs = {}
    if dog_breed:
        kwargs['dog_breed'] = dog_breed

    print(f"\n Calling tool '{tool_name}' with args {kwargs}]")
    print(f"\n[DEBUG] Calling tool '{tool_name}' with args {kwargs}")
    
    try:
        async with Client(SERVER_URL) as client:
            await client.ping()

            #kwargs unpacked internally, arguments param has to be a dictionary format
            result = await client.call_tool(tool_name, arguments=kwargs)
            
            print(f"[DEBUG] Raw result type: {type(result)}")
            print(f"[DEBUG] Raw result: {result}")
            
            # content is the actual message portion
            if result.content and len(result.content) > 0:
                
                #first content option
                actual_data = result.content[0].text

                print(f"[DEBUG] Extracted data: {actual_data}")
                return actual_data
            else:
                return "No data returned from MCP server"
            
    except Exception as e:
        
        error_msg = f"Error in Dog API gateway: {e}"

        print(f"[DEBUG] {error_msg}")
        
        return error_msg
    

async def main():
    dog_history_agent = AssistantAgent(
        name='Dog_History_Agent',
        description='Provides historical information about dog breeds and sub-breeds',
        system_message="You provide historical information about dog breeds.",
        model_client=bedrock_client
    )

    dog_mcp_agent = AssistantAgent(
        name='dog_mcp_agent',
        description='Fetches dog breed data, sub-breeds, and images from the Dog API via MCP server',  
        system_message=dog_mcp_agent_prompt,
        model_client=bedrock_client,
        tools=[get_dog_mcp_tools, call_dog_mcp]
    )

    selector_prompt = """Select the appropriate agent based on the user's question:

    - Dog_History_Agent: For questions about breed history, characteristics, or general information
    - dog_mcp_agent: For requests to fetch/show breed lists, sub-breeds, or images from the Dog API

    If the user asks about history or characteristics, choose Dog_History_Agent.
    If the user asks to get/show/fetch breed data, lists, sub-breeds, or images, choose dog_mcp_agent.
    """

    selectorgc = SelectorGroupChat(
        participants=[dog_history_agent, dog_mcp_agent],
        model_client=bedrock_client,
        selector_prompt=selector_prompt,
        max_turns=3
    )

    user_question = await asyncio.to_thread(input, 'What do you want to ask about a dog breed? \n')

    print(f"\n=== USER QUESTION: {user_question} ===\n")

    try:
      async with asyncio.timeout(60):
          
          result = await selectorgc.run(task=user_question)

          print(f"\n FINAL RESULT")

          if result.messages:
                
            print(result.messages[-1].content)

    except asyncio.TimeoutError:
        
        print("\n timeout: SelectorGroupChat took more than 60 seconds")

if __name__ == "__main__":
    asyncio.run(main())

