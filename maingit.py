import os, json, time
import sys
import requests
import base64
import re
import pyfiglet
import colorama
from github import Github, Auth
from progress.spinner import MoonSpinner
from colorama import init, Fore, Style
init(autoreset=True)
# banner
setting_banner = """
╔════════════════════════════════════╦════════╗
║    ████ ████ █████ █ █    ██ █████ ║  V 3.2 ║
║   ██  █ █      █   █ █   ██        ║CREATIVE║
║  ██ ███ █    GITHUB SUPPORT  ███   ║   HD   ║
║ ██    █ █      █   █ █ ██          ╠════════╣
║██    A█C████  T█  I█V███    E█████ ║SETTING.║
╚════════════════════════════════════╩════════╝"""

running_banner = """
╔════════════════════════════════════╦════════╗
║    ████ ████ █████ █ █    ██ █████ ║  V 3.2 ║
║   ██  █ █      █     █   ██        ║CREATIVE║
║  ██ ███ █    GITHUB SUPPORT  ███   ║   HD   ║
║ ██    █ █      █   █ █ ██          ╠════════╣
║██A    █ C███   T   I V██    E█████ ║ START  ║
╚════════════════════════════════════╩════════╝"""

# banner function
def banner(logo):
    os.system("clear")
    print(logo,"     \nDevelop by AMS - CREATIVE-HD")
    print("------------------------------------------------") 
    print("                   ACTIVE MODE\n"
        + "    ▝  ▘         GitHub Support\n"
        + " █ ███████ █     TERMUX AUTO START \n "
        + "█ █ 3.2 █ █ CCMINER AFTER BOOT DEVICE\n"
        + "   ███████       RUNNING AUTOMATIC\n"
        + "    ██ ██                             AUG.2025")
    print("------------------------------------------------\n")


# install miner function 
def install():
    # os.system("git clone --single-branch -b ARM https://github.com/monkins1010/ccminer")
    os.system("git clone https://github.com/creativeHHD/ccminer_mmv")

