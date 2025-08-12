import time
import openai
import streamlit as st
from openai.types import chat
from typing import List, Tuple, Optional
from .message import Message, ReasoningSource

class Thinking:
    def __init__(self, thinking_tag: str = "think"):
        self.thinking_tag = thinking_tag
        
    def _display_thinking(self, reasoning_steps: List[str], current_thinking: str = "", is_thinking: bool = False) -> None:
        if reasoning_steps or current_thinking or is_thinking:
            with st.expander("Thinking...", expanded=True):
                for i, step in enumerate(reasoning_steps):
                    st.markdown(step.strip())
                    if i < len(reasoning_steps) - 1:
                        st.divider()

                if current_thinking:
                    if reasoning_steps:
                        st.divider()
                    st.markdown(current_thinking.strip())
                elif is_thinking and not current_thinking:
                    if reasoning_steps:
                        st.divider()
                    st.markdown("*Thinking...*")

    def stream_with_thinking(self, stream: openai.Stream[chat.ChatCompletionChunk]) -> Tuple[Message, str, str]:
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

        message = Message.from_openai_message({'role': 'assistant', 'content': full_content}, reasoning=full_reasoning if full_reasoning else None)
        return message, full_content, full_reasoning

    def display_message_thinking(self, message: Message, expanded: bool = False) -> None:
        if message.has_reasoning():
            with st.expander("Thought Process", expanded=expanded):
                for i, reasoning in enumerate(message.reasoning):
                    st.markdown(reasoning.strip())
                    if i < len(message.reasoning) - 1:
                        st.divider()

                if message.reasoning_source:
                    st.caption(f"*Reasoning source: {message.reasoning_source.value}*")

    def extract_thinking_from_content(self, content: str) -> Tuple[str, List[str]]:
        message = Message(role="temp", content=content)
        return message.get_clean_content(), message.reasoning or []

    def stream_generic_llm(self, stream_generator, content_field: str = "content", thinking_field: Optional[str] = None) -> Tuple[Message, str]:
        full_content = ""
        full_reasoning = ""
        
        thinking_container = st.container()
        content_container = st.container()
        
        thinking_placeholder = thinking_container.empty()
        content_placeholder = content_container.empty()

        for chunk in stream_generator:
            time.sleep(0.03)
            
            if content_field in chunk and chunk[content_field]:
                chunk_content = chunk[content_field]
                temp_message = Message(role="temp", content=full_content + chunk_content)
                if temp_message.has_reasoning() and temp_message.reasoning_source == ReasoningSource.CONTENT_TAGS:
                    full_content = temp_message.get_clean_content()
                    full_reasoning = "\n".join(temp_message.reasoning)
                    if full_reasoning:
                        with thinking_placeholder.container():
                            with st.expander("Thinking...", expanded=True):
                                st.markdown(full_reasoning.strip())
                else:
                    full_content += chunk_content

            if thinking_field and thinking_field in chunk and chunk[thinking_field]:
                full_reasoning += chunk[thinking_field]
                
                with thinking_placeholder.container():
                    with st.expander("Thinking...", expanded=True):
                        st.markdown(full_reasoning.strip())
            
            if full_content.strip():
                content_placeholder.markdown(full_content)

        thinking_placeholder.empty()

        if full_reasoning.strip():
            with thinking_container:
                with st.expander("Thought Process", expanded=False):
                    st.markdown(full_reasoning.strip())

        if full_content.strip():
            content_placeholder.markdown(full_content)

        reasoning_source = ReasoningSource.SEPARATE_FIELD if thinking_field else ReasoningSource.CONTENT_TAGS
        message = Message(
            role="assistant",
            content=full_content,
            reasoning=[full_reasoning] if full_reasoning else None,
            reasoning_source=reasoning_source if full_reasoning else None
        )

        return message, full_content

def create_message_with_thinking(role: str, content: str, thinking: Optional[List[str]] = None) -> Message:
    return Message(role=role, content=content, reasoning=thinking)

def convert_legacy_messages(legacy_messages: List[dict]) -> List[Message]:
    converted = []
    for msg in legacy_messages:
        if 'thinking' in msg:
            thinking = msg.pop('thinking')
            message = Message(**msg, reasoning=thinking)
        else:
            message = Message(**msg)
        converted.append(message)
    return converted