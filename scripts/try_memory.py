"""Check the reducer by hand: uv run python scripts/try_memory.py"""

from agrivibe.agents.orchestrator.memory import Finding, merge_findings

weather = {"weather": Finding(summary="119.6 mm of rain", data={"rainfall_last_7_days_mm": 119.6})}
farm = {"farm_context": Finding(summary="NDVI up 6.5%", data={"ndvi_change_percentage": 6.5})}

both = merge_findings(weather, farm)
print("parallel finish keeps both:", sorted(both))
print("empty update clears:", merge_findings(both, {}))