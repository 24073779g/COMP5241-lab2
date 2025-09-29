import os
from datetime import datetime
import json
from abc import ABC, abstractmethod

# Database adapters
class DatabaseAdapter(ABC):
    @abstractmethod
    def get_notes(self):
        pass
    
    @abstractmethod
    def create_note(self, title, content):
        pass
    
    @abstractmethod
    def delete_note(self, note_id):
        pass
    
    @abstractmethod
    def update_note(self, note_id, title, content):
        pass

class PostgreSQLAdapter(DatabaseAdapter):
    def __init__(self):
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        self.connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )
        self.init_table()
    
    def init_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
    
    def get_notes(self):
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
            notes = cursor.fetchall()
            return [dict(note) for note in notes]
    
    def create_note(self, title, content):
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "INSERT INTO notes (title, content) VALUES (%s, %s) RETURNING *",
                (title, content)
            )
            note = cursor.fetchone()
            self.connection.commit()
            return dict(note)
    
    def delete_note(self, note_id):
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
            self.connection.commit()
            return cursor.rowcount > 0
    
    def update_note(self, note_id, title, content):
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "UPDATE notes SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *",
                (title, content, note_id)
            )
            note = cursor.fetchone()
            self.connection.commit()
            return dict(note) if note else None

class MongoDBAdapter(DatabaseAdapter):
    def __init__(self):
        import pymongo
        
        connection_string = os.getenv('MONGODB_URI')
        self.client = pymongo.MongoClient(connection_string)
        self.db = self.client[os.getenv('MONGODB_DB_NAME', 'notesapp')]
        self.collection = self.db.notes
    
    def get_notes(self):
        notes = list(self.collection.find().sort('created_at', -1))
        for note in notes:
            note['id'] = str(note['_id'])
            del note['_id']
        return notes
    
    def create_note(self, title, content):
        note_data = {
            'title': title,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        result = self.collection.insert_one(note_data)
        note_data['id'] = str(result.inserted_id)
        del note_data['_id']
        return note_data
    
    def delete_note(self, note_id):
        from bson import ObjectId
        result = self.collection.delete_one({'_id': ObjectId(note_id)})
        return result.deleted_count > 0
    
    def update_note(self, note_id, title, content):
        from bson import ObjectId
        update_data = {
            'title': title,
            'content': content,
            'updated_at': datetime.now().isoformat()
        }
        result = self.collection.find_one_and_update(
            {'_id': ObjectId(note_id)},
            {'$set': update_data},
            return_document=pymongo.ReturnDocument.AFTER
        )
        if result:
            result['id'] = str(result['_id'])
            del result['_id']
        return result

class FileAdapter(DatabaseAdapter):
    def __init__(self):
        self.notes_file = 'notes.json'
    
    def load_notes(self):
        if not os.path.exists(self.notes_file):
            return []
        try:
            with open(self.notes_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_notes(self, notes):
        with open(self.notes_file, 'w') as f:
            json.dump(notes, f, indent=2)
    
    def get_next_id(self, notes):
        if not notes:
            return 1
        return max(note['id'] for note in notes) + 1
    
    def get_notes(self):
        notes = self.load_notes()
        notes.sort(key=lambda x: x['created_at'], reverse=True)
        return notes
    
    def create_note(self, title, content):
        notes = self.load_notes()
        new_note = {
            'id': self.get_next_id(notes),
            'title': title,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        notes.append(new_note)
        self.save_notes(notes)
        return new_note
    
    def delete_note(self, note_id):
        notes = self.load_notes()
        original_length = len(notes)
        notes = [note for note in notes if note['id'] != note_id]
        self.save_notes(notes)
        return len(notes) < original_length
    
    def update_note(self, note_id, title, content):
        notes = self.load_notes()
        for note in notes:
            if note['id'] == note_id:
                note['title'] = title
                note['content'] = content
                note['updated_at'] = datetime.now().isoformat()
                self.save_notes(notes)
                return note
        return None

def get_database_adapter():
    """Factory function to get the appropriate database adapter"""
    db_type = os.getenv('DATABASE_TYPE', 'file').lower()
    
    if db_type == 'postgresql':
        return PostgreSQLAdapter()
    elif db_type == 'mongodb':
        return MongoDBAdapter()
    else:
        return FileAdapter()