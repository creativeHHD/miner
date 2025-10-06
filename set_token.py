import os
import json
import time
import sys
import getpass
# banner
token_banner = """
╔════════════════════════════════════╦════════╗
║    ████ ████ █████ █ █    ██ █████ ║   V.1  ║
║   ██  █ █      █   █ █   ██        ║CREATIVE║
║  ██ ███ █ GITHUB_ACCESS_TOKEN ██   ║   HD   ║
║ ██    █ █      █   █ █ ██          ╠════════╣
║██   A █C████ T █  I█V███   E █████ ║ +TOKEN ║
╚════════════════════════════════════╩════════╝"""

# banner function
def banner(logo):
    os.system("clear")
    print(logo,"\n      Development by AMS - CREATIVE-HD")
    print("-----------------------------------------------")    
    print("                TOKEN MODE\n"
        + ""
        + "           GITHUB_ACCESS_TOKEN FOR TERMUX \n"
        + "           Pool,Wallet,Name,Cpu On Github \n"
        + "                  RUNING AUTOMATIC\n"
        + "                                       AUG.2025")
    print("-----------------------------------------------\n")

# --- โค้ดเริ่มต้นทำงาน ---

# 1. โหลดไฟล์ miner.json ที่มีอยู่ (เพื่อตรวจสอบ Token เก่า)
json_path = "set-miner/miner.json"
data = {}
existing_token = ""

try:
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # ดึงค่า Token เก่า
            existing_token = data.get('GITHUB_ACCESS_TOKEN', "").strip()
    # ถ้าไม่มีโฟลเดอร์ ให้สร้าง
    if not os.path.exists(os.path.dirname(json_path)):
         os.makedirs(os.path.dirname(json_path), exist_ok=True)
         
except Exception as e:
    # หากไฟล์เสีย ให้เริ่มใหม่
    print(f"Warning: Failed to load existing config ({e}). Will proceed to set new token.")
    pass

# ----------------------------------------------------
# *** ส่วนที่แก้ไข: ตรรกะการตรวจสอบและออกจากโปรแกรม ***

if existing_token and len(existing_token) >= 40: # ตรวจสอบความยาวขั้นต่ำ
    banner(token_banner)
    print(f"--- ✅ Found existing GitHub Access Token (Prefix: {existing_token[:5]}...). ---")
    print("If you want to change it, type 'y' or press any key. Otherwise, press Enter to continue.")
    
    # ใช้ input ธรรมดาเพื่อถามผู้ใช้ว่าจะเปลี่ยนหรือไม่
    change_or_continue = input("Action: ").strip() 
    
    if not change_or_continue:
        # ผู้ใช้กด Enter เพื่อใช้ Token เดิม
        print("Using existing token. Exiting setup in 3 seconds...")
        time.sleep(3)
        sys.exit(0) # <<< ออกจากสคริปต์ทันที
        
# ----------------------------------------------------
# *** ส่วนที่ให้กรอก Token ใหม่ (รันเฉพาะเมื่อไม่มี Token หรือต้องการเปลี่ยน) ***

banner(token_banner)
print("โปรดรอรับค่า Access Token...")
new_token = getpass.getpass("INPUT GITHUB_ACCESS_TOKEN: ")

# 2. ตรวจสอบค่า (ถ้าผู้ใช้ยกเลิกหรือค่าว่างเปล่า)
if not new_token or new_token.strip() == "":
    sys.exit("Error: รับค่า Access Token ไม่สำเร็จ")

try:
    # 3. บันทึก Token ใหม่ (ทับค่าเก่า)
    data['GITHUB_ACCESS_TOKEN'] = new_token
    
    # 4. บันทึกกลับลงในไฟล์
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    # ข้อความตอบรับค่าส่ง Access Token
    print("\n---------------------------------------------------------")
    print("✅ SUCCESS: ได้รับและบันทึก GITHUB ACCESS TOKEN เรียบร้อยแล้ว")
    print("---------------------------------------------------------\n")

except Exception as e:
    print(f"ERROR: Failed to save token: {e}")
