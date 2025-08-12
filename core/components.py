import time
import openai
import streamlit as st
from openai.types import chat
from typing import List, Tuple

class Thinking:
    def _display_thinking(self, completed_thinking: List[str], current_thinking: str, is_thinking: bool) -> None:
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

    def stream_with_thinking(self, stream: openai.Stream[chat.ChatCompletionChunk]) -> Tuple[str, List[str], str]:
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

        return full_content, [full_reasoning] if full_reasoning else [], full_content
