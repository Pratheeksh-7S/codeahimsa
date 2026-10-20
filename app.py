"""CodeAhimsa web chat (Streamlit). Run: streamlit run app.py"""

import streamlit as st

from codeahimsa.tutor import Tutor

st.set_page_config(page_title="CodeAhimsa", page_icon="🪷")
st.title("🪷 CodeAhimsa")
st.caption("A coding tutor that refuses to hand over the answer. Guardrail: Strands Decider 2B")

with st.sidebar:
    st.header("Demo controls")
    eager = st.toggle("Eager tutor prompt (gives full code)", value=False)
    guarded = st.toggle("Decider 2B guardrail", value=True)
    if st.button("New chat"):
        st.session_state.clear()
        st.rerun()

mode = (eager, guarded)
if st.session_state.get("mode") != mode:
    st.session_state.mode = mode
    st.session_state.tutor = Tutor(eager=eager, guarded=guarded)
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])
        for d in msg.get("decisions", []):
            blocked = d["verdict"].startswith("guide") or d["verdict"] == "fallback"
            label = "🛑 BLOCKED" if blocked else "✅ passed"
            with st.expander(f"{label} · spoils {d['spoils_solution']:.2f} · "
                             f"grounded {d['grounded']:.2f} · {d['latency_ms']:.0f} ms"):
                st.code(d["proposed_reply"], language=None)

if prompt := st.chat_input("Ask about your code..."):
    st.session_state.history.append({"role": "user", "text": prompt})
    with st.spinner("Thinking... (Bedrock writes, Decider checks)"):
        out = st.session_state.tutor.ask(prompt)
    st.session_state.history.append(
        {"role": "assistant", "text": out["reply"], "decisions": out["decisions"]}
    )
    st.rerun()
