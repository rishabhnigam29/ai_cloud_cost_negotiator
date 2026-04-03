# AI Cloud Cost Negotiator

An AI agent that analyzes your AWS bill, finds savings, drafts a negotiation email, and simulates the negotiation with two AI agents.

## Setup

```bash
cd 02_cost_negotiator
uv sync
cp .env.example .env
# Add your OpenAI API key to .env
```

## Run

```bash
# Full pipeline: analysis + negotiation simulation
uv run python run.py

# Just analyze the bill
uv run python run.py --analyze-only

# Just run the negotiation simulation
uv run python run.py --negotiate-only
```

## Architecture

```
ReAct Agent Loop:
  Think → Pick Tool → Read Result → Think Again → ... → Final Answer
  (Agent decides which tools to call and in what order)

Negotiation Simulator (separate):
  Customer Agent <-> AWS Rep Agent (multi-round dialogue with hidden constraints)
```

The agent uses the ReAct pattern — it reasons about what to do, picks a tool, observes the result, and repeats until it has enough information to deliver a complete analysis with a negotiation email.

## Tools

| Tool | What it does |
|------|-------------|
| `analyze_bill` | Parses AWS bill JSON, extracts cost breakdown by service with utilization data |
| `find_savings` | Scans for zombies, oversized instances, missing RIs, orphaned volumes, S3 lifecycle gaps |

The agent uses these two tools to gather data, then writes the negotiation email and action plan itself as its final answer.

## Stack

- Python 3.11+
- LangChain ReAct Agent (reasoning + tool use)
- OpenAI GPT-4o (LLM)
- Pydantic (structured output)
- Rich (terminal UI)
