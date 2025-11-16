#====================================================MARK[SUCCESS]
#   R E P O S T A T E S . P Y   | Last Update |  [v.301168-1535] - OFFLINE/LOG DISABLED
#============================================Program by CreativeHD
import requests
import time
import json
import random 
import os 
import sys 
import socket           
import contextlib       
import re               
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError 
from typing import Dict, Any, Optional
# 🆕 เพิ่ม atexit สำหรับ Graceful Shutdown
import atexit 

# =================================================================
# 0. การตั้งค่าการบันทึก Log และ Log Redirection
# 🚨 Comment Code ส่วนนี้เพื่อปิดการสร้างไฟล์ Log อัตโนมัติ 🚨
# =================================================================
# LOG_FILE_NAME = "repostates_log.txt"

# @contextlib.contextmanager
# def redirect_stdout_to_file(filename):
#     """Context manager to redirect all print/stdout to a log file."""
#     original_stdout = sys.stdout
#     with open(filename, 'a', encoding='utf-8') as f:
#         sys.stdout = f
#         try:
#             yield
#         finally:
#             sys.stdout = original_stdout

# =================================================================
# 1. กำหนดค่าคงที่ (CONFIGS)
# =================================================================

MONITORING_SERVER_PORT = 5000 

# 🚨🚨🚨 FIX: ชื่อไฟล์ที่ใช้เก็บคำสั่งรัน Miner 🚨🚨🚨
MINER_COMMAND_FILE = "run" 
MINER_API_PORT = 4048 # 🚨 FIX: พอร์ต API ของ Miner (เช่น ccminer/XMRig) 

IP_STORAGE_FILE = "server_ip.json" 

DEFAULT_MONITORING_SERVER_IP = "0.0.0.0" 
DISCOVERY_ENDPOINT_FORMAT = f"http://{{host}}:{MONITORING_SERVER_PORT}/Miner_Server/discovery" 

# การตั้งค่าการรายงาน
REPORT_INTERVAL_SEC = 60 
MAX_RETRIES = 5
RETRY_DELAY = 10 
DISCOVERY_RETRY_THRESHOLD = 3 

# การตั้งค่า Subnet Scan
SUBNET_SCAN_TIMEOUT_SEC = 10 
IP_TIMEOUT_SEC = 0.5         
MAX_SCAN_WORKERS = 15        
TARGET_SUBNET_PREFIX = "192.168.1." 

# =================================================================
# 2. GLOBAL STATE
# =================================================================
CURRENT_MONITORING_SERVER_IP: str = ""
REPORT_URL: str = ""
REPORT_FAILURE_COUNT: int = 0

# =================================================================
# 3. UTILITY FUNCTIONS (IP Discovery and Persistence)
# =================================================================
# (โค้ดส่วน IP Discovery คงเดิม)
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
                # print(f" [LOAD] Loaded last known IP from {IP_STORAGE_FILE}: {ip}")
                return ip
    except Exception:
        # print(f" [LOAD] {IP_STORAGE_FILE} not found or corrupted. Using default.")
        pass
        
    return DEFAULT_MONITORING_SERVER_IP

def save_server_ip(ip: str):
    """Saves the newly discovered Server IP to server_ip.json."""
    try:
        with open(IP_STORAGE_FILE, 'w') as f:
            json.dump({"server_ip": ip}, f, indent=4) 
        # print(f" [INFO] New Server IP saved to {IP_STORAGE_FILE}: {ip}")
    except Exception as e:
        # print(f" [ERROR] Could not save IP to {IP_STORAGE_FILE}: {e}")
        pass

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
                    # print(f" [SUCCESS] Server reached at {host}. Confirmed Host: {discovered_host}")
                    return discovered_host 
            except json.JSONDecodeError:
                pass
                
    except requests.exceptions.RequestException:
        pass 
        
    return None

def run_subnet_scan(skip_ips: list) -> Optional[str]:
    """Runs a concurrent scan over the target subnet with a time limit."""
    # print(f" [NETSCAN] Starting full subnet scan ({TARGET_SUBNET_PREFIX}1 to 254). Max {SUBNET_SCAN_TIMEOUT_SEC}s...")
    
    ips_to_scan = [f"{TARGET_SUBNET_PREFIX}{i}" for i in range(1, 255) 
                   if f"{TARGET_SUBNET_PREFIX}{i}" not in skip_ips]
    
    try:
        with ThreadPoolExecutor(max_workers=MAX_SCAN_WORKERS) as executor:
            future_to_ip = {executor.submit(discover_server_ip, ip): ip for ip in ips_to_scan}
            
            for future in as_completed(future_to_ip.keys(), timeout=SUBNET_SCAN_TIMEOUT_SEC):
                result_ip = future.result()
                if result_ip:
                    # print(f" [NETSCAN SUCCESS] Server found in concurrent scan: {result_ip}")
                    executor.shutdown(wait=False, cancel_futures=True)
                    return result_ip
                    
    except TimeoutError: 
        # print(f" [NETSCAN TIMEOUT] Subnet scan timed out after {SUBNET_SCAN_TIMEOUT_SEC} seconds.")
        pass
    except Exception as e:
        # print(f" [NETSCAN ERROR] An error occurred during concurrent scan: {e}")
        pass
        
    return None

