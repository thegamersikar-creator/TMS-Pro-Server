from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ==========================================
# 1. MASTER SETTINGS (Yahan apka data aayega)
# ==========================================
NVR_IP = "192.168.1.17"
AUTH_HEADER = "Basic YWRtaW46YWRtaW5AMTIz" # admin:admin@123 ka Encrypted roop

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
GOOGLE_SHEET_URL = "YOUR_GOOGLE_SHEET_URL"

def send_telegram_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

# ==========================================
# 2. ESP32 YAHAN SE TASK LEGA
# ==========================================
@app.route('/api/get_task', methods=['GET'])
def get_task():
    # Server ESP32 ko target bhejega ki NVR me kahan attack karna he
    return jsonify({
        "target_url": f"http://{NVR_IP}/cgi-bin/configManager.cgi?action=getConfig&name=VideoIn",
        "auth": AUTH_HEADER
    })

# ==========================================
# 3. ESP32 YAHAN RAW DATA BHEJEGA (Brain Processing)
# ==========================================
@app.route('/api/process_data', methods=['POST'])
def process_data():
    try:
        data = request.json
        raw_text = data.get('raw_data', '')
        
        if "ERROR" in raw_text or not raw_text:
            return jsonify({"oled_l1": "NVR OFFLINE", "oled_l2": "Check LAN Cable"})

        active_cams = []
        
        # 🧠 THE BRAIN: NVR ke text ko padhna
        for line in raw_text.split('\n'):
            if 'RemoteName=' in line:
                cam_name = line.split('=')[1].strip()
                if cam_name: # Agar camera ka naam khali nahi he to matlab wo on he
                    active_cams.append(cam_name)
                    
        total_active = len(active_cams)
        
        # 👉 Yahan apka Google Sheet update hoga
        try:
            requests.post(GOOGLE_SHEET_URL, json={"status": "Online", "cams": total_active}, timeout=2)
        except: pass

        # 👉 Telegram Alert aur OLED Control
        if total_active == 0:
            send_telegram_alert("🚨 TMS PRO ALERT: Sare Camera Offline ho gaye hain! Site check karein.")
            oled_l1 = "WARNING: ALL DOWN"
            oled_l2 = "System Alert Sent"
        else:
            oled_l1 = "SYSTEM SECURE"
            oled_l2 = f"Live Cams: {total_active}"

        # Server ESP ko batayega ki screen par kya chhapna he
        return jsonify({"oled_l1": oled_l1, "oled_l2": oled_l2})

    except Exception as e:
        return jsonify({"oled_l1": "SERVER ERROR", "oled_l2": "Processing Fail"})

# ==========================================
# 4. SERVER START
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
