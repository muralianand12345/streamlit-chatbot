import openai
from openai.types import chat
from pydantic import BaseModel
from typing import Union, Optional, Any, List

class Message(BaseModel):
    role: str
    content: Union[str, dict]
    thinking: Optional[List[str]] = None

class LLM:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, **kwargs: Any) -> None:
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key, **kwargs)

    def invoke(self, model: str, messages: List[Message], **kwargs: Any) -> openai.Stream[chat.ChatCompletionChunk]:

        streams: openai.Stream[chat.ChatCompletionChunk] = self.client.chat.completions.create(
            model=model,
            messages=[{"role": msg.role, "content": msg.content} for msg in messages],
            stream=True,
            reasoning_effort="high",
            **kwargs
        )

        return streams
        