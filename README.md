# Noesis_gdg

Generate learning checkpoints with Gemini. You can now ground outputs on your own syllabus or notebook using retrieval.

## Setup
- Install deps: `pip install -r requirements.txt`
- Export API key: `export GEMINI_API_KEY=your_key`
- Run locally: `python app.py` then open http://localhost:5000

## Using your syllabus/notebook (RAG)
- In the form, paste reference text or upload `.txt`, `.md`, `.ipynb`, `.json`, or `.pdf` files.
- We chunk up to ~20k characters, embed with Gemini, and retrieve the top chunks (shown with rank and score) to guide checkpoint generation.
- The checkpoints page shows the exact chunks used so you can verify grounding.

## Notes
- Keep the uploaded file reasonably small; large files are trimmed before chunking.
- Ensure `FLASK_SECRET_KEY` is set in production.