from typing import Union, Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class Message(BaseModel):
    role: str
    content: Union[str, Dict[str, Any]]
    reasoning: Optional[List[str]] = Field(default=None, description="Extracted reasoning/thinking steps")
    
    def __init__(self, **data):
        if 'thinking' in data:
            data['reasoning'] = data.pop('thinking')
        
        super().__init__(**data)
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not isinstance(v, (str, dict)):
            raise ValueError("Content must be either string or dict")
        return v
    
    @classmethod
    def from_openai_message(cls, message: Dict[str, Any], reasoning: Optional[str] = None) -> 'Message':
        return cls(role=message.get('role', 'assistant'), content=message.get('content', ''), reasoning=[reasoning] if reasoning else None)
    
    def get_clean_content(self) -> str:
        if isinstance(self.content, dict):
            return str(self.content)
        return self.content
    
    def has_reasoning(self) -> bool:
        return self.reasoning is not None and len(self.reasoning) > 0
    
    def to_openai_format(self) -> Dict[str, Any]:
        return {'role': self.role, 'content': self.get_clean_content()}

    def __str__(self) -> str:
        reasoning_info = f" (with {len(self.reasoning)} reasoning steps)" if self.has_reasoning() else ""
        return f"Message(role={self.role}, content_length={len(self.get_clean_content())}{reasoning_info})"