#====================================================MARK[SUCCESS]
#   R E P O S T A T E . P Y       | Last Update |  [v.281068-1221]
#============================================Program by CreativeHD
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
DEFAULT_MONITORING_SERVER_IP = "192.168.1.111" 

# 🚨 FIX: Endpoint สำหรับ Discovery ต้องเป็น /Miner_Server/discovery
DISCOVERY_ENDPOINT_FORMAT = f"http://{{host}}:{MONITORING_SERVER_PORT}/Miner_Server/discovery" 

# การตั้งค่าการรายงาน
REPORT_INTERVAL_SEC = 60 
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
# 3. UTILITY FUNCTIONS (IP Discovery and Persistence)
# =================================================================

def save_server_ip(ip: str):
    """Saves the discovered server IP to a JSON file."""
    try:
        with open(IP_STORAGE_FILE, 'w') as f:
            json.dump({'MONITORING_SERVER_IP': ip}, f, indent=4)
        print(f" [INFO] New Server IP saved to {IP_STORAGE_FILE}: {ip}")
    except Exception as e:
        print(f" [ERROR] Failed to save IP to {IP_STORAGE_FILE}: {e}")

def load_server_ip() -> str:
    """Loads the server IP from a JSON file, หรือใช้ค่า DEFAULT"""
    try:
        if os.path.exists(IP_STORAGE_FILE):
            with open(IP_STORAGE_FILE, 'r') as f:
                data = json.load(f)
                ip = data.get('MONITORING_SERVER_IP')
                if ip:
                    print(f" [INFO] Server IP loaded from file: {ip}")
                    return ip
    except Exception as e:
        print(f" [WARNING] Could not load IP from file. Using default IP. ({e})")
        
    print(f" [INFO] Using default Server IP: {DEFAULT_MONITORING_SERVER_IP}")
    return DEFAULT_MONITORING_SERVER_IP

def discover_server_ip(ip_to_check: str) -> Optional[str]:
    """Attempts to find the server's correct IP using the discovery endpoint."""
    discovery_url = DISCOVERY_ENDPOINT_FORMAT.format(host=ip_to_check)
    print(f" [DISCOVERY] Trying to reach Server at: {discovery_url}")
    
    try:
        response = requests.get(discovery_url, timeout=3) 
        response.raise_for_status() 
        
        data = response.json()
        discovered_host = data.get('HostAddress') 

        if discovered_host:
            print(f" [SUCCESS] Server reached at {ip_to_check}. Confirmed Host: {discovered_host}")
            return discovered_host
        
    except requests.exceptions.RequestException as e:
        print(f" [DISCOVERY FAILED] Cannot connect to {ip_to_check} for discovery: {e}")
        return None
    
    return None 

def update_server_ip_if_needed():
    """
    ตรรกะหลักในการโหลด, Discovery, และบันทึก IP Server
    """
    global CURRENT_MONITORING_SERVER_IP, REPORT_URL, REPORT_FAILURE_COUNT
    
    last_known_ip = load_server_ip()
    
    discovered_ip = discover_server_ip(last_known_ip)
    
    if not discovered_ip and last_known_ip != DEFAULT_MONITORING_SERVER_IP:
        # ลอง Discovery ด้วยค่ามาตรฐาน
        print(f" [FALLBACK] Last known IP failed. Trying default IP: {DEFAULT_MONITORING_SERVER_IP}")
        discovered_ip = discover_server_ip(DEFAULT_MONITORING_SERVER_IP)
        
    if discovered_ip:
        CURRENT_MONITORING_SERVER_IP = discovered_ip
        
        # บันทึก IP ใหม่ ถ้ามันไม่ตรงกับ IP ที่โหลดมาล่าสุด/ค่ามาตรฐาน
        if discovered_ip != last_known_ip:
            print(f" [UPDATE] Server IP changed from {last_known_ip} to {discovered_ip}. Saving to file.")
            save_server_ip(discovered_ip)
        else:
             print(f" [CONFIRM] Server IP {discovered_ip} is consistent with last known IP.")
    
    else:
        # ถ้าล้มเหลวทั้งหมด ให้ใช้ IP ล่าสุด/ค่ามาตรฐานต่อไป 
        CURRENT_MONITORING_SERVER_IP = last_known_ip
        print(f" [CRITICAL] All discovery failed. Using last known IP for report: {CURRENT_MONITORING_SERVER_IP}")
        
    # 🚨 FIX: REPORT_URL ต้องเป็น /report_stats
    REPORT_URL = f"http://{CURRENT_MONITORING_SERVER_IP}:{MONITORING_SERVER_PORT}/report_stats"
    print(f" [CONFIG] Final Report URL: {REPORT_URL}")
    
    REPORT_FAILURE_COUNT = 0


