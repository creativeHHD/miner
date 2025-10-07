import os
import json
import time
import sys
import getpass
import colorama
from colorama import Back, Fore, Style, init
from inputimeout import inputimeout, TimeoutOccurred
# banner
token_banner = """
╔════════════════════════════════════╦════════╗
║    ████ ████ █████ █ █    ██ █████ ║  V.3.2 ║
║   ██  █ █      █   █ █   ██        ║CREATIVE║
║  ██ ███ █ GITHUB_ACCESS_TOKEN ██   ║   HD   ║
║ ██    █ █      █   █ █ ██          ╠════════╣
║██   A █C████ T █  I█V███   E █████ ║ +TOKEN ║
╚════════════════════════════════════╩════════╝"""

# banner function
def banner(logo):
    os.system("clear")
    print(logo,"")
    print(f"{Fore.CYAN}{Style.BRIGHT}Program by AMS - CREATIVE-HD{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}-----------------------------------------------{Style.RESET_ALL}")    
    print(f"                     TOKEN MODE\n"
        + ""
        + "           GITHUB_ACCESS_TOKEN FOR TERMUX \n"
        + "           Pool,Wallet,Name,Cpu On Github \n"
        + "                  RUNNING AUTOMATIC\n"
        + f"                                       {Fore.CYAN}{Style.BRIGHT}AUG.2025{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}-----------------------------------------------{Style.RESET_ALL}")

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
    print("╔═╗╦╔╦╗   ╔═╗╔═╗╔═╗╔═╗╔═╗╔═╗   ╔╦╗╔═╗╦╔═╔═╗╔╗╔")
    print("║ ╦║ ║    ╠═╣║  ║  ║╣ ╚═╗╚═╗    ║ ║ ║╠╩╗║╣ ║║║")
    print("╚═╝╩ ╩────╩ ╩╚═╝╚═╝╚═╝╚═╝╚═╝────╩ ╚═╝╩ ╩╚═╝╝╚╝")
    print(f"--- ✅ Found existing GitHub Access Token (Prefix: {existing_token[:5]}...). ---")
    print("If you want to change it, type 'y' or press any key. Otherwise\nPress Enter or wait to continue.. ")
    print("You have 5 seconds to respond.")
    
    # ใช้ input ธรรมดาเพื่อถามผู้ใช้ว่าจะเปลี่ยนหรือไม่
    #change_or_continue = input("Action: ").strip()
    change_or_continue = None # กำหนดค่าเริ่มต้น
    TIMEOUT_SECONDS = 5
    
    try:
        # ใช้ inputimeout() แทน input()
        change_or_continue = inputimeout(prompt="Action: ", timeout=TIMEOUT_SECONDS).strip()
    except TimeoutOccurred:
        # หากเกิด timeout, change_or_continue จะยังคงเป็น None 
        # ซึ่งจะทำให้โค้ดไปทำงานใน if not change_or_continue:
        print("\n--- ⏳ Timeout! No input received. ---")
    except Exception as e:
        # ดักจับข้อผิดพลาดอื่น ๆ ที่อาจเกิดขึ้น
        print(f"An error occurred: {e}")
        
    # ใช้ .strip() เพื่อลบช่องว่าง/ขึ้นบรรทัดใหม่
    # ถ้าเกิด TimeoutOccurred: change_or_continue จะเป็น None ทำให้ if not change_or_continue เป็นจริง
    # ถ้าผู้ใช้กด Enter: change_or_continue จะเป็น "" ทำให้ if not change_or_continue เป็นจริง
    if not change_or_continue or change_or_continue.lower() == "": 
        # ผู้ใช้กด Enter หรือเกิด Timeout เพื่อใช้ Token เดิม
        print("Using existing token. Exiting setup in 3 seconds...")
        time.sleep(3)
        sys.exit(0) # <<< ออกจากสคริปต์ทันที
    
        # ถ้าผู้ใช้ตอบอะไรก็ตามที่ไม่ใช่ Enter หรือ Timeout (เช่น 'y', 'n', 'test')
        print(f"User chose to change (Input: {change_or_continue}). Continuing with new token setup...")
        
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
