import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.postgres import PostgresSaver


# Load environment variables
load_dotenv()

uri=os.getenv("SUPABASE_URI")
# ==========================================
# Gemini 3.6 Flash
# ==========================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)


# ==========================================
# Generate Answer
# ==========================================

def generate_answer(question, relevant_chunks):
    """
    Generate an answer using Gemini 3.6 Flash
    based only on retrieved PDF chunks.
    """

    # Combine retrieved chunks
    context = "\n\n".join(relevant_chunks)

    # Prompt
    prompt = f"""
You are an AI PDF Assistant.

Your job is to answer the user's question
using provided in the pdf.

Do NOT use outside knowledge.

If the answer cannot be found in the
provided context, respond:

"I couldn't find the answer in the uploaded document."

Keep the answer clear, accurate, and concise.

================ PDF CONTEXT ================

{context}

================ USER QUESTION ================

{question}

================ ANSWER ================
"""

    # Send request to Gemini 3.6 Flash
    response = llm.invoke(prompt)

    # Get response content
    content = response.content

    # ==========================================
    # Handle structured response
    # ==========================================

    if isinstance(content, list):

        text_parts = []

        for item in content:

            if isinstance(item, dict):

                if item.get("type") == "text":
                    text_parts.append(
                        item.get("text", "")
                    )

            elif isinstance(item, str):

                text_parts.append(item)

        return "".join(text_parts).strip()

    # ==========================================
    # Normal string response
    # ==========================================

    return str(content).strip()