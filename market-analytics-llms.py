import autogen
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests

#llm config
config_list = [{
    "model": 'anthropic.claude-3-5-sonnet-20240620-v1:0',  
    "api_type": "bedrock",
    "aws_region": "us-east-1",
    "aws_profile_name": "devan2"
}]

llm_config = {"config_list": config_list, "cache_seed": 42}


def get_company_news(company_name: str) -> str:
    """
    Searches online for recent news about a given company
    and returns the top 3 headlines.
    """
    # Print a message to the console to show the tool is running
    print(f"\n EXECUTING TOOL: get_company_news for {company_name} \n")
    
    results = []
    try:
        # Use DuckDuckGo Search to find news articles
        with DDGS() as ddgs:
            search_results = list(ddgs.news(f"{company_name} business news", max_results=5))

        if not search_results:
            return f"No recent news found for {company_name}."

        # Format the top 3 headlines
        for i, result in enumerate(search_results[:3]):
            results.append(f"{i+1}. {result['title']}")
        
        return "\n".join(results)
    except Exception as e:
        return f"An error occurred while searching for news: {e}"



#Agents

#user proxy excutres functions (if needed) and acts as poc for user to agents
user_proxy = autogen.UserProxyAgent(
    name="VP_of_Innovation",
    system_message="A human executive who wants a market analysis for a new product.",
    code_execution_config=False,
    code_execution_config={"work_dir": "coding"},
    human_input_mode="NEVER",
    # **** CHANGE 1: ADD TERMINATION LOGIC ****
    # This tells the UserProxy that if it sees a message with "TERMINATE" in it, the task is done.
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)

#Market Researcher agent
researcher = autogen.AssistantAgent(
    name="Market_Researcher",
    llm_config=llm_config,
    # **** CHANGE 2: MAKE THE PROMPT MORE RESTRICTIVE ****
    system_message="""You are a market researcher. Your job is to brainstorm a plausible target audience, 
    potential competitors, and key market trends for a given product.
    Provide your findings in a structured list.
    DO NOT perform any other tasks like SWOT analysis or writing a report. Your turn ends after you provide the research.
    """,
)

#SWOT Analyst agent
swot_analyst = autogen.AssistantAgent(
    name="SWOT_Analyst",
    llm_config=llm_config,
    # **** CHANGE 3: MAKE THE PROMPT MORE RESTRICTIVE ****
    system_message="""You are a business analyst. Your job is to take the market research findings
    and create a structured SWOT analysis (Strengths, Weaknesses, Opportunities, Threats).
    Only perform the SWOT analysis. Do not critique it or write a final report.

    You also have a tool called 'get_company_news'. Use it for searching up major competing companies
    """,
)

# Critique agent
critique = autogen.AssistantAgent(
    name="Critique",
    llm_config=llm_config,
    # **** CHANGE 4: MAKE THE PROMPT MORE RESTRICTIVE ****
    system_message="""You are a skeptical venture capitalist. Your job is to review the SWOT analysis.
    Challenge at least one point in the analysis with a constructive question or a potential blind spot.
    Your feedback should be concise and aimed at strengthening the final report.
    After your critique, say 'The analysis is ready for final report.' DO NOT write the report yourself.
    """,
)

#Report agent
report_writer = autogen.AssistantAgent(
    name="Report_Writer",
    llm_config=llm_config,
    system_message="""You are a professional business writer. Your job is to take the entire conversation history,
    including the initial research, the SWOT analysis, and the critique, and write a final, polished
    executive summary. The summary should be concise (under 250 words) and ready for a board meeting.
    After your summary, you MUST end your message with the single word 'TERMINATE'.
    """,
)

autogen.register_function(
    get_company_news,
    caller=swot_analyst,       # The agent that can ask to use the tool
    executor=user_proxy,        # The agent that will run the tool
    description="Search for recent news about a company to inform the SWOT analysis.",
)


#making manager, and gc
agents = [user_proxy, researcher, swot_analyst, critique, report_writer]

groupchat = autogen.GroupChat(
    agents=agents,
    messages=[],
    max_round=12, 
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config,
    system_message="""You are a project manager. Your job is to manage the conversation flow between the agents.
    The goal is to produce a market analysis report.
    The required flow is: Research -> SWOT Analysis -> Critique -> Final Report.
    Do not speak unless you need to steer the conversation.
    The conversation ends when the Report_Writer says 'TERMINATE'.
    """,
)


#user can input what we want to do market analysis for
product = input("Enter the product or topic for market analysis")

#initiating groupchat with initialization message
user_proxy.initiate_chat(
    manager,
    message=f"""Team, our new fictional product is {product}: \n.
    Please conduct a market analysis, create a SWOT report, get it critiqued, and deliver a final summary report.
    """,
)

print("\n\n chat log")
for msg in groupchat.messages:
    speaker = msg['name']
    content = msg['content'].strip()
    print(f"-> {speaker}:\n{content}\n")