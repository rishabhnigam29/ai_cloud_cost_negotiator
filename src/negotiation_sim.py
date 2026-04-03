"""Multi-agent negotiation simulator.

Two LLM agents — a Customer and an AWS Sales Rep — negotiate credits/discounts
based on the savings analysis. This is the theatrical demo moment for the video.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from rich.console import Console
from rich.panel import Panel

from src.config import get_llm

console = Console()

CUSTOMER_SYSTEM = """You are a savvy cloud customer negotiating with AWS for credits and discounts.

Your situation:
- Monthly AWS bill: ${total_bill:,.0f}/month (${annual_bill:,.0f}/year)
- You've identified ~${savings:,.0f}/month in optimization opportunities
- You want AWS credits to offset migration costs
- Your opening ask: ${ask:,.0f} in credits
- Your minimum acceptable: ${minimum:,.0f} in credits
- You're willing to commit to 1-year Reserved Instances as leverage

Negotiation tactics:
- Start firm but professional
- Mention you're evaluating GCP/Azure (even if you're not seriously)
- Emphasize your growth trajectory — you're a growing account
- If they lowball, counter with specific technical commitments (RIs, support tier upgrade)
- Don't accept less than your minimum without getting something else (free support, training credits)

Keep responses concise (2-4 sentences). Be realistic and professional.
Do NOT reveal your minimum acceptable amount."""

AWS_REP_SYSTEM = """You are an AWS account manager negotiating with a customer requesting credits.

The customer's account:
- Monthly spend: ${total_bill:,.0f}/month
- They've done a thorough cost analysis and found optimizations
- They're asking for credits to offset optimization migration costs

Your constraints:
- You can offer up to ${max_credit:,.0f} in credits (but start lower)
- You'd prefer to offer Reserved Instance discounts over direct credits
- You want to retain the customer and grow the account
- End of quarter — you have some extra flexibility on credits

Negotiation tactics:
- Start by acknowledging their analysis (shows respect)
- First offer should be about 40% of their ask
- Push them toward RI commitments (locks in revenue for AWS)
- If they mention competitors, take it seriously but don't panic
- Offer non-monetary value: AWS support upgrade, solution architect time, training credits
- Find a win-win — you want them to feel good about staying with AWS

Keep responses concise (2-4 sentences). Be realistic and professional."""


def run_negotiation(
    total_bill: float = 1847.63,
    savings_found: float = 400.0,
    ask_amount: float = 1200.0,
    minimum_amount: float = 600.0,
    max_rounds: int = 6,
) -> None:
    """Run a multi-agent negotiation simulation."""

    customer_llm = get_llm(temperature=0.7)
    aws_llm = get_llm(temperature=0.7)

    annual_bill = total_bill * 12
    max_credit = ask_amount * 0.75  # AWS can go up to 75% of ask

    customer_system = CUSTOMER_SYSTEM.format(
        total_bill=total_bill,
        annual_bill=annual_bill,
        savings=savings_found,
        ask=ask_amount,
        minimum=minimum_amount,
    )

    aws_system = AWS_REP_SYSTEM.format(
        total_bill=total_bill,
        max_credit=max_credit,
    )

    customer_messages = [SystemMessage(content=customer_system)]
    aws_messages = [SystemMessage(content=aws_system)]

    # Customer opens
    console.print()
    console.print(Panel("[bold]NEGOTIATION SIMULATOR[/bold]\nCustomer vs AWS Account Manager", style="cyan"))
    console.print()

    customer_opener = customer_llm.invoke(
        customer_messages + [
            HumanMessage(content=(
                "Start the negotiation. Introduce yourself, reference your cost analysis, "
                "and make your opening ask for credits. Be direct but professional."
            ))
        ]
    )

    customer_messages.append(customer_opener)
    _print_message("Customer", customer_opener.content, "green")

    for round_num in range(max_rounds):
        # AWS responds
        aws_messages.append(HumanMessage(content=f"Customer says: {customer_opener.content}"))
        aws_response = aws_llm.invoke(aws_messages)
        aws_messages.append(aws_response)
        _print_message("AWS Rep", aws_response.content, "yellow")

        # Check if deal is done
        if _is_deal_closed(aws_response.content):
            break

        # Customer responds
        prompt = f"AWS rep says: {aws_response.content}"
        if round_num == max_rounds - 1:
            prompt += "\n\nThis is the final round. Make your best final offer or accept their last proposal."

        customer_messages.append(HumanMessage(content=prompt))
        customer_opener = customer_llm.invoke(customer_messages)
        customer_messages.append(customer_opener)
        _print_message("Customer", customer_opener.content, "green")

        if _is_deal_closed(customer_opener.content):
            break

    console.print()
    console.print(Panel("[bold]NEGOTIATION COMPLETE[/bold]", style="cyan"))


def _print_message(speaker: str, message: str, color: str):
    console.print()
    console.print(Panel(
        message,
        title=f"[bold {color}]{speaker}[/bold {color}]",
        border_style=color,
        padding=(1, 2),
    ))


def _is_deal_closed(message: str) -> bool:
    close_signals = ["deal", "agree", "accept", "let's move forward", "sounds good", "we have a deal"]
    message_lower = message.lower()
    return any(signal in message_lower for signal in close_signals)