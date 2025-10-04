import os, json, time
import sys
from progress.spinner import MoonSpinner

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
# 1. รับค่า Token จาก Argument ที่ส่งมาจาก ADB
# โครงสร้างคำสั่ง: python set_token.py "YOUR_TOKEN"
banner(token_banner)
if len(sys.argv) < 2:
    sys.exit("Error: No token provided.")

new_token = sys.argv[1] # Token จะอยู่ที่ตำแหน่งที่ 1

# 2. โหลดไฟล์ miner.json ที่มีอยู่
json_path = "set-miner/miner.json"
data = {}

try:
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # สร้างโฟลเดอร์ถ้าไม่มี
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
    # 3. บันทึก Token ใหม่
    data['GITHUB_ACCESS_TOKEN'] = new_token
    
    # 4. บันทึกกลับลงในไฟล์
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("SUCCESS: GITHUB_ACCESS_TOKEN saved to miner.json")

except Exception as e:
    print(f"ERROR: Failed to save token: {e}")
