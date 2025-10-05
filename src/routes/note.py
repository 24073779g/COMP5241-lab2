from flask import Blueprint, jsonify, request
from src.models.note import Note
from src.lib.supabase_client import supabase

note_bp = Blueprint('note', __name__)

def get_note_tags(note_id=None):
    """Helper function to get tags for notes"""
    try:
        # First get the note_tags entries
        note_tags_query = supabase.from_('note_tags').select('note_id, tag_id')
        if note_id:
            note_tags_query = note_tags_query.eq('note_id', note_id)
        note_tags_result = note_tags_query.execute()
        
        if not note_tags_result.data:
            return {}
            
        # Get all unique tag IDs
        tag_ids = list(set(item['tag_id'] for item in note_tags_result.data))
        
        # Get all the tags
        tags_result = supabase.from_('tags').select('*').in_('id', tag_ids).execute()
        
        # Create a map of tag_id to tag data
        tag_map = {tag['id']: tag for tag in tags_result.data}
        
        # Create the final note_tags_map
        note_tags_map = {}
        for item in note_tags_result.data:
            note_id = item['note_id']
            tag_id = item['tag_id']
            if note_id not in note_tags_map:
                note_tags_map[note_id] = []
            if tag_id in tag_map:
                note_tags_map[note_id].append(tag_map[tag_id])
        
        print(f"Note tags map: {note_tags_map}")  # Debug log
        return note_tags_map
    except Exception as e:
        print(f"Error getting note tags: {str(e)}")
        import traceback
        print(traceback.format_exc())  # Print full stack trace
        return {}

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes with their tags, ordered by most recently updated"""
    try:
        # Get tag filter from query parameters
        tag_filter = request.args.get('tags')
        tag_ids = tag_filter.split(',') if tag_filter else []

        # Build the base query for notes with tags
        if tag_ids:
            # Use a subquery to filter notes with specific tags
            query = supabase.from_('note_tags')\
                .select('note_id')\
                .in_('tag_id', tag_ids)\
                .execute()
            
            if not query.data:
                return jsonify([])  # No notes found with these tags
            
            note_ids = [item['note_id'] for item in query.data]
            
            # Get the filtered notes with their tags
            query = supabase.from_('notes')\
                .select('''
                    *,
                    tags:note_tags(
                        tag:tags(
                            id,
                            name,
                            color,
                            created_at
                        )
                    )
                ''')\
                .in_('id', note_ids)
        else:
            # If no tags specified, get all notes with their tags
            print("\n=== FETCHING NOTES WITH TAGS ===")
            query = supabase.from_('notes')\
                .select('''
                    *,
                    note_tags(
                        *,
                        tag:tags(*)
                    )
                ''')
            print("=== QUERY PREPARED ===\n")

        # Execute the query with ordering
        response = query.order('updated_at', desc=True).execute()
        
        print("\n=== DEBUGGING SUPABASE RESPONSE ===")
        print("Response data type:", type(response.data))
        print("Number of notes:", len(response.data) if response.data else 0)
        for idx, note in enumerate(response.data):
            print(f"\nNote {idx + 1}:")
            print("Keys in note:", note.keys())
            if 'note_tags' in note:
                print("note_tags data:", note['note_tags'])
        print("==============================\n")
        
        # Process the response to format tags correctly
        notes_data = []
        seen_notes = set()  # To handle potential duplicates from the join

        # Try to fetch tag associations using the helper (avoids nested select issues / RLS)
        note_tags_map = get_note_tags()
        print("Note tags map from helper:", note_tags_map)

        for note_data in response.data:
            try:
                # Skip if we've already processed this note
                note_id = note_data.get('id')
                if note_id in seen_notes:
                    continue
                seen_notes.add(note_id)

                print(f"\nProcessing note: {note_id}")  # Debug log
                print(f"Note data keys: {list(note_data.keys())}")  # Debug log

                # First try the helper mapping (works even if nested selects are restricted)
                tags = []
                if note_tags_map and note_id in note_tags_map:
                    tags = note_tags_map.get(note_id, [])
                    print(f"Using helper tags for {note_id}: {tags}")
                else:
                    # Fallback: try to parse nested structures returned by Supabase
                    print("Helper map missing or empty for this note; falling back to nested parsing")
                    # try 'note_tags' structure
                    if 'note_tags' in note_data and note_data['note_tags']:
                        for nt in note_data['note_tags']:
                            if nt and isinstance(nt, dict) and 'tag' in nt and nt['tag']:
                                tags.append(nt['tag'])
                    # try 'tags' structure (older aliasing)
                    elif 'tags' in note_data and note_data['tags']:
                        # 'tags' may be an array of note_tag objects with nested 'tag' or direct tag dicts
                        for t in note_data['tags']:
                            if isinstance(t, dict):
                                if 'tag' in t and t['tag']:
                                    tags.append(t['tag'])
                                elif 'id' in t:
                                    tags.append(t)

                print(f"Final tags list for note {note_id}: {tags}")

                # Create the complete note data
                processed_note_data = {
                    'id': note_data.get('id'),
                    'title': note_data.get('title', ''),
                    'content': note_data.get('content', ''),
                    'created_at': note_data.get('created_at', ''),
                    'updated_at': note_data.get('updated_at', ''),
                    'tags': tags,
                    'event_date': note_data.get('event_date'),
                    'event_time': note_data.get('event_time')
                }

                print(f"Processed note data: {processed_note_data}")  # Debug log
                note = Note.from_dict(processed_note_data)
                notes_data.append(note.to_dict())

            except Exception as e:
                print(f"Error processing note {note_data.get('id')}: {str(e)}")  # For debugging
                import traceback
                print(traceback.format_exc())
                continue  # Skip this note if there's an error

        return jsonify(notes_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note with optional tags"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        # Create the note first
        note_payload = {
            'title': data['title'],
            'content': data['content']
        }
        # Optional event fields
        if 'event_date' in data:
            note_payload['event_date'] = data['event_date']
        if 'event_time' in data:
            note_payload['event_time'] = data['event_time']

        response = supabase.table('notes').insert(note_payload).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to create note'}), 500
            
        note_id = response.data[0]['id']
        
        # If tags are provided, create the note-tag associations
        if 'tags' in data and isinstance(data['tags'], list):
            tag_associations = [
                {'note_id': note_id, 'tag_id': tag_id}
                for tag_id in data['tags']
            ]
            if tag_associations:
                supabase.table('note_tags').insert(tag_associations).execute()
        
        # Fetch the complete note with tags
        complete_note = supabase.from_('notes')\
            .select('''
                *,
                tags:note_tags(
                    tag:tags(*)
                )
            ''')\
            .eq('id', note_id)\
            .execute()
            
        if complete_note.data:
            note = Note.from_dict(complete_note.data[0])
            return jsonify(note.to_dict()), 201
            
        return jsonify({'error': 'Failed to fetch created note'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    try:
        response = supabase.from_('notes')\
            .select('''
                *,
                tags:note_tags(
                    tag:tags(*)
                )
            ''')\
            .eq('id', note_id)\
            .execute()
            
        if not response.data:
            return jsonify({'error': 'Note not found'}), 404
            
        note_data = response.data[0]
        # First try to get tags via helper (works around nested select/RLS issues)
        try:
            note_tags_map = get_note_tags(note_id)
        except Exception:
            note_tags_map = {}

        tags = []
        if note_tags_map and note_id in note_tags_map:
            tags = note_tags_map.get(note_id, [])
            print(f"Using helper tags for note {note_id}: {tags}")
        else:
            # Fallback: parse nested structures returned by Supabase
            print(f"Falling back to nested parsing for note {note_id}. Raw keys: {list(note_data.keys())}")
            # try 'note_tags' structure
            if 'note_tags' in note_data and note_data['note_tags']:
                for nt in note_data['note_tags']:
                    if nt and isinstance(nt, dict) and 'tag' in nt and nt['tag']:
                        tags.append(nt['tag'])
            # try 'tags' structure (older aliasing)
            elif 'tags' in note_data and note_data['tags']:
                for t in note_data['tags']:
                    if isinstance(t, dict):
                        if 'tag' in t and t['tag']:
                            tags.append(t['tag'])
                        elif 'id' in t:
                            tags.append(t)
        
        # Create the complete note data
        processed_note_data = {
            'id': note_data.get('id'),
            'title': note_data.get('title', ''),
            'content': note_data.get('content', ''),
            'created_at': note_data.get('created_at', ''),
            'updated_at': note_data.get('updated_at', ''),
            'tags': tags,
            'event_date': note_data.get('event_date'),
            'event_time': note_data.get('event_time')
        }
        
        note = Note.from_dict(processed_note_data)
        return jsonify(note.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note and its tags"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update note content if provided
        update_data = {}
        if 'title' in data:
            update_data['title'] = data['title']
        if 'content' in data:
            update_data['content'] = data['content']
        
        if update_data:
            # allow updating event fields as well
            if 'event_date' in data:
                update_data['event_date'] = data['event_date']
            if 'event_time' in data:
                update_data['event_time'] = data['event_time']

            response = supabase.table('notes').update(update_data).eq('id', note_id).execute()
            if not response.data:
                return jsonify({'error': 'Note not found'}), 404
        
        # Update tags if provided
        if 'tags' in data:
            # First, remove all existing tag associations
            supabase.table('note_tags').delete().eq('note_id', note_id).execute()
            
            # Then, create new tag associations
            if isinstance(data['tags'], list) and data['tags']:
                tag_associations = [
                    {'note_id': note_id, 'tag_id': tag_id}
                    for tag_id in data['tags']
                ]
                supabase.table('note_tags').insert(tag_associations).execute()
        
        # Fetch the updated note with tags
        response = supabase.from_('notes')\
            .select('''
                *,
                tags:note_tags(
                    tag:tags(*)
                )
            ''')\
            .eq('id', note_id)\
            .execute()
            
        if response.data:
            note = Note.from_dict(response.data[0])
            return jsonify(note.to_dict())
        return jsonify({'error': 'Failed to fetch updated note'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/generate', methods=['POST'])
def generate_notes():
    """Generate placeholder notes. Request JSON: { count: int (default 1), prefix: str (optional) }"""
    try:
        data = request.json or {}
        count = int(data.get('count', 1))
        prefix = data.get('prefix', 'Generated Note')

        created = []
        for i in range(count):
            title = f"{prefix} #{i+1}"
            content = data.get('content') or f"This is autogenerated content for {title}."
            payload = {'title': title, 'content': content}
            if 'event_date' in data:
                payload['event_date'] = data['event_date']
            if 'event_time' in data:
                payload['event_time'] = data['event_time']

            resp = supabase.table('notes').insert(payload).execute()
            if resp.data:
                created.append(resp.data[0])

        return jsonify([Note.from_dict(item).to_dict() for item in created]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        response = supabase.table('notes').delete().eq('id', note_id).execute()
        if not response.data:
            return jsonify({'error': 'Note not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    try:
        response = supabase.table('notes').select('*').or_(
            f"title.ilike.%{query}%,content.ilike.%{query}%"
        ).order('updated_at', desc=True).execute()
        
        notes = [Note.from_dict(note) for note in response.data]
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

