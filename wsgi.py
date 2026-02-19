from flask import Flask
import sys
import traceback as tb

app = Flask(__name__)

error_info = {"error": None, "traceback": None}

# 실제 앱 로드 시도
try:
    from web_app import create_app
    app = create_app()
    print("✓ web_app loaded successfully", file=sys.stderr)
except Exception as e:
    error_info["error"] = str(e)
    error_info["traceback"] = tb.format_exc()
    print(f"✗ Failed to load web_app: {e}", file=sys.stderr)
    print(tb.format_exc(), file=sys.stderr)
    
    @app.route('/')
    def home():
        return {
            "status": "ERROR", 
            "message": "앱 초기화 실패",
            "error": error_info["error"],
            "traceback": error_info["traceback"]
        }, 500
