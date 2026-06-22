#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

FitKG Interactive Assistant — RAG chat + body map + KG facts.



  pip install streamlit openai

  python fitkg_build_rag_index.py

  streamlit run fitkg_assistant.py

"""

from __future__ import annotations



import os

from pathlib import Path



import streamlit as st



from fitkg_body_svg import REGION_QUERIES, render_body_svg
from fitkg_kimore_bridge import KIMORE_CLASSES, get_kimore_preset, regions_for_kimore
from fitkg_rag import FitKGRAG, llm_configured, llm_provider, load_dotenv



OUT = Path(__file__).resolve().parent / "outputs" / "fitkg_kg"





@st.cache_resource

def load_rag() -> FitKGRAG:

    return FitKGRAG()





def process_query(rag: FitKGRAG, query: str, use_llm: bool) -> tuple[str, dict]:

    ctx = rag.retrieve(query)

    reply = rag.answer(query, use_llm=use_llm)

    return reply, ctx





def main():

    load_dotenv()

    st.set_page_config(page_title="FitKG Assistant", layout="wide")

    st.title("FitKG Fitness Assistant")

    st.caption(

        "RAG over 11,544 fitness passages + 8k entities · front/back muscle map · "

        "optional NVIDIA NIM / OpenAI for natural answers"

    )



    if not (OUT / "graph.json").is_file():

        st.error("Run `python fitkg_eda.py` first.")

        st.stop()

    if not (OUT / "rag_index.json").is_file():

        st.error("Run `python fitkg_build_rag_index.py` then refresh.")

        st.stop()



    rag = load_rag()



    if "messages" not in st.session_state:

        st.session_state.messages = []

    if "highlight" not in st.session_state:

        st.session_state.highlight = []

    if "last_ctx" not in st.session_state:

        st.session_state.last_ctx = {}



    with st.sidebar:

        prov = llm_provider()

        use_llm = st.toggle("LLM answers", value=llm_configured())

        if prov:

            st.caption(f"Provider: **{prov}** · model `{os.environ.get('FITKG_CHAT_MODEL', 'default')}`")

        elif use_llm:

            st.caption("Set `NVIDIA_API_KEY` or `OPENAI_API_KEY` in `.env`")

        st.markdown("**KIMORE clinical exercises**")
        kimore = st.selectbox(
            "PG-XFormer class",
            [""] + list(KIMORE_CLASSES),
            format_func=lambda x: get_kimore_preset(x)["label_en"] if x else "Select…",
            key="kimore_pick",
        )
        if st.button("Load KIMORE preset", use_container_width=True) and kimore:
            preset = get_kimore_preset(kimore)
            st.session_state.trigger_q = preset["fitkg_query"]
            st.session_state.highlight = regions_for_kimore(kimore)
        st.markdown("**Examples**")

        for q in ("squat muscles trained", "swimming benefits", "dumbbell chest"):

            if st.button(q, use_container_width=True):

                st.session_state.trigger_q = q



    col_body, col_chat, col_facts = st.columns([1, 1.5, 1])



    with col_body:

        st.subheader("Muscle map")

        st.caption("Blue = muscles linked via FitKG 锻炼 (trains) edges")

        st.markdown(render_body_svg(st.session_state.highlight), unsafe_allow_html=True)

        region = st.selectbox(

            "Click a region",

            [""] + sorted(REGION_QUERIES.keys()),

            format_func=lambda x: x.replace("_", " ").title() if x else "Select…",

        )

        if st.button("Explore region", use_container_width=True) and region:

            st.session_state.trigger_q = REGION_QUERIES[region]

            hl = [region]

            if region.endswith("_l"):

                hr = region.replace("_l", "_r")

                if hr in REGION_QUERIES:

                    hl.append(hr)

            st.session_state.highlight = hl



    with col_chat:

        st.subheader("Chat")

        for msg in st.session_state.messages:

            with st.chat_message(msg["role"]):

                st.markdown(msg["content"])



        q = st.session_state.pop("trigger_q", None) or st.chat_input(

            "Ask about muscles, exercises, form…"

        )

        if q:

            st.session_state.messages.append({"role": "user", "content": q})

            reply, ctx = process_query(rag, q, use_llm)

            st.session_state.messages.append({"role": "assistant", "content": reply})

            st.session_state.highlight = ctx.get("regions", st.session_state.highlight)

            st.session_state.last_ctx = ctx

            st.rerun()



    with col_facts:

        st.subheader("Knowledge graph")

        ctx = st.session_state.last_ctx

        if ctx.get("muscle_info"):

            for block in ctx["muscle_info"][:2]:

                muscles = block.get("muscles") or []

                if muscles:

                    st.markdown("**Muscles (锻炼 / trains)**")

                    for m in muscles[:8]:

                        st.markdown(f"- {m.get('label_en', '')} ({m.get('label_zh', '')})")

        if ctx.get("nodes"):

            st.markdown("**Matched entities**")

            for n in ctx["nodes"][:6]:

                st.markdown(f"**{rag._display(n)}**")

                st.caption(f"{n.get('type_en')} · {n.get('label_zh', '')}")

        if ctx.get("triples"):

            st.markdown("**Relations**")

            for line in ctx["triples"][:8]:

                st.markdown(line)

        if ctx.get("passages"):

            with st.expander("Source passages"):

                for p in ctx["passages"][:2]:

                    st.text(p["text_zh"][:400] + "…")

        if not ctx:

            st.info("Ask a question to load graph context.")

        st.link_button(

            "Open graph + skeleton explorer",

            "http://localhost:8766/fitkg_graph_ui/",

        )





if __name__ == "__main__":

    main()

