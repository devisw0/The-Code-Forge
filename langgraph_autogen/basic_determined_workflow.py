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
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage,HumanMessage
import operator
import requests
import os
from dotenv import load_dotenv
from balldontlie import BalldontlieAPI
from typing import Optional
from langgraph.graph import StateGraph, END





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

load_dotenv()

balldontlie_key = os.environ['BALLDONTLIE_API_KEY']

api = BalldontlieAPI(api_key=balldontlie_key)




class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str



def call_llm_for_routing(prompt):
    """Helper to call Bedrock LLM for routing decision"""
    
    messages = [{"role": "user", "content": prompt}]
    
    response = bedrock_client.create(
        messages=messages,
        max_tokens=100 #dont need alot of tokens, since im using this func for routing
    )
    
    return response.content


def intelligent_router(state: AgentState):
    """Router that uses Bedrock to make decisions"""
    
    last_message = state["messages"][-1]["content"]
    all_messages = state["messages"]
    
    routing_prompt = f"""
    Last message in conversation: "{last_message}"
    All messages in the conversation: {all_messages},
    
    Available agents:

    - researcher: does research on any topic
    - writer: writes polished content, can write based off research
    - football_fan: is able to use tools to provide information about nfl teams and players

    Which agent should respond next? Respond with ONLY: researcher, writer, football_fan, or END
   
    """
    
    decision = call_llm_for_routing(routing_prompt)
    return decision.strip().lower()


#_____________Tools__________________

def nfl_teams_info(division: Optional[str] = None, conference: Optional[str] = None):
    
    """
    division:	Returns teams that belong to this division

    conference:	Returns teams that belong to this conference

    example response from the api can be like this:

        {
    "data": [
        {
        "id": 18,
        "conference": "NFC",
        "division": "EAST",
        "location": "Philadelphia",
        "name": "Eagles",
        "full_name": "Philadelphia Eagles",
        "abbreviation": "PHI"
        },
        ...
    ]
    }
    
    """

    url = 'https://api.balldontlie.io//nfl/v1/teams'
    
    headers = {
        "Authorization": balldontlie_key
    }

    params = {
        "division":division,
        "conference":conference
    }

    response = requests.get(url=url,headers=headers,params=params)

    response.raise_for_status()

    return response.json()


def get_player_info(first_name: Optional[str] = None, last_name: Optional[str] = None, search: Optional[str] = None):
    
    """
    Fetches NFL players with specific priority:
    1. If 'search' is provided, ONLY 'search' will be used.
    2. Otherwise, 'first_name' and/or 'last_name' will be used.

    - Search returns players whose first or last name matches this value. 
        For example, ?search=lamar will return players that have 'lamar' in their first or last name.

    - first_name returns players whose first name matches this value. 
        For example, ?search=lamar will return players that have 'lamar' in their first name

    - last_name returns returns players whose last name matches this value. 
        For example, ?search=jackson will return players that have 'jackson' in their last name.


        example of api return format:

            {
    "data": [
        {
        "id": 33,
        "first_name": "Lamar",
        "last_name": "Jackson",
        "position": "Quarterback",
        "position_abbreviation": "QB",
        "height": "6' 2\"",
        "weight": "205 lbs",
        "jersey_number": "8",
        "college": "Louisville",
        "experience": "7th Season",
        "age": 27,
        "team": {
            "id": 6,
            "conference": "AFC",
            "division": "NORTH",
            "location": "Baltimore",
            "name": "Ravens",
            "full_name": "Baltimore Ravens",
            "abbreviation": "BAL"
        }
        },
        ...
    ],
    "meta": { "next_cursor": 25, "per_page": 25 }
    }
    """

    url = 'https://api.balldontlie.io/nfl/v1/players'

    headers = {
        "Authorization":balldontlie_key
    }

    params = {}

    
    if search is not None:
        #search term provided
        params = {'search': search}
    else:
        #if no search then using first and/or last name
        if first_name is not None:
            params['first_name'] = first_name
        if last_name is not None:
            params['last_name'] = last_name
            
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() 
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}") 
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")
    
    return None

    


researcher = AssistantAgent(
    name="researcher",
    model_client=bedrock_client,
    system_message="You gather information and research topics."
)

writer = AssistantAgent(
    name="writer",
    model_client=bedrock_client,
    system_message="You create polished content."
)

football_fan = AssistantAgent(
    name = 'football_fan',
    model_client=bedrock_client,
    system_message="You are a knowledgable football fan who is able to use tools",
    tools=[nfl_teams_info, get_player_info]
)

async def researcher_node(state: AgentState):
    messages = [{"role": "user", "content": msg.content} for msg in state["messages"]]
    
    response = await researcher.run(task=messages[-1]["content"])
    
    return {"messages": [HumanMessage(content=str(response))]}

async def writer_node(state: AgentState):

    messages = [{"role": "user", "content": msg.content} for msg in state["messages"]]

    response = await writer.run(task=messages[-1]["content"])

    return {"messages": [HumanMessage(content=str(response))]}

async def football_fan_node(state: AgentState):

    messages = [{"role": "user", "content": msg.content} for msg in state["messages"]]

    response = await football_fan.run(task=messages[-1]["content"])

    return {"messages": [HumanMessage(content=str(response))]}





workflow = StateGraph(AgentState)

# adding nodes
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("football_fan", football_fan_node)

#entry point node
workflow.set_entry_point("researcher")

#adding conditional edges
for agent_name in ["researcher", "writer", "football_fan"]:
    workflow.add_conditional_edges(
        agent_name, #from which node
        intelligent_router, #routing function
        {
            #router output map to the actual nodes

            "researcher": "researcher",
            "writer": "writer",
            "football_fan": "football_fan",
            "END": END
        }
    )

app = workflow.compile()

result = app.invoke({
    "messages": [HumanMessage(content="Tell me about Lamar Jackson")],
    "next": ""
})

print(result["messages"])