import sys
import os
import subprocess
import time
import shutil
import threading
import logging

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QComboBox,
    QMessageBox, QGraphicsBlurEffect
)
from PyQt6.QtCore import Qt, QTimer, QPoint

# ==================【參數與路徑】==================
localver = "7.3.0"
creatName = "作者：Jed(Mis)"
updatateTime = "更新：2025/06/10"
StableVer = r"\\project-4\Xanthus_Tools\XanThusTools\Xanthus\bat\disk\ver.txt"
BetaVer = r"\\project-4\Xanthus_Tools\XanThusTools\Xanthus\bat\disk\beta-ver.txt"
StableExe = r"\\project-4\Xanthus_Tools\XanThusTools\Xanthus\bat\disk\diskLink.exe"
BetaExe = r"\\project-4\Xanthus_Tools\XanThusTools\Xanthus\bat\disk\beta-diskLink.exe"
passpath = r"\\project-4\Xanthus_Tools\XanthusMember_pass"
passfile = f"{os.environ.get('COMPUTERNAME', 'UnknownPC')}_帳號密碼.txt"
passfull = os.path.join(passpath, passfile)
# ================================================

PROJECTS = ["無特殊需求", "Yameme專案", "剪輯專用"]
DRIVE_MAP = {
    "U:": r"\\project-4\Xanthus_Tools",
    "Z:": r"\\Project\PROJECTS\Work",
    "Y:": r"\\Project-3\Projects\Work",
    "V:": r"\\project-4\Projects\Work",
    "W:": r"\\192.168.2.247\Projects",
    "X:": r"\\Project-6\Projects\Work",
    "S:": r"\\Project-7\Project\Work",
}

UPDATER_DIR = r"C:\\ProgramData\\XanthusUpdater"
UPDATER_EXE = os.path.join(UPDATER_DIR, "temp_updater.exe")
OLD_EXE_PATH = os.path.abspath(sys.argv[0])
NEW_EXE_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "temp_new.exe")
BETA_TARGET_EXE = os.path.join(os.path.expanduser("~"), "Desktop", "beta-磁碟機連線.exe")

if not os.path.exists(UPDATER_DIR):
    os.makedirs(UPDATER_DIR, exist_ok=True)

# ------------------------------------------------

