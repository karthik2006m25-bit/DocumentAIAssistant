import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


def save_message(session_id, role, message):

    supabase.table("conversations").insert({
        "session_id": session_id,
        "role": role,
        "message": message
    }).execute()

def save_query(session_id, role, message):

    supabase.table("queries").insert({
        "session_id": session_id,
        "role": role,
        "message": message
    }).execute()

def save_response(session_id, role, message):

    supabase.table("responses").insert({
        "session_id": session_id,
        "role": role,
        "message": message
    }).execute()    
      

def get_conversation(session_id):

    response = (
        supabase
        .table("conversations")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )

    

    return response.data