import time
import openai
import streamlit as st
from openai.types import chat
from typing import Any, Literal
from .llm import LLM
from .message import Message

class Thinking:
    def thinking_message(self, stream: openai.Stream[chat.ChatCompletionChunk]) -> Message:
        full_content = ""
        full_reasoning = ""
        
        thinking_container = st.container()
        content_container = st.container()
        
        thinking_placeholder = thinking_container.empty()
        content_placeholder = content_container.empty()

        for chunk in stream:
            time.sleep(0.03)

            if hasattr(chunk.choices[0].delta, 'reasoning') and chunk.choices[0].delta.reasoning is not None:
                full_reasoning += chunk.choices[0].delta.reasoning
                with thinking_placeholder.container():
                    with st.expander("Thinking...", expanded=True):
                        st.markdown(full_reasoning.strip())
            
            if chunk.choices[0].delta.content is not None:
                full_content += chunk.choices[0].delta.content
                if full_content.strip():
                    content_placeholder.markdown(full_content)

        thinking_placeholder.empty()
        if full_reasoning.strip():
            with thinking_container:
                with st.expander("Thought Process", expanded=False):
                    st.markdown(full_reasoning.strip())

        if full_content.strip():
            content_placeholder.markdown(full_content)

        return Message.from_openai_message({'role': 'assistant', 'content': full_content}, reasoning=full_reasoning if full_reasoning else None)

    def display_message(self, message: Message, expanded: bool = False) -> None:
        if message.has_reasoning():
            with st.expander("Thought Process", expanded=expanded):
                for i, reasoning in enumerate(message.reasoning):
                    st.markdown(reasoning.strip())
                    if i < len(message.reasoning) - 1:
                        st.divider()


def play_audio(enable: bool, client: LLM, text: str, model: str = "playai-tts", voice: str = "Fritz-PlayAI", response_format: Literal['mp3', 'opus', 'aac', 'flac', 'wav', 'pcm'] = "wav", **kwargs: Any) -> None:
    try:
        if enable:
            st.audio(client.audio(text=text, model=model, voice=voice, response_format=response_format, **kwargs), format=f'audio/{response_format}', autoplay=True)
    except openai.RateLimitError:
        st.toast('Rate limit exceeded. Please try again later.', icon="⚠️")
    except Exception:
        st.toast('Unable to generate audio', icon="⚠️")
