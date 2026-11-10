"""Check the tool helpers and tool schemas: uv run python scripts/try_tools.py"""

from agrivibe.agents.orchestrator.memory import Finding, Requirements
from agrivibe.agents.orchestrator.tools import as_text, brief, save_requirements

req = Requirements(field_id="SL-PADDY-MINNERIYA", crop="paddy", problem="urea timing", timeframe="this week")
print(brief("Rain in the last week?", req))
print("---")
print(as_text(Finding(summary="119.6 mm of rain", data={"rainfall_last_7_days_mm": 119.6})))
print("---")
print("model sees these arguments:", list(save_requirements.args))