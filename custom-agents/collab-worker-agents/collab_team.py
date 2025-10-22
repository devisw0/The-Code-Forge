import asyncio
from pydantic import Field, BaseModel
from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, MessageContext, message_handler, default_subscription, RoutedAgent,TopicId
from autogen_ext.models.anthropic import AnthropicChatCompletionClient, BedrockInfo, AnthropicBedrockChatCompletionClient
from autogen_core.models import ModelInfo, UserMessage
from autogen_agentchat.messages import TextMessage
import boto3
from autogen_agentchat.agents import AssistantAgent

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


