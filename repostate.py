#====================================================MARK[SUCCESS]
#   R E P O S T A T E . P Y       | Last Update |  [v.301068-1250]
#============================================Program by CreativeHD
import requests
import time
import json
import random 
import os 
import sys 
import socket           # Standard Library
import contextlib       # Standard Library
# 🚨 FIX: เปลี่ยนการ Import สำหรับ concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError 
from typing import Dict, Any, Optional

# =================================================================
# 0. การตั้งค่าการบันทึก Log และ Log Redirection
# =================================================================
LOG_FILE_NAME = "repostate_log.txt"

@contextlib.contextmanager
def redirect_stdout_to_file(filename):
    """Context manager to redirect all print/stdout to a log file."""
    original_stdout = sys.stdout
    with open(filename, 'a', encoding='utf-8') as f:
        sys.stdout = f
        try:
            yield
        finally:
            sys.stdout = original_stdout

# =================================================================
# 1. กำหนดค่าคงที่ (CONFIGS)
# =================================================================

MONITORING_SERVER_PORT = 5000 
IP_STORAGE_FILE = "server_ip.json" 

# *** ⚠️ IP เริ่มต้นที่คาดว่า Server รันอยู่ (ค่ามาตรฐาน 0.0.0.0 คือให้ค้นหาเอง) ***
DEFAULT_MONITORING_SERVER_IP = "0.0.0.0" 

# Endpoint สำหรับ Discovery
DISCOVERY_ENDPOINT_FORMAT = f"http://{{host}}:{MONITORING_SERVER_PORT}/Miner_Server/discovery" 

# การตั้งค่าการรายงาน
REPORT_INTERVAL_SEC = 60 
MAX_RETRIES = 5
RETRY_DELAY = 10 
DISCOVERY_RETRY_THRESHOLD = 3 

# การตั้งค่า Subnet Scan
SUBNET_SCAN_TIMEOUT_SEC = 10 # จำกัดเวลาสแกน Subnet ทั้งหมด
IP_TIMEOUT_SEC = 0.5         # Timeout สำหรับการลองต่อ IP หนึ่งครั้ง
MAX_SCAN_WORKERS = 15        # จำนวน Thread สำหรับสแกนพร้อมกัน
TARGET_SUBNET_PREFIX = "192.168.1." # วงเครือข่ายที่ต้องการสแกน

# =================================================================
# 2. GLOBAL STATE
# =================================================================
CURRENT_MONITORING_SERVER_IP: str = ""
REPORT_URL: str = ""
REPORT_FAILURE_COUNT: int = 0

# =================================================================
# 3. UTILITY FUNCTIONS (IP Discovery and Persistence)
# =================================================================

