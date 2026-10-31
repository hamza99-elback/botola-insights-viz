"""Entry point:  streamlit run streamlit_app.py

Kept at the project root on purpose: Streamlit only hot-reloads modules inside the entry
script's folder, so starting from here makes edits to bi_studio/, charts/, etc. reload too.
"""
from botola_insights_app.app import main

main()
