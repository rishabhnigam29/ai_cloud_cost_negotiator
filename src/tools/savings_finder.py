import json
from langchain_core.tools import tool


@tool
def find_savings(bill_path: str) -> str:
    """Scan AWS bill data for cost savings opportunities using heuristic rules.
    Checks for: zombie resources, oversized instances, Reserved Instance candidates,
    Spot Instance candidates, over-provisioned storage, S3 lifecycle gaps,
    orphaned volumes, and unused Lambda functions.
    Returns raw findings for the agent to interpret and prioritize."""
    bill_path = bill_path.strip("'\"")
    with open(bill_path) as f:
        bill = json.load(f)

    findings = []

    for svc in bill["services"]:
        for item in svc.get("line_items", []):
            name = item["description"]
            cost = item.get("monthly_cost", 0)
            cpu = item.get("avg_cpu_utilization")
            mem = item.get("avg_memory_utilization")

            # Zombie resources — near-zero utilization
            if cpu is not None and cpu < 5 and mem is not None and mem < 10:
                findings.append(
                    f"ZOMBIE: {name} (${cost:.2f}/mo) — CPU: {cpu}%, Mem: {mem}%"
                )

            # Oversized instances — low but not zero usage
            if cpu is not None and 5 <= cpu < 25 and cost > 50:
                findings.append(
                    f"OVERSIZED: {name} (${cost:.2f}/mo) — CPU: {cpu}%, Mem: {mem}%"
                )

            # Reserved Instance candidates — high steady usage on on-demand
            if (cpu is not None and cpu > 60
                    and item.get("pricing_model") == "on_demand"
                    and item.get("hours_running", 0) >= 672):
                savings = cost * 0.35
                findings.append(
                    f"RI CANDIDATE: {name} (${cost:.2f}/mo) — {cpu}% CPU, "
                    f"{item['hours_running']}hrs on-demand. ~${savings:.2f}/mo savings with 1yr RI"
                )

            # Spot candidates — batch/training workloads
            if ("training" in name.lower() or "batch" in name.lower()) and item.get("pricing_model") == "on_demand":
                findings.append(
                    f"SPOT CANDIDATE: {name} (${cost:.2f}/mo) — batch/training workload on on-demand"
                )

            # Over-provisioned storage
            storage_total = item.get("storage_gb")
            storage_used = item.get("storage_used_gb")
            if storage_total and storage_used and (storage_used / storage_total) < 0.4:
                findings.append(
                    f"OVER-PROVISIONED STORAGE: {name} — {storage_used}GB used of {storage_total}GB"
                )

            # S3 lifecycle opportunities
            breakdown = item.get("last_accessed_breakdown")
            if breakdown:
                old_pct = float(breakdown.get("over_90_days", "0%").replace("%", ""))
                if old_pct > 50:
                    findings.append(
                        f"S3 LIFECYCLE: {name} (${cost:.2f}/mo) — {old_pct}% data unaccessed 90+ days"
                    )

            if item.get("access_pattern") == "rare":
                findings.append(f"S3 COLD DATA: {name} (${cost:.2f}/mo) — rarely accessed")

            # Orphaned resources
            if "unattached" in name.lower() or "orphaned" in name.lower():
                findings.append(f"ORPHANED: {name} (${cost:.2f}/mo) — not attached to anything")

            # Lambda issues
            if "function" in name.lower():
                invocations = item.get("invocations", 0)
                mem_mb = item.get("memory_mb")
                if invocations == 0:
                    findings.append(f"UNUSED LAMBDA: {name} — zero invocations")
                elif mem_mb and mem_mb >= 1024 and cost > 10:
                    findings.append(f"LAMBDA OVER-PROVISIONED: {name} (${cost:.2f}/mo) — {mem_mb}MB allocated")

            # Idle load balancers
            if "load balancer" in name.lower() and item.get("tags", {}).get("Environment") == "staging":
                findings.append(f"IDLE LB: {name} (${cost:.2f}/mo) — staging with minimal traffic")

    if not findings:
        return "No obvious savings found. Infrastructure looks well-optimized."

    return f"Found {len(findings)} opportunities:\n" + "\n".join(f"  {i+1}. {f}" for i, f in enumerate(findings))