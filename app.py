import re
import time
import streamlit as st
from openai import OpenAI

col1, col2 = st.columns([1, 3])
with col1:
    st.image("assets/image.png", width=150)
with col2:
    st.title("Chat:blue[BOT] with Reasoning")
    st.subheader("Powered by :red[Groq's] **Qwen-3 32B** Model", divider=True)

client = OpenAI(
    base_url="https://api.groq.com/openai/v1", api_key=st.secrets["OpenAI_key"]
)

LLM_MODEL = "qwen/qwen3-32b"

#/think  -> should think before answering the question
#/no-think -> should not think before answering the question
SYSTEM_PROMPT = """
You are 'Rambo Kamlesh', a helpful chatbot who answers users questions. 

/think before answering the question, and provide your thought process in a structured manner.

INSTRUCTIONS:
1. Always answer users questions in English do not use any other language.
2. Use markdown formatting to make your answers more readable.
3. Start the conversation with a friendly greeting and introduction.
"""

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = LLM_MODEL
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]


def extract_thinking_and_content(text):
    think_pattern = r"<think>(.*?)</think>"
    thinking_matches = re.findall(think_pattern, text, re.DOTALL)
    cleaned_text = re.sub(think_pattern, "", text, flags=re.DOTALL).strip()

    open_think = text.count("<think>")
    close_think = text.count("</think>")
    is_thinking = open_think > close_think

    current_thinking = ""
    if is_thinking:
        last_think_pos = text.rfind("<think>")
        if last_think_pos != -1:
            current_thinking = text[last_think_pos + 7 :]

    return thinking_matches, current_thinking, cleaned_text, is_thinking


def display_thinking(completed_thinking, current_thinking, is_thinking):
    if completed_thinking or current_thinking or is_thinking:
        with st.expander("Thinking...", expanded=True):
            for i, think in enumerate(completed_thinking):
                st.markdown(think.strip())
                if i < len(completed_thinking) - 1:
                    st.divider()

            if current_thinking:
                if completed_thinking:
                    st.divider()
                st.markdown(current_thinking.strip())
            elif is_thinking and not current_thinking:
                if completed_thinking:
                    st.divider()
                st.markdown("*Thinking...*")


def stream_with_thinking(stream):
    full_content = ""
    thinking_container = st.container()
    content_container = st.container()

    thinking_placeholder = thinking_container.empty()
    content_placeholder = content_container.empty()

    for chunk in stream:
        time.sleep(0.05) # To avoid rate limit and ensure smooth streaming
        if chunk.choices[0].delta.content is not None:
            full_content += chunk.choices[0].delta.content

            completed_thinking, current_thinking, cleaned_content, is_thinking = (
                extract_thinking_and_content(full_content)
            )

            with thinking_placeholder.container():
                display_thinking(completed_thinking, current_thinking, is_thinking)

            if cleaned_content and not is_thinking:
                content_placeholder.markdown(cleaned_content)

    final_completed, final_current, final_content, final_thinking = (
        extract_thinking_and_content(full_content)
    )
    thinking_placeholder.empty()

    if final_completed:
        with thinking_container:
            with st.expander("Thought Process.", expanded=False):
                for i, think in enumerate(final_completed):
                    st.markdown(think.strip())
                    if i < len(final_completed) - 1:
                        st.divider()

    if final_content:
        content_placeholder.markdown(final_content)

    return full_content, final_completed, final_content


for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and "thinking" in message:
            with st.expander("Thought Process.", expanded=False):
                for i, think in enumerate(message["thinking"]):
                    st.markdown(think.strip())
                    if i < len(message["thinking"]) - 1:
                        st.divider()
        st.markdown(message["content"])

if prompt := st.chat_input("What's on your mind?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        full_response, thinking_matches, cleaned_content = stream_with_thinking(stream)

        assistant_message = {
            "role": "assistant",
            "content": cleaned_content or full_response,
        }
        if thinking_matches:
            assistant_message["thinking"] = thinking_matches

        st.session_state.messages.append(assistant_message)
