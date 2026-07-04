from config import SUPABASE_URL, SUPABASE_KEY

try:
    from supabase import create_client, Client
    db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    SUPABASE_AVAILABLE = True
except:
    SUPABASE_AVAILABLE = False
    _memory_store = {"sessions": {}, "recovered": [], "attempts": []}

class Database:
    @staticmethod
    def save_session(phone: str, session_string: str):
        if SUPABASE_AVAILABLE:
            db.table("sessions").upsert({
                "phone": phone,
                "session_string": session_string,
                "created_at": "now()"
            }).execute()
        else:
            _memory_store["sessions"][phone] = session_string

    @staticmethod
    def get_session(phone: str):
        if SUPABASE_AVAILABLE:
            result = db.table("sessions").select("session_string").eq("phone", phone).execute()
            if result.data:
                return result.data[0].get("session_string")
        return _memory_store["sessions"].get(phone)

    @staticmethod
    def log_recovered(phone: str):
        if SUPABASE_AVAILABLE:
            db.table("recovered").insert({"phone": phone, "recovered_at": "now()"}).execute()
        else:
            _memory_store["recovered"].append({"phone": phone})

    @staticmethod
    def log_attempt(phone: str, status: str, reason: str = ""):
        if SUPABASE_AVAILABLE:
            db.table("attempts").insert({
                "phone": phone,
                "status": status,
                "reason": reason,
                "attempted_at": "now()"
            }).execute()
        else:
            _memory_store["attempts"].append({"phone": phone, "status": status, "reason": reason})
