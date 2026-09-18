from langgraph.prebuilt import create_react_agent
from llm import get_llm
from mcp_client import get_all_tools
from state import TravelState


async def hotel_agent_node(state: TravelState) -> TravelState:
    tools = await get_all_tools()
    search_tools = [t for t in tools if t.name == "search_hotels"]
    agent = create_react_agent(get_llm(), search_tools)

    constraints = state.get("trip_constraints", {})
    nights = constraints.get("duration_days", 4)
    query = (
        f"Cherche des hôtels à {constraints.get('destination')} pour {nights} nuits. "
        f"Résume 3 options avec gamme de prix et niveau de confort (économique/milieu/haut de gamme)."
    )
    result = await agent.ainvoke({"messages": [("user", query)]})
    summary = result["messages"][-1].content

    return {
        "hotel_results": {"summary": summary},
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
