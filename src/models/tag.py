from datetime import datetime
from typing import Dict, Any, List, Optional

class Tag:
    def __init__(self, id: str, name: str, color: str = '#6B73FF', created_at: Optional[str] = None):
        self.id = id
        self.name = name
        self.color = color
        self.created_at = created_at or datetime.utcnow().isoformat()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Tag':
        return Tag(
            id=str(data.get('id')),
            name=data.get('name', ''),
            color=data.get('color', '#6B73FF'),
            created_at=data.get('created_at', datetime.utcnow().isoformat())
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at
        }