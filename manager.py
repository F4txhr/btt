# ======================================================
# ISI LENGKAP FILE: manager.py
# ======================================================
import os, sys, signal, subprocess, time

MAIN_BOT_SCRIPT = "bot.py"
MAINTENANCE_BOT_SCRIPT = "maintenance_bot.py"
MAIN_BOT_PID_FILE = "main_bot.pid"
MAINTENANCE_BOT_PID_FILE = "maintenance_bot.pid"
LOG_FILE = "manager.log"
OP_LOCK_FILE = "manager.op.lock"

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
    # Skip start jika sudah berjalan
    expected_pid_file = MAIN_BOT_PID_FILE if script_name == MAIN_BOT_SCRIPT else MAINTENANCE_BOT_PID_FILE
    exist_pid = get_pid_from_file(expected_pid_file)
    if exist_pid and _is_process_running(exist_pid):
        log(f"{script_name} sudah berjalan dengan PID {exist_pid}. Lewati start.")
        return
    # Fallback cek ps
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True)
        for line in out.splitlines():
            if script_name in line and "grep" not in line:
                try:
                    pid = int(line.strip().split(None, 1)[0])
                    if _is_process_running(pid):
                        log(f"{script_name} terdeteksi via ps (PID {pid}). Lewati start.")
                        return
                except Exception:
                    pass
    except Exception:
        pass
    log(f"Menjalankan {script_name} di latar belakang...")
    command = f"PYTHONUNBUFFERED=1 nohup {sys.executable} {script_name} > {script_name}.log 2>&1 &"
    subprocess.Popen(command, shell=True)
    if _wait_for_pid_file(expected_pid_file, timeout_sec=30):
        log(f"Berhasil menjalankan {script_name} (PID file: {expected_pid_file}).")
    else:
        log(f"PERINGATAN: {script_name} belum menulis PID dalam batas waktu. Periksa log jika terjadi masalah.")

# --- TMUX SUPPORT ---

def _tmux_available() -> bool:
    try:
        subprocess.check_output(["tmux", "-V"], stderr=subprocess.STDOUT)
        return True
    except Exception:
        return False

def _tmux_session_name(script_name: str) -> str:
    return "btt-main" if script_name == MAIN_BOT_SCRIPT else "btt-maint"

def tmux_session_exists(session: str) -> bool:
    try:
        subprocess.check_call(["tmux", "has-session", "-t", session], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False

def tmux_start(script_name: str):
    session = _tmux_session_name(script_name)
    # Jalankan dengan tee agar tetap tercatat ke .log dan tampil di layar tmux
    cmd = f"PYTHONUNBUFFERED=1 {sys.executable} {script_name} 2>&1 | tee -a {script_name}.log"
    try:
        subprocess.check_call(["tmux", "new-session", "-d", "-s", session, cmd])
        log(f"Dijalankan di tmux session '{session}'.")
    except Exception as e:
        log(f"ERROR: Gagal menjalankan tmux session '{session}': {e}")

def tmux_attach(script_name: str):
    session = _tmux_session_name(script_name)
    if tmux_session_exists(session):
        log(f"Menempel ke tmux session: {session} (Ctrl+b d untuk detach)")
        try:
            subprocess.call(["tmux", "attach", "-t", session])
        except KeyboardInterrupt:
            pass
    else:
        follow_log_for(script_name)

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
        # Jika tmux ada dan session ada, attach; jika tidak, tail
        if _tmux_available() and tmux_session_exists(_tmux_session_name(MAIN_BOT_SCRIPT)):
            tmux_attach(MAIN_BOT_SCRIPT)
        else:
            follow_log_for(MAIN_BOT_SCRIPT)
    elif maint_pid and _is_process_running(maint_pid):
        if _tmux_available() and tmux_session_exists(_tmux_session_name(MAINTENANCE_BOT_SCRIPT)):
            tmux_attach(MAINTENANCE_BOT_SCRIPT)
        else:
            follow_log_for(MAINTENANCE_BOT_SCRIPT)
    else:
        log("Tidak ada proses yang berjalan untuk diikuti log-nya.")

def _detect_active_process():
    """Mengembalikan (script_name, pid) dari proses yang aktif, atau (None, None) jika tidak ada."""
    main_pid = get_pid_from_file(MAIN_BOT_PID_FILE)
    if main_pid and _is_process_running(main_pid):
        return (MAIN_BOT_SCRIPT, main_pid)
    maint_pid = get_pid_from_file(MAINTENANCE_BOT_PID_FILE)
    if maint_pid and _is_process_running(maint_pid):
        return (MAINTENANCE_BOT_SCRIPT, maint_pid)
    # Fallback cek ps
    try:
        out = subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True)
        for line in out.splitlines():
            if MAINTENANCE_BOT_SCRIPT in line and "grep" not in line:
                try:
                    pid = int(line.strip().split(None, 1)[0]);
                    if _is_process_running(pid): return (MAINTENANCE_BOT_SCRIPT, pid)
                except Exception: pass
        for line in out.splitlines():
            if MAIN_BOT_SCRIPT in line and "grep" not in line:
                try:
                    pid = int(line.strip().split(None, 1)[0]);
                    if _is_process_running(pid): return (MAIN_BOT_SCRIPT, pid)
                except Exception: pass
    except Exception:
        pass
    return (None, None)

