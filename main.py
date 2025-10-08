import os
from autogen import AssistantAgent
from typing_extensions import Annotated
import autogen
import json
from autogen_ext.models.anthropic import AnthropicBedrockChatCompletionClient
import asyncio

config_list_bedrock = [{
    "model": "anthropic.claude-sonnet-4-20250514-v1:0", 
    "api_type": "bedrock",
    "aws_region": os.environ.get("AWS_REGION", "us-east-1"),
}]

llm_config_claude = {
    "config_list": config_list_bedrock,
    "temperature": 0.1,
    "timeout": 120,
}

async def main():  # ⬅️ Add async here
    assistant = AssistantAgent(
        name="ClaudeAssistant",
        system_message="You are a meticulous developer...",
        llm_config=llm_config_claude,
    )
    
    result = await assistant.run(task="whats 9+9")  # ⬅️ Add await here
    print(result)
    print(result.messages)
    print(result.messages[-1].content)

if __name__ == '__main__':
    asyncio.run(main())  # ⬅️ Use asyncio.run()