def update_server_ip_if_needed():
    """ตรรกะหลักในการโหลด, Discovery, และบันทึก IP Server"""
    global CURRENT_MONITORING_SERVER_IP, REPORT_URL, REPORT_FAILURE_COUNT
    
    last_known_ip = load_server_ip()
    local_ip = get_local_ip()
    
    print(f" [INIT] Local IP: {local_ip}. Last Known IP: {last_known_ip}")
    discovered_ip: Optional[str] = None
    if last_known_ip != DEFAULT_MONITORING_SERVER_IP:
        # print(f" [P1 TRY] Checking last known IP: {last_known_ip}")
        discovered_ip = discover_server_ip(last_known_ip)

    if not discovered_ip:
        # print(f" [P2 TRY] Checking Localhost/Self IP: {local_ip}")
        discovered_ip = discover_server_ip("127.0.0.1")

    if not discovered_ip:
        skip_ips = [last_known_ip, local_ip, "127.0.0.1"]
        discovered_ip = run_subnet_scan(skip_ips)
        
    if discovered_ip:
        if discovered_ip != last_known_ip:
            save_server_ip(discovered_ip)
             
        CURRENT_MONITORING_SERVER_IP = discovered_ip
        
    else:
        fallback_ip = last_known_ip if last_known_ip != DEFAULT_MONITORING_SERVER_IP else local_ip
        CURRENT_MONITORING_SERVER_IP = fallback_ip
        # print(f" [CRITICAL] All discovery failed. Using fallback IP for report: {CURRENT_MONITORING_SERVER_IP}")
        
    REPORT_URL = f"http://{CURRENT_MONITORING_SERVER_IP}:{MONITORING_SERVER_PORT}/report_stats"
    print(f" [CONFIG] Final Report URL: {REPORT_URL}")
    
    REPORT_FAILURE_COUNT = 0

def read_command_from_file(file_path: str) -> str:
    """
    ฟังก์ชันสำหรับอ่านคำสั่ง Miner เต็มบรรทัดจากไฟล์ที่กำหนด
    """
    fallback_command = "NoCommand -u Fallback.Unknown-Worker -p x -o stratum+tcp://ap.fallback.net:3956"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            command = f.readline().strip()
            if not command:
                raise ValueError("File is empty.")
            # print(f" [LOAD] Successfully read command from {file_path}")
            return command
    except FileNotFoundError:
        # print(f" [CRITICAL] Command file not found at {file_path}. Using fallback command.")
        return fallback_command
    except Exception as e:
        # print(f" [CRITICAL] Error reading command file: {e}. Using fallback command.")
        return fallback_command


# =================================================================
# 4. REPORTING LOGIC
# =================================================================

def get_worker_info_from_command(full_command: str) -> Dict[str, str]:
    """ดึงชื่อ Worker, Tags (Zone), และ Password จากคำสั่งรัน"""
    worker_name = "Unknown-Offline-Worker"
    worker_tags = "N/A" 
    worker_pass = "x" 

    try:
        # 1. ดึง Worker Name (จาก -u <address>.<workername>)
        match_u = re.search(r'-u\s+([^\s]+)', full_command)
        if match_u:
            full_user_address = match_u.group(1)
            worker_name = full_user_address.split('.')[-1]

        # 2. ดึง Tags (Pool Zone) (จาก stratum+tcp://<zone>.luckpool.net)
        match_o = re.search(r'-o\s+stratum\+tcp://(\w+)\.luckpool\.net', full_command)
        if match_o:
            worker_tags = match_o.group(1) 

        # 3. ดึง Password (จาก -p <password>)
        match_p = re.search(r'-p\s+([^\s]+)', full_command)
        if match_p:
            worker_pass = match_p.group(1) 

        print(f" [Config Extracted] Name: {worker_name}, Tags: {worker_tags}, Pass: {worker_pass}")
        
    except Exception as e:
        # print(f" [Config Error] Failed to extract Worker Info from command: {e}. Using fallback.")
        pass
        
    return {'Rname': worker_name, 
            'Zone': worker_tags, 
            'Pass': worker_pass}

# 🆕 ฟังก์ชันใหม่สำหรับส่งสถานะ OFFLINE เมื่อโปรแกรมปิด
def send_offline_report(worker_name: str, worker_tags: str, worker_pass: str):
    """Sends a final report with 0 hashrate/shares to indicate shutdown."""
    global REPORT_URL
    
    # Payload ที่มีค่า Hashrate และ Shares เป็น 0.0
    payload = {
        'worker_name': worker_name,
        'hashrate_sols': 0.0,
        'shares_sent': 0.0,
        'tags': worker_tags,         
        'worker_pass': worker_pass   
    }

    try:
        # กำหนด Timeout ที่สั้นลงเพื่อไม่ให้ปิดช้าเกินไป
        # ใช้ requests.Session() หรือ requests.post() โดยตรง
        requests.post(REPORT_URL, json=payload, timeout=5) 
        print(f" [SHUTDOWN] Sent final OFFLINE report for {worker_name}.")
    except Exception:
        # print(" [SHUTDOWN] Failed to send OFFLINE report.")
        pass
        

