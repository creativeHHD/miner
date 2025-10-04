import os
import json
import time
import sys
# banner
token_banner = """
╔════════════════════════════════════╦════════╗
║    ████ ████ █████ █ █    ██ █████ ║   V.1  ║
║   ██  █ █      █   █ █   ██        ║CREATIVE║
║  ██ ███ █      █   █ █  ██   ███   ║   HD   ║
║ ██    █ █      █   █ █ ██          ╠════════╣
║██   A █C████ T █  I█V███   E █████ ║ +TOKEN ║
╚════════════════════════════════════╩════════╝"""

# banner function
def banner(logo):
    os.system("clear")
    print(logo,"\n         Development by AMS - CREATIVE-HD")
    print("-----------------------------------------------") 
    print("                   TOKEN MODE\n"
        + ""
        + "          GITHUB_ACCESS_TOKEN FOR TERMUX \n"
        + "          Pool,Wallet,Name,Cpu On Github \n"
        + "                RUNING AUTOMATIC\n"
        + "                                       AUG.2025")
    print("-----------------------------------------------\n")
banner(token_banner)
print("โปรดรอรับค่า Access Token จาก PC...")
new_token = input("INPUT GITHUB_ACCESS_TOKEN: ") 

# ----------------------------------------------------
# ***โค้ดที่เพิ่ม: แสดงค่าที่ได้รับ***
print("\n--- Diagnostic: ค่า Token ที่ได้รับ ---")
if new_token and len(new_token) > 5:
    # แสดงค่า 5 ตัวแรก เพื่อยืนยันว่าได้รับ Token จริง (ไม่แสดงทั้ง Token เพื่อความปลอดภัย)
    print(f"Token Prefix (5 ตัวแรก): {new_token[:5]}...") 
else:
    print("Received Value: (ว่างเปล่าหรือไม่ถูกต้อง)")
print("----------------------------------------")
# ----------------------------------------------------

# 2. ตรวจสอบค่า (ถ้าผู้ใช้ยกเลิกหรือค่าว่างเปล่า)
if not new_token or new_token.strip() == "":
    sys.exit("Error: รับค่า Access Token ไม่สำเร็จ") # <--- เกิดขึ้นถ้า C# ส่งมาเป็นค่าว่าง

# 3. โหลดไฟล์ miner.json ที่มีอยู่ (โค้ดเดิม)
json_path = "set-miner/miner.json"

try:
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
    # 4. บันทึก Token ใหม่
    data['GITHUB_ACCESS_TOKEN'] = new_token
    
    # 5. บันทึกกลับลงในไฟล์
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    # ข้อความตอบรับค่าส่ง Access Token
    print("\n---------------------------------------------------------")
    print("✅ SUCCESS: ได้รับและบันทึก GITHUB ACCESS TOKEN เรียบร้อยแล้ว")
    print("---------------------------------------------------------\n")

except Exception as e:
    print(f"ERROR: Failed to save token: {e}")
