"""
Lance le système en ligne de commande pour tester le flux complet,
y compris la pause Human-in-the-Loop.
Usage: python main.py
"""
import asyncio
from langgraph.types import Command
from graph import build_graph


async def main():
    app = build_graph()
    config = {"configurable": {"thread_id": "session-1"}}

    query = input("Décris ton voyage : ")
    result = await app.ainvoke({"user_query": query, "llm_calls": 0}, config=config)

    # Si le graphe s'est arrêté sur l'interrupt (human_review)
    if "__interrupt__" in result:
        interrupt_data = result["__interrupt__"][0].value
        print("\n=== ITINÉRAIRE PROPOSÉ ===")
        print(interrupt_data["itinerary"])
        print("==========================")

        choice = input("\nApprouver ? (o/n) : ").strip().lower()
        if choice == "o":
            decision = {"decision": "approve"}
        else:
            feedback = input("Que faut-il changer ? : ")
            decision = {"decision": "request_changes", "feedback": feedback}

        result = await app.ainvoke(Command(resume=decision), config=config)

    print("\n=== RÉPONSE FINALE ===")
    print(result.get("final_response", result.get("itinerary_plan")))


if __name__ == "__main__":
    asyncio.run(main())
