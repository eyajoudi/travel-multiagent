"""
Interface web du système. Lance avec : streamlit run ui/app.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from langgraph.types import Command
from graph import build_graph

st.set_page_config(page_title="Planificateur de voyage multi-agent", page_icon="✈️")
st.title("✈️ Planificateur de voyage multi-agent")
st.caption("Supervisor + agents spécialisés + guardrails + human-in-the-loop (LangGraph + MCP)")


@st.cache_resource
def get_app():
    return build_graph()


def run_async(coro):
    return asyncio.run(coro)


# --- État de session ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "session-1"
if "stage" not in st.session_state:
    st.session_state.stage = "input"   # input -> review -> done
if "interrupt_data" not in st.session_state:
    st.session_state.interrupt_data = None
if "final_result" not in st.session_state:
    st.session_state.final_result = None

app = get_app()
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# --- Étape 1 : saisie utilisateur ---
if st.session_state.stage == "input":
    query = st.text_area("Décris ton voyage", placeholder="Ex: Plan a 4 day trip to Dubai for next month")
    if st.button("Planifier le voyage", type="primary") and query:
        with st.spinner("Les agents travaillent (guardrail → supervisor → agents spécialisés)..."):
            result = run_async(app.ainvoke({"user_query": query, "llm_calls": 0}, config=config))

        if result.get("final_response") and not result.get("itinerary_plan"):
            # Cas bloqué par le guardrail
            st.session_state.final_result = result["final_response"]
            st.session_state.stage = "done"
            st.rerun()
        elif "__interrupt__" in result:
            st.session_state.interrupt_data = result["__interrupt__"][0].value
            st.session_state.stage = "review"
            st.rerun()
        else:
            st.session_state.final_result = result.get("final_response") or result.get("itinerary_plan", {}).get("summary")
            st.session_state.stage = "done"
            st.rerun()

# --- Étape 2 : Human-in-the-loop (bloc 6 du schéma) ---
elif st.session_state.stage == "review":
    st.subheader("🧑‍✈️ Validation humaine requise")
    st.markdown(st.session_state.interrupt_data["itinerary"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approuver", type="primary"):
            with st.spinner("Finalisation..."):
                result = run_async(app.ainvoke(Command(resume={"decision": "approve"}), config=config))
            st.session_state.final_result = result.get("final_response")
            st.session_state.stage = "done"
            st.rerun()
    with col2:
        feedback = st.text_input("Changements demandés")
        if st.button("✏️ Demander des changements") and feedback:
            with st.spinner("L'agent itinéraire retravaille la proposition..."):
                result = run_async(
                    app.ainvoke(Command(resume={"decision": "request_changes", "feedback": feedback}), config=config)
                )
            if "__interrupt__" in result:
                st.session_state.interrupt_data = result["__interrupt__"][0].value
                st.rerun()
            else:
                st.session_state.final_result = result.get("final_response")
                st.session_state.stage = "done"
                st.rerun()

# --- Étape 3 : résultat final ---
elif st.session_state.stage == "done":
    st.subheader("📋 Itinéraire final")
    st.markdown(st.session_state.final_result)
    if st.button("🔄 Nouveau voyage"):
        st.session_state.stage = "input"
        st.session_state.thread_id = f"session-{os.urandom(4).hex()}"
        st.session_state.final_result = None
        st.rerun()
