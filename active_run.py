import os
import json
import time
import requests
import base64        # แก้ไข: เพิ่ม import base64 เพื่อถอดรหัส GitHub Content
import subprocess    # แก้ไข: ใช้ subprocess เพื่อรันคำสั่งอย่างปลอดภัย
from datetime import datetime

# *** หมายเหตุ: ต้องลบ 'from github import Github, Auth' ออก เพราะโค้ดนี้ใช้ requests/base64 แทน ***

# banner
setting_banner = """
╔════════════════════════════════════╦════════╗
║    ████ ████ █████ █ █    ██ █████ ║  V 3.2 ║
║   ██  █ █      █   █ █   ██        ║CREATIVE║
║  ██ ███ █   GITHUB SUPPORT   ███   ║   HD   ║
║ ██    █ █      █   █ █ ██          ╠════════╣
║██    A█C████  T█ I █V███    E█████ ║SETTING.║
╚════════════════════════════════════╩════════╝"""

running_banner = """
╔════════════════════════════════════╦════════╗
║    ████ ████ █████ █ █    ██ █████ ║  V 3.2 ║
║   ██  █ █      █   █ █   ██        ║CREATIVE║
║  ██ ███ █    GITHUB SUPPORT  ███   ║   HD   ║
║ ██    █ █      █   █ █ ██          ╠════════╣
║██A    █C████  T█  I█V███    E█████ ║ START  ║
╚════════════════════════════════════╩════════╝"""
waiting_banner = r"""


       ░░░░░░░█▀▀░▀█▀░█▀█░█▀▄░▀█▀░░░░░░
       ░░░░░░░▀▀█░░█░░█▀█░█▀▄░░█░░░░░░░
       ░▀░▀░▀░▀▀▀░░▀░░▀░▀░▀░▀░░▀ ▀ ▀░▀░
            
            
            
            (  (      ) (  ( /( 
            )\))(  ( /( )\ )\())
            ((_)()\ )(_)|(_|_))/
            _(()((_|(_)_ (_) |_
        _ _ \ V  V / _` || |  _|_ _ _ 
       (_|_|_)_/\_/\__,_||_|\__(_|_|_) """

active_banner = r"""
                                                
     /\   / ____|__   __|_   _\ \    / /  ____|
    /  \ | |       | |    | |  \ \  / /| |__   
   / /\ \| |     GITHUB SUPPORT \ \/ / |  __|  
  / ____ \ |____   | |   _| |_   \  /  | |____ 
 /_/    \_\_____|  |_|  |_____|   \/   |______|"""

# banner function
def banner(logo):
    os.system("cls" if os.name == "nt" else "clear")
    # ปรับปรุงการแสดงผลให้ใช้ตัวแปร logo ที่ส่งมา
    print(logo, "\nAMS - CREATIVE-HD")
    print("------------------------------------------------") 
    print("                   ACTIVE MODE\n"
        + "    () ()     --> GitHub Support <--\n"
        + " █ ███████ █     TERMUX AUTO START \n "
        + "█ █ 3.2 █ █ CCMINER AFTER BOOT DEVICE\n"
        + "   ███████       RUNNING AUTOMATIC\n"
        + "    ██ ██                            AUG.2025")
    print("------------------------------------------------\n")


# install miner function 
##def install():
    ##os.system("git clone https://github.com/creativeHHD/ccminer_mmv")

