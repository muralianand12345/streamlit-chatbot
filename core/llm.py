import openai
from openai.types import chat
from typing import Union, Optional, Any, List, Dict
from .message import Message

class LLM:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, **kwargs: Any) -> None:
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key, **kwargs)

    def invoke(self, model: str, messages: Union[List[Message], List[Dict[str, Any]]], include_reasoning_in_content: bool = False, **kwargs: Any) -> openai.Stream[chat.ChatCompletionChunk]:
        if messages and isinstance(messages[0], Message):
            if include_reasoning_in_content:
                api_messages = [msg.to_dict(include_reasoning=True) for msg in messages]
            else:
                api_messages = [msg.to_openai_format() for msg in messages]
        else:
            api_messages = messages

        streams: openai.Stream[chat.ChatCompletionChunk] = self.client.chat.completions.create(
            model=model,
            messages=api_messages,
            stream=True,
            **kwargs
        )

        return streams
    
    def invoke_sync(self, model: str, messages: Union[List[Message], List[Dict[str, Any]]], include_reasoning_in_content: bool = False, **kwargs: Any) -> Message:
        if messages and isinstance(messages[0], Message):
            if include_reasoning_in_content:
                api_messages = [msg.to_dict(include_reasoning=True) for msg in messages]
            else:
                api_messages = [msg.to_openai_format() for msg in messages]
        else:
            api_messages = messages

        response = self.client.chat.completions.create(
            model=model,
            messages=api_messages,
            **kwargs
        )
        
        content = response.choices[0].message.content or ""
        reasoning = getattr(response.choices[0].message, 'reasoning', None)

        return Message.from_openai_message({'role': 'assistant', 'content': content}, reasoning=reasoning)