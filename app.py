import streamlit as st
from config import Config
from core import LLM, Message, Thinking, Commands

col1, col2 = st.columns([1, 3])
with col1:
    st.image("assets/image.png", width=150)
with col2:
    st.title("Chat:blue[BOT] with Reasoning")
    st.subheader(f"Powered by :red[{Config.model}]", divider=True)

if "messages" not in st.session_state:
    st.session_state.messages = [Message(role="system", content=Config.system_prompt)]

client = LLM(base_url=Config.base_url, api_key=Config.api_key)

for message in st.session_state.messages:
    if message.role == "system":
        continue
    with st.chat_message(message.role):
        if message.role == "assistant" and message.thinking:
            with st.expander("Thought Process.", expanded=False):
                for i, think in enumerate(message.thinking):
                    st.markdown(think.strip())
                    if i < len(message.thinking) - 1:
                        st.divider()
        st.markdown(message.content)

if prompt := st.chat_input("What's on your mind? (Type /help for commands)"):
    if prompt.startswith("/"):
        command_response = Commands().execute(prompt)
        st.session_state.messages.append(Message(role="user", content=prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        if command_response:
            st.session_state.messages.append(Message(role="assistant", content=command_response))
            with st.chat_message("assistant"):
                st.markdown(command_response)
    else:
        st.session_state.messages.append(Message(role="user", content=prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.invoke(
                model=Config.model,
                messages=st.session_state.messages,
                extra_body={
                    'extra_body': {
                        "google": {
                            "thinking_config": {
                                "thinking_budget": 20000,
                                "include_thoughts": True
                            }
                        }
                    }
                }
            )

            full_response, thinking_matches, cleaned_content = Thinking().stream_with_thinking(stream)

            assistant_message = Message(
                role="assistant",
                content=cleaned_content or full_response,
                thinking=thinking_matches if thinking_matches else None
            )

            st.session_state.messages.append(assistant_message)
