from flask import Flask
import os

app = Flask(__name__)

# 데이터베이스가 필요 없는 간단한 앱으로 시작
@app.route('/')
def hello():
    return {"status": "Service is running"}, 200

@app.route('/health')
def health():
    return {"health": "ok"}, 200

# 실제 앱 임포트 시도 (선택적)
try:
    from web_app import create_app
    app = create_app()
except Exception as e:
    print(f"Warning: Could not load web_app: {e}")
    pass
