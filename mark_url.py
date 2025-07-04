from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for, Response
import csv
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

SAVE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR.mkdir(parents=True, exist_ok=True)
CSV_FILE = SAVE_DIR / "mark_log.csv"
ERROR_FILE = SAVE_DIR / "error_log.txt"

if not CSV_FILE.exists():
    with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["mark_id", "timestamp", "is_simulated"])

current_id = 1

# 简单的用户名密码保护
USERNAME = "zjbci"
PASSWORD = "20250704"

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        '需要登录才能访问此页面', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

HTML_PAGE = """
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <title>打标 Web 客户端</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
      padding: 1em;
      background-color: #f9f9f9;
    }
    h1 {
      font-size: 1.8em;
      margin-bottom: 0.5em;
    }
    button {
      font-size: 1.8em;
      padding: 0.8em 2em;
      margin: 10px;
      border-radius: 12px;
      border: none;
      background-color: #007bff;
      color: white;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    button:hover {
      background-color: #0056b3;
    }
    .log {
      margin-top: 1.5em;
      font-size: 1.3em;
      color: #28a745;
      text-align: center;
    }
    form {
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
      max-width: 320px;
    }
    input[type="number"] {
      font-size: 1.2em;
      padding: 0.5em;
      width: 100%;
      box-sizing: border-box;
      margin-top: 1em;
      border-radius: 8px;
      border: 1px solid #ccc;
    }
    a {
      margin-top: 1em;
      font-size: 1.2em;
      color: #007bff;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
</style>
</head>
<body>
  <h1>打标 Web 客户端</h1>
  <form action="/mark" method="post">
    <button type="submit">📍 打标</button>
  </form>

  <form action="/set_id" method="post">
    <input type="number" name="new_id" placeholder="设置起始 ID" required style="font-size:1.2em; padding: 0.5em; margin-top:1em;">
    <button type="submit">设置 ID</button>
  </form>
  
  <form action="/delete_last" method="post">
    <button type="submit" style="background-color:#dc3545;">删除上一条记录</button>
  </form>

  <div class=\"log\">{{ message }}</div>

  <a href=\"/download\" style=\"margin-top: 1em; font-size: 1.2em; color: blue; text-decoration: underline;\">⬇ 下载打标记录</a>
</body>
</html>
"""

@app.route("/", methods=["GET"])
@requires_auth
def index():
    return render_template_string(HTML_PAGE, message="")

@app.route("/mark", methods=["POST"])
@requires_auth
def mark():
    global current_id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(CSV_FILE, "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([current_id, now, 0])
        msg = f"打标成功 | ID: {current_id} | 时间: {now}"
        current_id += 1
        return render_template_string(HTML_PAGE, message=msg)
    except Exception as e:
        with open(ERROR_FILE, "a", encoding="utf-8") as ef:
            ef.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 打标失败: {e}\n")
        return render_template_string(HTML_PAGE, message=f"打标失败: {e}")

@app.route("/set_id", methods=["POST"])
@requires_auth
def set_id():
    global current_id
    try:
        new_id = int(request.form.get("new_id"))
        current_id = new_id
        msg = f"起始 ID 已设置为 {current_id}"
        return render_template_string(HTML_PAGE, message=msg)
    except Exception as e:
        return render_template_string(HTML_PAGE, message=f"设置 ID 失败: {e}")

@app.route("/download", methods=["GET"])
def download():
    if CSV_FILE.exists():
        return send_file(CSV_FILE, as_attachment=True)
    return "文件不存在", 404
    
@app.route("/delete_last", methods=["POST"])
@requires_auth
def delete_last():
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= 1:
            msg = "没有可删除的记录"
        else:
            with open(CSV_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[:-1])
            msg = "上一条打标记录已删除"
    except Exception as e:
        msg = f"删除失败: {e}"
    return render_template_string(HTML_PAGE, message=msg)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
