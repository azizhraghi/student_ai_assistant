import streamlit as st
import os

def render_sidebar(subtitle=""):
    """
    Renders the unified SaaS-like sidebar across all pages.
    Hides the default Streamlit navigation and shows a custom one.
    """
    # 1. Hide default Streamlit sidebar navigation
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        
        .nav-header {
            color: #1e293b;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .nav-subheader {
            color: #64748b;
            font-size: 0.85rem;
            margin-bottom: 24px;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # 2. Main Branding
        st.markdown('<div class="nav-header">🎓 Student AI Assistant</div>', unsafe_allow_html=True)
        if subtitle:
            st.markdown(f'<div class="nav-subheader">{subtitle}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="nav-subheader">Your personal AI companion</div>', unsafe_allow_html=True)

        # 3. Custom Navigation Menu
        st.markdown("### 🧭 Navigation")
        # Use page_link for fast, built-in routing
        st.page_link("app.py", label="Home Chat", icon="🏠")
        st.page_link("pages/1_Knowledge_Graph.py", label="Knowledge Graph", icon="🕸️")
        st.page_link("pages/2_Study_Room.py", label="Study Room", icon="👥")
        st.page_link("pages/3_Voice_Mode.py", label="Voice Mode", icon="🎤")
        st.page_link("pages/4_Dashboard.py", label="Dashboard", icon="📊")

        st.markdown("---")

        # 4. Global API Key Handling
        if not os.getenv("MISTRAL_API_KEY"):
            st.markdown("### 🔑 API Setup")
            api_key = st.text_input("Mistral API Key", type="password", key="global_api_key_input")
            if api_key:
                os.environ["MISTRAL_API_KEY"] = api_key
                st.success("✅ Key set!")
                st.rerun()
        else:
            st.success("✅ Mistral API Key loaded")
            
        st.markdown("---")
