from flask import Flask, request, jsonify
import requests
import datetime

app = Flask(__name__)

# ==========================================
# MASTER CONFIGURATION (APNE TOKENS YAHAN DALEIN)
# ==========================================
NVR_IP = "192.168.1.17"
AUTH_HEADER = "Basic YWRtaW46YWRtaW5AMTIz" # admin:admin@123

TELEGRAM_BOT_TOKEN = "8725841586:AAFmiTmYoF-8MF_0TiFB0RFCd5YjFfB22CY"
TELEGRAM_CHAT_ID = "1372860931"
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbw2vMHvqK4y-oQLgGP0ix5Q-9Jo7D1RXOfg6I3w9em3czMb2Y_uSUMgJoBowAcfg23xjA/exec"

def send_telegram_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

@app.route('/api/get_task', methods=['GET'])
def get_task():
    return jsonify({
        "target_url": f"http://{NVR_IP}/cgi-bin/configManager.cgi?action=getConfig&name=VideoIn",
        "auth": AUTH_HEADER
    })

@app.route('/api/process_data', methods=['POST'])
def process_data():
    try:
        data = request.json
        raw_text = data.get('raw_data', '')
        
        if "ERROR" in raw_text or not raw_text:
            try: requests.post(GOOGLE_SHEET_URL, json={"status": "OFFLINE", "cams": 0}, timeout=2)
            except: pass
            send_telegram_alert("🚨 TMS PRO CRITICAL ALERT 🚨\nNVR connection lost or Power Cut!")
            return jsonify({"oled_l1": "NVR OFFLINE", "oled_l2": "Check LAN/Power"})

        active_cams = []
        for line in raw_text.split('\n'):
            if 'RemoteName=' in line:
                cam_name = line.split('=')[1].strip()
                if cam_name: 
                    active_cams.append(cam_name)
                    
        total_active = len(active_cams)
        system_status = "SECURE" if total_active > 0 else "VIDEO LOSS"
        
        # Update Google Sheet
        try:
            requests.post(GOOGLE_SHEET_URL, json={"status": system_status, "cams": total_active}, timeout=2)
        except: pass

        # Telegram Alert Logic
        if total_active == 0:
            send_telegram_alert("🚨 TMS PRO ALERT 🚨\nALL CAMERAS OFFLINE! Immediate check required.")
            oled_l1 = "WARNING: ALL DOWN"
            oled_l2 = "Check Cameras"
        else:
            oled_l1 = "SYSTEM SECURE"
            oled_l2 = f"Live Cams: {total_active}"

        return jsonify({"oled_l1": oled_l1, "oled_l2": oled_l2})

    except Exception as e:
        return jsonify({"oled_l1": "SERVER ERROR", "oled_l2": "Sync Failed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
