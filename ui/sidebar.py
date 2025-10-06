import streamlit as st
from core.models import OPENAI_MODELS, LOCAL_MODELS
from core.chunking import MIN_CHUNK, MAX_CHUNK, DEFAULT_OVERLAP_MIN
from core.types import ModelSettings
from ui.state import busy, on_chunk_change, refresh_chunking_defaults

def render_sidebar() -> ModelSettings:
    with st.sidebar:
        #st.title("֎ AI Summarizer")
        st.markdown(
            """
            <h1 style='text-align: center; margin-top: -40px; margin-bottom: 20px; font-size: 30px;'>
                ֎ AI Summarizer
            </h1>
            <hr style='border-width: 3px; background-color: #A9A9A9;'/>
            """,
            unsafe_allow_html=True
        )
        st.header("🔧 Model Settings", divider="grey") 
        use_local = st.toggle("Use local models?", disabled=busy())
        selected_models = OPENAI_MODELS if not use_local else LOCAL_MODELS
        model_name = st.selectbox(
                                "OpenAI Models" if not use_local else "Local Models",
                                options=list(selected_models),
                                key="model_name",
                                disabled=busy()
                            )
        
        reasoning = ""
        verbosity = ""
        temperature = 1.0
        if model_name.startswith("gpt-5"):
            reasoning = st.selectbox(
                        "Reasoning",
                        options=["Minimal", "Low", "Medium", "High"],
                        index=1,
                        key="reasoning",
                        help="Higher reasoning increases the model's ability to understand and process complex information",
                        disabled=busy()
                    ).lower()
            verbosity = st.selectbox(
                        "Verbosity",
                        options=["Low", "Medium", "High"],
                        key="verbosity",
                        help="Verbosity determines how many output tokens are generated.",
                        disabled=busy()
                    ).lower()
        else:
            temperature = st.slider("Temperature", 0.0, 1.0, 0.2,
                        key="temperature",
                        disabled=busy())

        # Run the refresh when selection changed this render
        if model_name != st.session_state.get("_last_model", None):
            refresh_chunking_defaults(selected_models)
        st.session_state._last_model = model_name

        st.header("🧱 Chunk Settings", divider="grey") 

        chunk_size = st.slider(
            "Chunk size (tokens)",
            min_value=MIN_CHUNK,
            max_value=min(MAX_CHUNK, selected_models[model_name]["context"]),
            step=128,
            key="chunk_size",
            on_change=on_chunk_change,
            disabled=busy(),
            help="Target tokens per chunk (default to ~60% of the model's context)."
        )

        overlap = st.slider(
            "Overlap (tokens)",
            min_value=DEFAULT_OVERLAP_MIN,
            max_value=int(chunk_size * 0.5),
            step=64,
            key="overlap",
            disabled=busy(),
            help="Carry-over tokens from the tail of the previous chunk (defaults ~12% of chunk)."
        )

        strategy = st.selectbox(
            "Chunking strategy",
            options=["map-only", "map-reduce", "map-refine"],
            key="strategy",
            help=(
                "map-only: concat per-chunk summaries\n"
                "map-reduce: combine summaries in a final pass (robust default)\n"
                "map-refine: iterative refinement, preserves details"
            ),
            disabled=busy()
        )

        return ModelSettings(
            use_local=use_local,
            model_name=model_name,
            temperature=temperature,
            reasoning=reasoning,
            verbosity=verbosity,
            chunk_size=chunk_size,
            overlap=overlap,
            strategy=strategy,
        )