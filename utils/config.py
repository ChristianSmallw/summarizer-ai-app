# config.py
import os
from typing import Optional

def _from_streamlit(key: str) -> Optional[str]:
    try:
        import streamlit as st
        return st.secrets.get(key)  # works on Streamlit Cloud or local secrets.toml
    except Exception:
        return None

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    # 1) Streamlit secrets
    v = _from_streamlit(key)
    if v:
        return v

    # 2) Environment vars (PaaS secrets)
    v = os.getenv(key)
    if v:
        return v

    # 3) .env for local dev
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
        return os.getenv(key, default)
    except Exception:
        return os.getenv(key, default)
