import sys
import traceback

try:
    from web_app import create_app
    app = create_app()
except Exception as e:
    print(f"Error initializing app: {e}", file=sys.stderr)
    traceback.print_exc()
    # Fallback: Return a minimal Flask app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def status():
        return {"status": "Error during initialization"}, 500
