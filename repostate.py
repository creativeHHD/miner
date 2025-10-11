import requests
import time
import json
import random 
import os 

# =================================================================
# 1. กำหนดค่าคงที่ (CONFIGS)
# =================================================================

# *** ต้องแก้ไข IP Address ตรงนี้! ***
MONITORING_SERVER_IP = "192.168.1.111"  
REPORT_URL = f"http://{MONITORING_SERVER_IP}:5000/report_stats"
REPORT_INTERVAL_SEC = 300 # 300 วินาที = 5 นาที

# New: Retry configuration (เพิ่มความทนทานต่อเน็ตหลุดชั่วคราว)
MAX_RETRIES = 10 
RETRY_DELAY = 15 # 10 วินาที หน่วงเวลาก่อนลองส่งใหม่


# =================================================================
# 2. FUNCTION DEFINITION BLOCK (นิยามฟังก์ชันทั้งหมด)
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

def get_ccminer_stats():
    """ดึง Hashrate และ Shares (หรือค่าจำลอง)"""
    # *** ลบ Logic การจำลองเครื่องดับ (if random.random() < 0.1:) ออกไป ***
    
    # NEW LOGIC: ใช้ค่า Hashrate ปกติเสมอ (ระหว่างการทดสอบ)
    current_hashrate = random.uniform(20000000.0, 30000000.0) 
        
    current_shares = 100.0 + random.randint(1, 50) 
    
    return {
        'hashrate_sols': current_hashrate,
        'shares_sent': current_shares,
        'tags': 'MOBILE_CCMINER' 
    }

def send_report():
    """ส่งรายงานไปยัง Monitoring Server พร้อม Retry Logic"""
    stats = get_ccminer_stats()
    
    # 1. กำหนด Payload (ต้องทำก่อนเริ่มลูป Retry เพื่อไม่ให้เกิด NameError)
    payload = {
        'worker_name': WORKER_NAME,
        'hashrate_sols': stats['hashrate_sols'],
        'shares_sent': stats['shares_sent'],
        'tags': stats['tags']
    }
    
    # 2. เริ่ม Retry Loop
    for attempt in range(MAX_RETRIES):
        try:
            # ใช้ payload ที่ถูกกำหนดไว้ด้านบน
            response = requests.post(REPORT_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f" [REPORT SUCCESS] {WORKER_NAME}: Sent {stats['hashrate_sols']/1000000:.2f} M Sols.")
                return # สำเร็จ, ออกจากฟังก์ชัน
            else:
                # Server ตอบกลับแต่เป็น Error Code 4xx, 5xx
                msg = response.json().get('message', 'N/A')
                print(f" [REPORT FAILED] Server status {response.status_code}. Attempt {attempt+1}/{MAX_RETRIES}: {msg}")
        
        except requests.exceptions.RequestException as e:
            # เชื่อมต่อไม่สำเร็จ (Connection Refused, Timeout)
            print(f" [REPORT ERROR] Connect failed. Attempt {attempt+1}/{MAX_RETRIES}: {e}")

        # หน่วงเวลาสำหรับการ Retry ถัดไป
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    # ถ้าหลุดจากลูปแสดงว่าส่งไม่สำเร็จ
    print(f" [CRITICAL] Failed to report stats after {MAX_RETRIES} attempts. Waiting for next cycle.")


# =================================================================
# 3. GLOBAL VARIABLE ASSIGNMENT (กำหนดค่าที่ใช้ทั้งไฟล์)
# =================================================================
WORKER_NAME = load_worker_name() 


# =================================================================
# 4. MAIN EXECUTION BLOCK (โค้ดหลัก)
# =================================================================
if __name__ == '__main__':
    print(f"Starting reporting script for {WORKER_NAME} every {REPORT_INTERVAL_SEC} seconds...")
    while True:
        send_report() 
        time.sleep(REPORT_INTERVAL_SEC)
