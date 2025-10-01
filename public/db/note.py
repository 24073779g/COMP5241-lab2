from flask import Blueprint, jsonify, request
from db.note import Note, db
from datetime import datetime, date, time

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes/getAll', methods=['GET'])
def get_all_notes():
    notes = Note.query.order_by(Note.order.asc(), Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes/getById/<int:note_id>', methods=['GET'])
def get_note(note_id):
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/create', methods=['POST'])
def create_note():
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Require Title and Content'}), 400
        
        event_date = None
        if data.get('event_date'):
            try:
                event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date()
            except ValueError:
                pass

        event_time = None
        if data.get('event_time'):
            try:
                event_time = datetime.strptime(data['event_time'], '%H:%M').time()
            except ValueError:
                pass

        note = Note(
            title=data['title'],
            content=data['content'],
            tags=data.get('tags'),
            event_date=event_date,
            event_time=event_time
        )
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        note.tags = data.get('tags', note.tags)

        if 'event_date' in data:
            try:
                note.event_date = datetime.strptime(data['event_date'], '%Y-%m-%d').date() if data['event_date'] else None
            except ValueError:
                pass

        if 'event_time' in data:
            try:
                note.event_time = datetime.strptime(data['event_time'], '%H:%M').time() if data['event_time'] else None
            except ValueError:
                pass
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/updateOrder', methods=['PUT'])
def update_order():
    try:
        data = request.json
        note_ids = data.get('note_ids')
        if not note_ids or not isinstance(note_ids, list):
            return jsonify({'error': 'note_id(s) are required'}), 400
        for idx, note_id in enumerate(note_ids):
            note = Note.query.get(note_id)
            if note:
                note.order = idx
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    notes = Note.query.filter(
        (Note.title.contains(query)) | (Note.content.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/translate', methods=['POST'])
def translate():
    from src.llm import translate
    data = request.json
    content = data.get('content')
    target_lang = data.get('target_lang')
    if not content or not target_lang:
        return jsonify({'error': 'Content & Lang are required'}), 400
    try:
        translated = translate(content, target_lang)
        return jsonify({'translated_content': translated}), 200
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
