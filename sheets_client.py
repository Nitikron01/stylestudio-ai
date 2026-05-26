import json
import os

from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# โหลดค่า .env
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet():
    """เชื่อมต่อ Google Sheets"""

    json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")

    print("กำลังหาไฟล์ service account...")
    print("FILE PATH =", file_path)

    if json_str:
        info = json.loads(json_str)

        creds = Credentials.from_service_account_info(
            info,
            scopes=SCOPES
        )

    elif file_path:
        creds = Credentials.from_service_account_file(
            file_path,
            scopes=SCOPES
        )

    else:
        raise RuntimeError(
            "❌ ไม่พบการตั้งค่ากุญแจสิทธิ์ Google Service Account (.json)"
        )

    client = gspread.authorize(creds)

    sheet_id = os.getenv("GOOGLE_SHEETS_ID")

    return client.open_by_key(sheet_id).sheet1