from flask import Flask, render_template_string, request, jsonify, send_file
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

HTML_PAGE = """
<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <title>打标 Web 客户端</title>
  <style>
    body {
      font-family: sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    button {
      font-size: 2.5em;
      padding: 1em 2em;
      border-radius: 12px;
    }
    .log {
      margin-top: 2em;
      font-size: 1.5em;
      color: green;
    }
  </style>
</head>
<body>
  <form action="/mark" method="post">
    <button type="submit">📍 打标</button>
  </form>
  <div class="log">{{ message }}</div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_PAGE, message="")

@app.route("/mark", methods=["POST"])
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

@app.route("/download", methods=["GET"])
def download():
    if CSV_FILE.exists():
        return send_file(CSV_FILE, as_attachment=True)
    return "文件不存在", 404

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
