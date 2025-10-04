import sys
import os

# Add the parent directory to the Python path so we can import from api/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the Flask app from api/index.py
from api.index import application

# This is the entry point for Vercel
app = application

if __name__ == '__main__':
    app.run(debug=True)
