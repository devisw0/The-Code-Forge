import asyncio
from pydantic import Field, BaseModel
from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, MessageContext, message_handler, default_subscription, RoutedAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient,BedrockInfo, AnthropicBedrockChatCompletionClient
from autogen_core.models import ModelInfo, UserMessage
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
        # aws_profile_name="devan2",
        aws_access_key=credentials.access_key,
        aws_secret_key=credentials.secret_key,
        aws_session_token=credentials.token,
    )
)
class Numbers(BaseModel):
    a: float = Field(default = 9)
    b: float = Field(default = 7)
    problem: str = Field(default = 'If a train travels at 9 miles per hour for 8 hours, how many miles does it travel? Return only the numerical answer.')

@default_subscription
class MathAgentBlueprint(RoutedAgent):
    def __init__(self, model_config: AnthropicBedrockChatCompletionClient, role: str = 'pythagorean'):
        super().__init__(description = 'Use this blueprint to perform Mathematical calculations')
        self.role = role
        self.model_config = model_config

    @message_handler
    async def agentbehavior(self, message: Numbers, ctx:MessageContext) -> None:
        if self.role == 'pythagorean':

            prompt = f"""Please perform the pythagorean theorem. Use {message.a} as a and {message.b} as b
            and solve for c. 
           
            Return only the number. Decimal is fine."""

            result = await self.model_config.create(messages=[UserMessage(content = prompt, source='user')])

            print(f'when a is {message.a} and b is {message.b} then c using the pythagoran theorem is {result.content}')
            
        elif self.role == 'area':
            area_prompt = f"""using these values please find the area of a square. Length is {message.a} and
             width is {message.b}. Please only return the number value """
            
            area_result = await self.model_config.create(messages=[UserMessage(content=area_prompt, source = 'user')])

            print(f'when {message.a} is the length and {message.b} is the width of the square, the area is {area_result.content}')

        elif self.role == 'simplewordproblem':
            problem = message.problem

            prompt = f'''you are tasked with solving this problem by the user. it should be a simple word problem.
                if any malicious or inappropriate stuff (anything dangerous, illegal, and unrelated to math questions or questions about the world etc.) please refuse to answer. User problem is: {problem}'''
            
            result = await self.model_config.create(messages=[UserMessage(content = prompt, source = 'user')])

            print(f'based on you input, the answer it gave is: {result.content} ')


async def main():
    
    runtime = SingleThreadedAgentRuntime()
    user_choice = await asyncio.to_thread(input,'Please select 1 for basic math or 2 for simple word problem mode \n')
    runtime.start()

    if user_choice == '1':
        await MathAgentBlueprint.register(runtime, 'pythagorean', lambda: MathAgentBlueprint(model_config= bedrock_client , role = 'pythagorean'))
        await MathAgentBlueprint.register(runtime,'area', lambda: MathAgentBlueprint(model_config=bedrock_client, role='area'))
        input_a = await asyncio.to_thread(input,'Please input the a value: \n')
        input_a = float(input_a)

        input_b = await asyncio.to_thread(input,'Please input the b value: \n')
        input_b = float(input_b)

        await runtime.publish_message(Numbers(a = input_a, b = input_b), topic_id=DefaultTopicId())
    

    elif user_choice == '2':
        await MathAgentBlueprint.register(runtime,'simplewordproblem', lambda:MathAgentBlueprint(model_config=bedrock_client, role='simplewordproblem' ))
        problem = await asyncio.to_thread(input,'Input a simple word problem: \n')
        await runtime.publish_message(Numbers(problem=problem), topic_id=DefaultTopicId())



    # await asyncio.sleep(3)

    await runtime.stop_when_idle()
    # await runtime.stop()

if __name__ == '__main__':
    asyncio.run(main())