def check_and_update():
    try:
        with open(BetaVer, 'r', encoding='utf-8') as f:
            bv = f.read().strip()
    except FileNotFoundError:
        bv = None
    try:
        with open(StableVer, 'r', encoding='utf-8') as f:
            sv = f.read().strip()
    except FileNotFoundError:
        sv = None

    if bv and bv != localver:
        pass
    if sv and sv != localver:
        shutil.copy(StableExe, NEW_EXE_PATH)
        QMessageBox.warning(None, "版本更新", "檢測到新版本，必須更新才能使用，將自動下載並重啟！")
        if not os.path.exists(UPDATER_EXE):
            QMessageBox.critical(None, "更新錯誤", f"找不到更新程式：{UPDATER_EXE}")
            sys.exit(1)
        subprocess.Popen([UPDATER_EXE, OLD_EXE_PATH, NEW_EXE_PATH], shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit(0)


def fallback_to_guest():
    QMessageBox.information(None, "警告", "檔案伺服器無法連接，將使用 guest 帳號進行連線。")
    return "guest", ""


def read_account():
    if os.path.exists(passfull):
        with open(passfull, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if ";" in line and not line.startswith("#"):
                    user, passwd = line.split(";", 1)
                    return user.strip(), passwd.strip()
    QMessageBox.warning(None, "警告", "帳號密碼檔案異常，請檢查檔案內容。")
    return None, None


def add_credentials(user, passwd):
    targets = [
        "Project-6", "192.168.2.247", "project-4",
        "Project-3", "Project", "Project-7"
    ]
    for t in targets:
        subprocess.run(["cmdkey", "/add:" + t, "/user:" + user, "/pass:" + passwd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)


def clear_credentials():
    targets = [
        "Project-6", "192.168.2.247", "project-5", "project-4",
        "Project-3", "Project", "Project-7"
    ]
    for t in targets:
        subprocess.run(["cmdkey", "/delete:" + t], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)


def remove_all_drives():
    for d in DRIVE_MAP.keys():
        subprocess.run(["net", "use", d, "/delete", "/y"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)


def restart_network():
    subprocess.run(["net", "stop", "workstation"], timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(5)
    subprocess.run(["net", "start", "workstation"], timeout=10, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(5)


class ModernDiskUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("磁碟機連線工具")
        self.resize(500, 430)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.main = QWidget(self)
        self.main.setGeometry(0, 0, 500, 430)
        self.main.setStyleSheet("background-color: rgba(255,255,255,180);border-radius:10px;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(15)
        self.main.setGraphicsEffect(blur)

        self._offset = QPoint()

        self.btn_close = QPushButton(self.main)
        self.btn_close.setGeometry(10, 10, 12, 12)
        self.btn_close.setStyleSheet("background:#ff5f57;border:none;border-radius:6px;")
        self.btn_close.clicked.connect(self.close)

        self.btn_min = QPushButton(self.main)
        self.btn_min.setGeometry(28, 10, 12, 12)
        self.btn_min.setStyleSheet("background:#ffbd2e;border:none;border-radius:6px;")
        self.btn_min.clicked.connect(self.showMinimized)

        QLabel(localver, self.main).move(50, 8)
        QLabel(creatName, self.main).move(350, 8)
        QLabel(updatateTime, self.main).move(350, 30)

        if localver == StableVer:
            self.switch_btn = QPushButton("參與測試版", self.main)
            self.switch_btn.clicked.connect(self.confirm_beta)
            self.switch_btn.setStyleSheet("background:#f0ad4e;color:white;border:none;border-radius:4px;")
        elif localver == BetaVer:
            self.switch_btn = QPushButton("退回穩定版", self.main)
            self.switch_btn.clicked.connect(self.confirm_stable)
            self.switch_btn.setStyleSheet("background:#5cb85c;color:white;border:none;border-radius:4px;")
        else:
            self.switch_btn = None
        if self.switch_btn:
            self.switch_btn.setGeometry(10, 35, 110, 28)

        self.btn_connect = QPushButton("連線磁碟機", self.main)
        self.btn_connect.setGeometry(150, 80, 200, 50)
        self.btn_connect.clicked.connect(self.on_connect)
        self.btn_connect.setStyleSheet("background:#007aff;color:white;font-weight:bold;border:none;border-radius:8px;")

        self.indicators = {}
        x = 20
        for d in DRIVE_MAP:
            lbl = QLabel(self.main)
            lbl.setGeometry(x, 160, 28, 28)
            lbl.setStyleSheet("background-color:rgba(204,204,204,180);border-radius:14px;")
            QLabel(d, self.main).move(x + 7, 210)
            self.indicators[d] = lbl
            x += 55

        QLabel("選擇專案：", self.main).move(60, 260)
        self.cmb = QComboBox(self.main)
        self.cmb.addItems(PROJECTS)
        self.cmb.setCurrentIndex(1)
        self.cmb.setGeometry(150, 260, 200, 30)
        self.btn_confirm = QPushButton("確定", self.main)
        self.btn_confirm.setGeometry(370, 260, 60, 30)
        self.btn_confirm.clicked.connect(self.on_confirm)
        self.btn_confirm.setStyleSheet("background:#34c759;color:white;border:none;border-radius:4px;")

        self.status_label = QLabel("", self.main)
        self.status_label.setGeometry(20, 380, 460, 28)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._offset)
            event.accept()

    def update_indicator(self, drive, success):
        lbl = self.indicators.get(drive)
        if lbl:
            color = '#4cd964' if success else '#ff3b30'
            lbl.setStyleSheet(f'background:{color};border-radius:14px;')

    def _update_status(self, msg):
        QTimer.singleShot(0, lambda m=msg: self.status_label.setText(m))

    def _enable_btn(self):
        QTimer.singleShot(0, lambda: self.btn_connect.setEnabled(True))

    def on_connect(self):
        self.btn_connect.setEnabled(False)
        self.status_label.setText('')
        threading.Thread(target=self._do_connect_steps, daemon=True).start()

    def _do_connect_steps(self):
        user, passwd = read_account()
        if not user or not passwd:
            self._update_status('帳號密碼讀取失敗，請聯絡MIS處理！')
            self._enable_btn()
            return
        self._update_status('正在清除認證...')
        self._clear_credentials_with_status()
        self._update_status('正在移除網路磁碟...')
        self._remove_all_drives_with_status()
        self._update_status('正在新增認證...')
        self._add_credentials_with_status(user, passwd)
        self._update_status('正在連線磁碟...')
        user, passwd, all_success = self._map_all_drives_with_retry_status(user, passwd)
        if all_success:
            self._update_status(f'歡迎[{user}]進入[Xanthus Team]網路！ (所有步驟完成)')
        else:
            self._update_status('多次嘗試後仍有磁碟機連線失敗，請檢查網路或帳號。 (所有步驟完成)')
        self._enable_btn()

    def _clear_credentials_with_status(self):
        targets = [
            'Project-6', '192.168.2.247', 'project-5', 'project-4',
            'Project-3', 'Project', 'Project-7'
        ]
        total = len(targets)
        for idx, t in enumerate(targets, start=1):
            subprocess.run(['cmdkey', '/delete:' + t], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            self._update_status(f'清除認證 {t} ({idx}/{total})')
        self._update_status('認證清除完成！')

    def _remove_all_drives_with_status(self):
        drives = list(DRIVE_MAP.keys())
        total = len(drives)
        for idx, d in enumerate(drives, start=1):
            result = subprocess.run(['net', 'use', d, '/delete', '/y'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            msg = f"[{'成功' if result.returncode==0 else '失敗'}] 移除 {d} ({idx}/{total})"
            self._update_status(msg)
        self._update_status('所有磁碟移除完成！')

    def _add_credentials_with_status(self, user, passwd):
        targets = [
            'Project-6', '192.168.2.247', 'project-4',
            'Project-3', 'Project', 'Project-7'
        ]
        total = len(targets)
        for idx, t in enumerate(targets, start=1):
            subprocess.run(['cmdkey', '/add:' + t, '/user:' + user, '/pass:' + passwd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            self._update_status(f'新增認證 {t} ({idx}/{total})')
        self._update_status('認證新增完成！')

    def _map_all_drives_with_retry_status(self, user, passwd):
        fail_count = 0
        max_retry = 3
        drives = list(DRIVE_MAP.items())
        for attempt in range(1, max_retry+1):
            all_success = True
            for idx, (d, path) in enumerate(drives, start=1):
                ret = subprocess.run(['net', 'use', d, path, f'/user:{user}', passwd, '/persistent:yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW).returncode
                ok = (ret == 0)
                msg = f"[{'成功' if ok else '失敗'}] 連線 {d} ({idx}/{len(drives)}) (第{attempt}次嘗試)"
                self._update_status(msg)
                self.update_indicator(d, ok)
                if not ok:
                    all_success = False
            if all_success:
                return user, passwd, True
            fail_count += 1
            if fail_count == 2:
                user, passwd = ("ReFlash_01", "@Qaz123@")
                self._update_status('第2次失敗，嘗試切換帳號並重試...')
                self._clear_credentials_with_status()
                self._remove_all_drives_with_status()
                self._add_credentials_with_status(user, passwd)
            elif fail_count == 3:
                self._update_status('第3次失敗，嘗試重啟網路服務並重試...')
                self.on_retry_limit()
                self._clear_credentials_with_status()
                self._remove_all_drives_with_status()
                self._add_credentials_with_status(user, passwd)
        return fallback_to_guest()

    def on_retry_limit(self):
        threading.Thread(target=self.restart_network, daemon=True).start()

    def restart_network(self):
        svc = 'workstation'
        self.safe_update(f'準備重啟服務：{svc} …')
        if self._stop_service(svc):
            time.sleep(2)
            if self._start_service(svc):
                self.safe_update('網路服務已重啟完成。')
            else:
                self.safe_update('啟動服務失敗，請手動檢查。')
        else:
            self.safe_update('停止服務失敗，請手動檢查。')

    def _stop_service(self, svc) -> bool:
        if not self.is_service_running(svc):
            self.safe_update('服務尚未啟動，跳過停止步驟。')
            return True
        try:
            subprocess.run(['net', 'stop', svc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
            self.safe_update('服務停止完成。')
            return True
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    def _start_service(self, svc) -> bool:
        try:
            subprocess.run(['net', 'start', svc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
            self.safe_update('服務啟動完成。')
            return True
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    def safe_update(self, msg):
        self._update_status(msg)

    def is_service_running(self, service_name):
        try:
            result = subprocess.run(['sc', 'query', service_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
            return 'RUNNING' in result.stdout
        except subprocess.TimeoutExpired:
            return False

    def on_confirm(self):
        sel = self.cmb.currentText()
        if sel == 'Yameme專案':
            subprocess.run(['net', 'use', 'Z:', '/delete', '/y'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(['net', 'use', 'Z:', r'\\Project-7\Project\Work', '/persistent:yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            QMessageBox.information(self, '切換完成', 'Z槽已切換為 Yameme專案！')
            self.update_indicator('Z:', True)
        elif sel == '剪輯專用':
            subprocess.run(['net', 'use', 'W:', '/delete', '/y'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(['net', 'use', 'W:', r'\\192.168.5.247\Projects', '/persistent:yes'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            QMessageBox.information(self, '切換完成', 'W槽已切換為 剪輯專用！')
            self.update_indicator('Z:', True)
        else:
            QMessageBox.information(self, '完成', '無特殊需求，磁碟機維持原連線。')

    def confirm_beta(self):
        if QMessageBox.question(self, '警告', '測試版極為不穩定，確定下載並使用?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self.download_and_update_beta, daemon=True).start()

    def confirm_stable(self):
        if QMessageBox.question(self, '確認', '是否確定下載並退回穩定版？', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self.download_and_update_stable, daemon=True).start()

    def download_and_update_beta(self):
        try:
            shutil.copy(BetaExe, NEW_EXE_PATH)
            QTimer.singleShot(0, lambda: QMessageBox.information(self, '下載完成', f'測試版已下載到桌面: {NEW_EXE_PATH}\n即將自動切換。'))
            if not os.path.exists(UPDATER_EXE):
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, '更新錯誤', f'找不到更新程式：{UPDATER_EXE}'))
                return
            subprocess.Popen([UPDATER_EXE, BETA_TARGET_EXE, NEW_EXE_PATH], shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
            QTimer.singleShot(1000, self.close)
        except Exception as e:
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, '下載失敗', f'無法下載測試版: {e}'))

    def download_and_update_stable(self):
        try:
            shutil.copy(StableExe, NEW_EXE_PATH)
            QTimer.singleShot(0, lambda: QMessageBox.information(self, '下載完成', f'穩定版已下載到桌面: {NEW_EXE_PATH}\n即將自動切換。'))
            if not os.path.exists(UPDATER_EXE):
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, '更新錯誤', f'找不到更新程式：{UPDATER_EXE}'))
                return
            subprocess.Popen([UPDATER_EXE, OLD_EXE_PATH, NEW_EXE_PATH], shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
            QTimer.singleShot(1000, self.close)
        except Exception as e:
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, '下載失敗', f'無法下載穩定版: {e}'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    check_and_update()
    ui = ModernDiskUI()
    ui.show()
    sys.exit(app.exec())
