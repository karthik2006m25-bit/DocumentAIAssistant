import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

const ACCEPTED_TYPES = ".pdf,.docx,.pptx";

async function requestJson(url, options) {
  const response = await fetch(url, options);
  let body;
  try {
    body = await response.json();
  } catch {
    if (!response.ok) {
      throw new Error(
        "The API server is unavailable or returned an invalid response. Start FastAPI and try again.",
      );
    }
    throw new Error("The API returned an invalid response.");
  }

  if (!response.ok) {
    throw new Error(
      body.detail || "Something went wrong. Please try again.",
    );
  }

  return body;
}

export default function App() {
  const [file, setFile] = useState(null);
  const [documentInfo, setDocumentInfo] = useState(null);
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  function chooseFile(nextFile) {
    setError("");
    if (nextFile && !/\.(pdf|docx|pptx)$/i.test(nextFile.name)) {
      setError("Choose a PDF, DOCX, or PPTX file.");
      return;
    }

    setFile(nextFile);
    setDocumentInfo(null);
    setSessionId("");
    setMessages([]);
  }

  async function processDocument(event) {
    event.preventDefault();
    if (!file) return;

    setIsProcessing(true);
    setError("");
    const formData = new FormData();
    formData.append("document", file);

    try {
      const result = await requestJson("/api/documents", {
        method: "POST",
        body: formData,
      });
      setDocumentInfo(result);
      setSessionId(result.session_id);
      setMessages([]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsProcessing(false);
    }
  }

  async function sendQuestion(event) {
    event.preventDefault();
    const submittedQuestion = question.trim();
    if (!submittedQuestion || !sessionId || isSending) return;

    setQuestion("");
    setError("");
    setMessages((current) => [
      ...current,
      { role: "user", content: submittedQuestion },
    ]);
    setIsSending(true);

    try {
      const result = await requestJson("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          question: submittedQuestion,
        }),
      });
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: result.answer,
          retrievedChunks: result.retrieved_chunks,
        },
      ]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSending(false);
    }
  }

  async function clearConversation() {
    setError("");
    try {
      const result = await requestJson(
        `/api/documents/${sessionId}/conversation`,
        { method: "DELETE" },
      );
      setSessionId(result.session_id);
      setMessages([]);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Karthik DOS Assistant home">
          <span className="brand-mark" aria-hidden="true">D</span>
          <span>Karthik DOS Assistant</span>
        </a>
        <span className="topbar-note">Your documents, understood</span>
      </header>

      <section className="workspace">
        <aside className="sidebar">
          <div className="intro">
            <span className="eyebrow">KARTHIK DOS ASSISTANT</span>
            <h1>Make sense of your documents.</h1>
            <p>Upload a file, then ask questions and get answers grounded in its content.</p>
          </div>

          <form className="upload-card" onSubmit={processDocument}>
            <label
              className={`drop-zone${dragging ? " is-dragging" : ""}`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                chooseFile(event.dataTransfer.files[0] || null);
              }}
            >
              <input
                type="file"
                accept={ACCEPTED_TYPES}
                onChange={(event) => chooseFile(event.target.files[0] || null)}
              />
              <span className="upload-icon" aria-hidden="true">↑</span>
              <strong>{file ? "Change your document" : "Drop a file here"}</strong>
              <span className="drop-hint">or <span className="browse-link">browse files</span></span>
              <span className="file-types">PDF, DOCX, or PPTX</span>
            </label>

            {file && (
              <div className="selected-file">
                <span className="file-icon" aria-hidden="true">DOC</span>
                <span className="file-name" title={file.name}>{file.name}</span>
                <button
                  type="button"
                  className="remove-file"
                  aria-label="Remove selected file"
                  onClick={() => chooseFile(null)}
                >
                  ×
                </button>
              </div>
            )}

            <button
              className="primary-button process-button"
              type="submit"
              disabled={!file || isProcessing}
            >
              {isProcessing ? <><span className="spinner" /> Processing…</> : "Process document"}
            </button>
            <p className="privacy-note"><span aria-hidden="true">✦</span> Document content powers your answers.</p>
          </form>

          {documentInfo && (
            <div className="document-status">
              <span className="status-dot" />
              <div>
                <strong>Document ready</strong>
                <span>{documentInfo.chunk_count} sections indexed</span>
              </div>
            </div>
          )}

          <div className="sidebar-footer">A smarter way to read.</div>
        </aside>

        <section className="chat-panel" aria-label="Karthik DOS Assistant chat">
          <div className="chat-header">
            <div className="chat-heading">
              <span className="assistant-avatar" aria-hidden="true">✦</span>
              <div>
                <h2>Document chat</h2>
                <p>{documentInfo ? documentInfo.filename : "Upload a document to get started"}</p>
              </div>
            </div>
            {documentInfo && (
              <button
                type="button"
                className="clear-button"
                onClick={clearConversation}
                disabled={isSending}
              >
                <span aria-hidden="true">↻</span> New chat
              </button>
            )}
          </div>

          <div className={`chat-content${messages.length ? " has-messages" : ""}`}>
            {messages.length === 0 && !documentInfo ? (
              <div className="empty-state">
                <div className="empty-illustration" aria-hidden="true">
                  <span className="paper paper-back" />
                  <span className="paper paper-front"><i /><i /><i /></span>
                  <span className="sparkle">✦</span>
                </div>
                <h3>Your next insight starts here</h3>
                <p>Upload a document on the left. I’ll read it and help you find the answers you need.</p>
                <div className="suggestions">
                  <span>Summarize key points</span>
                  <span>Find specific details</span>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="ready-state">
                <span className="ready-check" aria-hidden="true">✓</span>
                <h3>Your document is ready</h3>
                <p>Ask a question to begin exploring <strong>{documentInfo.filename}</strong>.</p>
                <div className="prompt-suggestion">“What are the main takeaways?”</div>
              </div>
            ) : (
              <div className="message-list">
                {messages.map((message, index) => (
                  <article className={`message-row ${message.role}`} key={`${index}-${message.role}`}>
                    {message.role === "assistant" && (
                      <span className="message-avatar" aria-hidden="true">✦</span>
                    )}
                    <div className="message-body">
                      <span className="message-label">{message.role === "user" ? "You" : "Karthik DOS Assistant"}</span>
                      <div className="message-bubble">
                        {message.role === "assistant" ? (
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        ) : (
                          message.content
                        )}
                      </div>
                      {message.retrievedChunks?.length > 0 && (
                        <details className="source-details">
                          <summary>View {message.retrievedChunks.length} document sections</summary>
                          {message.retrievedChunks.map((chunk, chunkIndex) => (
                            <blockquote key={chunkIndex}>{chunk}</blockquote>
                          ))}
                        </details>
                      )}
                    </div>
                  </article>
                ))}
                {isSending && (
                  <article className="message-row assistant">
                    <span className="message-avatar" aria-hidden="true">✦</span>
                    <div className="message-body">
                      <span className="message-label">Karthik DOS Assistant</span>
                      <div className="message-bubble typing"><i /><i /><i /></div>
                    </div>
                  </article>
                )}
                <div ref={chatEndRef} />
              </div>
            )}
          </div>

          {error && <div className="error-banner" role="alert">{error}</div>}

          <form className="composer" onSubmit={sendQuestion}>
            <label className="sr-only" htmlFor="question">Ask a question about your document</label>
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  sendQuestion(event);
                }
              }}
              placeholder={documentInfo ? "Ask anything about your document…" : "Your question will go here once a document is ready"}
              disabled={!documentInfo || isSending}
              rows={1}
            />
            <button
              className="send-button"
              type="submit"
              aria-label="Send message"
              disabled={!documentInfo || !question.trim() || isSending}
            >
              <span aria-hidden="true">↑</span>
            </button>
            <span className="composer-hint">Enter to send · Shift + Enter for a new line</span>
          </form>
        </section>
      </section>
    </main>
  );
}
