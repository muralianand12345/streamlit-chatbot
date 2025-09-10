import streamlit as st
from typing import Any
from config import Config
from core.llm import Message

class Commands:    
    COMMAND = {
        "clear-chat": "Clear's the chat history.",
        "new-chat": "Starts a new conversation.",
        "help": "Provides a list of available commands.",
        "features": "Lists the features of the chatbot."
    }

    def __init__(self, prefix: str = "/"):
        self.prefix = prefix

    def _commands(self, command: str, *args: Any) -> str:
        messages = [Message(role="system", content=Config.system_prompt)]
        if command == "clear-chat":
            st.session_state.messages = messages
            st.rerun()
            return "Chat history cleared."
        elif command == "new-chat":
            st.session_state.messages = messages
            st.rerun()
            return "New chat started."
        elif command == "help":
            help_text = "### Available commands:\n"
            for cmd, desc in self.COMMAND.items():
                help_text += f"- **/{cmd}**: {desc}\n"
            return help_text.strip()
        elif command == "features":
            return "### Features:\n- Chat history\n- Context awareness\n- Reasoning capabilities\n- Browser searching (Advanced Web search)\n- Python code execution"
        else:
            return f"Unknown command: {command}"


    def execute(self, message: str) -> str:
        if not message.startswith(self.prefix):
            return message
        command, *args = message[len(self.prefix):].split()
        return self._commands(command, *args)