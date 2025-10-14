import autogen

config_list = [{
    "model": 'anthropic.claude-3-5-sonnet-20240620-v1:0',  
    "api_type": "bedrock",
    "aws_region": "us-east-1",
    "aws_profile_name": "devan2"
}]

#assistant agent instance from autogen (performs task vs user proxy serves as poc form user and communicates back)
assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={"config_list": config_list}
)

#user proxy (user)
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False
)

# Start a conversation
print("Starting conversation with Bedrock-powered agent...\n")

user_proxy.initiate_chat(
    assistant,
    message="Hello! What's the capital of France? Please be brief."
)

print("\n✅ Success! Your first AutoGen + Bedrock agent works!")