def monitor_logs():
    """Mode monitor: otomatis mengikuti log proses aktif, berpindah saat proses berganti."""
    log("Memulai mode monitor log (Ctrl+C untuk keluar)...")
    current_script = None
    tail_proc = None
    try:
        while True:
            script, pid = _detect_active_process()
            if script != current_script:
                # hentikan tail lama jika ada
                if tail_proc and tail_proc.poll() is None:
                    try:
                        os.killpg(os.getpgid(tail_proc.pid), signal.SIGTERM)
                    except Exception:
                        try: tail_proc.terminate()
                        except Exception: pass
                    try: tail_proc.wait(timeout=2)
                    except Exception: pass
                tail_proc = None
                current_script = script
                if script:
                    log(f"Berpindah mengikuti log: {script}.log (PID: {pid})")
                    try:
                        tail_proc = subprocess.Popen(
                            ["tail", "-F", f"{script}.log"],
                            preexec_fn=os.setsid
                        )
                    except Exception as e:
                        log(f"ERROR: Gagal memulai tail untuk {script}.log: {e}")
                else:
                    log("Tidak ada proses aktif saat ini. Menunggu...")
            time.sleep(2)
    except KeyboardInterrupt:
        log("Monitor dihentikan oleh pengguna.")
    finally:
        if tail_proc and tail_proc.poll() is None:
            try:
                os.killpg(os.getpgid(tail_proc.pid), signal.SIGTERM)
            except Exception:
                try: tail_proc.terminate()
                except Exception: pass
            try: tail_proc.wait(timeout=2)
            except Exception: pass

if __name__ == "__main__":
    # Dukungan argumen: on [--follow] [--tmux], off [--follow] [--tmux], logs, monitor
    if len(sys.argv) < 2 or sys.argv[1] not in ['on', 'off', 'logs', 'monitor']:
        log("ERROR: Argumen tidak valid. Gunakan 'on [--follow] [--tmux]', 'off [--follow] [--tmux]', 'logs', atau 'monitor'."); sys.exit(1)
    mode = sys.argv[1]
    follow_flag = ('--follow' in sys.argv[2:])
    use_tmux_flag = ('--tmux' in sys.argv[2:]) or (os.getenv('MANAGER_TMUX', '0').lower() in ('1','true','yes'))
    is_interactive = sys.stdout.isatty()
    auto_follow = follow_flag or is_interactive

    if mode == 'logs':
        follow_running_logs(); sys.exit(0)
    if mode == 'monitor':
        monitor_logs(); sys.exit(0)

    # Operation lock agar tidak ada dua manager on/off berjalan bersamaan
    op_fd = None
    try:
        op_fd = os.open(OP_LOCK_FILE, os.O_CREAT | os.O_RDWR)
        import fcntl
        fcntl.flock(op_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        log("Operasi manager lain sedang berjalan. Coba lagi nanti.")
        sys.exit(1)

    try:
        if mode == 'on':
            log("--- MENGAKTIFKAN MODE MAINTENANCE ---")
            kill_process(MAIN_BOT_PID_FILE)
            if use_tmux_flag and _tmux_available():
                tmux_start(MAINTENANCE_BOT_SCRIPT)
            else:
                start_process(MAINTENANCE_BOT_SCRIPT)
            log("--- Mode maintenance SELESAI DIAKTIFKAN ---")
            if auto_follow:
                if use_tmux_flag and _tmux_available():
                    tmux_attach(MAINTENANCE_BOT_SCRIPT)
                else:
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
            if use_tmux_flag and _tmux_available():
                tmux_start(MAIN_BOT_SCRIPT)
            else:
                start_process(MAIN_BOT_SCRIPT)
            log("--- Mode maintenance SELESAI DINONAKTIFKAN ---")
            if auto_follow:
                if use_tmux_flag and _tmux_available():
                    tmux_attach(MAIN_BOT_SCRIPT)
                else:
                    follow_log_for(MAIN_BOT_SCRIPT)
    finally:
        # Lepaskan lock
        try:
            if op_fd is not None:
                import fcntl
                fcntl.flock(op_fd, fcntl.LOCK_UN)
                os.close(op_fd)
        except Exception:
            pass
