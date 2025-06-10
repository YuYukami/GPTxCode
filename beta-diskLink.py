import sys, os
import subprocess
import time
import shutil
import tkinter as tk
import threading
import logging
import shutil, tkinter as tk
from tkinter import ttk, messagebox

# ==================【參數與路徑】==================
localver        = "7.3.0"
creatName       = "作者：Jed(Mis)"
updatateTime    = "更新：2025/06/10"
StableVer       = r"\\project-4\Xanthus_Tools\XanThusTools\Xanthus\bat\disk\ver.txt"
BetaVer         = r"\\project-4\Xanthus_Tools\XanThusTools\Xanthus\bat\disk\beta-ver.txt"
StableExe       = r"\\project-4\Xanthus_Tools\XanThusTools\Xanthus\bat\disk\diskLink.exe"
BetaExe         = r"\\project-4\Xanthus_Tools\XanThusTools\Xanthus\bat\disk\beta-diskLink.exe"
passpath        = r"\\project-4\Xanthus_Tools\XanthusMember_pass"
passfile        = f"{os.environ.get('COMPUTERNAME', 'UnknownPC')}_帳號密碼.txt"
passfull        = os.path.join(passpath, passfile)
# ================================================
fail_count      = 0
fail_loop_point = 0
# ==================【網路檢測以及版本檢測】=================
try:
    with open(StableVer, 'r', encoding='utf-8') as f:
        sv = f.read().strip()
except FileNotFoundError:
    sv = None  # 如果檔案不存在，設置為 None
    logging.warning(f"StableVer 檔案不存在：{StableVer}")
    localver = "與伺服器斷線"

try:
    with open(BetaVer, 'r', encoding='utf-8') as f:
        bv = f.read().strip()
except FileNotFoundError:
    bv = None  # 如果檔案不存在，設置為 None
    logging.warning(f"BetaVer 檔案不存在：{BetaVer}")
# ================================================
PROJECTS = ["無特殊需求", "Yameme專案","剪輯專用"]
# ======【以下區塊為可編輯磁碟機路徑與目標主機】======
# 若要新增/刪除磁碟機，請編輯 DRIVE_MAP 這個 dict
DRIVE_MAP = {
    "U:": r"\\project-4\Xanthus_Tools",
    "Z:": r"\\Project\PROJECTS\Work",
    "Y:": r"\\Project-3\Projects\Work",
    "V:": r"\\project-4\Projects\Work",
    "W:": r"\\192.168.2.247\Projects",
    "X:": r"\\Project-6\Projects\Work",
    "S:": r"\\Project-7\Project\Work"
}
# 若要新增/刪除認證主機，請編輯 clear_credentials() 及 add_credentials() 內的 targets 清單

# ======【自動更新輔助程式整合區】======
# updater.exe 相關設定
UPDATER_DIR = r"C:\ProgramData\XanthusUpdater"  # 建議放在 C:\ProgramData 下，隱藏且所有用戶可存取
UPDATER_EXE = os.path.join(UPDATER_DIR, "temp_updater.exe")
OLD_EXE_PATH = os.path.abspath(sys.argv[0])  # 當前執行檔
NEW_EXE_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "temp_new.exe")  # 新版下載暫存路徑
BETA_TARGET_EXE = os.path.join(os.path.expanduser("~"), "Desktop", "beta-磁碟機連線.exe")

# 啟動前確保 updater 目錄存在
if not os.path.exists(UPDATER_DIR):
    os.makedirs(UPDATER_DIR, exist_ok=True)


