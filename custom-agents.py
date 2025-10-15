# from typing import Optional
import asyncio
from pydantic import BaseModel, Field

# from autogen_agentchat.agents import RoutedAgent
from autogen_core import SingleThreadedAgentRuntime, DefaultTopicId, MessageContext, message_handler, default_subscription, RoutedAgent




class Values(BaseModel):
    a:int = Field(default=10)
    b:int = Field(default=10)



@default_subscription
class Mathematics(RoutedAgent):
    def __init__(self, role_description: str = 'add'):
        super().__init__(description=f"Mathematics agent that performs {role_description} operations")
        self.role_description = role_description

    @message_handler
    async def calculate(self, message:Values, ctx: MessageContext) -> None:
        if self.role_description == 'add':
            total = message.a + message.b
            print(total)
        elif self.role_description == 'subtract':
            total = message.a - message.b
            print(total)
        


async def main():
    runtime = SingleThreadedAgentRuntime()

    await Mathematics.register(runtime, "adder", lambda: Mathematics('add'))
    await Mathematics.register(runtime, "subtractor", lambda: Mathematics('subtract'))

    runtime.start()

    await runtime.publish_message(Values(a = 7, b = 10),topic_id=DefaultTopicId())

    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())


