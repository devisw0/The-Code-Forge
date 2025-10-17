import asyncio
from pydantic import Field, BaseModel
from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, MessageContext, message_handler, default_subscription, RoutedAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient, BedrockInfo, AnthropicBedrockChatCompletionClient
from autogen_core.models import ModelInfo
from autogen_agentchat.messages import TextMessage 
import boto3
from yfinance_tools import price, historical_data, get_option_dates
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

class StockPriceRequest(BaseModel):

    company: str = Field(description="The stock ticker symbol, e.g., 'MSFT'")

class HistoricalDataRequest(BaseModel):

    company: str = Field(description="The stock ticker symbol, e.g., 'GOOGL'")

    period: str = Field(default="1y", description="The time period, e.g., '1y', '6mo'")


@default_subscription
class pricechecker(RoutedAgent):

    def __init__(self, model_config):

        super().__init__(description="Checks stock prices")

        self.assistant = AssistantAgent(
            name="price_assistant",
            model_client=model_config,
            tools=[price],
            system_message="Get current stock price using the price tool."
        )

    @message_handler
    async def process(self, message: StockPriceRequest, ctx: MessageContext) -> None:  
        print(f"[Price Checker] Processing {message.company}")

        response = await self.assistant.on_messages(
            [TextMessage(content=f"Get price for {message.company}", source='user')], 
            cancellation_token=ctx.cancellation_token)

        print(f"[Price Checker] Result: {response.chat_message.content}\n")


@default_subscription
class HistoricalAnalyzer(RoutedAgent):

    def __init__(self, model_config):

        super().__init__(description="Analyzes historical data")

        self.assistant = AssistantAgent(
            name="historical_assistant",
            model_client=model_config,
            tools=[historical_data],
            system_message="Fetch and analyze 1 year historical data."
        )

    @message_handler
    async def process(self, message: StockPriceRequest, ctx: MessageContext) -> None:

        print(f"[Historical Analyzer] Processing {message.company}")

        response = await self.assistant.on_messages(
            [TextMessage(content=f"Get 1y historical data for {message.company}", source='user')], 
            cancellation_token=ctx.cancellation_token)
        # top_10 = response.chat_message.content[10:100]
        print(f"[Historical Analyzer] Result: {response.chat_message.content}\n")


@default_subscription
class OptionsTracker(RoutedAgent):

    def __init__(self, model_config):

        super().__init__(description="Tracks option dates")

        self.assistant = AssistantAgent(
            name="options_assistant",
            model_client=model_config,
            tools=[get_option_dates],
            system_message="Get option expiration dates."
        )
   
    @message_handler
    async def process(self, message: StockPriceRequest, ctx: MessageContext) -> None:

        print(f"[Options Tracker] Processing {message.company}")

        response = await self.assistant.on_messages(
            [TextMessage(content=f"Get option dates for {message.company}", source='user')],  
            cancellation_token=ctx.cancellation_token)

        print(f"[Options Tracker] Result: {response.chat_message.content}\n")

async def main():
    runtime = SingleThreadedAgentRuntime()
    
    await pricechecker.register(runtime, "price_checker", lambda: pricechecker(bedrock_client))

    await HistoricalAnalyzer.register(runtime, "historical_analyzer", lambda: HistoricalAnalyzer(bedrock_client))

    await OptionsTracker.register(runtime, "options_tracker", lambda: OptionsTracker(bedrock_client))
    
    runtime.start()
    
    ticker = await asyncio.to_thread(input, "Enter stock ticker: ")

    print(f"Publishing single message for {ticker}\n")
    
    await runtime.publish_message(
        StockPriceRequest(company=ticker.upper()),
        topic_id=DefaultTopicId()
    )
    
    await runtime.stop_when_idle()

if __name__ == '__main__':
    asyncio.run(main())