import os
import uuid
import streamlit as st

from src.pdf_loader import extract_text, extract_text_from_pdf
from src.text_splitter import split_text
from src.embeddings import embeddings, create_embeddings
from src.vector_store import create_vector_store
from src.retriever import retrieve_chunks
from src.llm import generate_answer
from src.database import save_message, get_conversation, save_query, save_response


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="🤖",
    layout="wide"
)


# ==========================================
# TITLE
# ==========================================

st.title("🤖 AI Document Assistant")
st.write("Upload a document and have a conversation about it.")


# ==========================================
# SESSION STATE
# ==========================================

if "index" not in st.session_state:
    st.session_state.index = None

if "chunks" not in st.session_state:
    st.session_state.chunks = None

if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Unique conversation ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


# ==========================================
# PDF UPLOAD
# ==========================================

document = st.file_uploader(
    "📄 Upload your document",
    type=["pdf", "docx", "pptx"]
)


# ==========================================
# PROCESS PDF
# ==========================================

if document is not None:

    st.write(f"**Selected file:** `{document.name}`")

    if st.button("🔄 Process Document"):

        with st.spinner("Processing your document..."):

            # Create upload directory
            os.makedirs("data/uploads", exist_ok=True)

            # Save uploaded document
            doc_path = os.path.join(
                "data",
                "uploads",
                document.name
            )

            with open(doc_path, "wb") as f:
                f.write(document.getbuffer())

            # ----------------------------------
            # 1. Extract text
            # ----------------------------------

            text = extract_text(doc_path)

            if not text.strip():

                st.error(
                    "Could not extract text from this document. "
                    "It may be a scanned/image-based document."
                )

                st.stop()

            # ----------------------------------
            # 2. Split text
            # ----------------------------------

            chunks = split_text(text)

            if not chunks:

                st.error("No text chunks were created.")

                st.stop()

            # ----------------------------------
            # 3. Create embeddings
            # ----------------------------------

            vectors = create_embeddings(chunks)

            # ----------------------------------
            # 4. Create FAISS index
            # ----------------------------------

            index = create_vector_store(vectors)

            # ----------------------------------
            # Save PDF information
            # ----------------------------------

            st.session_state.index = index
            st.session_state.chunks = chunks
            st.session_state.pdf_processed = True
            st.session_state.pdf_name = document.name

            # New PDF = new conversation
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []

        st.success("✅ Document processed successfully!")

        st.info(
            f"📄 **{document.name}** was divided into "
            f"**{len(chunks)} chunks**."
        )


# ==========================================
# CHAT INTERFACE
# ==========================================

if st.session_state.pdf_processed:

    st.divider()

    st.subheader("💬 Chat with your Document")


    # ======================================
    # LOAD SAVED CONVERSATION
    # ======================================

    if not st.session_state.messages:

        saved_messages = get_conversation(
            st.session_state.session_id
        )

        if saved_messages:

            st.session_state.messages = [
                {
                    "role": message["role"],
                    "content": message["message"]
                }
                for message in saved_messages
            ]


    # ======================================
    # DISPLAY CHAT HISTORY
    # ======================================

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])


    # ======================================
    # CHAT INPUT
    # ======================================

    question = st.chat_input(
        "Ask a question about your Document..."
    )


    if question:

        # ==================================
        # DISPLAY USER MESSAGE
        # ==================================

        with st.chat_message("user"):

            st.markdown(question)


        # ==================================
        # SAVE USER MESSAGE LOCALLY
        # ==================================

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )


        # ==================================
        # SAVE USER MESSAGE TO SUPABASE
        # ==================================

        save_message(
            st.session_state.session_id,
            "user",
            question
        )
        save_query(
            st.session_state.session_id,
            "user",
            question
        )


        # ==================================
        # RETRIEVE PDF CHUNKS
        # ==================================

        with st.spinner("🔎 Searching the Document..."):

            relevant_chunks = retrieve_chunks(
                question,
                embeddings,
                st.session_state.index,
                st.session_state.chunks,
                k=3
            )


        # ==================================
        # IF NO RELEVANT INFORMATION
        # ==================================

        if not relevant_chunks:

            answer = (
                "I couldn't find relevant information "
                "in the uploaded document."
            )


        else:

            # ==================================
            # CONVERSATION HISTORY
            # ==================================

            conversation_history = ""

            for message in st.session_state.messages[:-1]:

                conversation_history += (
                    f"{message['role'].upper()}: "
                    f"{message['content']}\n"
                )


            # ==================================
            # PDF CONTEXT
            # ==================================

            context = "\n\n".join(
                relevant_chunks
            )


            # ==================================
            # PROMPT
            # ==================================

            prompt = f"""
You are an AI Document Assistant.
 You are created by Karthik Manoj

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

PDF context:
{context}

Current question:
{question}

Answer clearly and concisely.
"""


            # ==================================
            # GENERATE ANSWER
            # ==================================

            with st.spinner("🤖 Generating answer..."):

                answer = generate_answer(
                    prompt,
                    []
                )


        # ==================================
        # DISPLAY AI RESPONSE
        # ==================================

        with st.chat_message("assistant"):

            st.markdown(answer)


        # ==================================
        # SAVE AI MESSAGE LOCALLY
        # ==================================

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )


        # ==================================
        # SAVE AI MESSAGE TO SUPABASE
        # ==================================

        save_message(
            st.session_state.session_id,
            "assistant",
            answer
        )

        

        save_response(
            st.session_state.session_id,
            "assistant",
            answer
        )

        # ==================================
        # SHOW RETRIEVED CONTEXT
        # ==================================

        if relevant_chunks:

            with st.expander(
                "🔎 View retrieved PDF sections"
            ):

                for i, chunk in enumerate(
                    relevant_chunks,
                    start=1
                ):

                    st.markdown(
                        f"**Retrieved Section {i}**"
                    )

                    st.write(chunk)

                    st.divider()


# ==========================================
# CLEAR CONVERSATION
# ==========================================

if st.session_state.pdf_processed:

    if st.button("🗑️ Clear Conversation"):

        # Clear local chat
        st.session_state.messages = []

        # Create a new conversation ID
        st.session_state.session_id = str(
            uuid.uuid4()
        )

        st.rerun()
