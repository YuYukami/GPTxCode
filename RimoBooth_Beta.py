import sys
import re
import os
import zipfile
import rarfile
import json
import pyperclip
import shutil
import logging
from logging.handlers import RotatingFileHandler
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QLabel, QPushButton, QFileDialog, QHBoxLayout, QMessageBox, QGridLayout, QScrollArea, QVBoxLayout, QSizePolicy, QInputDialog, QComboBox, QLineEdit, QSplitter, QCheckBox, QFrame, QDialog, QGroupBox
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from io import BytesIO
from PIL import Image
from pathlib import Path

# 版本號:V1.4.0
# 創建日期:2025/05/27

# 設定 logger
logger = logging.getLogger("RimoBooth")
logger.setLevel(logging.DEBUG)  # 開發時使用 DEBUG，正式環境可改為 INFO

# 設定檔案處理器（每個檔案最大 5MB，保留 3 個備份）
file_handler = RotatingFileHandler(
    filename="RimoBooth.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
file_handler.setFormatter(file_fmt)
logger.addHandler(file_handler)

# 設定控制台處理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_fmt = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_fmt)
logger.addHandler(console_handler)

BASE_DIR = Path(__file__).parent
AVATAR_FILE = "Avatar.json"
LANGUAGE_FILE = BASE_DIR / "languages.json"
SCAN_RECORD_FILE = "scan_records.json"
IMAGE_CACHE_DIR = "CachedImages"
CONFIG_FILE = "config.json"



def load_config():
    """讀取用戶設置，如語言"""
    logger.info("開始讀取設定檔：%s", CONFIG_FILE)
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info("設定檔讀取成功")
            return config
        else:
            logger.warning("設定檔不存在，採用預設值")
            return {"language": "zh-TW"}  # 預設為繁體中文
    except Exception as e:
        logger.exception("讀取設定檔時發生例外，採用預設值")
        return {"language": "zh-TW"}

def save_config(config):
    """保存用戶設置"""
    logger.info("開始保存設定檔")
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("設定檔保存成功")
    except Exception as e:
        logger.exception("保存設定檔時發生錯誤")
        
# 創建圖片快取資料夾
if not os.path.exists(IMAGE_CACHE_DIR):
    os.makedirs(IMAGE_CACHE_DIR)
# 讀取Avatar
def load_avatars():
    if os.path.exists(AVATAR_FILE):
        with open(AVATAR_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []
# 保存Avatar
def save_avatars(avatars):
    with open(AVATAR_FILE, 'w', encoding='utf-8') as f:
        json.dump(avatars, f, indent=4)

# 讀取語言檔案

# 定義必要的語言鍵值
REQUIRED_KEYS = {
    "window_title",
    "author",
    "version",
    "reload",
    "add_character",
    "select_language",
    "new_database",
    "database_title",
    "database_message",
    "loading_title",
    "loading_message",
    "select_folder",
    "cache_title",
    "cache_message"
}

# 預設語言字串
DEFAULT_STRINGS = {
    "window_title": "衣服查詢器",
    "author": "創作者: Rimo",
    "version": "版本號: V1.4.0",
    "reload": "重新讀取",
    "add_character": "新增角色",
    "select_language": "選擇語言",
    "new_database": "新增資料庫",
    "database_title": "資料庫",
    "database_message": "沒有舊資料，是否要更新資料庫?",
    "loading_title": "讀取資料",
    "loading_message": "正在讀取資料，請稍候...",
    "select_folder": "請選擇 ZIP/RAR 資料夾",
    "cache_title": "建立快取",
    "cache_message": "是否建立圖片快取?"
}

def load_languages():
    """載入語言檔案，提供多語言支援並確保所有必要的鍵值都存在"""
    logger.debug(f"開始載入語言檔：{LANGUAGE_FILE}")
    
    # 預設語言設定
    DEFAULT_LANGS = {"zh-TW": DEFAULT_STRINGS.copy()}
    
    try:
        if not os.path.exists(LANGUAGE_FILE):
            logger.error(f"語言檔不存在：{LANGUAGE_FILE}")
            logger.warning("使用預設語言設定")
            return DEFAULT_LANGS

        with open(LANGUAGE_FILE, "r", encoding="utf-8") as f:
            langs = json.load(f)
            
        # 檢查每個語系是否有所有必要的鍵值
        for lang, entries in langs.items():
            missing = REQUIRED_KEYS - set(entries.keys())
            if missing:
                logger.warning(f"語系 {lang} 缺少以下鍵值：{missing}")
                logger.warning("將自動補充預設值")
                for key in missing:
                    entries[key] = DEFAULT_STRINGS.get(key, "")

        logger.debug(f"成功載入 {len(langs)} 種語言設定")
        return langs
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失敗 ({LANGUAGE_FILE})：{e.msg} (line {e.lineno} col {e.colno})")
        logger.warning("使用預設語言設定")
        return DEFAULT_LANGS
    except Exception as e:
        logger.exception("讀取語言檔時發生未預期錯誤")
        logger.warning("使用預設語言設定")
        return DEFAULT_LANGS
class ZipQueryApp(QWidget):
    # 定義標籤選項（與分類篩選項目相同）
    TAG_OPTIONS = ["服裝", "配件", "髮型", "其他"]    
    def __init__(self):
        try:
            logger.info("開始初始化 ZipQueryApp 基礎元件")
            super().__init__()
            
            # 1. 初始化基本樣式
            logger.info("正在套用對話框樣式")
            self._apply_dialog_style()
            
            # 2. 初始化基本變數
            logger.info("正在初始化基本設定")
            self.config = {"language": "zh-TW"}
            
            logger.info("正在載入語言檔")
            self.languages = load_languages()
            self.current_language = "zh-TW"
            
            logger.info("正在載入角色設定")
            self.avatars = load_avatars()
            logger.info(f"已載入 {len(self.avatars)} 個角色設定")
            
            self.sort_mode = "加入時間 ↓"
            self.zip_files = {}
            
            # 3. 語言選擇對話框
            logger.info("顯示語言選擇對話框")
            lang, ok = self._show_language_dialog()
            if ok and lang:
                self.config["language"] = lang
                self.current_language = lang
                save_config(self.config)
                logger.info(f"用戶已選擇語言: {lang}")
            else:
                logger.info("用戶取消選擇語言，使用預設值")
            
            # 4. 檢查資料庫文件
            logger.info("正在檢查資料庫文件")
            if not os.path.exists(SCAN_RECORD_FILE):
                logger.warning("找不到資料庫文件，詢問用戶是否要建立")
                if self._show_create_database_dialog():
                    try:
                        logger.info("開始建立新資料庫")
                        self.create_new_database()
                        logger.info("成功建立新資料庫")
                    except Exception as e:
                        logger.exception("建立資料庫失敗")
                        self._show_error_dialog("建立資料庫時發生錯誤", str(e))
                        QApplication.quit()
                        return
                else:
                    logger.info("用戶取消建立新資料庫，程式將結束")
                    QApplication.quit()
                    return
            
            # 5. 初始化 UI
            logger.info("開始初始化使用者介面")
            self.initUI()
            logger.info("使用者介面初始化完成")
            
            # 6. 載入並清理記錄
            logger.info("開始載入並清理記錄")
            self.clean_and_load_records()
            logger.info("記錄清理和載入完成")
            
            # 7. 顯示主視窗
            logger.info("顯示主視窗")
            self.show()
            logger.info("ZipQueryApp 初始化完成")
            
        except Exception as e:
            logger.exception("初始化 ZipQueryApp 時發生嚴重錯誤")
            self._show_error_dialog("錯誤", f"初始化程式時發生嚴重錯誤：\n{str(e)}")
            raise

    def _apply_dialog_style(self):
        """套用對話框樣式"""
        style = """
            QDialog {
                background-color: #F5F5F7;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QLabel {
                color: #1D1D1F;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton {
                background-color: #0071E3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0077ED;
            }
            QPushButton:pressed {
                background-color: #006EDB;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #D2D2D7;
                border-radius: 6px;
                background: white;
                min-width: 200px;
            }
            QMessageBox {
                background-color: #F5F5F7;
            }
        """
        self.setStyleSheet(style)

    def _show_language_dialog(self):
        """顯示美化的語言選擇對話框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("選擇語言")
        dialog.setFixedWidth(300)
        layout = QVBoxLayout()
        
        # 標題
        label = QLabel("請選擇您的語言:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # 語言選擇下拉框
        combo = QComboBox()
        combo.addItems(load_languages().keys())
        layout.addWidget(combo)
        
        # 按鈕
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("確定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return combo.currentText(), True
        return None, False

    def _show_create_database_dialog(self):
        """顯示美化的建立資料庫確認對話框"""
        msg = QMessageBox(self)
        msg.setWindowTitle("建立資料庫")
        msg.setText("找不到資料庫檔案(scan_records.json)")
        msg.setInformativeText("是否要建立新的資料庫？")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        return msg.exec() == QMessageBox.StandardButton.Yes

    def _show_error_dialog(self, title, message):
        """顯示美化的錯誤訊息對話框"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()

    def clean_and_load_records(self):
        """清理並載入記錄"""
        logger.info("開始清理並載入記錄")
        
        # 從程式所在資料夾讀取資料庫檔案
        scan_record_path = BASE_DIR / SCAN_RECORD_FILE
        logger.info("讀取資料庫檔案：%s", scan_record_path)
            
        try:
            with open(scan_record_path, "r", encoding="utf-8") as f:
                self.zip_files = json.load(f)
            logger.info("成功載入資料庫")
        except FileNotFoundError:
            logger.warning("找不到資料庫檔案，建立空的記錄")
            self.zip_files = {}
        except json.JSONDecodeError:
            logger.error("資料庫檔案格式錯誤")
            QMessageBox.warning(self, "警告", "資料庫檔案格式錯誤，將重置為空白資料庫")
            self.zip_files = {}

    def initUI(self):
        self.setWindowTitle("衣服查詢器")
        self.setGeometry(100, 100, 1100, 700)
        main_layout = QVBoxLayout()

        # ===== 上方統計/排序區 =====
        header_layout = QHBoxLayout()
        self.info_label = QLabel()
        header_layout.addWidget(self.info_label)
        
        # 新增重新載入按鈕
        self.reload_button = QPushButton("重新載入")
        self.reload_button.clicked.connect(self.reload_data)
        header_layout.addWidget(self.reload_button)
        # 新增角色
        self.add_character_button = QPushButton(self.languages[self.current_language]["add_character"])
        self.add_character_button.clicked.connect(self.add_new_character)
        header_layout.addWidget(self.add_character_button)
        # 新資料庫
        self.new_database_button = QPushButton(self.languages[self.current_language]["new_database"])
        self.new_database_button.clicked.connect(self.create_new_database)
        header_layout.addWidget(self.new_database_button)
        
        header_layout.addStretch()
        self.language_selector = QComboBox()
        self.language_selector.addItems(self.languages.keys())
        self.language_selector.currentTextChanged.connect(self.change_language)
        header_layout.addWidget(self.language_selector)
        main_layout.addLayout(header_layout)

        # ===== 主體區塊：QSplitter 左右分割 =====
        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)

        # ===== 左側篩選/搜尋欄 =====
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        # 搜尋欄
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜尋資產…")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self.on_search)
        left_layout.addWidget(self.search_input)
        # 類型篩選
        left_layout.addWidget(QLabel("資產類型："))
        self.asset_type_combo = QComboBox()
        self.asset_type_combo.addItems(["全部", "Avatar", "相關", "World"])
        self.asset_type_combo.currentTextChanged.connect(self.on_type_changed)
        left_layout.addWidget(self.asset_type_combo)
        # 分類篩選
        left_layout.addWidget(QLabel("分類："))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["全部", "服裝", "配件", "髮型", "其他"])
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        left_layout.addWidget(self.category_combo)
        # 標籤篩選
        left_layout.addWidget(QLabel("標籤："))
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("輸入標籤…")
        self.tag_input.returnPressed.connect(self.on_tag_search)
        left_layout.addWidget(self.tag_input)
        # 支援 Avatar
        self.avatar_support_checkbox = QCheckBox("僅顯示支援 Avatar")
        self.avatar_support_checkbox.stateChanged.connect(self.on_avatar_support_changed)
        left_layout.addWidget(self.avatar_support_checkbox)
        # 角色列表
        left_layout.addWidget(QLabel("角色："))
        self.character_combo = QComboBox()
        self.character_combo.addItems(self.avatars)
        self.character_combo.currentTextChanged.connect(self.filter_files)
        left_layout.addWidget(self.character_combo)
        left_layout.addStretch()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # ===== 右側分為預覽區和詳細資料區 =====
        right_container = QWidget()
        right_container_layout = QHBoxLayout()
        
        # === 中間預覽區 ===
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        
        # 排序區域
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("排序方式："))
        self.sort_mode_combo = QComboBox()
        modes = ['加入時間 ↓', '加入時間 ↑', '名稱 A→Z', '名稱 Z→A']
        self.sort_mode_combo.addItems(modes)
        self.sort_mode_combo.setCurrentText(self.sort_mode)
        self.sort_mode_combo.currentTextChanged.connect(self.on_sort_mode_changed)
        sort_layout.addWidget(self.sort_mode_combo)
        sort_layout.addStretch()
        preview_layout.addLayout(sort_layout)
        
        # 預覽區域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_container = QWidget()
        self.image_grid = QGridLayout()
        self.image_grid.setSpacing(5)  # 減小間距
        self.image_container.setLayout(self.image_grid)
        self.scroll_area.setWidget(self.image_container)
        preview_layout.addWidget(self.scroll_area)
        
        preview_widget.setLayout(preview_layout)
        right_container_layout.addWidget(preview_widget, 2)  # 佔據 2/3 空間
        
        # === 右側詳細資料區 ===
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        details_layout.setSpacing(10)
        
        # 標題
        details_layout.addWidget(QLabel("詳細資料"))
        
        # 修改按鈕
        self.edit_button = QPushButton("修改資料")
        self.edit_button.clicked.connect(self.edit_record)
        details_layout.addWidget(self.edit_button)
        
        # 預覽圖
        self.details_image = QLabel()
        self.details_image.setFixedSize(200, 200)
        self.details_image.setScaledContents(True)
        details_layout.addWidget(self.details_image)
        
        # 名稱（可點擊複製）
        self.details_name = QLabel()
        self.details_name.setCursor(Qt.CursorShape.PointingHandCursor)
        self.details_name.mousePressEvent = lambda e: self.copy_name_to_clipboard()
        details_layout.addWidget(self.details_name)
        
        # 網址
        self.details_url = QLabel()
        self.details_url.setWordWrap(True)
        details_layout.addWidget(self.details_url)
        
        # 標籤
        self.details_tags = QLabel()
        self.details_tags.setWordWrap(True)
        details_layout.addWidget(self.details_tags)
        
        details_layout.addStretch()
        details_widget.setLayout(details_layout)
        right_container_layout.addWidget(details_widget, 1)  # 佔據 1/3 空間
        
        right_container.setLayout(right_container_layout)
        splitter.addWidget(right_container)
        splitter.setSizes([250, 850])
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
        # 套用 macOS 類似風格（淺灰背景、圓角、藍色主按鈕）
        mac_style = """
        QWidget {
            background-color: #F2F2F2;
            font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 13px;
        }
        QListWidget, QScrollArea {
            background-color: #FFFFFF;
            border: 1px solid #D1D1D1;
            border-radius: 6px;
        }
        QPushButton {
            color: #007AFF;
            background-color: transparent;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #E5E5EA;
        }
        QPushButton:pressed {
            background-color: #D1D1D6;
        }
        QComboBox {
            background-color: #FFFFFF;
            border: 1px solid #D1D1D1;
            border-radius: 6px;
            padding: 4px 8px;
        }
        QLabel {
            color: #333333;
        }
        """
        # 初始載入資料與語言設定
        self.zip_files = self.load_scan_records()
        self.current_selected_character = None
        self.current_zip_paths = []
        self.sort_mode_combo.currentTextChanged.connect(self.on_view_mode_changed)
        self.on_sort_mode_changed(self.sort_mode_combo.currentText())
        self.setStyleSheet(mac_style)
        self.change_language(self.current_language)
        if self.avatars:
            self.character_combo.setCurrentIndex(0)
            self.filter_files()


    def create_new_database(self):
        """用戶選擇新的資料夾來創建新資料庫"""
        logger.info("開始建立新資料庫")
        
        new_folder = QFileDialog.getExistingDirectory(self, "選擇新的 ZIP/RAR 資料夾")
        if not new_folder:
            logger.warning("用戶取消選擇資料夾")
            return False
            
        try:
            logger.info("用戶選擇的資料夾: %s", new_folder)
            self.scan_folder = new_folder
            
            # 掃描壓縮檔
            self.zip_files = self.scan_archives(new_folder)
            
            # 建立資料庫檔案路徑（在程式同一資料夾）
            scan_record_path = BASE_DIR / SCAN_RECORD_FILE
            logger.info("將建立資料庫檔案：%s", scan_record_path)
            
            # 寫入 JSON 檔案
            with open(scan_record_path, 'w', encoding='utf-8') as f:
                json.dump(self.zip_files, f, indent=4, ensure_ascii=False)
            logger.info("成功建立新資料庫檔案: %s", scan_record_path)
            
            # 詢問是否建立圖片快取
            self.prompt_cache_creation()
            
            return True
        except Exception as e:
            logger.exception("建立資料庫時發生錯誤")
            QMessageBox.critical(self, "錯誤", f"建立資料庫時發生錯誤：\n{str(e)}")
            return False

    def on_view_mode_changed(self, text):
        # 更新每行顯示數量
        self.items_per_row = int(text.replace('每行 ', '').replace(' 個', ''))
        self.display_images()    
    def on_sort_mode_changed(self, text):
        # 更新排序方式
        self.sort_mode = text
        # 保存設定到 config
        self.config["sort_mode"] = text
        save_config(self.config)
        # 重新整理顯示
        self.display_images()

    def filter_files(self):
        """依照順序篩選檔案：資產類型 > 角色 > 分類 > 標籤"""
        logger.info("開始篩選檔案")
        
        # 確保 current_zip_paths 已初始化
        if not hasattr(self, 'current_zip_paths'):
            self.current_zip_paths = []
        
        # 檢查必要的屬性是否存在
        required_attrs = ['asset_type_combo', 'character_combo', 'category_combo', 'tag_input']
        for attr in required_attrs:
            if not hasattr(self, attr):
                logger.error(f"缺少必要的屬性: {attr}")
                return

        self.show_loading_dialog()
        self.character_combo.setEnabled(False)

        try:
            selected_type = self.asset_type_combo.currentText()
            selected_character = self.character_combo.currentText()
            selected_category = self.category_combo.currentText()
            tag_query = self.tag_input.text().strip().lower()

            # 檢查並記錄選擇的值
            logger.debug(f"選擇的類型: {selected_type}")
            logger.debug(f"選擇的角色: {selected_character}")
            logger.debug(f"選擇的分類: {selected_category}")
            logger.debug(f"標籤搜尋: {tag_query}")

            self.current_selected_character = selected_character
            self.current_zip_paths.clear()

            # 確保 zip_files 是字典類型
            if not isinstance(self.zip_files, dict):
                logger.error(f"zip_files 應該是字典類型，實際是 {type(self.zip_files)}")
                return

            # 按順序篩選
            for zip_name, data in self.zip_files.items():
                try:
                    # 1. 資產類型篩選
                    if selected_type != "全部" and data.get("type", "") != selected_type:
                        continue

                    # 2. 角色篩選
                    if not data.get("characters") or selected_character not in data["characters"]:
                        continue

                    # 3. 分類篩選
                    if selected_category != "全部" and selected_category not in data.get("category", []):
                        continue

                    # 4. 標籤篩選
                    if tag_query:
                        file_tags = [tag.lower() for tag in data.get("tags", [])]
                        if tag_query not in file_tags:
                            continue

                    # 檢查並添加有效的快取圖片路徑
                    cached_image = data.get("cached_image")
                    if cached_image and cached_image != "null":
                        cached_image_path = os.path.join(IMAGE_CACHE_DIR, cached_image)
                        if os.path.isfile(cached_image_path):
                            self.current_zip_paths.append(cached_image_path)
                            logger.debug(f"找到符合的檔案：{zip_name}")
                        else:
                            logger.warning(f"快取圖片路徑無效或不存在：{cached_image_path}")

                except Exception as item_e:
                    logger.error(f"處理項目 {zip_name} 時發生錯誤: {str(item_e)}")
                    continue

            if not isinstance(self.current_zip_paths, list):
                logger.warning("current_zip_paths 不是 list，重置為空列表")
                self.current_zip_paths = []

            logger.info(f"找到 {len(self.current_zip_paths)} 個符合的檔案")
            self.display_images()

        except Exception as e:
            logger.exception("篩選檔案時發生錯誤")
        finally:
            self.character_combo.setEnabled(True)
            self.hide_loading_dialog()

    # 切換 UI 語言
    def change_language(self, language):
        if language in self.languages:
            self.current_language = language
            self.config["language"] = language  # 記住用戶選擇的語言
            save_config(self.config)  # 存儲設定
            self.apply_language(language)
            print(f"🌍 切換語言至: {language}")

    def apply_language(self, lang_code):
        T = self.languages.get(lang_code, {})
        self.setWindowTitle(T.get("window_title", "衣服查詢器"))
        self.info_label.setText(f"{T.get('author', '')}   {T.get('version', '')}")
        self.reload_button.setText(T.get("reload", "重新載入"))
        self.add_character_button.setText(T.get("add_character", "新增角色"))
        self.language_selector.setToolTip(T.get("select_language", "切換語言"))
        self.new_database_button.setText(T.get("new_database", "新資料庫"))
        # 其他 UI 文字如有需要可在此補充

    def check_existing_data(self):
        """程式啟動時，先詢問語言，再確認資料庫位置"""
        # **如果 scan_records.json 不存在，先詢問語言**
        if not os.path.exists(SCAN_RECORD_FILE):
            lang, ok = QInputDialog.getItem(self, "Language", "Select your language:", list(self.languages.keys()), 0, False)
            if ok and lang:
                self.current_language = lang
                self.change_language(lang)
            # **詢問使用者 ZIP 資料夾**
            self.update_scan()
    def load_scan_records(self):
        """載入並正規化掃描記錄"""
        scan_record_path = BASE_DIR / SCAN_RECORD_FILE
        
        if scan_record_path.exists():
            with open(scan_record_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
            # 正規化每一筆記錄
            normalized_records = {}
            for zip_name, data in raw_data.items():
                normalized_name = normalize_filename(zip_name)
                normalized_data = normalize_record(data)
                
                if normalized_name in normalized_records:
                    # 如果已存在同名檔案，合併資料
                    normalized_records[normalized_name] = merge_records(
                        {normalized_name: normalized_records[normalized_name]},
                        {normalized_name: normalized_data}
                    )[normalized_name]
                else:
                    normalized_records[normalized_name] = normalized_data
                    
            # 寫回正規化後的資料
            with open(scan_record_path, 'w', encoding='utf-8') as f:
                json.dump(normalized_records, f, ensure_ascii=False, indent=4)
                
            return normalized_records
        return {}

    def filter_files(self):
        """依照順序篩選檔案：資產類型 > 角色 > 分類 > 標籤"""
        logger.info("開始篩選檔案")
        
        # 確保 current_zip_paths 已初始化
        if not hasattr(self, 'current_zip_paths'):
            self.current_zip_paths = []
        
        # 檢查必要的屬性是否存在
        required_attrs = ['asset_type_combo', 'character_combo', 'category_combo', 'tag_input']
        for attr in required_attrs:
            if not hasattr(self, attr):
                logger.error(f"缺少必要的屬性: {attr}")
                return

        self.show_loading_dialog()
        self.character_combo.setEnabled(False)

        try:
            selected_type = self.asset_type_combo.currentText()
            selected_character = self.character_combo.currentText()
            selected_category = self.category_combo.currentText()
            tag_query = self.tag_input.text().strip().lower()

            # 檢查並記錄選擇的值
            logger.debug(f"選擇的類型: {selected_type}")
            logger.debug(f"選擇的角色: {selected_character}")
            logger.debug(f"選擇的分類: {selected_category}")
            logger.debug(f"標籤搜尋: {tag_query}")

            self.current_selected_character = selected_character
            self.current_zip_paths.clear()

            # 確保 zip_files 是字典類型
            if not isinstance(self.zip_files, dict):
                logger.error(f"zip_files 應該是字典類型，實際是 {type(self.zip_files)}")
                return

            # 按順序篩選
            for zip_name, data in self.zip_files.items():
                try:
                    # 1. 資產類型篩選
                    if selected_type != "全部" and data.get("type", "") != selected_type:
                        continue

                    # 2. 角色篩選
                    if not data.get("characters") or selected_character not in data["characters"]:
                        continue

                    # 3. 分類篩選
                    if selected_category != "全部" and selected_category not in data.get("category", []):
                        continue

                    # 4. 標籤篩選
                    if tag_query:
                        file_tags = [tag.lower() for tag in data.get("tags", [])]
                        if tag_query not in file_tags:
                            continue

                    # 檢查並添加有效的快取圖片路徑
                    cached_image = data.get("cached_image")
                    if cached_image and cached_image != "null":
                        cached_image_path = os.path.join(IMAGE_CACHE_DIR, cached_image)
                        if os.path.isfile(cached_image_path):
                            self.current_zip_paths.append(cached_image_path)
                            logger.debug(f"找到符合的檔案：{zip_name}")
                        else:
                            logger.warning(f"快取圖片路徑無效或不存在：{cached_image_path}")

                except Exception as item_e:
                    logger.error(f"處理項目 {zip_name} 時發生錯誤: {str(item_e)}")
                    continue

            if not isinstance(self.current_zip_paths, list):
                logger.warning("current_zip_paths 不是 list，重置為空列表")
                self.current_zip_paths = []

            logger.info(f"找到 {len(self.current_zip_paths)} 個符合的檔案")
            self.display_images()

        except Exception as e:
            logger.exception("篩選檔案時發生錯誤")
        finally:
            self.character_combo.setEnabled(True)
            self.hide_loading_dialog()


    def show_loading_dialog(self):
        """顯示加載中對話框，根據當前語言變更顯示文字"""
        title = self.languages[self.current_language]["loading_title"]
        message = self.languages[self.current_language]["loading_message"]

        self.loading_dialog = QMessageBox(self)
        self.loading_dialog.setWindowTitle(title)
        self.loading_dialog.setText(message)
        self.loading_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self.loading_dialog.show()

    def hide_loading_dialog(self):
        if self.loading_dialog:
            self.loading_dialog.accept()
            self.loading_dialog = None
    def find_external_image(self, zip_path):
        folder = os.path.dirname(zip_path)
        zip_name, _ = os.path.splitext(os.path.basename(zip_path))
        
        for ext in ['.jpg', '.png']:
            image_path = os.path.join(folder, zip_name + ext)
            if os.path.exists(image_path):
                return image_path
        return None
    def copy_to_cache(self, source_path, archive_name):
        cached_image_path = os.path.join(IMAGE_CACHE_DIR, archive_name + ".jpg")
        shutil.copy(source_path, cached_image_path)




    def display_images(self):
        """顯示圖片到網格佈局中"""
        logger.info("開始顯示圖片")
        try:
            # 清除現有的圖片
            for i in reversed(range(self.image_grid.count())):
                widget = self.image_grid.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            row, col = 0, 0
            items_per_row = 4  # 預設每行顯示 4 張圖片

            for cached_image_path in self.current_zip_paths:
                if not cached_image_path or not os.path.isfile(cached_image_path):
                    logger.warning(f"忽略無效的快取圖片路徑：{cached_image_path}")
                    continue

                try:
                    pixmap = QPixmap(cached_image_path)
                    if not pixmap.isNull():
                        # 創建容器和佈局
                        container = QWidget()
                        vbox = QVBoxLayout()
                        vbox.setSpacing(5)
                        
                        # 設置圖片
                        label = QLabel()
                        scaled_pixmap = pixmap.scaled(150, 150, 
                                                Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
                        label.setPixmap(scaled_pixmap)
                        label.setFixedSize(150, 150)
                        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        # 添加到佈局
                        vbox.addWidget(label)
                        container.setLayout(vbox)
                        
                        # 添加到網格
                        self.image_grid.addWidget(container, row, col)
                        
                        # 更新行列位置
                        col += 1
                        if col >= items_per_row:
                            col = 0
                            row += 1
                    else:
                        logger.warning(f"無法載入圖片：{cached_image_path}")
                except Exception as e:
                    logger.error(f"處理圖片時發生錯誤 ({cached_image_path}): {str(e)}")
                    continue

        logger.info("圖片顯示完成")
        self.image_container.update()
        self.image_container.repaint()
        
    except Exception as e:
        logger.exception("顯示圖片時發生錯誤")
        QMessageBox.warning(self, "錯誤", f"顯示圖片時發生錯誤：\n{str(e)}")

    def open_archive(self, archive_path):
        if not os.path.exists(archive_path):
            print(f"⚠️ 嘗試開啟 ZIP 檔案，但該檔案不存在: {archive_path}")
            return None  # 避免程式崩潰
        
        if archive_path.lower().endswith(".rar"):
            return rarfile.RarFile(archive_path, 'r')
        return zipfile.ZipFile(archive_path, 'r')

    def copy_to_clipboard(self, event, name):
        # name 已經傳入純 display_name，但保險起見再雙重切割
        base, _ = os.path.splitext(name)
        base, _ = os.path.splitext(base)
        pyperclip.copy(base)
        QMessageBox.information(self, "名稱複製", f"已複製: {base}")
    # 保存圖片
    def copy_to_cache(self, source_path, archive_name):
        """複製 ZIP 同目錄的圖片到快取資料夾"""
        cached_image_path = os.path.join(IMAGE_CACHE_DIR, archive_name + ".jpg")
        try:
            shutil.copy(source_path, cached_image_path)
            print(f"✅ 圖片已複製到快取: {cached_image_path}")
            return cached_image_path
        except Exception as e:
            print(f"❌ 無法複製圖片 {source_path} 到快取: {e}")
            return None

    def convert_to_pixmap(self, image_data):
        image = Image.open(BytesIO(image_data))
        image = image.convert("RGBA")
        data = BytesIO()
        image.save(data, format='PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(data.getvalue())
        return pixmap
    
    def save_image(self, image_data, archive_name):
        """保存圖片到快取目錄"""
        try:
            cached_image_path = os.path.join(IMAGE_CACHE_DIR, archive_name + ".jpg")
            with open(cached_image_path, "wb") as f:
                f.write(image_data)
            logger.info(f"已保存圖片到快取：{cached_image_path}")
            return True
        except Exception as e:
            logger.error(f"保存圖片失敗 ({archive_name}): {str(e)}")
            return False


    def update_scan(self):
        """用戶選擇 ZIP 資料夾並更新掃描資料"""
        try:
            if not hasattr(self, 'scan_folder') or not self.scan_folder:
                self.scan_folder = QFileDialog.getExistingDirectory(
                    self, 
                    self.languages[self.current_language]["select_folder"]
                )
            
            if self.scan_folder:
                # 掃描 ZIP 資料
                self.zip_files = self.scan_archives(self.scan_folder)
                
                # 保存到 JSON 檔案
                try:
                    with open(SCAN_RECORD_FILE, 'w', encoding='utf-8') as f:
                        json.dump(self.zip_files, f, indent=4, ensure_ascii=False)
                    logger.info("成功更新 scan_records.json")
                except Exception as save_e:
                    logger.error(f"保存掃描記錄失敗: {str(save_e)}")
                    return False

                # 建立圖片快取
                self.prompt_cache_creation()
                return True
                
            return False
        except Exception as e:
            logger.exception("更新掃描資料時發生錯誤")
            return False

    def prompt_cache_creation(self):
        """詢問用戶是否建立快取"""
        try:
            # 取得當前語言的文字，如果不存在則使用預設值
            texts = self.languages.get(self.current_language, DEFAULT_STRINGS)
            title = texts.get("cache_title", DEFAULT_STRINGS["cache_title"])
            message = texts.get("cache_message", DEFAULT_STRINGS["cache_message"])

            reply = QMessageBox.question(
                self, 
                title, 
                message, 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                logger.info("用戶選擇建立圖片快取")
                self.create_image_cache()
            else:
                logger.info("用戶取消建立圖片快取")
                
        except Exception as e:
            logger.exception("顯示快取建立對話框時發生錯誤")
            # 如果發生錯誤，直接建立快取，避免程式中斷
            logger.info("因發生錯誤，自動建立圖片快取")
            self.create_image_cache()

            
    def create_image_cache(self):
        """ 建立圖片快取，確保 scan_records.json 正確記錄 cached_image """
        if not hasattr(self, 'scan_folder') or not self.scan_folder:
            logger.error("無法建立快取，scan_folder 未設定！")
            return
        
        logger.info("開始建立圖片快取")
        updated_records = False

        try:
            # 確保快取目錄存在
            if not os.path.exists(IMAGE_CACHE_DIR):
                os.makedirs(IMAGE_CACHE_DIR)
                logger.info(f"建立快取目錄：{IMAGE_CACHE_DIR}")

            # 檢查並確保 zip_files 是字典類型
            if not isinstance(self.zip_files, dict):
                logger.error(f"zip_files 應該是字典類型，實際是 {type(self.zip_files)}")
                return

            for zip_name, data in self.zip_files.items():
                try:
                    archive_path = os.path.join(self.scan_folder, zip_name)
                    if not os.path.exists(archive_path):
                        logger.warning(f"找不到壓縮檔：{archive_path}")
                        continue

                    archive_name = os.path.basename(archive_path)
                    cached_image_name = f"{archive_name}.jpg"
                    cached_image_path = os.path.join(IMAGE_CACHE_DIR, cached_image_name)

                    # 如果快取已存在且有效，跳過
                    if data.get("cached_image") and os.path.isfile(os.path.join(IMAGE_CACHE_DIR, data["cached_image"])):
                        logger.debug(f"快取已存在，跳過：{cached_image_name}")
                        continue

                    # 檢查 ZIP 同目錄是否有圖片
                    external_image = self.find_external_image(archive_path)
                    if external_image:
                        logger.debug(f"找到外部圖片：{external_image}")
                        if self.copy_to_cache(external_image, archive_name):
                            data["cached_image"] = cached_image_name
                            updated_records = True
                            logger.info(f"已建立快取（外部圖片）：{cached_image_name}")
                        continue

                    # 提取 ZIP 內部圖片
                    try:
                        with self.open_archive(archive_path) as archive:
                            if not archive:
                                logger.error(f"無法開啟壓縮檔：{archive_path}")
                                continue

                            image_files = [f for f in archive.namelist() if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                            if image_files:
                                with archive.open(image_files[0]) as image_file:
                                    image_data = image_file.read()
                                    self.save_image(image_data, archive_name)
                                    data["cached_image"] = cached_image_name
                                    updated_records = True
                                    logger.info(f"已建立快取（壓縮檔內圖片）：{cached_image_name}")
                    except Exception as zip_e:
                        logger.error(f"處理壓縮檔時發生錯誤 ({archive_path}): {str(zip_e)}")
                        data["cached_image"] = None

                except Exception as item_e:
                    logger.error(f"處理項目 {zip_name} 時發生錯誤: {str(item_e)}")
                    continue

            # 更新 scan_records.json
            if updated_records:
                try:
                    scan_record_path = BASE_DIR / SCAN_RECORD_FILE
                    with open(scan_record_path, 'w', encoding='utf-8') as f:
                        json.dump(self.zip_files, f, ensure_ascii=False, indent=4)
                    logger.info("已更新快取記錄")
                except Exception as save_e:
                    logger.error(f"保存快取記錄時發生錯誤: {str(save_e)}")

        except Exception as e:
            logger.exception("建立圖片快取時發生錯誤")
            QMessageBox.warning(self, "錯誤", f"建立圖片快取時發生錯誤：\n{str(e)}")
    def scan_archives(self, folder):
        """掃描 ZIP 資料夾，建立完整的 scan_records.json"""
        logger.info(f"開始掃描資料夾：{folder}")
        
        # 檢查目錄是否存在
        if not os.path.isdir(folder):
            logger.error(f"指定的資料夾不存在：{folder}")
            return {}

        # 先讀取現有記錄，以保留已有的 tags 和 url
        try:
            existing_records = self.load_scan_records()
            if not isinstance(existing_records, dict):
                logger.warning("現有記錄格式不正確，重置為空字典")
                existing_records = {}
        except Exception as e:
            logger.error(f"讀取現有記錄時發生錯誤：{str(e)}")
            existing_records = {}

        archive_files = {}
        
        try:
            for file in os.listdir(folder):
                try:
                    file_path = os.path.join(folder, file)
                    if not os.path.isfile(file_path):
                        continue

                    if file.lower().endswith(('.zip', '.rar')):
                        logger.debug(f"處理壓縮檔：{file}")
                        
                        # 檢查是否已有記錄
                        if file in existing_records:
                            archive_files[file] = existing_records[file]
                            logger.debug(f"使用現有記錄：{file}")
                            continue

                        # 建立新記錄
                        try:
                            with self.open_archive(file_path) as archive:
                                if not archive:
                                    logger.error(f"無法開啟壓縮檔：{file}")
                                    continue

                                # 基本資訊
                                archive_files[file] = {
                                    "type": "Avatar",  # 預設類型
                                    "characters": [],   # 支援的角色
                                    "category": [],    # 分類
                                    "tags": [],        # 標籤
                                    "cached_image": None,
                                    "added_time": datetime.now().isoformat()
                                }
                                logger.info(f"成功建立新記錄：{file}")
                        except Exception as zip_e:
                            logger.error(f"處理壓縮檔時發生錯誤 ({file}): {str(zip_e)}")
                            continue

                except Exception as file_e:
                    logger.error(f"處理檔案時發生錯誤 ({file}): {str(file_e)}")
                    continue

        logger.info(f"掃描完成，共處理 {len(archive_files)} 個檔案")
        return archive_files


    def add_new_character(self):
        text, ok = QInputDialog.getText(self, "新增角色", "請輸入角色名稱:")
        if ok and text:
            if text not in self.avatars:
                self.avatars.append(text)
                save_avatars(self.avatars)
                self.character_combo.addItem(text)

    def on_search(self):
        """
        搜尋欄按下 Enter 時觸發，根據輸入關鍵字過濾角色列表。
        """
        query = self.search_input.text().strip().lower()
        if not query:
            filtered = self.avatars
        else:
            filtered = [name for name in self.avatars if query in name.lower()]
        self.character_combo.clear()
        if filtered:
            self.character_combo.addItems(filtered)
        else:
            self.character_combo.addItem("找不到相符的角色")

    def on_type_changed(self, new_type):
        """當資產類型變更時觸發"""
        self.filter_files()  # 重新根據所選類型過濾顯示資產
        print(f"資產類型已更改為: {new_type}")

    def on_category_changed(self, new_category):
        """當分類變更時觸發"""
        self.filter_files()  # 重新根據所選分類過濾顯示資產
        print(f"資產分類已更改為: {new_category}")

    def on_tag_search(self):
        """當標籤輸入框按下 Enter 時觸發"""
        self.filter_files()  # 重新過濾檔案
        tag = self.tag_input.text().strip()
        print(f"🏷️ 使用標籤過濾: {tag}")

    def on_avatar_support_changed(self, state):
        """當 Avatar 支援勾選框狀態改變時觸發"""
        self.filter_files()  # 重新過濾檔案
        is_checked = bool(state)
        print(f"👥 {'只顯示多角色支援' if is_checked else '顯示所有'} 資產")

    def reload_data(self):
        """重新載入資料和快取"""
        print("🔄 開始重新載入資料...")
        
        # 重新載入設定檔
        self.config = load_config()
        self.languages = load_languages()
        self.avatars = load_avatars()
        
        # 重新掃描並更新資料
        if hasattr(self, 'scan_folder') and self.scan_folder:
            self.zip_files = self.scan_archives(self.scan_folder)
            with open(SCAN_RECORD_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.zip_files, f, indent=4, ensure_ascii=False)
                
            # 更新角色列表
            self.character_combo.clear()
            self.character_combo.addItems(self.avatars)
            
            # 重新載入圖片
            if self.character_combo.currentItem():
                self.filter_files()
                
            print("✅ 資料重新載入完成！")
        else:
            print("⚠️ 尚未設定資料夾，請先選擇 ZIP/RAR 資料夾")
            self.update_scan()        
    def display_file_details(self, normalized_name):
        """顯示檔案詳細資料"""
        if not normalized_name:
            self.clear_details()
            return

        try:
            # 確保檔名有 .zip 後綴
            if not normalized_name.endswith('.zip'):
                normalized_name += '.zip'
            print(f"🔍 正在查詢檔案詳細資料: {normalized_name}")
            print(f"📑 可用的檔案列表: {list(self.zip_files.keys())}")
            
            # 從記錄中獲取完整資料
            file_data = self.zip_files.get(normalized_name)
            if not file_data:
                print(f"❌ 找不到檔案資料: {normalized_name}")
                self.clear_details()
                return
            
            # 設置預覽圖
            cached_image = file_data.get("cached_image")
            if cached_image and cached_image != "null":
                image_path = os.path.join(IMAGE_CACHE_DIR, cached_image)
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.details_image.setPixmap(scaled_pixmap)
                    print(f"✅ 已載入詳細資料圖片: {image_path}")
            
            # 設置名稱（移除副檔名）
            base_name = os.path.splitext(normalized_name)[0]
            self.details_name.setText(base_name)
            
            # 設置網址（使用空字串替代 "null"）
            url = file_data.get("url", "")
            self.details_url.setText(f"網址: {url if url and url != 'null' else '無'}")
            
            # 設置標籤
            tags = file_data.get("tags", [])
            tag_text = ', '.join(tags) if tags and tags != ["null"] else '無'
            self.details_tags.setText(f"標籤: {tag_text}")
            
        except Exception as e:
            print(f"❌ 顯示詳細資料時發生錯誤: {e}")
            self.clear_details()    
    def clear_details(self):
        """清空詳細資料面板"""
        self.details_image.clear()
        self.details_name.setText("未選擇檔案")
        self.details_url.setText("網址: 無")
        self.details_tags.setText("標籤: 無")
        print("🧹 清空詳細資料面板")

    def copy_name_to_clipboard(self):
        """複製名稱到剪貼簿"""
        name = self.details_name.text()
        if name and name != "未選擇檔案":
            pyperclip.copy(name)
            QMessageBox.information(self, "複製成功", f"已複製名稱: {name}")    
    def edit_record(self, file_name):
        """編輯檔案記錄"""
        if not self.details_name.text() or self.details_name.text() == "未選擇檔案":
            return

        # 取得當前檔案資料
        file_data = self.zip_files.get(file_name, {})
        
        # 創建編輯對話框
        dialog = QDialog(self)
        dialog.setWindowTitle("編輯資料")
        dialog.setFixedWidth(400)
        layout = QVBoxLayout()
        
        # 網址輸入
        url_label = QLabel("網址:")
        url_input = QLineEdit(file_data.get("url", ""))
        layout.addWidget(url_label)
        layout.addWidget(url_input)
        
        # 已有標籤顯示
        current_tags = file_data.get("tags", [])
        tags_label = QLabel("現有標籤:")
        tags_display = QLabel(", ".join(current_tags) if current_tags else "無")
        layout.addWidget(tags_label)
        layout.addWidget(tags_display)
        
        # 新增標籤輸入
        new_tags_label = QLabel("新增標籤 (用逗號分隔):")
        new_tags_input = QLineEdit()
        new_tags_input.setPlaceholderText("例如: 可愛, 粉色, 洛麗塔")
        layout.addWidget(new_tags_label)
        layout.addWidget(new_tags_input)
        
        # 按鈕
        button_layout = QHBoxLayout()
        save_button = QPushButton("儲存")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        def on_save():
            # 取得並處理新標籤
            new_tags = [tag.strip() for tag in new_tags_input.text().split(",") if tag.strip()]
            
            # 更新檔案資料
            if "tags" not in file_data:
                file_data["tags"] = []
            
            # 合併新舊標籤並去除重複
            file_data["tags"].extend(new_tags)
            file_data["tags"] = list(dict.fromkeys(file_data["tags"]))
            
            # 更新網址
            file_data["url"] = url_input.text().strip()
            
            # 保存回檔案記錄
            self.zip_files[file_name] = file_data
            
            # 更新資料庫文件
            try:
                with open(os.path.join(self.scan_folder, SCAN_RECORD_FILE), 'w', encoding='utf-8') as f:
                    json.dump(self.zip_files, f, indent=4, ensure_ascii=False)
                logger.info("成功更新資料庫")
            except Exception as e:
                logger.exception("更新資料庫時發生錯誤")
                self._show_error_dialog("錯誤", f"更新資料庫時發生錯誤：\n{str(e)}")
            
            # 更新顯示
            self.display_file_details(file_name)
            dialog.accept()
        
        save_button.clicked.connect(on_save)
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec()
    def debug_file_info(self, file_name):
        """印出檔案相關的除錯資訊"""
        print("\n=== 檔案資訊除錯 ===")
        print(f"傳入的檔名: {file_name}")
        if file_name in self.zip_files:
            print(f"✅ 直接匹配成功")
        else:
            print(f"❌ 直接匹配失敗")
            
        # 嘗試加上 .zip 後綴
        with_zip = file_name if file_name.endswith('.zip') else file_name + '.zip'
        if with_zip in self.zip_files:
            print(f"✅ 加上 .zip 後匹配成功: {with_zip}")
        else:
            print(f"❌ 加上 .zip 後仍然失敗: {with_zip}")
        
        print("\n可用的檔案列表:")
        for key in self.zip_files.keys():
            print(f"- {key}")
        print("==================\n")

def normalize_filename(filename):
    """標準化檔案名稱，移除重複的 .zip 副檔名"""
    if filename.endswith('.zip.zip'):
        return filename[:-4]  # 移除重複的 .zip
    return filename

def normalize_record(data):
    """統一補齊缺失欄位，並確保型別正確"""
    # 預設欄位與型別
    template = {
        "characters": [],
        "cached_image": None,
        "tags": [],
        "url": "null"
    }
    
    normalized = {}
    for key, default in template.items():
        val = data.get(key, default)
        
        # 型別修正
        if key in ("characters", "tags"):
            if not isinstance(val, list):
                val = [val] if val is not None else []
        elif key in ("cached_image", "url"):
            if val is not None and not isinstance(val, str):
                val = str(val)
            elif val is None:
                val = "null"
                
        normalized[key] = val
    return normalized

def merge_records(old, new):
    """合併兩個記錄的資料，去重並保留有效值"""
    merged = {}
    for zip_name, new_data in new.items():
        normalized_name = normalize_filename(zip_name)  # 使用之前定義的 normalize_filename
        if normalized_name not in merged:
            merged[normalized_name] = normalize_record(new_data)
        else:
            base = merged[normalized_name]
            # 合併 characters 與 tags (去重)
            base["characters"] = list(set(base["characters"] + new_data.get("characters", [])))
            base["tags"] = list(set(base.get("tags", []) + new_data.get("tags", [])))
            # cached_image / url：以有效值為優先
            if new_data.get("cached_image"):
                base["cached_image"] = new_data["cached_image"]
            if new_data.get("url") and new_data["url"] != "null":
                base["url"] = new_data["url"]
            merged[normalized_name] = base
    return merged

def ensure_fields(record):
    """確保記錄包含所有必要的欄位"""
    if "characters" not in record:
        record["characters"] = []
    if "cached_image" not in record:
        record["cached_image"] = None
    if "tags" not in record:
        record["tags"] = ["null"]
    if "url" not in record:
        record["url"] = "null"
    return record

def merge_records(old_record, new_record):
    """合併兩筆記錄的資料"""
    merged = {}
    # 確保兩筆記錄都有完整欄位
    old_record = ensure_fields(old_record)
    new_record = ensure_fields(new_record)
    
    # 合併欄位
    merged["characters"] = list(set(old_record["characters"] + new_record["characters"]))
    merged["cached_image"] = new_record["cached_image"] or old_record["cached_image"]
    merged["tags"] = list(set(old_record["tags"] + new_record["tags"])) if old_record["tags"][0] != "null" and new_record["tags"][0] != "null" else (
        new_record["tags"] if new_record["tags"][0] != "null" else old_record["tags"]
    )
    merged["url"] = new_record["url"] if new_record["url"] != "null" else old_record["url"]
    
    return merged

def clean_scan_records():
    """清理並標準化 scan_records.json 的資料"""
    try:
        with open("scan_records.json", "r", encoding="utf-8") as f:
            records = json.load(f)
        
        # 建立新的乾淨記錄
        cleaned_records = {}
        
        # 處理每個記錄
        for filename, data in records.items():
            normalized_name = normalize_filename(filename)
            data = ensure_fields(data)
            
            if normalized_name in cleaned_records:
                # 如果檔案已存在，合併資料
                cleaned_records[normalized_name] = merge_records(cleaned_records[normalized_name], data)
            else:
                # 如果是新檔案，直接添加
                cleaned_records[normalized_name] = data
        
        # 寫回文件
        with open("scan_records.json", "w", encoding="utf-8") as f:
            json.dump(cleaned_records, f, ensure_ascii=False, indent=4)
            
        return True
    except Exception as e:
        print(f"清理記錄時發生錯誤: {str(e)}")
        return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ZipQueryApp()
    ex.show()
    sys.exit(app.exec())