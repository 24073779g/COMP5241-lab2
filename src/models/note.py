from datetime import datetime
from typing import Dict, Any, Optional, List
from .tag import Tag

class Note:
    def __init__(self, id: str, title: str, content: str, created_at: str, updated_at: str, tags: Optional[List[Tag]] = None, event_date: Optional[str] = None, event_time: Optional[str] = None):
        self.id = id
        self.title = title
        self.content = content
        self.created_at = created_at
        self.updated_at = updated_at
        self.tags = tags or []
        self.event_date = event_date
        self.event_time = event_time

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Note':
        # Debug logging
        print(f"Note data received: {data}")
        
        tags = []
        if 'tags' in data:
            print(f"Processing tags data in Note model: {data['tags']}")
            try:
                tag_list = data['tags']
                if isinstance(tag_list, list):
                    for tag_data in tag_list:
                        if isinstance(tag_data, dict):
                            print(f"Creating tag from data: {tag_data}")  # Debug log
                            tag = Tag.from_dict(tag_data)
                            print(f"Created tag object: {tag.to_dict()}")  # Debug log
                            tags.append(tag)
            except Exception as e:
                print(f"Error processing tags in Note model: {str(e)}")
                import traceback
                print(traceback.format_exc())  # Print full traceback
            
        return Note(
            id=str(data.get('id', '')),
            title=data.get('title', ''),
            content=data.get('content', ''),
            created_at=data.get('created_at', datetime.utcnow().isoformat()),
            updated_at=data.get('updated_at', datetime.utcnow().isoformat()),
            tags=tags,
            event_date=data.get('event_date'),
            event_time=data.get('event_time')
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': [tag.to_dict() for tag in self.tags],
            'event_date': self.event_date,
            'event_time': self.event_time
        }

