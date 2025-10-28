#=========================================================MARK OK 
#   R E P O S T A T E . P Y  || repostate.py Last Update 28/10/68
#==========================================PROGRAM BY Creative-HD
import requests
import time
import json
import random 
import os 
import sys 
from typing import Dict, Any, Optional

# =================================================================
# 1. กำหนดค่าคงที่ (CONFIGS)
# =================================================================

MONITORING_SERVER_PORT = 5000
IP_STORAGE_FILE = "server_ip.json" 

# *** ⚠️ IP เริ่มต้นที่คาดว่า Server รันอยู่ (ค่ามาตรฐาน) ***
# 🚨 FIX: ใช้ 127.0.0.1 เป็นค่า Default เพื่อให้ทดสอบบนเครื่องเดียวกันได้
# ในการรันจริง ต้องส่ง IP จริงผ่าน Command Line
DEFAULT_MONITORING_SERVER_IP = "127.0.0.1" 

# 🚨 FIX: Endpoint สำหรับ Discovery ต้องเป็น /Miner_Server/discovery
DISCOVERY_ENDPOINT_FORMAT = f"http://{{host}}:{MONITORING_SERVER_PORT}/Miner_Server/discovery" 

# การตั้งค่าการรายงาน
REPORT_INTERVAL_SEC = 30 
MAX_RETRIES = 5
RETRY_DELAY = 10 
DISCOVERY_RETRY_THRESHOLD = 3 

# =================================================================
# 2. GLOBAL STATE
# =================================================================
CURRENT_MONITORING_SERVER_IP: str = ""
REPORT_URL: str = ""
REPORT_FAILURE_COUNT: int = 0 

# =================================================================
# 3. HELPER FUNCTIONS
# =================================================================

def load_server_ip() -> str:
    """โหลด IP Server ที่ถูกบันทึกไว้ หรือใช้ค่าเริ่มต้น"""
    global CURRENT_MONITORING_SERVER_IP
    
    # 1. ตรวจสอบจาก Command Line Argument
    if len(sys.argv) > 1:
        # หากมี Argument ตัวที่ 1 ให้ใช้เป็น IP Server ทันที
        cmd_ip = sys.argv[1]
        print(f" [INFO] Using Server IP from Command Line: {cmd_ip}")
        CURRENT_MONITORING_SERVER_IP = cmd_ip
        return cmd_ip
    
    # 2. โหลดจากไฟล์
    try:
        with open(IP_STORAGE_FILE, 'r') as f:
            data = json.load(f)
            saved_ip = data.get("server_ip")
            if saved_ip:
                CURRENT_MONITORING_SERVER_IP = saved_ip
                return saved_ip
    except (FileNotFoundError, json.JSONDecodeError):
        pass # ใช้ค่าเริ่มต้น
        
    # 3. ใช้ค่าเริ่มต้น (หากยังไม่ถูกกำหนด)
    if not CURRENT_MONITORING_SERVER_IP:
        CURRENT_MONITORING_SERVER_IP = DEFAULT_MONITORING_SERVER_IP
        
    return CURRENT_MONITORING_SERVER_IP

def save_server_ip(ip: str):
    """บันทึก IP Server ลงในไฟล์"""
    data = {"server_ip": ip}
    try:
        with open(IP_STORAGE_FILE, 'w') as f:
            json.dump(data, f)
        print(f" [INFO] Server IP saved to {IP_STORAGE_FILE}: {ip}")
    except Exception as e:
        print(f" [ERROR] Failed to save IP to file: {e}")

def load_worker_config(key: str, default_value: Any) -> Any:
    """จำลองการโหลด Config ของ Worker (เช่น Name, Pass, Zone)"""
    # ในการทำงานจริง ฟังก์ชันนี้จะอ่านจากไฟล์ Config ของ Worker
    # แต่สำหรับตัวอย่างนี้ เราใช้ค่า Default
    return default_value 
    
def get_mock_stats(worker_name: str) -> Dict[str, Any]:
    """สร้าง Mock Data สำหรับการรายงาน"""
    return {
        # 🚨 FIX BUG: local_hashrate_sols_raw ต้องมีบั๊กคูณ 10 เกินมา
        "hashrate_sols_raw": random.uniform(10_000_000, 15_000_000), 
        "shares_sent": random.randint(10, 50),
        # Worker Name, Tags, Pass จะถูกเพิ่มใน send_report
    }

# =================================================================
# 4. REPORTING & DISCOVERY LOGIC
# =================================================================

def discover_server_ip(initial_ip: str) -> Optional[str]:
    """ทำการ Discovery Server IP Address"""
    global REPORT_URL
    print(f" [INFO] Attempting to discover server at {initial_ip}:{MONITORING_SERVER_PORT}")
    
    current_attempt = 0
    # 💡 ใช้ 1 IP เท่านั้น แต่ให้ Retry 3 ครั้งตาม DISCOVERY_RETRY_THRESHOLD
    while current_attempt < DISCOVERY_RETRY_THRESHOLD:
        try:
            url = DISCOVERY_ENDPOINT_FORMAT.format(host=initial_ip)
            response = requests.get(url, timeout=5) 
            response.raise_for_status() 

            discovery_data = response.json()
            new_host_address = discovery_data.get("HostAddress")
            new_report_url = discovery_data.get("ReportUrl")

            if new_host_address and new_report_url:
                print(f" [SUCCESS] Server discovered at IP: {new_host_address}")
                
                # 1. อัปเดต Global State
                REPORT_URL = new_report_url
                
                # 2. บันทึก IP ลงไฟล์
                save_server_ip(new_host_address)
                
                # 3. ส่ง IP ใหม่กลับไป
                return new_host_address
            else:
                print(" [ERROR] Discovery response incomplete.")

        except requests.exceptions.RequestException as e:
            current_attempt += 1
            print(f" [ERROR] Discovery failed at {initial_ip}. Attempt {current_attempt}/{DISCOVERY_RETRY_THRESHOLD}: {e}")
            time.sleep(1) # รอ 1 วินาทีก่อนลองใหม่
            
    return None

