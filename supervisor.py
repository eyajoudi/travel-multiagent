"""
Bloc "3. SUPERVISOR AGENT".
Comprend la demande, extrait les contraintes, et décide dynamiquement
quels agents spécialisés appeler. Plus besoin de workflow fixe écrit à la main.
"""
import json
from llm import get_llm, parse_json_response
from state import TravelState

SUPERVISOR_PROMPT = """Tu es le superviseur d'un système multi-agent de planification de voyage.
Agents disponibles : flight, hotel, weather, budget, itinerary.

Analyse la demande utilisateur et réponds UNIQUEMENT en JSON :
{{
  "selected_agents": ["flight", "hotel", ...],
  "trip_constraints": {{
      "origin": "...",
      "destination": "...",
      "duration_days": 0,
      "month_or_date": "...",
      "budget": "..."
  }},
  "reasoning": "explication courte du choix des agents"
}}

Choisis "itinerary" presque toujours (c'est la synthèse finale).
Choisis "budget" si l'utilisateur mentionne un budget ou si plusieurs agents coûteux sont utilisés.

Demande utilisateur : "{query}"
"""


def supervisor_node(state: TravelState) -> TravelState:
    llm = get_llm()
    prompt = SUPERVISOR_PROMPT.format(query=state["user_query"])
    response = llm.invoke(prompt)

    try:
        result = json.loads(parse_json_response(response.content))
    except json.JSONDecodeError:
        result = {
            "selected_agents": ["flight", "hotel", "weather", "itinerary"],
            "trip_constraints": {},
            "reasoning": "Fallback: parsing JSON échoué, agents par défaut sélectionnés.",
        }

    return {
        "selected_agents": result["selected_agents"],
        "trip_constraints": result["trip_constraints"],
        "supervisor_reasoning": result["reasoning"],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
