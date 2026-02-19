from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "OK", "message": "반도체 뉴스 서비스가 실행 중입니다"}, 200

# 실제 앱 로드 (선택사항)
if __name__ != '__main__':
    try:
        from web_app import create_app as create_real_app
        app = create_real_app()
    except:
        pass
