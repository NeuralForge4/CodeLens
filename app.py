from flask import Flask, jsonify, render_template, request

from analyzer import analyze_code

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    filename = payload.get("filename", "pasted_code.py")
    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "Paste or upload some Python code first."}), 400
    if len(code) > 100_000:
        return jsonify({"error": "Please keep the source code under 100,000 characters."}), 413
    if not filename.lower().endswith(".py"):
        return jsonify({"error": "This version accepts Python (.py) files only."}), 400
    try:
        return jsonify(analyze_code(code, filename))
    except Exception as exc:
        app.logger.exception("Analysis failed")
        return jsonify({"error": f"Analysis failed: {exc}"}), 500


if __name__ == "__main__":
    # Local development only. Use a production WSGI server when deploying.
    app.run(host="127.0.0.1", port=5000, debug=True)