# run miner function
def run():
    banner(running_banner)
    
    # 1. โหลดข้อมูล Rig Settings พื้นฐาน (ชื่อ repo, rig name) จาก miner.json
    try:
        with open("set-miner/miner.json", encoding="utf-8") as set_file:
            loads = json.load(set_file)
            namepro = loads['namepro']
            droom = loads['droom']
            rig_name = loads['Rname']
            access_token = loads.get('GITHUB_ACCESS_TOKEN') 
    except Exception as e:
        print(f"CRITICAL: Failed to load essential config from miner.json. Run set_miner() first. Error: {e}")
        time.sleep(5)
        return

    # 2. ตรวจสอบ Token (ต้องมี Token เพื่อดึง Config)
    if not access_token:
        print(f"Error: GITHUB_ACCESS_TOKEN not found. Use set_token.py to set the token.")
        time.sleep(5)
        return      

    # 3. ดึง Config ล่าสุดจาก GitHub และจัดรูปแบบคำสั่ง
    print(f"--- 🌐 Fetching and Syncing config for rig '{rig_name}' from GitHub ---")
    
    # *** แทนที่การดึง Config เดิมด้วยการเรียกใช้ฟังก์ชันใหม่ที่จัดการการอัปเดต ***
    try:
        # ฟังก์ชันนี้จะดึงค่า, จัดรูปแบบ, และทำการบันทึกค่า Pool/Wallet/Pass/CPU ลงใน loads['Pool'] ฯลฯ
        # และคืนค่าเป็น final_command ที่พร้อมรัน
        final_command = fetch_and_sync_github_config(
            owner="creativeHHD", # สันนิษฐานว่า Owner เป็น 'creativeHHD' ตามโค้ดเดิม
            repo_name=namepro, 
            file_path=f"{droom}.txt", 
            token=access_token, 
            rig_name=rig_name
        )
        
    except Exception as e:
        print(f"\n❌ CRITICAL: Failed to synchronize with GitHub. Error: {e}")
        final_command = None # ให้ final_command เป็น None หากดึงค่าล้มเหลว
        
    # 4. รัน Miner ด้วยคำสั่งที่ได้จาก GitHub ล่าสุด
    if final_command:
        ## ใช้ Miner Path ที่ถูกต้อง
        #miner_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ccminer_mmv', 'ccminer')
        print("------------- 🚀 STARTING CCMINER -------------")
        print("╔═╗╔╦╗╔═╗╦═╗╔╦╗  ╔═╗╔═╗╔╦╗╦╔╗╔╔═╗╦═╗  ╔╗╔╔═╗╦ ╦")
        print("╚═╗ ║ ╠═╣╠╦╝ ║   ║  ║  ║║║║║║║║╣ ╠╦╝  ║║║║ ║║║║")
        print("╚═╝ ╩ ╩ ╩╩╚═ ╩   ╚═╝╚═╝╩ ╩╩╝╚╝╚═╝╩╚═  ╝╚╝╚═╝╚╩╝")
        ## ใช้ execute_miner() ที่ถูกแก้ไขให้รันอย่างปลอดภัย
        #execute_miner(final_command, miner_path)
        write_and_run_script(final_command) 
    else:
        print("\nCRITICAL: Cannot run. No valid mining command found after GitHub sync.")
        time.sleep(5)


