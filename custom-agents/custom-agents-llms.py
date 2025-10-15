import asyncio
from pydantic import Field, BaseModel
from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, MessageContext, message_handler, default_subscription, RoutedAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient,BedrockInfo, AnthropicBedrockChatCompletionClient
from autogen_core.models import ModelInfo, UserMessage


