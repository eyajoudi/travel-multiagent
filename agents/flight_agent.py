from langgraph.prebuilt import create_react_agent
from llm import get_llm
from mcp_client import get_all_tools
from state import TravelState


async def flight_agent_node(state: TravelState) -> TravelState:
    tools = await get_all_tools()
    search_tools = [t for t in tools if t.name == "search_flights"]
    agent = create_react_agent(get_llm(), search_tools)

    constraints = state.get("trip_constraints", {})
    query = (
        f"Cherche des vols de {constraints.get('origin', 'ma ville')} vers "
        f"{constraints.get('destination')} pour {constraints.get('month_or_date', 'le mois prochain')}. "
        f"Résume les meilleures options (compagnie, prix approximatif, durée)."
    )
    result = await agent.ainvoke({"messages": [("user", query)]})
    summary = result["messages"][-1].content

    return {
        "flight_results": {"summary": summary},
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
