from flask import Flask
import sys
import traceback

app = Flask(__name__)

error_message = None

# 실제 앱 로드 시도
try:
    from web_app import create_app
    app = create_app()
    print("✓ web_app loaded successfully", file=sys.stderr)
except Exception as e:
    error_message = str(e)
    traceback.print_exc()
    print(f"✗ Failed to load web_app: {e}", file=sys.stderr)
    
    @app.route('/')
    def home():
        return {
            "status": "ERROR", 
            "message": "앱 초기화 실패",
            "error": error_message,
            "traceback": traceback.format_exc()
        }, 500