# ************* ส่วนที่ต้องเพิ่ม/แก้ไขในไฟล์ active_run.py *************
# *** เพิ่มฟังก์ชันใหม่นี้เพื่อจัดการการดึงค่าและการอัปเดต .json ***
def fetch_and_sync_github_config(owner, repo_name, file_path, token, rig_name):
    # ใช้ requests/base64 ในการดึงและถอดรหัส (เหมือนที่เราเคยทำ)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status() 

    data = response.json()
    config_content = base64.b64decode(data['content']).decode('utf-8')
    
    # หาบรรทัด Config
    found_line = None
    for line in config_content.splitlines():
        if rig_name in line:
            found_line = line.strip()
            break
            
    if not found_line:
        raise Exception(f"Rig name '{rig_name}' not found in the GitHub config file.")
        
    # แยกส่วนประกอบ
    values = [v.strip() for v in found_line.split('|')]
    if len(values) < 6:
        raise Exception("Incomplete config line. Expected 6+ parts (Status|Pool|Wallet|Worker|Pass|CPU).")

    # กำหนดตัวแปรจากค่าที่แยกได้
    # values[0] = Status (ไม่ใช้)
    run_pool = values[1]
    run_wallet = values[2]
    run_worker = values[3] # ใช้ Worker Name ที่ดึงมา
    run_password = values[4]
    run_cpu = values[5]

    # C. บันทึกข้อมูล Pool/Wallet/Pass/CPU ที่ดึงมาใหม่ลงใน miner.json (อัปเดตอัตโนมัติ)
    # เราไม่จำเป็นต้องตรวจสอบว่าข้อมูลต่างกันหรือไม่ แค่บันทึกทับไปเลย
    json_path = os.path.join("set-miner", "miner.json")
    with open(json_path, "r+", encoding="utf-8") as set_file:
        settings = json.load(set_file)
        # อัปเดตเฉพาะค่าการขุด (ไม่กระทบ namepro, droom, Rname, Token)
        settings.update({
            'Pool': run_pool,
            'Wallet': run_wallet,
            'Pass': run_password,
            'Cpu': run_cpu
        })
        set_file.seek(0)
        json.dump(settings, set_file, indent=4)
        set_file.truncate()
        
    print(f"✅ Config Synced from GitHub. Worker: {run_worker}, Threads: {run_cpu}")

    # สร้างคำสั่งสุดท้าย:
    final_command_raw = (
        f"{run_pool} "  
        f"-u {run_wallet}.{run_worker} " # ใช้ Worker Name ที่ดึงมา
        f"-p {run_password} "        
        f"-t {run_cpu}"             
    )
    return final_command_raw # คืนค่าเป็นคำสั่งดิบ

def write_and_run_script(miner_command_raw):
    """สร้างไฟล์ 'run' ใหม่ พร้อม Shebang และคำสั่งรัน CCMiner ล่าสุด"""
    RUN_SCRIPT_PATH = "run"  # ไฟล์ run อยู่ในโฟลเดอร์เดียวกับ active_run.py (/ccminer/run)
    
    try:
        # 1. เขียน Shell Script ลงในไฟล์ 'run'
        with open(RUN_SCRIPT_PATH, "w") as f:
            # Shebang: บอกระบบว่าเป็น Bash Script
            ##f.write("#!/bin/bash\n") 
            # คำสั่งนำทาง: ต้องแน่ใจว่าทำงานในโฟลเดอร์ ccminer_mmv ก่อนรัน ./ccminer
            ##f.write("cd ccminer_mmv\n") 
            # คำสั่งรันจริงที่ดึงมาจาก GitHub
            f.write(miner_command_raw + "\n") 
            
        # 2. ตั้งค่าให้ไฟล์ 'run' มีสิทธิ์รัน (+x)
        os.chmod(RUN_SCRIPT_PATH, 0o755) 

        print(f"✅ Updated mining command in ./{RUN_SCRIPT_PATH} for Auto-Boot (bash.bashrc).")
        
        # 3. รันไฟล์ 'run' ทันที
        print("--- 🚀 STARTING CCMINER NOW ---")
        subprocess.run(["./" + RUN_SCRIPT_PATH], check=True) # ใช้ "./run" ในการรัน
        
    except subprocess.CalledProcessError as e:
        print(f"\nCRITICAL: CCMiner exited with error code {e.returncode}. Execution failed.")
    except Exception as e:
        print(f"\nAn error occurred during script writing or execution: {e}")

