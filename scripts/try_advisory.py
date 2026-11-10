"""Run the Advisory Agent on hand-written evidence: uv run python scripts/try_advisory.py"""

from agrivibe.agents.advisory import build_advisory_agent
from agrivibe.config import Settings
from agrivibe.core.llm import create_chat_model

TASK = """Field: SL-PADDY-MINNERIYA (paddy)
Farmer's problem: whether to apply urea
Time frame: this week

Decision to make: Should the farmer apply urea this week?

Evidence:
weather:
119.6 mm of rain in the last 7 days; 26.3 mm forecast in the next 48 hours.
Data: {"rainfall_last_7_days_mm": 119.6, "rainfall_forecast_next_48_hours_mm": 26.3, "heavy_rain_recent": true}

farm_context:
The reading is unreliable: data quality is poor. NDVI 0.648 vs 0.608, up 6.5%. The field is uneven.
Data: {"ndvi_change_percentage": 6.5, "field_uniformity": "uneven", "data_quality": "poor"}"""

agent = build_advisory_agent(create_chat_model(Settings()))
result = agent.invoke({"messages": [{"role": "user", "content": TASK}]})
print(result["messages"][-1].text)
