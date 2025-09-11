import time
import openai
import streamlit as st
from openai.types import chat
from typing import Any, Literal, Union
from .llm import LLM
from .message import Message

class Thinking:
    def display_message(self, message: Message, expanded: bool = False) -> None:
        if message.has_reasoning():
            with st.expander("Thought Process", expanded=expanded):
                for i, reasoning in enumerate(message.reasoning):
                    st.markdown(reasoning.strip())
                    if i < len(message.reasoning) - 1:
                        st.divider()
                        
    def thinking_message(self, response: Union[chat.ChatCompletion, openai.Stream[chat.ChatCompletionChunk]], streaming: bool) -> Message:
        if streaming:
            return self._streaming_thinking(response)
        else:
            return self._non_streaming_thinking(response)

    def _streaming_thinking(self, response: openai.Stream[chat.ChatCompletionChunk]) -> Message:
        full_content = ""
        full_reasoning = ""

        thinking_container = st.container()
        content_container = st.container()

        thinking_placeholder = thinking_container.empty()
        content_placeholder = content_container.empty()

        for chunk in response:
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

    def _non_streaming_thinking(self, response: chat.ChatCompletion) -> Message:
        full_content = ""
        full_reasoning = ""

        thinking_container = st.container()
        content_container = st.container()

        if hasattr(response.choices[0].message, 'reasoning') and response.choices[0].message.reasoning is not None:
            full_reasoning = response.choices[0].message.reasoning
        if response.choices[0].message.content is not None:
            full_content = response.choices[0].message.content
        if full_reasoning.strip():
            with thinking_container:
                with st.expander("Thought Process", expanded=False):
                    st.markdown(full_reasoning.strip())
        if full_content.strip():
            with content_container:
                st.markdown(full_content)

        return Message.from_openai_message({'role': 'assistant', 'content': full_content}, reasoning=full_reasoning if full_reasoning else None)


def play_audio(enable: bool, client: LLM, text: str, model: str = "playai-tts", voice: str = "Fritz-PlayAI", response_format: Literal['mp3', 'opus', 'aac', 'flac', 'wav', 'pcm'] = "wav", **kwargs: Any) -> None:
    try:
        if enable:
            st.audio(client.audio(text=text, model=model, voice=voice, response_format=response_format, **kwargs), format=f'audio/{response_format}', autoplay=True)
    except openai.RateLimitError:
        st.toast('Rate limit exceeded. Please try again later.', icon="⚠️")
    except Exception:
        st.toast('Unable to generate audio', icon="⚠️")
