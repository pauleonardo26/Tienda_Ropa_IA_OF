import os
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")


print("Token cargado:", bool(WHATSAPP_TOKEN))
print("Phone ID:", WHATSAPP_PHONE_NUMBER_ID)
print("Verify token:", WHATSAPP_VERIFY_TOKEN)