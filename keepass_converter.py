import os
import sys
import csv
import requests
import tempfile
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFileDialog,
    QMessageBox, QVBoxLayout, QLineEdit
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QIcon, QDesktopServices
from pykeepass import create_database

# // 欢迎使用打包keepass转置工具 * 小旭

GOOGLE_SHEET_URL = "https://www.youtube.com/playlist?list=PLx6mhMXQVPdXc2jL0yluuADXt2BwMDESR"    # ← 记得换成真实链接
TUTORIAL_URL = "https://docs.google.com/spreadsheets/d/1j6PZ8dkdtHBGLhhYDKggLp9PHIC9x98ENub2v5KbiWE/edit?gid=13182535#gid=13182535"

# 下载保护参数
DOWNLOAD_TIMEOUT = 60          # 秒
MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024   # 20 MB

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DragDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV 密钥工坊")
        self.setFixedSize(330, 380)
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: #f8f9fa;")

        self.font_large = QFont("Segoe UI", 48, QFont.Bold)
        self.font_button = QFont("Segoe UI", 12, QFont.Bold)

        # 教程按钮
        self.template_button = QPushButton("教程", self)
        self.template_button.setFixedSize(40, 30)
        self.template_button.move(self.width() - 45, 10)
        self.template_button.setStyleSheet("""
            QPushButton {
                background-color: #0e7437;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a54d1;
            }
        """)
        self.template_button.clicked.connect(self.open_template)

        # 模板按钮
        self.tutorial_button = QPushButton("模板", self)
        self.tutorial_button.setFixedSize(40, 30)
        self.tutorial_button.move(self.width() - 45, 45)
        self.tutorial_button.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a54d1;
            }
        """)
        self.tutorial_button.clicked.connect(self.open_tutorial)

        self.drag_label = QLabel("+", self)
        self.drag_label.setFont(self.font_large)
        self.drag_label.setAlignment(Qt.AlignCenter)
        self.drag_label.setFixedSize(220, 220)
        self.drag_label.setStyleSheet("""
            QLabel {
                border: 3px dashed purple;
                color: #4a0080;
                background-color: white;
                border-radius: 10px;
            }
            QLabel:hover {
                background-color: #f0f0ff;
            }
        """)
        self.drag_label.mousePressEvent = self.open_file_dialog

        self.file_path_display = QLineEdit(self)
        self.file_path_display.setPlaceholderText("拖入或选择CSV文件或粘贴谷歌生成下载链接")
        self.file_path_display.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #ccc;
                padding: 6px;
                color: #333;
            }
        """)

        self.generate_button = QPushButton("生成 KeePass 文件", self)
        self.generate_button.setFont(self.font_button)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        self.generate_button.clicked.connect(self.generate_kdbx)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.drag_label, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.file_path_display)
        layout.addSpacing(10)
        layout.addWidget(self.generate_button)
        layout.setContentsMargins(30, 30, 30, 30)
        self.setLayout(layout)

    def open_template(self):
        QDesktopServices.openUrl(QUrl(GOOGLE_SHEET_URL))

    def open_tutorial(self):
        QDesktopServices.openUrl(QUrl(TUTORIAL_URL))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.csv'):
                self.file_path_display.setText(file_path)
            else:
                self.show_message("错误", "请拖入有效的 CSV 文件。")

    def open_file_dialog(self, event=None):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 CSV 文件", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.file_path_display.setText(file_path)

    def show_message(self, title, text, file_path=None):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)

        if file_path:
            open_button = msg.addButton("打开文件", QMessageBox.AcceptRole)
            open_button.setStyleSheet("""
                QPushButton {
                    background-color: #0e7437;
                    color: white;
                    padding: 8px;
                    min-width: 80px;
                    font-size: 10pt;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #5a54d1;
                }
            """)
        msg.addButton(QMessageBox.Ok)

        msg.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                padding: 8px;
                min-width: 80px;
                font-size: 10pt;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)
        msg.exec()

        if file_path and msg.clickedButton().text() == "打开文件":
            # 跨平台打开文件
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                os.system(f'open "{file_path}"')
            else:
                os.system(f'xdg-open "{file_path}"')

    def _download_csv(self, url: str) -> str:
        """安全下载 CSV，返回临时文件路径。失败抛异常。"""
        try:
            with requests.get(
                url,
                timeout=DOWNLOAD_TIMEOUT,
                stream=True,               # 流式读取，避免一次载入内存
                allow_redirects=True
            ) as resp:
                resp.raise_for_status()

                # 优先检查 Content-Length
                content_length = resp.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_DOWNLOAD_SIZE:
                    raise ValueError(
                        f"文件过大（{int(content_length)/1024/1024:.1f} MB），"
                        f"超过限制 {MAX_DOWNLOAD_SIZE/1024/1024:.0f} MB"
                    )

                # 流式写入临时文件并实时检查大小
                tmp = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".csv", mode="wb"
                )
                downloaded = 0
                try:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        downloaded += len(chunk)
                        if downloaded > MAX_DOWNLOAD_SIZE:
                            raise ValueError(
                                f"下载内容超过限制 {MAX_DOWNLOAD_SIZE/1024/1024:.0f} MB"
                            )
                        tmp.write(chunk)
                    tmp.close()
                    return tmp.name
                except Exception:
                    tmp.close()
                    if os.path.exists(tmp.name):
                        os.unlink(tmp.name)
                    raise
        except requests.Timeout:
            raise TimeoutError(f"下载超时（>{DOWNLOAD_TIMEOUT} 秒）")
        except requests.RequestException as e:
            raise RuntimeError(f"网络错误：{e}")

    def generate_kdbx(self):
        path = self.file_path_display.text().strip()
        if not path:
            self.show_message("错误", "请输入或选择 CSV 文件路径或下载链接。")
            return

        is_temp = False          # 标记是否是程序自己下载的临时文件
        try:
            if path.lower().startswith(("http://", "https://")):
                path = self._download_csv(path)
                is_temp = True

            if not os.path.exists(path):
                self.show_message("错误", "找不到文件。")
                return

            file_path, password = self.create_kdbx(path)
            self.show_message(
                "成功",
                f"{os.path.basename(file_path)}\n密码：{password}",
                file_path
            )
        except Exception as e:
            self.show_message("错误", str(e))
        finally:
            # 只清理我们自己下载的临时 CSV，绝不碰用户本地文件
            if is_temp and path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def create_kdbx(self, csv_file_path):
        db_password = "111"
        filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.kdbx'
        output_dir = os.path.dirname(
            os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)
        )
        kdbx_file = os.path.join(output_dir, filename)

        kp = create_database(kdbx_file, password=db_password)
        parent_group = kp.add_group(kp.root_group, datetime.now().strftime('%Y-%m-%d'))
        group_email = kp.add_group(parent_group, 'FB邮箱')
        group_account = kp.add_group(parent_group, 'FB账号')

        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            for row in reader:
                if len(row) < 9:
                    continue
                identifier = row[0]

                email_entry = kp.add_entry(
                    group_email, f"邮箱-{identifier}", row[1], row[2], ""
                )
                if row[3]:
                    email_entry.otp = (
                        f'otpauth://totp/{row[1]}?secret={row[3]}&issuer=邮箱-{identifier}'
                    )
                email_entry.notes = row[4]

                account_entry = kp.add_entry(
                    group_account, f"账号-{identifier}", row[5], row[6], ""
                )
                if row[7]:
                    account_entry.otp = (
                        f'otpauth://totp/{row[5]}?secret={row[7]}&issuer=账号-{identifier}'
                    )
                account_entry.notes = row[8]

        kp.save()
        return kdbx_file, db_password

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon_path = resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = DragDropWidget()
    window.show()
    sys.exit(app.exec())