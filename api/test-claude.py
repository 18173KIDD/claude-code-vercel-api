# api/test-claude.py - Python版 Claude Code SDK テスト用API
import json
import asyncio
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler

try:
    import anyio
    from claude_code_sdk import query, ClaudeCodeOptions
    SDK_AVAILABLE = True
except ImportError as e:
    SDK_AVAILABLE = False
    IMPORT_ERROR = str(e)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """GET リクエストでテスト実行"""
        
        # CORS ヘッダー設定
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if not SDK_AVAILABLE:
            # SDKがインポートできない場合
            response = {
                "status": "error",
                "message": "Claude Code SDK インポートエラー",
                "error": {
                    "type": "import_error",
                    "details": IMPORT_ERROR,
                    "suggestion": "requirements.txt の claude-code-sdk が正しくインストールされていません"
                },
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            return
        
        # Claude Code SDK テスト実行
        try:
            print("🧪 Python版 Claude Code SDK テスト開始...")
            
            # 非同期関数を同期的に実行
            result = asyncio.run(self.test_claude_code_sdk())
            
            response = {
                "status": "success",
                "message": "Python版 Claude Code SDK テスト成功！",
                "data": result,
                "environment": {
                    "python_version": f"{__import__('sys').version}",
                    "anyio_available": True,
                    "claude_sdk_available": True
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Claude Code SDK エラー: {e}")
            
            # エラーの詳細分析
            error_type = "unknown"
            suggestion = ""
            
            if "auth" in str(e).lower():
                error_type = "authentication"
                suggestion = "Claude認証設定が必要です。claude auth login を実行してください。"
            elif "timeout" in str(e).lower():
                error_type = "timeout"
                suggestion = "処理時間制限（5秒）に引っかかりました。"
            elif "module" in str(e).lower() or "import" in str(e).lower():
                error_type = "dependency"
                suggestion = "claude-code-sdk のインストールに問題があります。"
            elif "permission" in str(e).lower():
                error_type = "permission"
                suggestion = "Vercel環境でのファイルアクセス権限に問題があります。"
            
            response = {
                "status": "error",
                "message": "Python版 Claude Code SDK テスト失敗",
                "error": {
                    "type": error_type,
                    "message": str(e),
                    "suggestion": suggestion
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # JSON レスポンス送信
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    async def test_claude_code_sdk(self):
        """Claude Code SDK の実際のテスト"""
        print("📤 Claude に 'Hello Claude! 2+2は？' を送信中...")
        
        messages = []
        start_time = time.time()
        
        try:
            # 5秒でタイムアウト（Vercelの制限対策）
            async with anyio.fail_after(5):
                
                # Claude Code SDK オプション設定
                options = ClaudeCodeOptions(
                    max_turns=1,              # 1ターンのみ
                    allowed_tools=[],         # ツール使用なしでシンプルに
                    output_format="text",     # テキスト形式
                    permission_mode="default"
                )
                
                async for message in query(
                    prompt="Hello Claude! 2+2は何ですか？日本語で短く答えて。",
                    options=options
                ):
                    print(f"📨 メッセージ受信: {message}")
                    messages.append(str(message))
                    
                    # 最初のメッセージで十分
                    if len(messages) >= 1:
                        break
        
        except asyncio.TimeoutError:
            raise Exception("Timeout after 5 seconds")
        except Exception as e:
            raise Exception(f"Claude Code SDK Error: {e}")
        
        processing_time = time.time() - start_time
        
        return {
            "prompt": "Hello Claude! 2+2は何ですか？",
            "messages": messages,
            "message_count": len(messages),
            "processing_time_seconds": round(processing_time, 2),
            "sdk_version": "claude-code-sdk (Python)"
        }
    
    def do_OPTIONS(self):
        """CORS プリフライトリクエスト対応"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """今後のPOSTリクエスト対応用"""
        self.send_response(405)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "error": "Method not allowed",
            "message": "現在はGETのみサポートしています",
            "supported_methods": ["GET", "OPTIONS"]
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
