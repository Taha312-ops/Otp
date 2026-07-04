import sys
import os
from flask import Flask, request

# افزودن مسیر ریشه به sys.path تا ایمپورت‌ها کار کنند
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import app as telegram_app
import telegram

app = Flask(__name__)

@app.route('/api/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return "Webhook is active.", 200
    try:
        update_data = request.get_json()
        if not update_data:
            return "No data", 400
        update = telegram.Update.de_json(update_data, telegram_app.bot)
        telegram_app.process_update(update)
        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500

# برای اجرای محلی (اختیاری)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