# 2. 清除認證
def clear_credentials():
    targets = [
        "Project-6", "192.168.2.247", "project-5", "project-4",
        "Project-3", "Project", "Project-7"
    ]
    for t in targets:
        subprocess.run(["cmdkey", "/delete:" + t], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

# 3. 移除網路磁碟
def remove_all_drives():
    for d in ["U:", "V:", "W:", "X:", "Y:", "Z:", "S:"]:
        subprocess.run(["net", "use", d, "/delete", "/y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

# 4. 版本自動比對與自動更新（優化，強制更新，無法連線可繼續但警告）
def check_and_update():
    try:
        if bv and bv != localver:
            # Beta版本檢查邏輯
            pass  # Beta版本暫時不需要即時更新
            if sv and sv != localver:
                # 穩定版本檢查邏輯
                shutil.copy(StableExe, NEW_EXE_PATH)
                tk.messagebox.showwarning("版本更新", "檢測到新版本，必須更新才能使用，將自動下載並重啟！")
                if not os.path.exists(UPDATER_EXE):
                    tk.messagebox.showerror("更新錯誤", f"找不到更新程式：{UPDATER_EXE}")
                    sys.exit(1)
                subprocess.Popen([UPDATER_EXE, OLD_EXE_PATH, NEW_EXE_PATH], shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
                sys.exit(0)
    except FileNotFoundError:
        tk.messagebox.showwarning("警告", "找不到版本號檔案，將繼續使用舊版本。\n（無法連接檔案伺服器）")
    except Exception as e:
        tk.messagebox.showwarning("警告", f"版本檢查失敗：{e}\n將繼續使用舊版本。")


# 修正：新增一個函式以確保程式可以使用 guest 帳號進行連線
def fallback_to_guest():
    tk.messagebox.showinfo("警告", "檔案伺服器無法連接，將使用 guest 帳號進行連線。")
    return "guest", ""

# 5. 讀取帳密
def read_account():
    """
    從指定路徑(passfull)讀取帳號密碼 (格式：user;passwd)
    讀取失敗時跳出 warning，並回傳 (None, None)
    """
    if os.path.exists(passfull):
        with open(passfull, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if ";" in line and not line.startswith("#"):
                    user, passwd = line.split(";", 1)
                    return user.strip(), passwd.strip()
    # 如果執行到此，表示讀取失敗
    messagebox.showwarning("警告", "帳號密碼檔案異常，請檢查檔案內容。")
    return None, None

# 6. 新增認證
def add_credentials(user, passwd):
    targets = [
        "Project-6", "192.168.2.247", "project-4",
        "Project-3", "Project", "Project-7"
    ]
    for t in targets:
        subprocess.run(["cmdkey", "/add:" + t, "/user:" + user, "/pass:" + passwd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

# 7. 連線磁碟
def map_all_drives(user, passwd):
    global fail_count
    for d, path in DRIVE_MAP.items():
        result = subprocess.run(
            ["net", "use", d, path, "/user:" + user, passwd, "/persistent:yes"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            print(f"{d} 連線成功")
        else:
            print(f"{d} 連線失敗，錯誤代碼：{result.returncode}")
            fail_count += 1

# 8. 失敗重試與自動解碼帳號
def fail_rejoin(fail_times):
    # 這裡可自動切換帳密，也可彈窗請 MIS 輸入
    if fail_times == 2:
        return "ReFlash_01", "@Qaz123@"
    elif fail_times == 3:
        return "ReFlash_02", "@Qaz123@"
    else:
        return None, None

# 9. 連線失敗時自動重啟網路服務再重試
def restart_network():
    subprocess.run(["net", "stop", "workstation"],timeout=10 ,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(5)
    subprocess.run(["net", "start", "workstation"],timeout=10 ,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(5)

def map_all_drives_with_retry(user, passwd, update_status_cb):
    original_user, original_passwd = user, passwd
    max_retry = 3
    for attempt in range(1, max_retry+1):
        all_success = True
        clear_credentials()  # 清除認證
        time.sleep(3)  # 等待 3 秒
        for d, path in DRIVE_MAP.items():
            ret = subprocess.run(
                ["net", "use", d, path, f"/user:{user}", passwd, "/persistent:yes"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
            ).returncode
            update_status_cb(d, ret == 0)
            if ret != 0:
                all_success = False
        if all_success:
            return user, passwd, True
        # 第2、3次失敗時，先用備援帳號嘗試
        if attempt in (2, 3):
            tmp_user = f"ReFlash_0{attempt-1}"
            tmp_pass = "@Qaz123@"
            restart_network()
            clear_credentials()
            time.sleep(3)  # 等待 3 秒
            add_credentials(tmp_user, tmp_pass)
            all_success_tmp = True
            for d, path in DRIVE_MAP.items():
                ret = subprocess.run(
                    ["net", "use", d, path, f"/user:{tmp_user}", tmp_pass, "/persistent:yes"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
                ).returncode
                update_status_cb(d, ret == 0)
                if ret != 0:
                    all_success_tmp = False
            if all_success_tmp:
                # 備援帳號成功，立即切回原帳號再試一次
                clear_credentials()
                time.sleep(3)  # 等待 3 秒
                add_credentials(original_user, original_passwd)
                all_success_origin = True
                for d, path in DRIVE_MAP.items():
                    ret = subprocess.run(
                        ["net", "use", d, path, f"/user:{original_user}", original_passwd, "/persistent:yes"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
                    ).returncode
                    update_status_cb(d, ret == 0)
                    if ret != 0:
                        all_success_origin = False
                if all_success_origin:
                    return original_user, original_passwd, True
                else:
                    return original_user, original_passwd, False
            # 若備援帳號也失敗，繼續下一輪
            user, passwd = original_user, original_passwd
            clear_credentials()
            time.sleep(3)  # 等待 3 秒
            add_credentials(user, passwd)
        elif attempt == 3:
            restart_network()
            clear_credentials()
            time.sleep(3)  # 等待 3 秒
            add_credentials(user, passwd)
    return fallback_to_guest()  # 使用 guest 帳號進行連線

class ModernDiskUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("磁碟機連線工具")
        self.geometry("500x430")
        self.configure(bg="#f8f9fa")
        self.resizable(False, False)
        # 自動偵測圖示路徑，兼容 PyInstaller 打包與原始碼執行
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
            ico_path = os.path.join(base_path, 'server3.ico')
            self.iconbitmap(ico_path)
        except Exception:
            pass

        # 頂部資訊區
        tk.Label(self, text=f"{localver}", font=("Segoe UI", 11, "bold"), bg="#f8f9fa", fg="#222").place(x=10, y=8)
        tk.Label(self, text=f"{creatName}", font=("Segoe UI", 11), bg="#f8f9fa", fg="#222").place(x=350, y=8)
        tk.Label(self, text=f"{updatateTime}", font=("Segoe UI", 11), bg="#f8f9fa", fg="#222").place(x=350, y=30)
        # 版本切換按鈕
        if bv == sv: # 測試版與穩定版相同，則不顯示按鈕
            self.switch_btn = None
        elif localver == sv:
            self.switch_btn = tk.Button(self, text="參與測試版", bg="#f0ad4e", fg="white", font=("Segoe UI", 10, "bold"), command=self.confirm_beta)
        elif localver == bv:
            self.switch_btn = tk.Button(self, text="退回穩定版", bg="#5cb85c", fg="white", font=("Segoe UI", 10, "bold"), command=self.confirm_stable)
        else:
            self.switch_btn = None
        if self.switch_btn:
            self.switch_btn.place(x=10, y=35, width=110, height=28)
        # 連線按鈕
        self.btn_connect = tk.Button(self, text="連線磁碟機", font=("Segoe UI", 16, "bold"),
                                     bg="#007aff", fg="white", relief="flat", command=self.on_connect)
        self.btn_connect.place(x=150, y=80, width=200, height=50)

        # 燈號顯示
        self.canvas = tk.Canvas(self, width=420, height=60, bg="#f8f9fa", highlightthickness=0, bd=0)
        self.canvas.place(x=40, y=160)
        self.indicators = self.draw_indicators()

        # 專案下拉選單
        tk.Label(self, text="選擇專案：", font=("Segoe UI", 12), bg="#f8f9fa", fg="#222").place(x=60, y=260)
        self.project_var = tk.StringVar(value=PROJECTS[1])
        self.cmb = ttk.Combobox(self, textvariable=self.project_var, values=PROJECTS, state="readonly", font=("Segoe UI", 12))
        self.cmb.place(x=150, y=260, width=200, height=30)
        self.btn_confirm = tk.Button(self, text="確定", font=("Segoe UI", 12), bg="#34c759", fg="white", relief="flat", command=self.on_confirm)
        self.btn_confirm.place(x=370, y=260, width=60, height=30)

        # 狀態提示區（置中）
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(self, textvariable=self.status_var, font=("Segoe UI", 11),
                                     bg="#f8f9fa", fg="#d0021b", anchor="center", justify="center")
        self.status_label.place(x=20, y=380, width=460, height=28)
        

    def draw_indicators(self):
        ind = {}
        x = 20
        for d in DRIVE_MAP:
            cid = self.canvas.create_oval(x, 10, x+28, 38, fill="#cccccc", outline="")
            self.canvas.create_text(x+14, 50, text=d, fill="#222", font=("Segoe UI", 11))
            ind[d] = cid
            x += 55
        return ind

    def update_status(self, drive, success):
        cid = self.indicators.get(drive)
        if cid:
            color = "#4cd964" if success else "#ff3b30"
            self.canvas.itemconfig(cid, fill=color)

    def on_connect(self):
        self.btn_connect.config(state="disabled")
        self.status_var.set("")
        threading.Thread(target=self._do_connect_steps, daemon=True).start()

    def _do_connect_steps(self):
        user, passwd = read_account()
        if not user or not passwd:
            self._update_status("帳號密碼讀取失敗，請聯絡MIS處理！")
            self._enable_btn()
            return
        # 2. 清除認證
        self._update_status("正在清除認證...")
        self._clear_credentials_with_status()
        # 3. 移除所有磁碟
        self._update_status("正在移除網路磁碟...")
        self._remove_all_drives_with_status()
        # 4. 新增認證
        self._update_status("正在新增認證...")
        self._add_credentials_with_status(user, passwd)
        # 5. 連線磁碟（含重試/換帳密/重啟網路）
        self._update_status("正在連線磁碟...")
        user, passwd, all_success = self._map_all_drives_with_retry_status(user, passwd)
        if all_success:
            self._update_status(f"歡迎[{user}]進入[Xanthus Team]網路！ (所有步驟完成)")
        else:
            self._update_status("多次嘗試後仍有磁碟機連線失敗，請檢查網路或帳號。 (所有步驟完成)")
        self._enable_btn()

    def _update_status(self, msg):
        self.after(0, lambda: self.status_var.set(msg))

    def _enable_btn(self):
        self.after(0, lambda: self.btn_connect.config(state="normal"))

    def _clear_credentials_with_status(self):
        targets = [
            "Project-6", "192.168.2.247", "project-5", "project-4",
            "Project-3", "Project", "Project-7"
        ]
        total = len(targets)
        for idx, t in enumerate(targets, start=1):
            subprocess.run(["cmdkey", "/delete:" + t], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            self._update_status(f"清除認證 {t} ({idx}/{total})")
        self._update_status("認證清除完成！")

    def _remove_all_drives_with_status(self):
        drives = list(DRIVE_MAP.keys())
        total = len(drives)
        for idx, d in enumerate(drives, start=1):
            result = subprocess.run(["net", "use", d, "/delete", "/y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                msg = f"[成功] 移除 {d} ({idx}/{total})"
            else:
                msg = f"[失敗] 移除 {d} ({idx}/{total})"
            self._update_status(msg)
        self._update_status("所有磁碟移除完成！")

    def _add_credentials_with_status(self, user, passwd):
        targets = [
            "Project-6", "192.168.2.247", "project-4",
            "Project-3", "Project", "Project-7"
        ]
        total = len(targets)
        for idx, t in enumerate(targets, start=1):
            subprocess.run(["cmdkey", "/add:" + t, "/user:" + user, "/pass:" + passwd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            self._update_status(f"新增認證 {t} ({idx}/{total})")
        self._update_status("認證新增完成！")

    def _map_all_drives_with_retry_status(self, user, passwd):
        fail_count = 0
        max_retry = 3
        drives = list(DRIVE_MAP.items())
        for attempt in range(1, max_retry+1):
            all_success = True
            for idx, (d, path) in enumerate(drives, start=1):
                ret = subprocess.run(
                    ["net", "use", d, path, f"/user:{user}", passwd, "/persistent:yes"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
                ).returncode
                ok = (ret == 0)
                msg = f"[{'成功' if ok else '失敗'}] 連線 {d} ({idx}/{len(drives)}) (第{attempt}次嘗試)"
                self._update_status(msg)
                self.after(0, lambda d=d, ok=ok: self.update_status(d, ok))  # 即時更新燈號
                if not ok:
                    all_success = False
            if all_success:
                return user, passwd, True
            fail_count += 1
            if fail_count == 2:
                user, passwd = fail_rejoin(fail_count)
                if not user:
                    self._update_status("帳號切換失敗，已放棄重試。")
                    break
                self._update_status("第2次失敗，嘗試切換帳號並重試...")
                self._clear_credentials_with_status()
                self._remove_all_drives_with_status()
                self._add_credentials_with_status(user, passwd)
            elif fail_count == 3:
                self._update_status("第3次失敗，嘗試重啟網路服務並重試...")
                self.on_retry_limit()
                self._clear_credentials_with_status()
                self._remove_all_drives_with_status()
                self._add_credentials_with_status(user, passwd)
        return user, passwd, False

    def on_retry_limit(self):
        # 第3次失敗時呼叫
        threading.Thread(target=self.restart_network, daemon=True).start()

    def restart_network(self):
        svc = "workstation"
        self.safe_update(f"準備重啟服務：{svc} …")
        logging.info(f"Attempting to restart service: {svc}")

        if self._stop_service(svc):
            time.sleep(2)
            if self._start_service(svc):
                self.safe_update("網路服務已重啟完成。")
            else:
                self.safe_update("啟動服務失敗，請手動檢查。")
        else:
            self.safe_update("停止服務失敗，請手動檢查。")

    def _stop_service(self, svc) -> bool:
        if not self.is_service_running(svc):
            logging.info(f"{svc} not running, skip stop.")
            self.safe_update("服務尚未啟動，跳過停止步驟。")
            return True
        try:
            logging.info(f"Stopping {svc} …")
            subprocess.run(
                ["net", "stop", svc],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=20
            )
            logging.info(f"{svc} stopped.")
            self.safe_update("服務停止完成。")
            return True
        except subprocess.TimeoutExpired:
            logging.warning(f"Timeout stopping {svc}")
            return False
        except Exception as e:
            logging.exception(f"Error stopping {svc}: {e}")
            return False

    def _start_service(self, svc) -> bool:
        try:
            logging.info(f"Starting {svc} …")
            subprocess.run(
                ["net", "start", svc],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=20
            )
            logging.info(f"{svc} started.")
            self.safe_update("服務啟動完成。")
            return True
        except subprocess.TimeoutExpired:
            logging.warning(f"Timeout starting {svc}")
            return False
        except Exception as e:
            logging.exception(f"Error starting {svc}: {e}")
            return False

    def safe_update(self, msg):
        self.after(0, lambda: self._update_status(msg))

    def is_service_running(self, service_name):
        try:
            result = subprocess.run(
                ["sc", "query", service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )
            return "RUNNING" in result.stdout
        except subprocess.TimeoutExpired:
            return False

    def on_confirm(self):
        sel = self.project_var.get()
        if sel == "Yameme專案":
            subprocess.run(["net", "use", "Z:", "/delete", "/y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "use", "Z:", r"\\Project-7\Project\Work", "/persistent:yes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("切換完成", "Z槽已切換為 Yameme專案！")
            self.update_status("Z:", True)
        if sel == "剪輯專用":
            subprocess.run(["net", "use", "W:", "/delete", "/y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["net", "use", "W:", r"\\192.168.5.247\Projects", "/persistent:yes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("切換完成", "W槽已切換為 剪輯專用！")
            self.update_status("Z:", True)
        else:
            messagebox.showinfo("完成", "無特殊需求，磁碟機維持原連線。")

    def confirm_beta(self):
        if messagebox.askyesno("警告", "測試版極為不穩定，確定下載並使用?"):
            threading.Thread(target=self.download_and_update_beta, daemon=True).start()

    def confirm_stable(self):
        if messagebox.askyesno("確認", "是否確定下載並退回穩定版？"):
            threading.Thread(target=self.download_and_update_stable, daemon=True).start()

    def download_and_update_beta(self):
        try:
            shutil.copy(BetaExe, NEW_EXE_PATH)  # 下載到 temp_new.exe
            self.after(0, lambda: messagebox.showinfo("下載完成", f"測試版已下載到桌面: {NEW_EXE_PATH}\n即將自動切換。"))
            if not os.path.exists(UPDATER_EXE):
                self.after(0, lambda: messagebox.showerror("更新錯誤", f"找不到更新程式：{UPDATER_EXE}"))
                return
            subprocess.Popen([UPDATER_EXE, BETA_TARGET_EXE, NEW_EXE_PATH], shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
            self.after(1000, self.quit)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("下載失敗", f"無法下載測試版: {e}"))

    def download_and_update_stable(self):
        try:
            shutil.copy(StableExe, NEW_EXE_PATH)
            self.after(0, lambda: messagebox.showinfo("下載完成", f"穩定版已下載到桌面: {NEW_EXE_PATH}\n即將自動切換。"))
            if not os.path.exists(UPDATER_EXE):
                self.after(0, lambda: messagebox.showerror("更新錯誤", f"找不到更新程式：{UPDATER_EXE}"))
                return
            subprocess.Popen([UPDATER_EXE, OLD_EXE_PATH, NEW_EXE_PATH], shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
            self.after(1000, self.quit)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("下載失敗", f"無法下載穩定版: {e}"))

if __name__ == "__main__":
    check_and_update()
    app = ModernDiskUI()
    app.mainloop()