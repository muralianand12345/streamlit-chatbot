import re
import time
import openai
import streamlit as st
from config import Config
from typing import List, Tuple


class Thinking:
    def _extract_thinking_and_content(self, text: str, thinking_tag: str = Config.thinking_tag) -> Tuple[List[str], str, str, bool]:
        think_pattern = rf"<{thinking_tag}>(.*?)</{thinking_tag}>"
        thinking_matches = re.findall(think_pattern, text, re.DOTALL)
        cleaned_text = re.sub(think_pattern, "", text, flags=re.DOTALL).strip()

        open_think = text.count(f"<{thinking_tag}>")
        close_think = text.count(f"</{thinking_tag}>")
        is_thinking = open_think > close_think

        current_thinking = ""
        if is_thinking:
            last_think_pos = text.rfind(f"<{thinking_tag}>")
            if last_think_pos != -1:
                current_thinking = text[last_think_pos + len(f"<{thinking_tag}>") :]

        return thinking_matches, current_thinking, cleaned_text, is_thinking

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

    def stream_with_thinking(self, stream: openai.types.Completion) -> Tuple[str, List[str], str]:
        full_content = ""
        thinking_container = st.container()
        content_container = st.container()

        thinking_placeholder = thinking_container.empty()
        content_placeholder = content_container.empty()

        for chunk in stream:
            time.sleep(0.05)
            if chunk.choices[0].delta.content is not None:
                full_content += chunk.choices[0].delta.content

                completed_thinking, current_thinking, cleaned_content, is_thinking = (
                    self._extract_thinking_and_content(full_content)
                )

                with thinking_placeholder.container():
                    self._display_thinking(completed_thinking, current_thinking, is_thinking)

                if cleaned_content and not is_thinking:
                    content_placeholder.markdown(cleaned_content)

        final_completed, _, final_content, _ = (
            self._extract_thinking_and_content(full_content)
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
