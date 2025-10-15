import asyncio
from pydantic import Field, BaseModel
from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, MessageContext, message_handler, default_subscription, RoutedAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient,BedrockInfo, AnthropicBedrockChatCompletionClient
from autogen_core.models import ModelInfo, UserMessage

# config_list = {
#     "model": 'anthropic.claude-3-5-sonnet-20240620-v1:0',  
#     # "api_type": "bedrock",
#     "aws_region": "us-east-1",
#     "aws_profile_name": "devan2"
# }

# llm_config = {"config_list": config_list, "cache_seed": 42}

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
        # aws_profile_name="devan2"  # Try without this first - should auto-detect SSO
    )
)

class customervibe(BaseModel):
    name: str = Field(default = 'Applewood')
    keynotes: str = Field(default= 'Apple, Woody')
    target: str = Field(default = 'Fall')


@default_subscription
class FragranceAgent(RoutedAgent):
    def __init__(self, model_client: AnthropicBedrockChatCompletionClient, task: str = 'add'):            
            super().__init__(description=f"This agent will be doing {task}")
            self.task = task
            self.model_client = model_client
    @message_handler
    async def Process(self, message:customervibe, ctx: MessageContext):
        if self.task == 'marketingcopyagent':

            prompt = f"""Create compelling marketing copy for "{message.name}". Key Notes: {message.keynotes}

            Target: {message.target}. Write about these ingrediants and their significance. Also include relation to target"""

            response = await self.model_client.create(
                messages=[UserMessage(content=prompt, source="user")]
            )

            print(f'Marketing Blurb: {response}')

        elif  self.task == 'ingredientstoryagent':

            prompt = f"""Write a short, compelling story about the origin or sourcing of 
            a key ingredient in {message.keynotes}"""

            response = await self.model_client.create(messages=[UserMessage(content = prompt, source = 'user')])

            print(f'Ingrediant Story: {response}')
        
        # elif self.task == 'imagegeneration':
            #prompt = f""create a prompt which can be used for the ___ image generation api that reflect what was
            # inputted for the {message.name} , {message.keynotes} and {message.target}""
            
            #response = await self.model_client.create(messages=[UserMessage(content = prompt, source = 'user')])


            #image generation api?, repsonse for prompt

async def main():
    runtime = SingleThreadedAgentRuntime()

    await FragranceAgent.register(runtime, 'marketingcopyagent', lambda:FragranceAgent('marketingcopyagent') )
    await FragranceAgent.register(runtime, 'ingredientstoryagent', lambda:FragranceAgent('ingredientstoryagent') )
    
    runtime.start()

    task_map = {
        '1': 'marketingcopyagent',
        '2': 'ingredientstoryagent'
    }

    FragranceName = input('input hypothetical fragrance')


    await runtime.publish_message(customervibe(name=FragranceName,keynotes='Woody',target='Fall'))

    await runtime.stop_when_idle()


                

        
    



