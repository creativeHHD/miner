import subprocess
import sys
import os
import time
import re
import pdb;

def read_until_prompt(process, prompt_pattern, command_name=""):
    """
    Reads output from a subprocess until the expected prompt is found.
    Also handles interactive prompts by automatically responding with 'y'.
    """
    interactive_pattern = re.compile(
        r"\[y/n\]|\(yes/no\)|(Y/N)|(y/n)|(Y/i/N/O/D/Z)|(Y/I/N/N/Z)|[default=N]?|Do you want to continue"
    )
    
    start_time = time.time()
    while True:
        line = process.stdout.readline()
        
        # Check if the process has terminated
        if process.poll() is not None:
            if line:
                print(line, end='')
            return False, "Process terminated unexpectedly."

        # Check for timeout
        if time.time() - start_time > 300: # 5 minutes timeout
            return False, f"Timeout after 300 seconds waiting for prompt after '{command_name}'."
        
        # Process the line if it's not empty
        if line:
            print(line, end='')
            sys.stdout.flush()

            # Check for interactive prompts
            if interactive_pattern.search(line):
                print(f"[{command_name}] Auto-responding with 'y'")
                process.stdin.write('y\n')
                process.stdin.flush()
            
            # Check for the expected prompt
            if prompt_pattern.search(line.strip()):
                return True, "Prompt found."

def execute_adb_command_sync(adb_path, args):
    """
    Executes a single adb command and waits for it to complete.
    This is more reliable for non-interactive commands.
    """
    full_command = [adb_path] + args
    print(f"Executing: {' '.join(full_command)}")
    try:
        subprocess.run(full_command, check=True, text=True, capture_output=True, timeout=30)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("Command timed out.")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
                
def force_open_termux(adb_path):
    """
    Forces Termux to open on the screen by sending key events and explicit am start.
    This function uses independent subprocesses for reliability.
    """
    print("กำลังตรวจสอบสถานะหน้าจอ...")
    screen_status_proc = subprocess.run([adb_path, 'shell', 'dumpsys power | grep mScreenOn'], capture_output=True, text=True)
    if 'mScreenOn=false' in screen_status_proc.stdout:
        print("หน้าจอถูกปิดอยู่... กำลังสั่งให้เปิดหน้าจอ")
        execute_adb_command_sync(adb_path, ['shell', 'input keyevent 26']) # KEYCODE_POWER

    # สั่งให้ Termux หยุดการทำงานก่อน เพื่อป้องกันไม่ให้ทำงานในพื้นหลัง
    print("กำลังบังคับปิด Termux...")
    execute_adb_command_sync(adb_path, ['shell', 'am force-stop com.termux'])
    time.sleep(2) # หน่วงเวลาเล็กน้อยเพื่อให้แอปหยุดทำงาน

    # Send Home key to go to home screen
    print("กำลังสั่งให้กลับไปหน้า Home...")
    execute_adb_command_sync(adb_path, ['shell', 'input keyevent 3']) # KEYCODE_HOME
    time.sleep(1)

    # Re-launch Termux with explicit intent to bring to foreground
    print("กำลังสั่งให้เปิด Termux อย่างชัดเจน...")
    execute_adb_command_sync(adb_path, ['shell', 'am start --user 0 -n com.termux/.app.TermuxActivity'])
    time.sleep(5) # Wait for app to come to foreground
    
# --------------------
# Main script logic starts here (no main() function)
# --------------------

# กำหนดพาธของ ADB อัตโนมัติ (สามารถแก้ไขได้หากต้องการระบุพาธแบบเต็ม)
adb_path = 'adb'
if len(sys.argv) > 1:
    adb_path = sys.argv[1]

# Define prompt patterns
adb_prompt = re.compile(r'[$#]\s*$')
termux_prompt = re.compile(r'~ \$')

child = None

try:
    print("กำลังเริ่มต้นเซสชัน ADB shell...")
    child = subprocess.Popen(
        [adb_path, 'shell'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    
    success, message = read_until_prompt(child, adb_prompt, "Initial ADB Prompt")
    if not success:
        raise Exception(f"ไม่สามารถเชื่อมต่อกับ ADB shell ได้: {message}")
    
    print("เซสชัน ADB shell พร้อมใช้งาน")

    # Call the new function to force open Termux
    force_open_termux(adb_path)

    print("กำลังรอพร้อมท์ของ Termux โปรดตรวจสอบหน้าจออุปกรณ์ของคุณ...")
    success, message = read_until_prompt(child, termux_prompt, "Termux App Start")
    if not success:
        raise Exception(f"ไม่สามารถเปิด Termux และรอพร้อมท์ได้: {message}")
        
    print("Termux พร้อมใช้งานแล้ว! เริ่มส่งคำสั่ง...")
    
    # ขั้นตอนหลัก: รวมการทำงานของ Code 2
    print("กำลังรันคำสั่ง apt update และจัดการการตอบคำถามอัตโนมัติ...")
    
    # ส่งคำสั่ง apt update
    child.stdin.write("apt update\n")
    child.stdin.flush()
    
    # รอจนกว่า apt update จะทำงานเสร็จและพบ prompt อีกครั้ง
    success, message = read_until_prompt(child, termux_prompt, "apt update")
    if not success:
        print(f"ข้อผิดพลาด: การรันคำสั่ง 'apt update' ล้มเหลว: {message}")

    # ส่งคำสั่งที่เหลือทั้งหมด
    commands_to_run = [
        "termux-setup-storage",
        "apt upgrade -y",
        "pkg install git -y",
        "git clone https://github.com/creativeHHD/begin",
        "cd begin",
        "sh begin.sh",
        "git clone https://github.com/creativeHHD/begin",
        "cd begin",
        "sh getgo.sh"
    ]
    
    for cmd in commands_to_run:
        print(f"กำลังรันคำสั่ง: {cmd}")
        child.stdin.write(cmd + "\n")
        child.stdin.flush()
        # Use the correct prompt pattern for the command
        success, message = read_until_prompt(child, termux_prompt, cmd)
        if not success:
            print(f"ข้อผิดพลาด: การรันคำสั่ง '{cmd}' ล้มเหลว: {message}")
            break
    
    print("STATUS: Command execution complete.")
    
except FileNotFoundError:
    print(f"ข้อผิดพลาด: ไม่พบ ADB ที่พาธ '{adb_path}' โปรดตรวจสอบว่าติดตั้งและเข้าถึงได้ถูกต้อง")
    sys.exit(1)
except Exception as e:
    print(f"เกิดข้อผิดพลาด: {e}")
    sys.exit(1)
finally:
    if child and child.poll() is None:
        child.terminate()
        child.wait()
        print("เซสชันถูกปิดแล้ว")
