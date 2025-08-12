import streamlit as st
from config import Config
from core import LLM, Message, Thinking, Commands

st.set_page_config(initial_sidebar_state="collapsed")

col1, col2 = st.columns([1, 3])
with col1:
    st.image("assets/image.png", width=150)
with col2:
    st.title("Chat:blue[BOT] with Reasoning")
    st.subheader(f"Powered by :red[{Config.model}]", divider=True)

if "messages" not in st.session_state:
    system_message = Message(role="system", content=Config.system_prompt, reasoning_source=None)
    st.session_state.messages = [system_message]

client = LLM(base_url=Config.base_url, api_key=Config.api_key)
thinking = Thinking(thinking_tag=Config.thinking_tag)

for message in st.session_state.messages:
    if message.role == "system":
        continue
        
    with st.chat_message(message.role):
        if message.role == "assistant" and message.has_reasoning():
            thinking.display_message_thinking(message, expanded=False)
        st.markdown(message.get_clean_content())

if prompt := st.chat_input("What's on your mind? (Type /help for commands)"):
    if prompt.startswith("/"):
        command_response = Commands().execute(prompt)
        user_message = Message(role="user", content=prompt)

        st.session_state.messages.append(user_message)
        with st.chat_message("user"):
            st.markdown(prompt)

        if command_response:
            assistant_message = Message(role="assistant", content=command_response)
            st.session_state.messages.append(assistant_message)
            with st.chat_message("assistant"):
                st.markdown(command_response)
    
    else:
        user_message = Message(role="user", content=prompt)
        st.session_state.messages.append(user_message)
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            api_messages = [msg.to_openai_format() for msg in st.session_state.messages]
            stream = client.invoke(
                model=Config.model,
                messages=api_messages,
                temperature=0.7,
                tool_choice="required",
                tools=[{"type": "browser_search"}, {"type": "code_interpreter"}]
            )

            assistant_message, full_response, full_reasoning = thinking.stream_with_thinking(stream)
            st.session_state.messages.append(assistant_message)

with st.sidebar:
    def export_chat_history() -> list:
        exported_chats = []
        for msg in st.session_state.messages:
            if msg.role != "system":
                exported_chats.append({"role": msg.role, "content": msg.get_clean_content(), "reasoning": msg.reasoning, "reasoning_source": msg.reasoning_source.value if msg.reasoning_source else None})
        return exported_chats

    st.download_button("Export Chat History", data=str(export_chat_history()), file_name="chat_history.json", mime="application/json")