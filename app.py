import openai
import streamlit as st
from config import Config
from datetime import datetime, timezone
from core import LLM, Message, Thinking, Commands, play_audio, send_webhook, WebhookError

st.set_page_config(initial_sidebar_state="collapsed")

col1, col2 = st.columns([1, 3])
with col1:
    st.image("assets/image.png", width=150)
with col2:
    st.title("Reasoning Chat:blue[BOT]")
    st.subheader(f"Powered by :red[Groq]", divider=True)

if "messages" not in st.session_state:
    system_message = Message(role="system", content=Config.system_prompt.replace("<current_time>", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")))
    st.session_state.messages = [system_message]
if "chat_model" not in st.session_state:
    st.session_state.chat_model = Config.model[0]
if "tts_model" not in st.session_state:
    st.session_state.tts_model = Config.tts_model[0]
if "tts_voice" not in st.session_state:
    st.session_state.tts_voice = Config.tts_voice[0]
if "streaming" not in st.session_state:
    st.session_state.streaming = True

client = LLM(base_url=Config.base_url, api_key=Config.api_key)
thinking = Thinking()

for idx, message in enumerate(st.session_state.messages):
    if message.role == "system":
        continue
        
    with st.chat_message(message.role):
        if message.role == "assistant" and message.has_reasoning():
            thinking.display_message(message, expanded=False)
        if message.role == "assistant":
            msg_col, btn_col = st.columns([0.90, 0.10])
            with msg_col:
                st.markdown(message.get_clean_content())
            with btn_col:
                play_audio(
                    enable=st.session_state.tts_model is not None,
                    client=client,
                    text=message.get_clean_content(),
                    model=st.session_state.tts_model,
                    voice=st.session_state.tts_voice
                )
        else:
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
                msg_col, btn_col = st.columns([0.90, 0.10])
                with msg_col:
                    st.markdown(command_response)
                with btn_col:
                    play_audio(
                        enable=st.session_state.tts_model is not None,
                        client=client,
                        text=command_response,
                        model=st.session_state.tts_model,
                        voice=st.session_state.tts_voice
                    )

    else:
        user_message = Message(role="user", content=prompt)
        st.session_state.messages.append(user_message)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                api_messages = [msg.to_openai_format() for msg in st.session_state.messages]
                response = client.invoke(
                    model=st.session_state.chat_model,
                    messages=api_messages,
                    stream=st.session_state.streaming,
                    temperature=0.7,
                    reasoning_effort="low",
                    tool_choice="auto",
                    tools=[{"type": "browser_search"}, {"type": "code_interpreter"}]
                )

                message = thinking.thinking_message(response=response, streaming=st.session_state.streaming)

            except openai.RateLimitError:
                st.toast('Rate limit exceeded. Please try again later.', icon="⚠️")
                st.error("Rate limit exceeded. Please try again later.")
            except openai.LengthFinishReasonError:
                st.toast('The model response was too long and was cut off.', icon="⚠️")
                st.error("The model response was too long and was cut off.")
            except Exception as e:
                st.toast('Failed to generate response. Try again later.', icon="⚠️")
                st.error(f"Exception: {e}")

            st.session_state.messages.append(message)

            # LOGGING VIA WEBHOOK | USED FOR DEBUGGING & ANALYTICS | DATA IS NOT SHARED WITH ANY THIRD PARTY
            if Config.webhook_url:
                try:
                    payload = {"embeds":[{"author":{"name":"Streamlit Chatbot","icon_url":"","url":"http://chatbot-murlee.streamlit.app"},"fields":[{"name":"User","value":f"```{user_message.get_clean_content()[:2000]}```","inline":False},{"name":"Assistant","value":f"```{message.get_clean_content()[:2000]}```"}]}],"username":"Chatbot"}
                    send_webhook(payload=payload, url=Config.webhook_url)
                except WebhookError as we:
                    pass

            msg_col, btn_col = st.columns([0.90, 0.10])
            with msg_col:
                pass
            with btn_col:
                play_audio(
                    enable=st.session_state.tts_model is not None,
                    client=client,
                    text=message.get_clean_content(),
                    model=st.session_state.tts_model,
                    voice=st.session_state.tts_voice
                )

with st.sidebar:
    def export_chat_history() -> list:
        exported_chats = []
        for msg in st.session_state.messages:
            if msg.role != "system":
                exported_chats.append({"role": msg.role, "content": msg.get_clean_content(), "reasoning": msg.reasoning})
        return exported_chats
        
    selected_model = st.selectbox("Choose LLM", options=Config.model, index=Config.model.index(st.session_state.chat_model))
    if selected_model != st.session_state.chat_model:
        st.session_state.chat_model = selected_model
        st.rerun()

    selected_tts_model = st.selectbox("Choose TTS Model", options=Config.tts_model, index=Config.tts_model.index(st.session_state.tts_model) if st.session_state.tts_model in Config.tts_model else 0)
    if selected_tts_model != st.session_state.tts_model:
        st.session_state.tts_model = selected_tts_model
        if selected_tts_model is None:
            st.session_state.tts_voice = Config.tts_voice[0]
        st.rerun()

    tts_voice_disabled = selected_tts_model is None
    selected_tts_voice = st.selectbox("Choose TTS Voice", options=Config.tts_voice, index=Config.tts_voice.index(st.session_state.tts_voice) if st.session_state.tts_voice in Config.tts_voice else 0, disabled=tts_voice_disabled)
    if not tts_voice_disabled and selected_tts_voice != st.session_state.tts_voice:
        st.session_state.tts_voice = selected_tts_voice
        st.rerun()

    streaming_option = st.checkbox("Streaming", value=st.session_state.streaming)
    if streaming_option != st.session_state.streaming:
        st.session_state.streaming = streaming_option
        st.rerun()

    if Config.webhook_url:
        st.markdown("**Note:** Chat data are logged via webhook for debugging and analytics purposes. The data is not shared with any third party.")

    st.download_button("Export Chat History", data=str(export_chat_history()), file_name="chat_history.json", mime="application/json")