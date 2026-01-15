# Kraftd Docs Backend (MVP)

## Setup Instructions

1. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run the FastAPI server:
   ```powershell
   uvicorn main:app --reload
   ```

## Project Structure
- `main.py` — FastAPI entry point
- `document_processing/` — PDF, Word, Excel, OCR modules
- `workflow/` — Procurement workflow orchestration
- `output/` — Output generation (Excel, PDF, Word)

## Next Steps
- Implement API endpoints in `main.py`
- Add modules for document processing, workflow, and output
