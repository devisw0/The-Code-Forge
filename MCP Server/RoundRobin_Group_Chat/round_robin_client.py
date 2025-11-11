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



async def get_tools_info():
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
        print(f"[Tool Error: {e}]")
        return f"Error connecting to server or listing tools: {e}"
    

