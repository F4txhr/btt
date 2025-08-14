# ======================================================
# ISI LENGKAP FILE: manager.py
# ======================================================
import os, sys, signal, subprocess, time

MAIN_BOT_SCRIPT = "bot.py"
MAINTENANCE_BOT_SCRIPT = "maintenance_bot.py"
MAIN_BOT_PID_FILE = "main_bot.pid"
MAINTENANCE_BOT_PID_FILE = "maintenance_bot.pid"
LOG_FILE = "manager.log"

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}\n"
    print(full_message.strip())
    with open(LOG_FILE, "a") as f: f.write(full_message)

def get_pid_from_file(pid_file):
    try:
        with open(pid_file, 'r') as f: return int(f.read().strip())
    except: return None

def kill_process(pid_file):
    pid = get_pid_from_file(pid_file)
    if pid:
        log(f"Mencoba mengirim sinyal shutdown ke proses {pid}...")
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(5)
            log(f"Proses {pid} seharusnya sudah berhenti.")
            if os.path.exists(pid_file): os.remove(pid_file)
            return True
        except ProcessLookupError:
            log(f"PERINGATAN: Proses {pid} tidak ditemukan. Membersihkan file PID.")
            if os.path.exists(pid_file): os.remove(pid_file)
            return True
        except Exception as e:
            log(f"ERROR: Gagal menghentikan proses {pid}: {e}")
            return False
    else:
        log(f"INFO: Tidak ada file PID untuk {pid_file}.")
        return True

def start_process(script_name):
    log(f"Menjalankan {script_name} di latar belakang...")
    command = f"nohup {sys.executable} {script_name} > {script_name}.log 2>&1 &"
    subprocess.Popen(command, shell=True)
    log(f"Berhasil menjalankan {script_name}.")

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ['on', 'off']:
        log("ERROR: Argumen tidak valid. Gunakan 'on' atau 'off'."); sys.exit(1)
    mode = sys.argv[1]
    if mode == 'on':
        log("--- MENGAKTIFKAN MODE MAINTENANCE ---")
        kill_process(MAIN_BOT_PID_FILE); start_process(MAINTENANCE_BOT_SCRIPT)
        log("--- Mode maintenance SELESAI DIAKTIFKAN ---")
    elif mode == 'off':
        log("--- MENONAKTIFKAN MODE MAINTENANCE ---")
        kill_process(MAINTENANCE_BOT_PID_FILE); start_process(MAIN_BOT_SCRIPT)
        log("--- Mode maintenance SELESAI DINONAKTIFKAN ---")
