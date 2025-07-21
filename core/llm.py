import openai
from pydantic import BaseModel
from typing import Union, Optional, Any, List

class Message(BaseModel):
    role: str
    content: Union[str, dict]
    thinking: Optional[List[str]] = None

class LLM:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, **kwargs: Any) -> None:
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key, **kwargs)

    def invoke(self, model: Optional[str] = None, messages: Optional[Message] = None, **kwargs: Any) -> openai.types.Completion:
        if messages is None:
            raise ValueError("Messages must be provided for streaming.")
        
        streams = self.client.chat.completions.create(
            model=model,
            messages=[{"role": msg.role, "content": msg.content} for msg in messages],
            stream=True,
            **kwargs
        )

        return streams
        