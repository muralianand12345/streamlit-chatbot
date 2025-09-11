import openai
from openai.types import chat
from typing import Union, Optional, Any, List, Dict, Literal
from .message import Message

class LLM:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, **kwargs: Any) -> None:
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key, **kwargs)

    def invoke(self, model: str, messages: Union[List[Message], List[Dict[str, Any]]], stream: bool = True, **kwargs: Any) -> Union[chat.ChatCompletion, openai.Stream[chat.ChatCompletionChunk]]:
        if messages and isinstance(messages[0], Message):
            api_messages = [msg.to_openai_format() for msg in messages]
        else:
            api_messages = messages

        response: Union[chat.ChatCompletion, openai.Stream[chat.ChatCompletionChunk]] = self.client.chat.completions.create(
            model=model,
            messages=api_messages,
            stream=stream,
            **kwargs
        )

        return response

    def audio(self, text: str, model: str = "playai-tts", voice: str = "Fritz-PlayAI", response_format: Literal['mp3', 'opus', 'aac', 'flac', 'wav', 'pcm'] = "wav", **kwargs: Any) -> bytes:
        response = self.client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format,
            **kwargs
        )

        return response.content