def set_miner():
    # โค้ดเดิม: banner, input, save (มีการตัดบรรทัด Token ออก)
    banner(setting_banner) 
    while True:
        try:
            namepro = input("Enter project name \n[ตัวอย่าง : https://github.com/ID/.1.?]\n : ").strip()
            droom = input("\nEnter config file name \n[ตัวอย่าง : https://github.com/ID/.1./2?]\n : ").strip()
            Rname = input("\nEnter Worker [ชื่อเครื่อง]\n : ").strip()
            
            # *** บรรทัดที่ถูกตัดออก: ***
            # github_token = input("Enter GitHub Personal Access Token (or press Enter if known): ").strip()
            # ***

            if not all([namepro, droom, Rname]):
                print(f"\nเกิดข้อผิดพลาด: โปรดระบุข้อมูลให้ครบถ้วน!")
                time.sleep(2)
                continue
            
            puts = {
                'namepro': namepro,
                'droom': droom,
                'Rname': Rname,
                # *** แก้ไข: ไม่ต้องใส่ 'GITHUB_ACCESS_TOKEN' ใน puts แล้ว 
                # *** เพราะไฟล์อื่นจะจัดการและบันทึกไว้ใน miner.json เอง
            }
            if not os.path.exists("set-miner"):
                os.makedirs("set-miner")
                
            # ถ้ามีไฟล์อยู่แล้ว ให้อ่านค่า Token เก่ามาเก็บไว้ก่อน (ถ้าจำเป็น)
            existing_token = ""
            if os.path.isfile("set-miner/miner.json"):
                try:
                    with open("set-miner/miner.json", 'r', encoding="utf-8") as f:
                        existing_data = json.load(f)
                        existing_token = existing_data.get('GITHUB_ACCESS_TOKEN', "")
                except:
                    pass
            
            # บันทึกค่าใหม่ และรวม Token เก่าเข้าไป
            puts['GITHUB_ACCESS_TOKEN'] = existing_token 
            
            with open("set-miner/miner.json", "w", encoding="utf-8") as set_file:
                json.dump(puts, set_file, indent=4)
            break
        except Exception as e:
            print(f"\nเกิดข้อผิดพลาด: {e}")
            os.system("cls" if os.name == "nt" else "clear")
            print("              [..โปรดรอ..]")
            time.sleep(2)

# โค้ดหลัก
if __name__ == "__main__":
    try:
       while True:
            # Initial wait/clear screen logic
            os.system("cls" if os.name == "nt" else "clear")
            banner(waiting_banner)
            time.sleep(2)
        
            # 1. ติดตั้ง CCMiner ถ้ายังไม่มี
            ##if not os.path.exists("ccminer_mmv"):
                ##print("ccminer_mmv not found. Running installation...")
                ##install()
                # หลังติดตั้ง ต้องตั้งค่าพื้นฐาน
                ##set_miner() 
                # ดำเนินการต่อในลูปเพื่อให้รัน run() ครั้งแรก
            
            # 2. จัดการโฟลเดอร์ set-miner
            if not os.path.exists("set-miner"):
                 os.makedirs("set-miner")
                 set_miner() # ตั้งค่าถ้าโฟลเดอร์หายไป
             
            # 3. ตรวจสอบไฟล์ config
            if os.path.isfile("set-miner/miner.json"):
                # ตรวจสอบว่ามีข้อมูลหลักที่จำเป็นครบถ้วนหรือไม่ (เพื่อข้าม set_miner)
                try:
                    with open("set-miner/miner.json", 'r', encoding="utf-8") as f:
                        loads = json.load(f)
                
                    # ตรวจสอบคีย์ที่ต้องระบุครั้งแรก (namepro, droom, Rname)
                    if all(key in loads for key in ['namepro', 'droom', 'Rname']):
                        # *** ตรรกะสำคัญ: ข้ามการตั้งค่าและรันทันที ***
                        run()
                        break # ออกจาก Loop เมื่อรันเสร็จ (หรือเมื่อ CCMiner ถูกยกเลิก)
                    else:
                        print("Initial setup data is incomplete. Running set_miner()...")
                        set_miner()
                except:
                    # ถ้าไฟล์เสียหรือไม่สมบูรณ์ ให้รัน set_miner ใหม่
                    print("Configuration file corrupted. Running set_miner()...")
                    set_miner()
            else:
                # ถ้าไม่มีไฟล์ config ให้ตั้งค่า (ครั้งแรก)
                set_miner()

    # 2. <<< except KeyboardInterrupt ต้องอยู่ตรงกับ try แรกสุด
    except KeyboardInterrupt: 
        # ดักจับสัญญาณ Ctrl + C เพื่อให้จบโปรแกรมอย่างสวยงาม
        print("\n\n--- 🛑 Program terminated by user (Ctrl+C). ---")
        sys.exit(0)


