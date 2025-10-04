import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.db.user import db
from src.routes.user import user_bp
from src.routes.note import note_bp
from dotenv import load_dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

CORS(app)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')

load_dotenv()
# Set a default SQLite database if DATABASE_URL is not provided
database_url = os.getenv("DATABASE_URL")
if not database_url:
    # Use SQLite as fallback for local development
    database_url = "sqlite:///notes.db"
    
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def serve_index():
    return send_from_directory('../src/pages', 'index.html')

@app.route('/debug')
def debug():
    return "Python application is working!", 200

@app.route('/debug/routes')
def debug_routes():
    """Debug endpoint to show all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    return jsonify(routes)

application = app