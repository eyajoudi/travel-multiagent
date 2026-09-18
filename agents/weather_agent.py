from langgraph.prebuilt import create_react_agent
from llm import get_llm
from mcp_client import get_all_tools
from state import TravelState


async def weather_agent_node(state: TravelState) -> TravelState:
    tools = await get_all_tools()
    weather_tools = [t for t in tools if t.name == "get_weather_forecast"]
    agent = create_react_agent(get_llm(), weather_tools)

    constraints = state.get("trip_constraints", {})
    query = (
        f"Donne les prévisions météo pour {constraints.get('destination')} et déduis-en "
        f"des conseils de bagages (vêtements à prévoir)."
    )
    result = await agent.ainvoke({"messages": [("user", query)]})
    summary = result["messages"][-1].content

    return {
        "weather_info": {"summary": summary},
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
