"""
État partagé entre tous les agents (le "TravelState" du schéma).
LangGraph passe cet objet à chaque nœud, chaque agent lit/écrit dedans.
"""
import operator
from typing import TypedDict, Optional, List, Dict, Any
from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class TravelState(TypedDict, total=False):
    # 1. Entrée utilisateur
    user_query: str

    # 2. Guardrail d'entrée
    is_valid: bool
    block_reason: Optional[str]

    # 3. Décision du Supervisor
    selected_agents: List[str]        # ex: ["flight", "hotel", "weather"]
    trip_constraints: Dict[str, Any]  # ex: {"destination": "Dubai", "duration_days": 4}
    supervisor_reasoning: str

    # 4. Résultats des agents spécialisés
    flight_results: Optional[Dict[str, Any]]
    hotel_results: Optional[Dict[str, Any]]
    weather_info: Optional[Dict[str, Any]]
    budget_analysis: Optional[Dict[str, Any]]
    itinerary_plan: Optional[Dict[str, Any]]

    # 5. Historique de conversation (utile pour debug / LangSmith)
    messages: Annotated[list, add_messages]
    # operator.add : plusieurs agents en parallèle (fan-out) peuvent écrire ici
    # dans le même "tick" — sans ça LangGraph lève InvalidUpdateError.
    llm_calls: Annotated[int, operator.add]

    # 6. Human-in-the-loop
    hitl_decision: Optional[str]      # "approve" | "request_changes"
    hitl_feedback: Optional[str]

    # 7. Sortie finale
    final_response: Optional[str]
