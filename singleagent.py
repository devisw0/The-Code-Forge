import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.anthropic import AnthropicBedrockChatCompletionClient

async def main():
    model_client = AnthropicBedrockChatCompletionClient(
        model="us.anthropic.claude-sonnet-4-5-20250514-v1:0",
        bedrock_info={
            "aws_region": "us-east-1"  # ← Changed from "region"
        }
    )
    
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        description="A helpful assistant"
    )
    
    result = await assistant.run(task="What's 9+9?")
    print(result)

if __name__ == '__main__':
    asyncio.run(main())