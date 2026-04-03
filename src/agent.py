"""ReAct agent that analyzes AWS bills and drafts a negotiation strategy."""

from langchain.agents import create_agent

from src.config import get_llm
from src.tools.bill_analyzer import analyze_bill
from src.tools.savings_finder import find_savings


SYSTEM_PROMPT = """You are an expert AWS cost optimization consultant.

You have access to tools that help you analyze AWS bills and find savings.
Use them to build a complete picture, then deliver your recommendations.

Your workflow:
1. First, call analyze_bill to understand the current spend breakdown
2. Then, call find_savings to identify specific optimization opportunities
3. Finally, using everything you've learned, write a negotiation email to AWS

For the negotiation email:
- Address it to "AWS Account Team"
- Reference the annual spend to show account value
- List the top 3-5 specific findings (with dollar amounts)
- Ask for credits equal to ~3 months of identified savings
- Mention willingness to commit to Reserved Instances as leverage
- Include internal negotiation notes (opening ask, minimum acceptable, tactics)

Be specific with numbers. Don't make up data — only use what the tools return."""


def run_agent(bill_path: str) -> str:
    """Run the ReAct cost optimization agent. Returns the agent's final answer."""
    llm = get_llm()
    tools = [analyze_bill, find_savings]

    agent = create_agent(
        llm,
        tools,
        system_prompt=SYSTEM_PROMPT,
        debug=False
    )

    result = agent.invoke({
        "messages": [(
            "human",
            f"Analyze the AWS bill at '{bill_path}', find all savings opportunities, "
            f"then write a professional negotiation email I can send to my AWS account manager. "
            f"Include an internal-only section with negotiation tactics."
        )]
    })

    # Extract output from the result
    if isinstance(result, dict) and "messages" in result:
        last_message = result["messages"][-1]
        return last_message.content if hasattr(last_message, "content") else str(last_message)

    return str(result)