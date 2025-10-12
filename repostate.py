import requests
import time
import json
import random 
import os 
import sys 

# =================================================================
# 1. กำหนดค่าคงที่ (CONFIGS)
# =================================================================

# *** ต้องแก้ไข IP Address ตรงนี้! ***
MONITORING_SERVER_IP = "192.168.1.111"  
REPORT_URL = f"http://{MONITORING_SERVER_IP}:5000/report_stats"
REPORT_INTERVAL_SEC = 300 
MAX_RETRIES = 20 
RETRY_DELAY = 10 


# =================================================================
# 2. FUNCTION DEFINITION BLOCK
# =================================================================

def load_worker_name():
    """ดึงค่า 'Rname' (Worker Name) จากไฟล์ set-miner/miner.json"""
    config_path = os.path.join("set-miner", "miner.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as set_file:
                config_data = json.load(set_file)
                worker_name = config_data.get('Rname')
                if worker_name:
                    print(f" [Config Loaded] Worker Name: {worker_name}")
                    return worker_name
        except Exception as e:
            print(f" [Config Error] Failed to read or parse miner.json. Error: {e}")
            pass
            
    print(" [Config Error] Worker Name not found in miner.json. Using fallback 'Unknown-Worker'.")
    return "Unknown-Worker"

def load_worker_tags():
    """
    ดึงค่า 'Pass' (ซึ่งเก็บ Hybrid/Solo Status) จากไฟล์ miner.json 
    เพื่อใช้เป็น Tags ในการรายงาน
    """
    json_path = os.path.join("set-miner", "miner.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as set_file:
                config_data = json.load(set_file)
                # *** แก้ไข: ดึงจากคีย์ 'Pass' ตามคำขอ ***
                worker_tags = config_data.get('Pass') 
                if worker_tags:
                    print(f" [Config Loaded] Worker Tags (Pass): {worker_tags}")
                    return worker_tags
        except:
            pass
    # หากไม่พบไฟล์หรือคีย์ ให้ส่งค่าที่ปลอดภัยกลับไป
    print(" [Config Warning] 'Pass' key not found in miner.json. Using fallback 'N/A_TAG'.")
    return "N/A_TAG"


def get_ccminer_stats():
    """ดึง Hashrate และ Shares (ใช้ค่าจำลอง Hashrate ปกติ)"""
    
    current_hashrate = random.uniform(20000000.0, 30000000.0) 
    current_shares = 100.0 + random.randint(1, 50) 
    
    return {
        'hashrate_sols': current_hashrate,
        'shares_sent': current_shares,
        'tags': 'N/A' 
    }

def send_report():
    """ส่งรายงานไปยัง Monitoring Server พร้อม Retry Logic"""
    stats = get_ccminer_stats()
    
    # 1. กำหนด Payload
    payload = {
        'worker_name': WORKER_NAME,
        'hashrate_sols': stats['hashrate_sols'],
        'shares_sent': stats['shares_sent'],
        # *** แก้ไข: ใช้ค่า Tags ที่โหลดมา ***
        'tags': WORKER_TAGS 
    }
    
    # 2. เริ่ม Retry Loop
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(REPORT_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f" [REPORT SUCCESS] {WORKER_NAME}: Sent {stats['hashrate_sols']/1000000:.2f} M Sols. (Tags: {WORKER_TAGS})")
                return 
            else:
                msg = response.json().get('message', 'N/A')
                print(f" [REPORT FAILED] Server status {response.status_code}. Attempt {attempt+1}/{MAX_RETRIES}: {msg}")
        
        except requests.exceptions.RequestException as e:
            print(f" [REPORT ERROR] Connect failed. Attempt {attempt+1}/{MAX_RETRIES}: {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    print(f" [CRITICAL] Failed to report stats after {MAX_RETRIES} attempts. Waiting for next cycle.")


# =================================================================
# 3. GLOBAL VARIABLE ASSIGNMENT 
# =================================================================
# *** แก้ไขชื่อตัวแปรให้ตรงกับ Tags ***
WORKER_TAGS = load_worker_tags() 
WORKER_NAME = load_worker_name() 


# =================================================================
# 4. MAIN EXECUTION BLOCK 
# =================================================================
if __name__ == '__main__':
    if WORKER_NAME == "Unknown-Worker":
        print(" [FATAL] Worker Name not set. Please run active_run.py to set up the worker name (Rname).")
        sys.exit(1)
        
    print(f"Starting reporting script for {WORKER_NAME} every {REPORT_INTERVAL_SEC} seconds...")
    while True:
        send_report() 
        time.sleep(REPORT_INTERVAL_SEC)
