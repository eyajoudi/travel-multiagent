"""
Bloc "2. INPUT GUARDRAIL" du schéma.
Vérifie que la demande est pertinente (voyage), sûre, et valide (a assez d'infos)
avant de laisser le Supervisor démarrer.
"""
import json
from llm import get_llm, parse_json_response
from state import TravelState

GUARDRAIL_PROMPT = """Tu es un filtre de sécurité pour un assistant de voyage.
Analyse la demande utilisateur ci-dessous et réponds UNIQUEMENT en JSON, sans texte autour :
{{
  "pass": true ou false,
  "reason": "raison courte si bloqué, sinon chaîne vide"
}}

Bloque si la demande :
- n'a aucun rapport avec le voyage/tourisme
- demande quelque chose d'illégal ou dangereux
- est incompréhensible ou vide

Demande utilisateur : "{query}"
"""


def input_guardrail_node(state: TravelState) -> TravelState:
    llm = get_llm()
    prompt = GUARDRAIL_PROMPT.format(query=state["user_query"])
    response = llm.invoke(prompt)

    try:
        result = json.loads(parse_json_response(response.content))
    except json.JSONDecodeError:
        result = {"pass": True, "reason": ""}  # fail-open pour ne pas bloquer par erreur de parsing

    return {
        "is_valid": result.get("pass", True),
        "block_reason": result.get("reason", ""),
        "llm_calls": 1,
    }


def route_after_guardrail(state: TravelState) -> str:
    """Fonction de routage conditionnel utilisée dans le graphe."""
    return "supervisor" if state.get("is_valid") else "blocked"
