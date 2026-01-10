import json
import os
from pathlib import Path
from typing import Callable, List, Dict, Any

from flask import Flask, render_template, request, redirect, url_for, flash


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

NOTEBOOK_PATH = Path(__file__).resolve().parent / "backend_logic.ipynb"
_generate_fn_cache: Callable[[str], List[Dict[str, Any]]] | None = None
_notebook_mtime: float | None = None


def load_notebook_generator() -> Callable[[str], List[Dict[str, Any]]]:
    global _generate_fn_cache, _notebook_mtime
    current_mtime = NOTEBOOK_PATH.stat().st_mtime
    if _generate_fn_cache is not None and _notebook_mtime == current_mtime:
        return _generate_fn_cache

    with NOTEBOOK_PATH.open("r", encoding="utf-8") as f:
        nb = json.load(f)

    namespace: Dict[str, Any] = {}
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        if source.lstrip().startswith("pip "):
            # avoid running installer cells
            continue
        exec(source, namespace)

    if "generate_checkpoints" not in namespace:
        raise RuntimeError("generate_checkpoints not found in notebook")

    _generate_fn_cache = namespace["generate_checkpoints"]
    _notebook_mtime = current_mtime
    return _generate_fn_cache


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
        generator = load_notebook_generator()
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
    app.run(debug=True, port=5000)