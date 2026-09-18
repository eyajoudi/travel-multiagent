from llm import get_llm
from state import TravelState

PROMPT = """Tu es l'agent itinéraire, tu fais la synthèse finale du voyage.
Demande initiale: {query}
Contraintes: {constraints}
Vols: {flights}
Hôtels: {hotels}
Météo: {weather}
Budget: {budget}

Construis un itinéraire jour par jour (Jour 1, Jour 2, ...) avec activités,
transport et repas suggérés. Reste réaliste et concis.
"""

REVISION_PROMPT = """Voici l'itinéraire que tu avais proposé précédemment :
---
{previous_itinerary}
---

L'utilisateur a demandé ce changement précis : "{feedback}"

Réécris l'itinéraire complet (Jour 1, Jour 2, ...) en appliquant CE changement.
Garde tout le reste identique sauf ce qui est directement concerné par la demande.
"""


async def itinerary_agent_node(state: TravelState) -> TravelState:
    llm = get_llm()
    feedback = state.get("hitl_feedback")

    if feedback and state.get("itinerary_plan"):
        # Reprise après "request_changes" : on part de l'itinéraire précédent + le feedback
        prompt = REVISION_PROMPT.format(
            previous_itinerary=state["itinerary_plan"].get("summary", ""),
            feedback=feedback,
        )
    else:
        prompt = PROMPT.format(
            query=state["user_query"],
            constraints=state.get("trip_constraints", {}),
            flights=state.get("flight_results", {}).get("summary", "N/A") if state.get("flight_results") else "N/A",
            hotels=state.get("hotel_results", {}).get("summary", "N/A") if state.get("hotel_results") else "N/A",
            weather=state.get("weather_info", {}).get("summary", "N/A") if state.get("weather_info") else "N/A",
            budget=state.get("budget_analysis", {}).get("summary", "N/A") if state.get("budget_analysis") else "N/A",
        )

    response = await llm.ainvoke(prompt)

    return {
        "itinerary_plan": {"summary": response.content},
        # On efface le feedback consommé pour ne pas le réappliquer en boucle
        "hitl_feedback": None,
        "llm_calls": 1,
    }
