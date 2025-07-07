from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for, Response
import csv
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

SAVE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# 总记录文件（不分日期，始终追加）
CSV_FILE = SAVE_DIR / "mark_log.csv"
# 每日记录文件（按天存）
today_str = datetime.now().strftime("%Y-%m-%d")
DAILY_FILE = SAVE_DIR / f"daily_log_{today_str}.csv"

ERROR_FILE = SAVE_DIR / "error_log.txt"

# 初始化文件头
for file in [CSV_FILE, DAILY_FILE]:
    if not file.exists():
        with open(file, "w", newline='', encoding="utf-8") as f:
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

  <form action="/clear" method="post">
    <button type="submit" style="background-color:#dc3545;">🗑 清空所有记录</button>
  </form>

  <form action="/delete_last" method="post">
    <button type="submit" style="background-color:#ff8800;">撤销今日最后一条</button>
  </form>

  <div class=\"log\">{{ message }}</div>

  <a href="/download" style="margin-top: 1em; font-size: 1.2em; color: blue; text-decoration: underline;">⬇ 下载总记录</a>
  <a href="/download_today" style="margin-top: 0.5em; font-size: 1.2em; color: green; text-decoration: underline;">⬇ 下载今日记录</a>
</body>
  <form action="/download_selected" method="post">
    <label style="margin-top: 1em; font-size: 1em;">选择要下载的日期（可多选）</label>
    <select name="dates" multiple size="5" style="margin-top: 0.5em; padding: 0.5em; font-size: 1em; width: 90%; max-width: 300px;">
      {% for file in history_files %}
        <option value="{{ file }}">{{ file }}</option>
      {% endfor %}
    </select>
    <button type="submit" style="margin-top: 0.5em; background-color: #555;">⬇ 批量下载选中记录</button>
  </form>
</body>
</html>
"""

@app.route("/", methods=["GET"])
@requires_auth
def index():
    history_files = [f.name for f in SAVE_DIR.glob("daily_log_*.csv")]
    return render_template_string(HTML_PAGE, message="", history_files=history_files)

@app.route("/mark", methods=["POST"])
@requires_auth
def mark():
    global current_id
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        for file in [CSV_FILE, DAILY_FILE]:
            with open(file, "a", newline='', encoding="utf-8") as f:
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

@app.route("/download_today", methods=["GET"])
def download_today():
    if DAILY_FILE.exists():
        return send_file(DAILY_FILE, as_attachment=True)
    return "今日记录不存在", 404
    return "文件不存在", 404

@app.route("/clear", methods=["POST"])
@requires_auth
def clear_log():
    global current_id
    try:
        with open(CSV_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["mark_id", "timestamp", "is_simulated"])
        current_id = 1
        msg = "✅ 打标记录已清空"
    except Exception as e:
        msg = f"清空失败: {e}"
    return render_template_string(HTML_PAGE, message=msg)

@app.route("/delete_last", methods=["POST"])
@requires_auth
def delete_last():
    try:
        with open(DAILY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= 1:
            msg = "没有可删除的记录"
        else:
            with open(DAILY_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[:-1])
            msg = "✅ 已删除今日最后一条记录"
    except Exception as e:
        msg = f"删除失败: {e}"
    return render_template_string(HTML_PAGE, message=msg)

@app.route("/download_selected", methods=["POST"])
@requires_auth
def download_selected():
    from flask import make_response
    import zipfile
    from io import BytesIO
    selected = request.form.getlist("dates")
    if not selected:
        return render_template_string(HTML_PAGE, message="请选择至少一个文件")
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for filename in selected:
            file_path = SAVE_DIR / filename
            if file_path.exists():
                zip_file.write(file_path, arcname=filename)
    zip_buffer.seek(0)
    response = make_response(zip_buffer.read())
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = 'attachment; filename=selected_logs.zip'
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
