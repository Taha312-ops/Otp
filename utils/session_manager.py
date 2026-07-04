import logging
from pyrogram import Client, errors
from config import API_ID, API_HASH
from utils.database import Database

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, phone: str):
        self.phone = phone
        self.client = None

    async def login_with_otp(self, otp: str, password: str = None):
        try:
            existing_session = Database.get_session(self.phone)
            self.client = Client(
                f"session_{self.phone}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=existing_session
            )
            await self.client.connect()

            try:
                me = await self.client.get_me()
                Database.log_recovered(self.phone)
                return {"status": "success", "user": me.phone_number}
            except errors.AuthKeyUnregistered:
                pass

            sent_code = await self.client.send_code(self.phone)

            try:
                await self.client.sign_in(self.phone, sent_code.phone_code_hash, otp)
            except errors.SessionPasswordNeeded:
                if password:
                    await self.client.check_password(password)
                else:
                    return {"status": "2fa_required"}

            me = await self.client.get_me()
            session_string = await self.client.export_session_string()
            Database.save_session(self.phone, session_string)
            Database.log_recovered(self.phone)
            return {"status": "success", "user": me.phone_number}

        except errors.PhoneCodeInvalid:
            return {"status": "error", "reason": "Invalid OTP"}
        except errors.PasswordHashInvalid:
            return {"status": "error", "reason": "Invalid 2FA password"}
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {"status": "error", "reason": str(e)}
        finally:
            if self.client:
                await self.client.disconnect()
