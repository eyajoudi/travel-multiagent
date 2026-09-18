from llm import get_llm
from state import TravelState

PROMPT = """Tu es un agent budget voyage. Voici les infos collectées :
- Contraintes: {constraints}
- Vols: {flights}
- Hôtels: {hotels}

Estime un budget total approximatif (vol + hôtel + repas + activités) pour le voyage,
et donne 2-3 recommandations pour économiser. Sois concis (max 150 mots).
"""


async def budget_agent_node(state: TravelState) -> TravelState:
    llm = get_llm()
    prompt = PROMPT.format(
        constraints=state.get("trip_constraints", {}),
        flights=state.get("flight_results", {}).get("summary", "N/A") if state.get("flight_results") else "N/A",
        hotels=state.get("hotel_results", {}).get("summary", "N/A") if state.get("hotel_results") else "N/A",
    )
    response = await llm.ainvoke(prompt)

    return {
        "budget_analysis": {"summary": response.content},
        "llm_calls": 1,
    }
