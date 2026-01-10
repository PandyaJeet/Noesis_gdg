# Noesis

A lightweight Flask UI that calls a notebook-based Gemini 2.5 Flash helper to turn a problem statement into structured engineering checkpoints. The UI renders the generated checkpoints with optional client-side checkboxes to track completion.

## Prerequisites
- Python 3.11+
- `pip`
- A Gemini API key in the environment variable `GEMINI_API_KEY`

## Setup
1. (Optional) Create and activate a virtual environment
	```bash
	python -m venv .venv
	source .venv/bin/activate
	```
2. Install dependencies
	```bash
	pip install flask google-generativeai
	```

## Run
```bash
export GEMINI_API_KEY="YOUR_KEY"
cd project
python app.py
```
Then open http://127.0.0.1:5000.

## How it works
- The UI lives in [project/templates/index.html](project/templates/index.html) (form) and [project/templates/checkpoints.html](project/templates/checkpoints.html) (results) with styling in [project/static/style.css](project/static/style.css).
- The Flask server in [project/app.py](project/app.py) loads the notebook and exposes GET `/` and POST `/generate`.
- The Gemini call and JSON shaping logic live in [project/backend_logic.ipynb](project/backend_logic.ipynb); `generate_checkpoints(problem_statement)` is invoked from Flask.

## Notes
- Checkboxes on the results page are purely client-side state.
- If generation fails (e.g., bad key or malformed model output), the page will show a fallback error message.