# run miner function
def run():
    banner(running_banner)
    
    # 1. โหลดข้อมูล Rig Settings เพื่อใช้ในการค้นหาและ Fallback (ถ้าจำเป็น)
    with open("set-miner/miner.json", encoding="utf-8") as set_file:
        loads = json.load(set_file)
        namepro = loads['namepro']
        droom = loads['droom']
        rig_name = loads['Rname']
 
        # *** เปลี่ยนมาอ่านจาก JSON แทน Environment Variable ***
        access_token = loads.get('GITHUB_ACCESS_TOKEN') 
    # ... (ส่วนการตรวจสอบ access_token) ...
    # เตรียมตัวแปรสำหรับค่าที่รัน
    run_pool, run_wallet, run_password, run_cpu = None, None, None, None
    
    if not access_token:
        print(f"{Fore.YELLOW}Error: GITHUB_ACCESS_TOKEN not found in miner.json. Set the token.")
        time.sleep(3)
        set_miner() # หรือฟังก์ชันที่นำผู้ใช้ไปใส่ Token
        return    

    try:
        # **A. พยายามดึงข้อมูลล่าสุดจาก GitHub**
        print(f"{Fore.CYAN}--- 🌐 Fetching config for rig '{rig_name}' from GitHub ---")
        g = Github(auth=Auth.Token(access_token))
        repo_name = f"creativeHHD/{namepro}"
        repo = g.get_repo(repo_name)
        file_path = f"{droom}.txt"
        
        file_content_obj = repo.get_contents(file_path)
        file_content = file_content_obj.decoded_content.decode('utf-8')
        lines = file_content.strip().split('\n')
        
        found_line = None
        for line in lines:
            if rig_name in line:
                found_line = line
                break
                
        if found_line:
            print(f"{Fore.GREEN}✅ Config line found: {found_line}")
            
            # **B. แยกส่วนประกอบ (สมมติว่าใช้ Pipe '|' เป็นตัวแบ่ง)**
            try:
                values = [v.strip() for v in found_line.split('|')]
                # values[0] คือ status, values[1] คือ pool, values[2] คือ wallet, etc.
                
                run_pool = values[1]
                run_wallet = values[2]
                run_password = values[4]
                run_cpu = values[5] if len(values) > 5 else 1 # ใช้ค่าเริ่มต้น 1
                
                # C. บันทึกข้อมูลที่ดึงมาใหม่ลงใน miner.json (สำหรับใช้เป็น Fallback)
                loads['Pool'] = run_pool
                loads['Wallet'] = run_wallet
                loads['Pass'] = run_password
                loads['Cpu'] = run_cpu
                with open("set-miner/miner.json", "w") as set_file:
                    json.dump(loads, set_file, indent=4)
                print(f"{Fore.YELLOW}* Updated miner.json with latest GitHub config.")
                
            except IndexError:
                print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ Error: The row for '{rig_name}' does not have enough columns (expected 6+).")
                raise Exception("Invalid GitHub config format.") # ยกเลิกการทำงานถ้า format ผิด
        else:
            print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ Rig name '{rig_name}' not found in the GitHub file.")
            raise Exception("Rig configuration not found.")
            
    except Exception as e:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}❌ An error occurYELLOW while fetching from GitHub: {e}")
        # **D. ใช้ค่า Fallback จาก miner.json ที่มีอยู่**
        try:
            if 'Pool' in loads and loads['Pool']:
                print(f"{Fore.YELLOW}* Attempting to use existing config from miner.json...")
                run_pool = loads['Pool']
                run_wallet = loads['Wallet']
                run_password = loads.get('Pass', 'x')
                run_cpu = loads.get('Cpu', 1)
            else:
                raise Exception("No config available locally.")
        except Exception as fallback_error:
            print(f"{Fore.YELLOW}{Style.BRIGHT}❌ CRITICAL: Cannot run. GitHub failed and no local config available.")
            time.sleep(5)
            return

    # E. รัน Miner (ใช้ตัวแปร run_...)
    print("--- 🚀 STARTING CCMINER ---")
    print(f"Pool: {run_pool}, Wallet: {run_wallet}.{rig_name}, CPU: {run_cpu}")
    os.system(f"cd ccminer_mmv && ./ccminer -a verus -o {run_pool} -u {run_wallet}.{rig_name} -p {run_password} -t {run_cpu}")

def set_miner():
    banner(setting_banner) # สมมติว่าฟังก์ชันนี้มีอยู่แล้ว
    while True:
        try:
            namepro = input("Enter project name [ตัวอย่าง : www.github.com/ID/?] : ")
            droom = input("Enter room in project [ตัวอย่าง : www.github.com/ID/xxx/?] : ")
            Rname = input("Enter Worker [ชื่อเครื่อง] : ")
            
            if not all([namepro, droom, Rname]):
                print(f"\n{Fore.YELLOW}เกิดข้อผิดพลาด: โปรดระบุข้อมูลให้ครบถ้วน!")
                time.sleep(2)
                continue
            
            puts = {
                'namepro': namepro,
                'droom': droom,
                'Rname': Rname
            }
            with open("set-miner/miner.json", "w") as set_file:
                json.dump(puts, set_file, indent=4)
            break
        except Exception as e:
            print(f"\n{Fore.YELLOW}เกิดข้อผิดพลาด: {e}")
        os.system("clear")
        with MoonSpinner(text="                 โปรดรอ...", color="yellow") as bar:
            for _ in range(100):
                time.sleep(0.05)
                bar.next()
            time.sleep(2)

# โค้ดหลัก
if __name__ == "__main__":
    while True:
        os.system("clear")
        with MoonSpinner(text="                 โปรดรอ...", color="yellow") as bar:
            for _ in range(100):
                time.sleep(0.05)
                bar.next()

        if not os.path.exists("ccminer_mmv"):
            # ควรจะมีฟังก์ชัน install() ที่ดาวน์โหลดและติดตั้ง ccminer
            print("ccminer_mmv not found. Running installation...")
            install()
            break
        
        if os.path.exists("set-miner"):
            if os.path.isfile("set-miner/miner.json"):
                run()
                break
            else:
                set_miner()
        else:
            os.system("mkdir set-miner")
            set_miner()    
    