def get_local_ip() -> str:
    """Gets the local IP address of the client machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) 
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def load_server_ip() -> str:
    """Loads the last known Server IP from server_ip.json."""
    try:
        with open(IP_STORAGE_FILE, 'r') as f:
            data = json.load(f)
            ip = data.get('server_ip')
            if ip:
                print(f" [LOAD] Loaded last known IP from {IP_STORAGE_FILE}: {ip}")
                return ip
    except Exception:
        print(f" [LOAD] {IP_STORAGE_FILE} not found or corrupted. Using default.")
        
    return DEFAULT_MONITORING_SERVER_IP

def save_server_ip(ip: str):
    """Saves the newly discovered Server IP to server_ip.json."""
    try:
        with open(IP_STORAGE_FILE, 'w') as f:
            # Note: ใช้ key เป็น 'server_ip' เพื่อความสอดคล้อง
            json.dump({"server_ip": ip}, f, indent=4) 
        print(f" [INFO] New Server IP saved to {IP_STORAGE_FILE}: {ip}")
    except Exception as e:
        print(f" [ERROR] Could not save IP to {IP_STORAGE_FILE}: {e}")

def discover_server_ip(host: str) -> Optional[str]:
    """Attempts to connect to the discovery endpoint on the given host."""
    discovery_url = DISCOVERY_ENDPOINT_FORMAT.format(host=host)
    
    if host == "0.0.0.0" or host == "":
        return None

    try:
        response = requests.get(discovery_url, timeout=IP_TIMEOUT_SEC) 
        
        if response.status_code == 200:
            try:
                data = response.json()
                discovered_host = data.get('HostAddress') 

                if discovered_host:
                    print(f" [SUCCESS] Server reached at {host}. Confirmed Host: {discovered_host}")
                    # 🚨 FIX: คืนค่า discovered_host
                    return discovered_host 
            except json.JSONDecodeError:
                pass
                
    except requests.exceptions.RequestException:
        pass 
        
    return None

def run_subnet_scan(skip_ips: list) -> Optional[str]:
    """Runs a concurrent scan over the target subnet with a time limit."""
    print(f" [NETSCAN] Starting full subnet scan ({TARGET_SUBNET_PREFIX}1 to 254). Max {SUBNET_SCAN_TIMEOUT_SEC}s...")
    
    ips_to_scan = [f"{TARGET_SUBNET_PREFIX}{i}" for i in range(1, 255) 
                   if f"{TARGET_SUBNET_PREFIX}{i}" not in skip_ips]
    
    try:
        with ThreadPoolExecutor(max_workers=MAX_SCAN_WORKERS) as executor:
            future_to_ip = {executor.submit(discover_server_ip, ip): ip for ip in ips_to_scan}
            
            # 🚨 FIX: ใช้ as_completed และดักจับ TimeoutError มาตรฐาน
            for future in as_completed(future_to_ip.keys(), timeout=SUBNET_SCAN_TIMEOUT_SEC):
                result_ip = future.result()
                if result_ip:
                    print(f" [NETSCAN SUCCESS] Server found in concurrent scan: {result_ip}")
                    executor.shutdown(wait=False, cancel_futures=True)
                    return result_ip
                    
    except TimeoutError: # ดักจับ TimeoutError จาก concurrent.futures
        print(f" [NETSCAN TIMEOUT] Subnet scan timed out after {SUBNET_SCAN_TIMEOUT_SEC} seconds.")
    except Exception as e:
        # พิมพ์ Error อื่นๆ ที่ไม่ใช่ Timeout
        print(f" [NETSCAN ERROR] An error occurred during concurrent scan: {e}")
        
    return None

def update_server_ip_if_needed():
    """
    ตรรกะหลักในการโหลด, Discovery, และบันทึก IP Server (Strongest Priority Logic)
    """
    global CURRENT_MONITORING_SERVER_IP, REPORT_URL, REPORT_FAILURE_COUNT
    
    last_known_ip = load_server_ip()
    local_ip = get_local_ip()
    
    print(f" [INIT] Local IP: {local_ip}. Last Known IP: {last_known_ip}")
    discovered_ip: Optional[str] = None
    
    # --- 1. PRIORITY 1: ลอง IP ล่าสุดที่รู้จัก (Last Known IP from JSON) ---
    if last_known_ip != DEFAULT_MONITORING_SERVER_IP:
        print(f" [P1 TRY] Checking last known IP: {last_known_ip}")
        discovered_ip = discover_server_ip(last_known_ip)

    # --- 2. PRIORITY 2: ลอง IP ของเครื่อง Client เอง (Localhost/Self-Discovery) ---
    if not discovered_ip:
        print(f" [P2 TRY] Checking Localhost/Self IP: {local_ip}")
        discovered_ip = discover_server_ip("127.0.0.1")
        if not discovered_ip:
            # 🚨 Note: client 192.168.1.102 พยายามเชื่อมต่อตัวเอง 192.168.1.102 
            # ซึ่งไม่น่าจะมี Server รันอยู่ จึงข้ามไป
            # discovered_ip = discover_server_ip(local_ip)
            pass

    # --- 3. PRIORITY 3: Full Subnet Scan ---
    if not discovered_ip:
        skip_ips = [last_known_ip, local_ip, "127.0.0.1"]
        discovered_ip = run_subnet_scan(skip_ips)
        
    # --- 4. Finalizing ---
    if discovered_ip:
        
        if discovered_ip != last_known_ip:
            print(f" [UPDATE] Server IP changed from {last_known_ip} to {discovered_ip}. Saving to file.")
            save_server_ip(discovered_ip)
        else:
             print(f" [CONFIRM] Server IP {discovered_ip} is consistent with last known IP.")
             
        CURRENT_MONITORING_SERVER_IP = discovered_ip
        
    else:
        # ถ้าล้มเหลวทั้งหมด ให้ใช้ IP ล่าสุด/ค่ามาตรฐาน/Local IP เป็นทางเลือกสุดท้าย
        fallback_ip = last_known_ip if last_known_ip != DEFAULT_MONITORING_SERVER_IP else local_ip
        CURRENT_MONITORING_SERVER_IP = fallback_ip
        print(f" [CRITICAL] All discovery failed. Using fallback IP for report: {CURRENT_MONITORING_SERVER_IP}")
        
    # 🚨 กำหนด URL สำหรับการรายงาน
    REPORT_URL = f"http://{CURRENT_MONITORING_SERVER_IP}:{MONITORING_SERVER_PORT}/report_stats"
    print(f" [CONFIG] Final Report URL: {REPORT_URL}")
    
    REPORT_FAILURE_COUNT = 0


# =================================================================
# 4. REPORTING LOGIC
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

def generate_random_sols() -> float:
    """Generates a random M Sol/s value for demonstration."""
    return random.uniform(2000000.0, 3000000.0) 

def send_report(worker_name: str, worker_tags: str, worker_pass: str) -> bool:
    """Sends the worker status report to the monitoring server."""
    global REPORT_URL, REPORT_FAILURE_COUNT
    
    stats = {
        'hashrate_sols': generate_random_sols(),
        'shares_sent': 100.0 + random.randint(1, 50),
    }

    # 1. เตรียมข้อมูล Payload
    payload = {
        'worker_name': worker_name,
        'hashrate_sols': stats['hashrate_sols'],
        'shares_sent': stats['shares_sent'],
        'tags': worker_tags,         
        'worker_pass': worker_pass   
    }

    # 2. พยายามส่งรายงาน
    for attempt in range(MAX_RETRIES):
        try:
            # เพิ่ม timeout 10 วินาที สำหรับ request
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
    
    # 🆕 ใช้งาน Context Manager เพื่อบันทึก Output
    with redirect_stdout_to_file(LOG_FILE_NAME):
        
        # 1. เพิ่ม Timestamp ลงใน Log เพื่อบอกว่าเริ่มรันเมื่อไหร่
        print(f"\n========================================================")
        print(f" [SESSION START] {time.ctime()}")
        print(f"========================================================")

        # โหลด Config สำหรับ Worker
        WORKER_NAME = load_worker_config('Rname', "Unknown-Worker")
        WORKER_TAGS = load_worker_config('Zone', "AP") 
        WORKER_PASS = load_worker_config('Pass', "x")  

        if WORKER_NAME == "Unknown-Worker":
            print(" [FATAL] Worker Name not set. Exiting.")
            sys.exit(1)
            
        # เริ่มต้นการค้นหา IP
        update_server_ip_if_needed()
        
        print(f" [START] Starting reporting loop for worker {WORKER_NAME} every {REPORT_INTERVAL_SEC} seconds...")
        
        # 3. Main Loop
        while True:
            
            report_success = send_report(WORKER_NAME, WORKER_TAGS, WORKER_PASS) 
            
            # 4. ตรวจสอบการล้มเหลวและเรียก Discovery ซ้ำ
            if not report_success and REPORT_FAILURE_COUNT >= DISCOVERY_RETRY_THRESHOLD:
                print(f" [REDISCOVERY] Initiating server IP rediscovery due to {REPORT_FAILURE_COUNT} consecutive failures.")
                update_server_ip_if_needed()

            time.sleep(REPORT_INTERVAL_SEC)
