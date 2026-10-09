import uuid

import streamlit as st


def render_chat(graph):
    if "chat_thread" not in st.session_state:
        st.session_state.chat_thread = str(uuid.uuid4())
        st.session_state.chat_history = []

    if st.sidebar.button("New chat"):
        del st.session_state["chat_thread"]
        st.rerun()

    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(text)

    if prompt := st.chat_input("Ask anything"):
        st.session_state.chat_history.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)
        config = {"configurable": {"thread_id": st.session_state.chat_thread}}
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = graph.invoke({"messages": [("user", prompt)]}, config)
            reply = result["messages"][-1].content
            st.markdown(reply)
        st.session_state.chat_history.append(("assistant", reply))
