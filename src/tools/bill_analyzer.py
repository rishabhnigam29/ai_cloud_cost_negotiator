import json
from langchain_core.tools import tool


@tool
def analyze_bill(bill_path: str) -> str:
    """Load and analyze an AWS bill JSON file. Returns a structured breakdown
    of spending by service with resource-level details including utilization,
    storage usage, and pricing model."""
    bill_path = bill_path.strip("'\"")
    with open(bill_path) as f:
        bill = json.load(f)

    total = bill["total_cost"]
    services = sorted(bill["services"], key=lambda s: s["total_cost"], reverse=True)

    lines = [
        f"Account: {bill['account_name']}",
        f"Period: {bill['billing_period']}",
        f"Total: ${total:,.2f}/month",
        "",
        "=== Spend by Service ===",
    ]

    for svc in services:
        pct = (svc["total_cost"] / total) * 100
        lines.append(f"  {svc['service']}: ${svc['total_cost']:,.2f} ({pct:.1f}%)")

    lines.append("")
    lines.append("=== Resource Details ===")

    for svc in services:
        for item in svc.get("line_items", []):
            parts = [f"[{svc['service']}] {item['description']}: ${item.get('monthly_cost', 0):,.2f}"]

            if "avg_cpu_utilization" in item:
                parts.append(f"CPU: {item['avg_cpu_utilization']}%")
            if "avg_memory_utilization" in item:
                parts.append(f"Mem: {item['avg_memory_utilization']}%")
            if "pricing_model" in item:
                parts.append(f"Pricing: {item['pricing_model']}")
            if "hours_running" in item:
                parts.append(f"Hours: {item['hours_running']}")
            if "storage_gb" in item and "storage_used_gb" in item:
                usage_pct = (item["storage_used_gb"] / item["storage_gb"]) * 100
                parts.append(f"Storage: {item['storage_used_gb']}/{item['storage_gb']}GB ({usage_pct:.0f}%)")
            if "invocations" in item:
                parts.append(f"Invocations: {item['invocations']:,}")
            if "access_pattern" in item:
                parts.append(f"Access: {item['access_pattern']}")
            if "last_accessed_breakdown" in item:
                breakdown = item["last_accessed_breakdown"]
                parts.append(f">90 days: {breakdown.get('over_90_days', 'N/A')}")

            tags = item.get("tags", {})
            env = tags.get("Environment", "")
            if env:
                parts.append(f"Env: {env}")

            lines.append("  " + " | ".join(parts))

    return "\n".join(lines)