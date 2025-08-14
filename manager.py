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

def _is_process_running(pid: int) -> bool:
    if not pid: return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True

def kill_process(pid_file):
    pid = get_pid_from_file(pid_file)
    if pid:
        log(f"Mencoba mengirim sinyal shutdown ke proses {pid}...")
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            log(f"PERINGATAN: Proses {pid} tidak ditemukan saat SIGTERM. Membersihkan file PID.")
            if os.path.exists(pid_file): os.remove(pid_file)
            return True
        except Exception as e:
            log(f"ERROR: Gagal mengirim SIGTERM ke proses {pid}: {e}")
        # tunggu hingga 30 detik
        for _ in range(30):
            if not _is_process_running(pid): break
            time.sleep(1)
        if _is_process_running(pid):
            log(f"Proses {pid} masih berjalan, mengirim SIGKILL...")
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception as e:
                log(f"ERROR: Gagal mengirim SIGKILL ke proses {pid}: {e}")
            # tunggu 5 detik lagi
            for _ in range(5):
                if not _is_process_running(pid): break
                time.sleep(1)
        if _is_process_running(pid):
            log(f"ERROR: Proses {pid} masih berjalan setelah upaya penghentian.")
            return False
        log(f"Proses {pid} telah berhenti.")
        if os.path.exists(pid_file): os.remove(pid_file)
        return True
    else:
        log(f"INFO: Tidak ada file PID untuk {pid_file}.")
        return True

def _wait_for_pid_file(pid_file: str, timeout_sec: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout_sec:
        if os.path.exists(pid_file):
            pid = get_pid_from_file(pid_file)
            if _is_process_running(pid):
                return True
        time.sleep(1)
    return False

def start_process(script_name):
    log(f"Menjalankan {script_name} di latar belakang...")
    command = f"nohup {sys.executable} {script_name} > {script_name}.log 2>&1 &"
    subprocess.Popen(command, shell=True)
    expected_pid_file = MAIN_BOT_PID_FILE if script_name == MAIN_BOT_SCRIPT else MAINTENANCE_BOT_PID_FILE
    if _wait_for_pid_file(expected_pid_file, timeout_sec=30):
        log(f"Berhasil menjalankan {script_name} (PID file: {expected_pid_file}).")
    else:
        log(f"PERINGATAN: {script_name} belum menulis PID dalam batas waktu. Periksa log jika terjadi masalah.")

def follow_log_for(script_name):
    """Menampilkan log real-time untuk proses tertentu (Ctrl+C untuk keluar)."""
    log_file = f"{script_name}.log"
    log(f"Menampilkan log real-time: {log_file} (tekan Ctrl+C untuk berhenti)")
    try:
        subprocess.call(f"tail -F {log_file}", shell=True)
    except KeyboardInterrupt:
        pass

def follow_running_logs():
    """Mengikuti log dari proses yang sedang berjalan (main/maintenance)."""
    main_pid = get_pid_from_file(MAIN_BOT_PID_FILE)
    maint_pid = get_pid_from_file(MAINTENANCE_BOT_PID_FILE)
    if main_pid and _is_process_running(main_pid):
        follow_log_for(MAIN_BOT_SCRIPT)
    elif maint_pid and _is_process_running(maint_pid):
        follow_log_for(MAINTENANCE_BOT_SCRIPT)
    else:
        log("Tidak ada proses yang berjalan untuk diikuti log-nya.")

if __name__ == "__main__":
    # Dukungan argumen: on [--follow], off [--follow], logs
    if len(sys.argv) < 2 or sys.argv[1] not in ['on', 'off', 'logs']:
        log("ERROR: Argumen tidak valid. Gunakan 'on [--follow]', 'off [--follow]' atau 'logs'."); sys.exit(1)
    mode = sys.argv[1]
    follow = ('--follow' in sys.argv[2:])
    if mode == 'logs':
        follow_running_logs(); sys.exit(0)
    if mode == 'on':
        log("--- MENGAKTIFKAN MODE MAINTENANCE ---")
        kill_process(MAIN_BOT_PID_FILE)
        start_process(MAINTENANCE_BOT_SCRIPT)
        log("--- Mode maintenance SELESAI DIAKTIFKAN ---")
        if follow:
            follow_log_for(MAINTENANCE_BOT_SCRIPT)
    elif mode == 'off':
        log("--- MENONAKTIFKAN MODE MAINTENANCE ---")
        # Pastikan maintenance bot benar-benar mati
        if not kill_process(MAINTENANCE_BOT_PID_FILE):
            log("ERROR: Gagal mematikan proses maintenance sepenuhnya. Membatalkan start bot utama.")
            sys.exit(1)
        # Tambahan guard: pastikan tidak ada proses maintenance tersisa
        time.sleep(1)
        pid = get_pid_from_file(MAINTENANCE_BOT_PID_FILE)
        if pid and _is_process_running(pid):
            log("ERROR: Maintenance bot masih berjalan. Tidak memulai bot utama.")
            sys.exit(1)
        start_process(MAIN_BOT_SCRIPT)
        log("--- Mode maintenance SELESAI DINONAKTIFKAN ---")
        if follow:
            follow_log_for(MAIN_BOT_SCRIPT)
