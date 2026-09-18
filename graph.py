"""
Assemble tout le schéma en un graphe LangGraph :
guardrail -> supervisor -> (agents spécialisés en parallèle) -> budget -> itinerary
-> human review (interrupt) -> [approve -> fin | request_changes -> refait itinerary]
"""
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt
from langgraph.checkpoint.memory import MemorySaver

from state import TravelState
from guardrails import input_guardrail_node, route_after_guardrail
from supervisor import supervisor_node
from agents.flight_agent import flight_agent_node
from agents.hotel_agent import hotel_agent_node
from agents.weather_agent import weather_agent_node
from agents.budget_agent import budget_agent_node
from agents.itinerary_agent import itinerary_agent_node


def blocked_node(state: TravelState) -> TravelState:
    return {"final_response": f"Demande refusée : {state.get('block_reason', 'raison inconnue')}"}


def fan_out_to_agents(state: TravelState):
    """Routage dynamique : envoie l'état vers chaque agent choisi par le Supervisor,
    en parallèle (c'est la partie 'Selected Dynamically' du schéma)."""
    agent_map = {
        "flight": "flight_agent",
        "hotel": "hotel_agent",
        "weather": "weather_agent",
    }
    sends = [
        Send(agent_map[a], state) for a in state.get("selected_agents", []) if a in agent_map
    ]
    return sends if sends else ["budget_agent"]


def join_before_budget(state: TravelState) -> TravelState:
    """Point de synchronisation après le fan-out parallèle."""
    return {}


def human_review_node(state: TravelState) -> TravelState:
    """Bloc '6. HUMAN-IN-THE-LOOP'. Coupe l'exécution et attend une décision humaine."""
    decision = interrupt(
        {
            "question": "Voici l'itinéraire proposé. Approuvez-vous ?",
            "itinerary": state.get("itinerary_plan", {}).get("summary", ""),
        }
    )
    return {
        "hitl_decision": decision.get("decision", "approve"),
        "hitl_feedback": decision.get("feedback", ""),
    }


def route_after_review(state: TravelState) -> str:
    if state.get("hitl_decision") == "request_changes":
        return "itinerary_agent"  # boucle vers l'agent concerné
    return "final_response"


def final_response_node(state: TravelState) -> TravelState:
    return {"final_response": state.get("itinerary_plan", {}).get("summary", "")}


def build_graph():
    graph = StateGraph(TravelState)

    graph.add_node("input_guardrail", input_guardrail_node)
    graph.add_node("blocked", blocked_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("flight_agent", flight_agent_node)
    graph.add_node("hotel_agent", hotel_agent_node)
    graph.add_node("weather_agent", weather_agent_node)
    graph.add_node("join", join_before_budget)
    graph.add_node("budget_agent", budget_agent_node)
    graph.add_node("itinerary_agent", itinerary_agent_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("final_response", final_response_node)

    graph.add_edge(START, "input_guardrail")
    graph.add_conditional_edges(
        "input_guardrail", route_after_guardrail, {"supervisor": "supervisor", "blocked": "blocked"}
    )
    graph.add_edge("blocked", END)

    graph.add_conditional_edges("supervisor", fan_out_to_agents, ["flight_agent", "hotel_agent", "weather_agent", "budget_agent"])
    graph.add_edge("flight_agent", "join")
    graph.add_edge("hotel_agent", "join")
    graph.add_edge("weather_agent", "join")
    graph.add_edge("join", "budget_agent")
    graph.add_edge("budget_agent", "itinerary_agent")
    graph.add_edge("itinerary_agent", "human_review")
    graph.add_conditional_edges(
        "human_review", route_after_review, {"itinerary_agent": "itinerary_agent", "final_response": "final_response"}
    )
    graph.add_edge("final_response", END)

    # MemorySaver : gère nativement les appels async (ainvoke) utilisés partout dans l'app.
    # SqliteSaver (version sync) plantait sur ainvoke ; AsyncSqliteSaver existe mais suppose
    # une boucle asyncio stable — incompatible avec Streamlit qui relance une boucle à chaque
    # interaction. Conséquence : l'état d'une conversation en pause (HITL) ne survit pas à un
    # redémarrage de l'app. Acceptable pour ce projet ; à revoir avec un vrai backend persistant
    # (Postgres) pour un déploiement multi-utilisateurs sérieux.
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
