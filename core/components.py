import time
import openai
import streamlit as st
from .message import Message
from openai.types import chat

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
                if message.reasoning_source:
                    st.caption(f"*Reasoning source: {message.reasoning_source.value}*")