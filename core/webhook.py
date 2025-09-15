import requests
from config import Config
from typing import TypedDict, Optional, List

class WebhookPayload(TypedDict):
    user: str
    thinking: Optional[List[str]] = None
    assistant: str
class WebhookError(Exception):
    pass

class WebhookLogger:
    def __init__(self):
        self.url = Config.webhook_url 

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
        if not text:
            return []
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    def _add_field_chunks(self, all_fields: List[dict], title: str, text: str) -> None:
        chunks = self._chunk_text(text)
        for i, chunk in enumerate(chunks):
            name = f"{title} (cont.)" if i > 0 else title
            value = f"```{chunk}```"
            if len(value) > 1024:
                value = value[:1018] + "```"
            all_fields.append({"name": name[:256], "value": value, "inline": False})

    def _parse_payload(self, payload: WebhookPayload) -> dict:
        
        fields: List[dict] = []

        user_message = payload['user']
        thinking_message = payload.get('thinking', None)
        assistant_message = payload['assistant']

        #USER
        self._add_field_chunks(fields, "User", user_message or "-")
        
        # THINKING
        if thinking_message:
            if isinstance(thinking_message, str):
                thinking_list = [thinking_message]
            elif isinstance(thinking_message, list):
                thinking_list = [str(x) for x in thinking_message]
            else:
                thinking_list = [str(thinking_message)]

            full_thinking = "\n\n".join(thinking_list)
            self._add_field_chunks(fields, "Thinking", full_thinking)

        #ASSISTANT
        self._add_field_chunks(fields, "Assistant", assistant_message or "-")

        embeds: List[dict] = []
        max_embeds = 10
        max_fields_per_embed = 25
        idx = 0
        total_fields = len(fields)

        while idx < total_fields and len(embeds) < max_embeds:
            slice_end = min(idx + max_fields_per_embed, total_fields)
            embed_fields = fields[idx:slice_end]
            embed = { "author": { "name": "Streamlit Chatbot", "url": "http://chatbot-murlee.streamlit.app" }, "fields": embed_fields }
            embeds.append(embed)
            idx = slice_end

        if idx < total_fields:
            embeds[-1]["fields"].append({ "name": "Note", "value": "Output truncated to fit Discord limits.", "inline": False })

        return { "username": "Chatbot", "allowed_mentions": {"parse": []}, "embeds": embeds }


    def log(self, payload: WebhookPayload) -> None:
        if not self.url:
            return
        try:
            parsed_payload = self._parse_payload(payload)
            response = requests.post(self.url, json=parsed_payload, timeout=10)
            if response.status_code != 204:
                body = None
                try:
                    body = response.json()
                except Exception:
                    body = response.text
                raise WebhookError(f"Failed to send webhook: {response.status_code} - {body}")
        except requests.RequestException as e:
            raise WebhookError(f"Failed to send webhook: {e}")