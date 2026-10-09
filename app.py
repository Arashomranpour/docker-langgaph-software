import streamlit as st

from ui.chat_view import render_chat
from ui.developer_view import render_developer
from workflows.chat import build_chat_graph
from workflows.developer import build_developer_graph

st.set_page_config(page_title="LangGraph Assistant", page_icon="💬")


@st.cache_resource
def get_graphs():
    return build_chat_graph(), build_developer_graph()


chat_graph, dev_graph = get_graphs()

mode = st.sidebar.radio("Mode", ["Chat mode", "Developer mode"])

if mode == "Chat mode":
    st.title("Chat")
    render_chat(chat_graph)
else:
    st.title("Developer mode")
    render_developer(dev_graph)
