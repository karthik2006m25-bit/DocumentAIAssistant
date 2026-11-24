import uuid
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from src.database import save_message, save_query, save_response
from src.embeddings import create_embeddings, embeddings
from src.llm import generate_answer
from src.pdf_loader import extract_text
from src.retriever import retrieve_chunks
from src.text_splitter import split_text
from src.vector_store import create_vector_store


SUPPORTED_FILE_TYPES = {".pdf", ".docx", ".pptx"}


@dataclass
class DocumentSession:
    filename: str
    index: object
    chunks: list[str]
    messages: list[dict[str, str]] = field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str
    question: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    retrieved_chunks: list[str]


app = FastAPI(title="Karthik DOS Assistant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

document_sessions: dict[str, DocumentSession] = {}


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/documents")
async def process_document(document: UploadFile = File(...)):
    filename = Path(document.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a PDF, DOCX, or PPTX document.",
        )

    content = await document.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    document_path = upload_dir / f"{uuid.uuid4()}{suffix}"
    document_path.write_bytes(content)

    text = await run_in_threadpool(extract_text, str(document_path))
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from this document. It may be scanned or image-based.",
        )

    chunks = await run_in_threadpool(split_text, text)
    if not chunks:
        raise HTTPException(status_code=422, detail="No text chunks were created.")

    vectors = await run_in_threadpool(create_embeddings, chunks)
    index = await run_in_threadpool(create_vector_store, vectors)

    session_id = str(uuid.uuid4())
    document_sessions[session_id] = DocumentSession(
        filename=filename,
        index=index,
        chunks=chunks,
    )
    return {
        "session_id": session_id,
        "filename": filename,
        "chunk_count": len(chunks),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session = document_sessions.get(request.session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Document session not found. Please upload and process your document again.",
        )

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be blank.")

    session.messages.append({"role": "user", "content": question})
    await run_in_threadpool(save_message, request.session_id, "user", question)
    await run_in_threadpool(save_query, request.session_id, "user", question)

    relevant_chunks = await run_in_threadpool(
        retrieve_chunks,
        question,
        embeddings,
        session.index,
        session.chunks,
        3,
    )

    if not relevant_chunks:
        answer = "I couldn't find relevant information in the uploaded document."
    else:
        conversation_history = "".join(
            f"{message['role'].upper()}: {message['content']}\n"
            for message in session.messages[:-1]
        )
        context = "\n\n".join(relevant_chunks)
        prompt = f"""
You are an AI Document Assistant.
You are created by Karthik Manoj.

Answer the user's question using ONLY the
information available in the document context.

You also have access to the previous conversation
to understand follow-up questions.

Do NOT use outside knowledge.

If the answer cannot be found in the document context,
say:

"I couldn't find the answer in the uploaded document."

Previous conversation:
{conversation_history}

Document context:
{context}

Current question:
{question}

Answer clearly and concisely.
"""
        answer = await run_in_threadpool(generate_answer, prompt, [])

    session.messages.append({"role": "assistant", "content": answer})
    await run_in_threadpool(
        save_message, request.session_id, "assistant", answer
    )
    await run_in_threadpool(
        save_response, request.session_id, "assistant", answer
    )

    return ChatResponse(answer=answer, retrieved_chunks=relevant_chunks)


@app.delete("/api/documents/{session_id}/conversation")
async def clear_conversation(session_id: str):
    session = document_sessions.pop(session_id, None)
    if session is None:
        raise HTTPException(status_code=404, detail="Document session not found.")

    new_session_id = str(uuid.uuid4())
    session.messages.clear()
    document_sessions[new_session_id] = session
    return {"session_id": new_session_id}