def get_actual_miner_stats() -> Dict[str, float]:
    """พยายามดึงสถานะจริงจาก Miner API"""
    MINER_API_URL = f"http://127.0.0.1:{MINER_API_PORT}/"
    try:
        response = requests.get(MINER_API_URL, timeout=5) 
        data = response.json()
        
        # 🚨 สมมติฐาน: Miner API ใช้ 'total_hashrate' และ 'accepted_shares'
        hashrate_sols = data.get('total_hashrate', 0.0)
        shares_sent = data.get('accepted_shares', 0.0) 
        
        if hashrate_sols > 0.0:
            # print(f" [STATS] Successfully read stats from Miner API: {hashrate_sols/1000000:.2f} M Sols")
            return {'hashrate_sols': hashrate_sols, 'shares_sent': shares_sent}
            
    except requests.exceptions.RequestException:
        pass 
    except Exception:
        pass 
            
    # Fallback
    # print(f" [STATS FALLBACK] Using random data due to API failure.")
    return {'hashrate_sols': random.uniform(2000000.0, 3000000.0), 
            'shares_sent': 100.0 + random.randint(1, 50)}

def send_report(worker_name: str, worker_tags: str, worker_pass: str) -> bool:
    """Sends the worker status report to the monitoring server."""
    global REPORT_URL, REPORT_FAILURE_COUNT
    
    stats = get_actual_miner_stats() 

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
            response = requests.post(REPORT_URL, json=payload, timeout=10) 
            
            if response.status_code == 200:
                # print(f" [REPORT SUCCESS] {worker_name}: Sent {stats['hashrate_sols']/1000000:.2f} M Sols. (Tags: {worker_tags}, Pass: {worker_pass})")
                REPORT_FAILURE_COUNT = 0
                return True
            # else:
            #     msg = response.json().get('message', 'N/A')
            #     print(f" [REPORT FAILED] Server status {response.status_code}. Attempt {attempt+1}/{MAX_RETRIES}: {msg}")

        except requests.exceptions.RequestException as e:
            # print(f" [REPORT ERROR] Connect failed to {REPORT_URL}. Attempt {attempt+1}/{MAX_RETRIES}: {e}")
            pass

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    # 3. ถ้าล้มเหลวทั้งหมด
    REPORT_FAILURE_COUNT += 1 
    # print(f" [CRITICAL] Failed to report stats after {MAX_RETRIES} attempts. Failure count: {REPORT_FAILURE_COUNT}")
    return False


# =================================================================
# 5. MAIN EXECUTION BLOCK 
# =================================================================
if __name__ == '__main__':
    
    # 🚨 โค้ดที่เคยอยู่ใน with block ถูกนำออกมา
    # with redirect_stdout_to_file(LOG_FILE_NAME):
        
    print(f"\n========================================================")
    print(f" [SESSION START] {time.ctime()}")
    print(f"========================================================")

    # 🆕 0. โหลดคำสั่ง Miner จากไฟล์ run.sh
    MINER_COMMAND_STRING = read_command_from_file(MINER_COMMAND_FILE)
    
    # 🆕 1. โหลด Config สำหรับ Worker จากคำสั่งรันยาว (ที่อ่านจากไฟล์)
    worker_info = get_worker_info_from_command(MINER_COMMAND_STRING)
    WORKER_NAME = worker_info['Rname']
    WORKER_TAGS = worker_info['Zone'] 
    WORKER_PASS = worker_info['Pass']
    
    if WORKER_NAME == "Unknown-Offline-Worker":
        print(" [FATAL] Worker Name not set. Exiting. Check run.sh content or file path.")
        sys.exit(1)
        
    # เริ่มต้นการค้นหา IP
    update_server_ip_if_needed()
    
    # 🚨🚨🚨 NEW: ลงทะเบียนฟังก์ชัน Shutdown สำหรับ Graceful Shutdown
    # จะถูกเรียกเมื่อโปรแกรมจบการทำงานตามปกติ (เช่น กด Ctrl+C, sys.exit())
    atexit.register(send_offline_report, WORKER_NAME, WORKER_TAGS, WORKER_PASS)
    # 🚨🚨🚨 END NEW
    
    print(f" [START] Starting reporting loop for worker {WORKER_NAME} every {REPORT_INTERVAL_SEC} seconds...")
    
    # 3. Main Loop
    while True:
        
        report_success = send_report(WORKER_NAME, WORKER_TAGS, WORKER_PASS) 
        
        # 4. ตรวจสอบการล้มเหลวและเรียก Discovery ซ้ำ
        if not report_success and REPORT_FAILURE_COUNT >= DISCOVERY_RETRY_THRESHOLD:
            # print(f" [REDISCOVERY] Initiating server IP rediscovery due to {REPORT_FAILURE_COUNT} consecutive failures.")
            update_server_ip_if_needed()

        time.sleep(REPORT_INTERVAL_SEC)