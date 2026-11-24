# Karthik DOS Assistant

The application uses a FastAPI backend and a React (Vite) frontend. Upload a PDF, DOCX, or PPTX file, then ask questions about its contents.

## Requirements

- Python 3.10+
- Node.js 18+
- Google Gemini API key
- Supabase project URL and key

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your-google-api-key
GEMINI_API_KEY=your-gemini-api-key
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-key
```

The Supabase project must have the `conversations`, `queries`, and `responses` tables used by `src/database.py`.

## Run locally

Install the Python dependencies and start the API:

```bash
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

In another terminal, install the frontend dependencies and start Vite:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend URL printed by Vite (normally `http://localhost:5173`). The Vite development server proxies `/api` requests to FastAPI on port 8000. FastAPI's interactive API documentation is available at `http://localhost:8000/docs`.

Document indexing and active chat sessions are held in the API process memory. Uploaded files are saved under `data/uploads` with generated filenames; chat messages are also written to Supabase.
