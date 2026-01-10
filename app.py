import os
import threading
import webbrowser
from importlib import reload
from typing import List, Dict, Any

from flask import Flask, render_template, request, redirect, url_for, flash

import backend_logic as bl

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")


def get_generator() -> Any:
    # Reload on each request to pick up edits without restarting the server.
    return reload(bl).generate_checkpoints


def _open_browser(url: str) -> None:
    # Open the app in the default browser after the server starts.
    webbrowser.open(url)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    problem = request.form.get("problem", "").strip()
    if not problem:
        flash("Please enter a problem statement.")
        return redirect(url_for("index"))

    checkpoints: List[Dict[str, Any]] = []
    error: str | None = None
    try:
        generator = get_generator()
        checkpoints = generator(problem)
    except Exception as exc:  # pylint: disable=broad-except
        error = f"Failed to generate checkpoints: {exc}"

    return render_template(
        "checkpoints.html",
        problem=problem,
        checkpoints=checkpoints,
        error=error,
    )


if __name__ == "__main__":
    # Avoid double-opening when the reloader spawns a child process.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, _open_browser, args=["http://localhost:5000"]).start()

    app.run(debug=True, host="0.0.0.0", port=5000)