def update_server_ip_if_needed():
    """ตรวจสอบ IP ที่บันทึกไว้และทำการ Discovery ใหม่ถ้าจำเป็น"""
    global CURRENT_MONITORING_SERVER_IP, REPORT_URL
    
    initial_ip = load_server_ip()

    # ตรวจสอบว่ามี IP ที่บันทึกไว้ และมี Report URL แล้วหรือไม่ (เพื่อประหยัดการ Discovery)
    if initial_ip and REPORT_URL:
        # ถ้ามีข้อมูลครบถ้วน ให้ลองใช้เลย (กรณีรันซ้ำ)
        print(f" [INFO] Using saved server IP: {initial_ip}")
        CURRENT_MONITORING_SERVER_IP = initial_ip
        return True

    # ทำการ Discovery Server IP
    discovered_ip = discover_server_ip(initial_ip)
    
    if discovered_ip:
        CURRENT_MONITORING_SERVER_IP = discovered_ip
        return True
    else:
        print(" [FATAL] Server Discovery failed completely. Cannot continue.")
        sys.exit(1)


def send_report(worker_name: str, worker_tags: str, worker_pass: str) -> bool:
    """ส่งรายงานสถิติไปยัง Server"""
    global REPORT_FAILURE_COUNT, REPORT_URL
    
    if not REPORT_URL:
        print(" [CRITICAL] REPORT_URL is missing. Attempting re-discovery...")
        update_server_ip_if_needed()
        if not REPORT_URL: return False

    stats_data = get_mock_stats(worker_name)
    
    # 📌 สร้าง Payload ตาม API Contract
    payload = {
        "worker_name": worker_name,
        "hashrate_sols_raw": stats_data["local_hashrate_sols_raw"],
        "shares_sent": stats_data["local_shares_sent"],
        "tags": worker_tags,
        "worker_pass": worker_pass,
    }

    # 💡 Retry Logic
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(REPORT_URL, json=payload, timeout=15)
            response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)

            print(f" [REPORT] Worker {worker_name} reported successfully to {REPORT_URL}. Hashrate: {payload['local_hashrate_sols_raw']:.0f} Sols/s")
            REPORT_FAILURE_COUNT = 0
            return True

        except requests.exceptions.RequestException as e:
            print(f" [ERROR] Failed to report stats to {REPORT_URL}. Attempt {attempt+1}/{MAX_RETRIES}: {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    # 3. ถ้าล้มเหลวทั้งหมด
    REPORT_FAILURE_COUNT += 1 
    print(f" [CRITICAL] Failed to report stats after {MAX_RETRIES} attempts. Failure count: {REPORT_FAILURE_COUNT}")
    
    # 💡 ถ้าล้มเหลวเกินขีดจำกัด ให้ลบ IP ที่บันทึกไว้เพื่อบังคับ Discovery ใหม่
    if REPORT_FAILURE_COUNT >= DISCOVERY_RETRY_THRESHOLD:
        print(" [CRITICAL] Failure threshold reached. Deleting saved IP to force full discovery.")
        # ลบไฟล์ IP เพื่อบังคับให้โหลดค่าเริ่มต้น (หรือค่าจาก Command Line) ในครั้งถัดไป
        if os.path.exists(IP_STORAGE_FILE):
             os.remove(IP_STORAGE_FILE)
             
    return False


# =================================================================
# 5. MAIN EXECUTION BLOCK 
# =================================================================
if __name__ == '__main__':
    
    WORKER_NAME = load_worker_config('Rname', "Unknown-Worker")
    # 🚨 FIX: แยกตัวแปร Tags (Zone) และ Pass
    WORKER_TAGS = load_worker_config('Zone', "AP") # สมมติว่า Tags/Zone ใช้ Key 'Zone'
    WORKER_PASS = load_worker_config('Pass', "x")  # Pass ใช้ Key 'Pass'

    if WORKER_NAME == "Unknown-Worker":
        print(" [FATAL] Worker Name not set. Exiting.")
        sys.exit(1)
        
    update_server_ip_if_needed()
    
    print(f" [START] Starting reporting loop for worker {WORKER_NAME} every {REPORT_INTERVAL_SEC} seconds...")
    while True:
        
        report_success = send_report(WORKER_NAME, WORKER_TAGS, WORKER_PASS)
        
        # 💡 ถ้าล้มเหลวในการ Report (report_success == False) ให้ลอง Discovery ใหม่ทันที
        if not report_success:
            update_server_ip_if_needed()
            
        time.sleep(REPORT_INTERVAL_SEC)