# =================================================================
# 4. FUNCTION DEFINITION BLOCK (Config & Stats)
# =================================================================

def load_worker_config(key: str, default_val: str) -> str:
    """ดึงค่าจาก set-miner/miner.json"""
    config_path = os.path.join("set-miner", "miner.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as set_file:
                config_data = json.load(set_file)
                value = config_data.get(key)
                if value:
                    print(f" [Config Loaded] {key}: {value}")
                    return value
        except Exception as e:
            print(f" [Config Error] Failed to read or parse miner.json for {key}. Error: {e}")
            
    print(f" [Config Warning] {key} not found. Using fallback '{default_val}'.")
    return default_val


def get_ccminer_stats():
    """ดึง Hashrate และ Shares (ใช้ค่าจำลอง Hashrate ปกติ)"""
    
    # 🚨 NOTE: Hashrate ที่นี่คือ H/s (Sols/sec)
    current_hashrate = random.uniform(2000000.0, 3000000.0) # 2.00M - 3.00M Sols/sec
    current_shares = 100.0 + random.randint(1, 50) 
    
    return {
        'hashrate_sols': current_hashrate, 
        'shares_sent': current_shares,
    }


def send_report(worker_name, worker_tags, worker_pass):
    """ส่งรายงานไปยัง Monitoring Server พร้อม Retry Logic"""
    global REPORT_URL, REPORT_FAILURE_COUNT
    
    stats = get_ccminer_stats()
    
    # 1. กำหนด Payload
    payload = {
        'worker_name': worker_name,
        'hashrate_sols': stats['hashrate_sols'],
        'shares_sent': stats['shares_sent'],
        'tags': worker_tags,         # ส่ง AP/EU/NA
        'worker_pass': worker_pass   # ส่ง hybrid/x
    }
    
    # 2. เริ่ม Retry Loop
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(REPORT_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f" [REPORT SUCCESS] {worker_name}: Sent {stats['hashrate_sols']/1000000:.2f} M Sols. (Tags: {worker_tags}, Pass: {worker_pass})")
                REPORT_FAILURE_COUNT = 0 
                return True
            else:
                msg = response.json().get('message', 'N/A')
                print(f" [REPORT FAILED] Server status {response.status_code}. Attempt {attempt+1}/{MAX_RETRIES}: {msg}")
        
        except requests.exceptions.RequestException as e:
            print(f" [REPORT ERROR] Connect failed to {REPORT_URL}. Attempt {attempt+1}/{MAX_RETRIES}: {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    # 3. ถ้าล้มเหลวทั้งหมด
    REPORT_FAILURE_COUNT += 1 
    print(f" [CRITICAL] Failed to report stats after {MAX_RETRIES} attempts. Failure count: {REPORT_FAILURE_COUNT}")
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
        
        if not report_success and REPORT_FAILURE_COUNT >= DISCOVERY_RETRY_THRESHOLD:
            print(f" [REDISCOVERY] Initiating server IP rediscovery due to {REPORT_FAILURE_COUNT} consecutive failures.")
            update_server_ip_if_needed()

        time.sleep(REPORT_INTERVAL_SEC)
