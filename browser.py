import os
import hashlib
import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QPushButton, QStyle, QListWidget, QSplitter, QFileDialog, QMessageBox, QDialog, QLabel, QTextEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
# 移除webview导入
from PyQt6.QtCore import QUrl, QTimer, Qt, QPoint
from PyQt6.QtGui import QIcon, QShortcut, QScreen, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口为无边框样式，确保完全无边框
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # 设置窗口背景透明以避免任何边框
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 确保窗口激活时无额外边框
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # 检查密码文件是否存在
        self.password_file = 'password.txt'
        self.is_authenticated = False
        
        # 初始化错误日志文件
        self.error_log_file = 'error_log.txt'
        try:
            open(self.error_log_file, 'a').close()
        except Exception as e:
            print(f"无法创建错误日志文件: {e}")
        
        # 如果密码文件存在，显示密码输入对话框
        if os.path.exists(self.password_file):
            self.show_password_dialog()
        else:
            # 首次运行，设置密码
            self.show_set_password_dialog()
            
        # 如果用户未通过验证，不继续初始化浏览器
        if not self.is_authenticated:
            return
            
        # 检查是否有清除历史记录的通知需要显示
        if os.path.exists('history_cleared.txt'):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "您的浏览记录已被清除！", QMessageBox.StandardButton.Ok)
            os.remove('history_cleared.txt')
            
        self.setWindowTitle("GFY浏览器")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1280, 720)
        
        # 创建主容器
        self.main_container = QWidget()
        self.main_container.setObjectName("mainContainer")
        self.main_container.setStyleSheet("#mainContainer { background-color: #f5f5f5; border: none; }")
        self.setCentralWidget(self.main_container)
        
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow { background-color: transparent; }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget {
                border: 1px solid #ddd;
                background-color: white;
            }
            QSplitter::handle {
                background-color: #ddd;
                width: 2px;
            }
        """)
        
        # 创建导航栏
        nav_bar = QWidget()
        nav_bar.setFixedHeight(40)
        nav_bar.setStyleSheet("background-color: #4a90e2;")
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(8, 3, 8, 3)
        nav_layout.setSpacing(8)
        
        self.back_btn = QPushButton("<")
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.forward_btn = QPushButton(">" )
        self.url_bar = QLineEdit()
        self.go_btn = QPushButton("Go")
        self.bookmark_btn = QPushButton("☆")
        self.history_btn = QPushButton("历史")
        self.clear_btn = QPushButton("清除历史记录")
        self.toggle_sidebar_btn = QPushButton("收藏夹")
        self.settings_btn = QPushButton("设置")
        self.screenshot_btn = QPushButton("截图")
        
        # 添加窗口控制按钮
        self.minimize_btn = QPushButton("_")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("X")
        
        # 设置窗口控制按钮样式
        window_controls_style = """
            min-width: 30px;
            max-width: 30px;
            font-weight: bold;
        """
        self.minimize_btn.setStyleSheet(window_controls_style)
        self.maximize_btn.setStyleSheet(window_controls_style)
        self.close_btn.setStyleSheet(window_controls_style + "background-color: #e74c3c;")
        
        # 连接窗口控制按钮信号
        self.minimize_btn.clicked.connect(self.showMinimized)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.close)
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.refresh_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.url_bar)
        nav_layout.addWidget(self.go_btn)
        nav_layout.addWidget(self.bookmark_btn)
        nav_layout.addWidget(self.history_btn)
        nav_layout.addWidget(self.clear_btn)
        nav_layout.addWidget(self.toggle_sidebar_btn)
        nav_layout.addWidget(self.settings_btn)
        nav_layout.addWidget(self.screenshot_btn)
        
        # 添加窗口控制按钮到布局末尾
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.minimize_btn)
        nav_layout.addWidget(self.maximize_btn)
        nav_layout.addWidget(self.close_btn)
        
        nav_bar.setLayout(nav_layout)
        
        # 创建浏览器视图
        self.browser = WebEngineView()
        self.history_list = []
        
        # 读取起始页配置
        self.homepage_url = "https://www.baidu.com"
        try:
            with open('homepage.txt', 'r') as f:
                url = f.read().strip()
                if url:
                    self.homepage_url = url
        except FileNotFoundError:
            pass
            
        self.browser.setUrl(QUrl(self.homepage_url))
        
        # 创建收藏夹侧边栏
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.itemClicked.connect(self.navigate_to_bookmark)
        
        # 创建历史记录侧边栏
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.navigate_to_history)
        
        # 使用QSplitter创建可调整的布局
        splitter = QSplitter()
        splitter.addWidget(self.bookmarks_list)
        splitter.addWidget(self.history_list)
        splitter.addWidget(self.browser)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 移除所有边距
        layout.addWidget(nav_bar)
        layout.addWidget(splitter)
        
        self.main_container.setLayout(layout)
        
        # 初始隐藏侧边栏
        self.bookmarks_list.hide()
        self.history_list.hide()
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        self.history_btn.clicked.connect(self.toggle_history)
        
        # 确保历史记录文件存在 (延迟到delayed_initialization中处理)
            
        # 连接信号
        self.go_btn.clicked.connect(self.navigate_to_url)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.refresh_btn.clicked.connect(self.browser.reload)
        self.bookmark_btn.clicked.connect(self.add_bookmark)
        self.clear_btn.clicked.connect(self.clear_history_and_cookies)
        self.back_btn.clicked.connect(self.browser.back)
        self.back_btn.setEnabled(self.browser.history().canGoBack())
        self.forward_btn.clicked.connect(self.browser.forward)
        self.browser.page().urlChanged.connect(self.update_url)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        
        # 延迟加载部分资源
        QTimer.singleShot(100, self.delayed_initialization)
        
        # 窗口拖动变量初始化
        self.dragging = False
        self.drag_position = QPoint()
    
    def toggle_maximize(self):
        """切换窗口最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        # 更新最大化按钮状态
        self.update_maximize_button()
    
    def update_maximize_button(self):
        """根据窗口状态更新最大化按钮的文本"""
        if self.isMaximized():
            self.maximize_btn.setText("◱")
        else:
            self.maximize_btn.setText("□")
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于窗口拖动"""
        # 只有在导航栏区域按下鼠标才能拖动窗口
        nav_bar = self.centralWidget().layout().itemAt(0).widget()
        if event.button() == Qt.MouseButton.LeftButton and nav_bar.underMouse():
            # 如果窗口是最大化状态，先恢复为普通大小
            if self.isMaximized():
                self.showNormal()
                # 确保最大化按钮图标正确更新
                self.update_maximize_button()
            
            # 记录鼠标在导航栏上的点击位置（相对于窗口左上角）
            self.dragging = True
            self.drag_position = event.position().toPoint()  # 使用相对位置
            event.accept()
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于窗口拖动"""
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            # 确保导航栏被点击部分始终跟随鼠标
            # 使用全局位置减去记录的相对位置来计算新的窗口位置
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，结束窗口拖动"""
        self.dragging = False
        event.accept()
    
    def delayed_initialization(self):
        """延迟初始化非关键组件"""
        # 加载历史记录和书签
        self.load_history()
        self.load_bookmarks()
        
        # 设置1秒后自动执行Go功能的定时器
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.navigate_to_url)
        self.timer.start(1000)
        
    def update_url(self, q):
        self.url_bar.setText(q.toString())
        self.back_btn.setEnabled(self.browser.history().canGoBack())
        
    def add_bookmark(self):
        url = self.url_bar.text()
        if url:
            if not url.startswith('http'):
                url = 'http://' + url
            
            # 检查网址是否已存在
            try:
                with open('bookmarks.txt', 'r') as f:
                    bookmarks = [line.strip() for line in f]
                    if url in bookmarks:
                        from PyQt6.QtWidgets import QMessageBox
                        reply = QMessageBox.question(self, '取消收藏', 
                            '该网址已在收藏夹中，是否取消收藏？',
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        if reply == QMessageBox.StandardButton.Yes:
                            # 从文件中删除该网址
                            with open('bookmarks.txt', 'w') as f:
                                for bookmark in bookmarks:
                                    if bookmark != url:
                                        f.write(bookmark + '\n')
                            self.bookmark_btn.setText("☆")
                            self.load_bookmarks()
                        return
            except FileNotFoundError:
                pass
                
            with open('bookmarks.txt', 'a') as f:
                f.write(url + '\n')
            self.bookmark_btn.setText("★")
            self.load_bookmarks()
                
    def navigate_to_url(self):
        url = self.url_bar.text()
        
        # 检查特殊输入'gfy'
        if url.lower() == 'gfy':
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "彩蛋", "恭喜你发现了GFY浏览器的隐藏彩蛋！\n\n开发者: GFY", QMessageBox.StandardButton.Ok)
            return
            
        if not url.startswith('http'):
            url = 'http://' + url
        self.browser.setUrl(QUrl(url))
        
        # 获取网页标题
        def get_title(title):
            try:
                # 记录历史（包含标题和时间）
                from datetime import datetime
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open('history.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{url}||{title}||{current_time}\n")
                self.load_history()
            except Exception as e:
                print(f"保存历史记录时出错: {e}")
            finally:
                # 确保信号只连接一次
                self.browser.page().titleChanged.disconnect(get_title)
         
        self.browser.page().titleChanged.connect(get_title)
        
        # 检查当前网址是否已收藏
        try:
            with open('bookmarks.txt', 'r') as f:
                bookmarks = [line.strip() for line in f]
                if url in bookmarks:
                    self.bookmark_btn.setText("★")
                else:
                    self.bookmark_btn.setText("☆")
        except FileNotFoundError:
            self.bookmark_btn.setText("☆")
        
    def load_bookmarks(self):
        self.bookmarks_list.clear()
        try:
            with open('bookmarks.txt', 'r') as f:
                for line in f:
                    url = line.strip()
                    if url:
                        self.bookmarks_list.addItem(url)
        except FileNotFoundError:
            pass
            
    def load_history(self):
        self.history_list.clear()
        try:
            with open('history.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('||')
                    if len(parts) == 3:
                        url, title, time = parts
                        self.history_list.addItem(f"{time} - {title} - {url}")
                    elif len(parts) == 2:
                        url, title = parts
                        self.history_list.addItem(f"{title} - {url}")
                    elif len(parts) == 1 and parts[0]:  # 兼容旧格式
                        self.history_list.addItem(parts[0])
        except FileNotFoundError:
            pass
        except UnicodeDecodeError:
            try:
                with open('history.txt', 'r', encoding='gbk') as f:
                    for line in f:
                        parts = line.strip().split('||')
                        if len(parts) == 3:
                            url, title, time = parts
                            self.history_list.addItem(f"{time} - {title} - {url}")
                        elif len(parts) == 2:
                            url, title = parts
                            self.history_list.addItem(f"{title} - {url}")
                        elif len(parts) == 1 and parts[0]:
                            self.history_list.addItem(parts[0])
            except Exception as e:
                print(f"加载历史记录时出错: {e}")
            
    def navigate_to_history(self, item):
        text = item.text()
        # 从历史记录文本中提取URL
        if ' - ' in text and 'http' in text:
            # 格式为"时间 - 标题 - URL"或"标题 - URL"
            url = text.split(' - ')[-1]
        else:
            url = text
        self.url_bar.setText(url)
        self.browser.setUrl(QUrl(url))
            
    def navigate_to_bookmark(self, item):
        url = item.text()
        self.url_bar.setText(url)
        self.browser.setUrl(QUrl(url))
        
        # 获取网页标题并记录历史
        def get_title(title):
            try:
                # 记录历史（包含标题和时间）
                from datetime import datetime
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open('history.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{url}||{title}||{current_time}\n")
                self.load_history()
            except Exception as e:
                print(f"保存历史记录时出错: {e}")
            finally:
                # 确保信号只连接一次
                self.browser.page().titleChanged.disconnect(get_title)
         
        self.browser.page().titleChanged.connect(get_title)
        
        # 检查当前网址是否已收藏
        try:
            with open('bookmarks.txt', 'r') as f:
                bookmarks = [line.strip() for line in f]
                if url in bookmarks:
                    self.bookmark_btn.setText("★")
                else:
                    self.bookmark_btn.setText("☆")
        except FileNotFoundError:
            self.bookmark_btn.setText("☆")
            
    def clear_history_and_cookies(self):
        # 清除历史记录文件
        try:
            open('history.txt', 'w').close()
            if hasattr(self, 'history_list'):
                self.history_list.clear()
            # 创建清除记录标记文件
            with open('history_cleared.txt', 'w') as f:
                f.write('1')
            # 创建密码错误标记文件
            with open('password_error.txt', 'w') as f:
                f.write('1')
        except Exception as e:
            print(f"清除历史记录时出错: {e}")
            
        # 清除浏览器cookie（仅在密码错误时）
        if os.path.exists('password_error.txt'):
            try:
                if hasattr(self, 'browser') and self.browser:
                    self.browser.page().profile().cookieStore().deleteAllCookies()
            except Exception as e:
                print(f"清除cookie时出错: {e}")
        
    def toggle_sidebar(self):
        if self.bookmarks_list.isVisible():
            self.bookmarks_list.hide()
        else:
            self.bookmarks_list.show()
            self.history_list.hide()
            
    def toggle_history(self):
        if self.history_list.isVisible():
            self.history_list.hide()
        else:
            self.history_list.show()
            self.bookmarks_list.hide()
            
    def show_password_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("输入密码")
        dialog.resize(300, 150)
        
        layout = QVBoxLayout()
        
        password_label = QLabel("请输入密码:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        submit_btn = QPushButton("确定")
        submit_btn.clicked.connect(lambda: self.verify_password(dialog))
        
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(submit_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
        
    def show_set_password_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("设置密码")
        dialog.resize(300, 200)
        
        layout = QVBoxLayout()
        
        password_label = QLabel("设置新密码:")
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        confirm_label = QLabel("确认密码:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        submit_btn = QPushButton("确定")
        submit_btn.clicked.connect(lambda: self.set_password(dialog))
        
        layout.addWidget(password_label)
        layout.addWidget(self.new_password_input)
        layout.addWidget(confirm_label)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(submit_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
        
    def log_error(self, error_msg):
        """记录错误到日志文件"""
        from datetime import datetime
        try:
            with open(self.error_log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {error_msg}\n")
        except Exception as e:
            print(f"记录错误日志失败: {e}")
            
    def verify_password(self, dialog):
        try:
            # 初始化错误计数器
            if not hasattr(self, 'password_attempts'):
                self.password_attempts = 0
                
            with open(self.password_file, 'r') as f:
                stored_hash = f.read().strip()
                
            input_hash = hashlib.sha256(self.password_input.text().encode()).hexdigest()
            
            if input_hash == stored_hash:
                self.is_authenticated = True
                self.password_attempts = 0  # 重置计数器
                dialog.close()
                # 继续初始化浏览器
                self.initialize_browser()
                return  # 验证成功后直接返回
                
            # 密码错误处理
            self.password_attempts += 1
            
            # 仅在第三次错误时清除历史记录
            if self.password_attempts == 3:
                self.clear_history_and_cookies()
                # 创建密码错误标记文件
                with open('password_error.txt', 'w') as f:
                    f.write('1')
                QMessageBox.warning(self, "安全警告", "密码错误次数过多，已清除历史记录！\n\n出于安全考虑，您的浏览记录和cookies已被清除。")
                dialog.close()
                sys.exit(1)
            else:
                QMessageBox.warning(self, "错误", f"密码错误，请重试！剩余尝试次数: {3 - self.password_attempts}")
                
        except Exception as e:
            error_msg = f"验证密码时出错: {e}"
            self.log_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            
    def set_password(self, dialog):
        if self.new_password_input.text() != self.confirm_password_input.text():
            QMessageBox.warning(self, "错误", "两次输入的密码不一致！")
            return
            
        if not self.new_password_input.text():
            QMessageBox.warning(self, "错误", "密码不能为空！")
            return
            
        try:
            password_hash = hashlib.sha256(self.new_password_input.text().encode()).hexdigest()
            with open(self.password_file, 'w') as f:
                f.write(password_hash)
                
            self.is_authenticated = True
            dialog.close()
            QMessageBox.information(self, "成功", "密码设置成功！")
            # 继续初始化浏览器
            self.initialize_browser()
        except Exception as e:
            error_msg = f"保存密码时出错: {e}"
            self.log_error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            
    def initialize_browser(self):
        """初始化浏览器界面"""
        # 检查是否有密码错误标记文件
        if os.path.exists('password_error.txt'):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "您连续三次密码错误，浏览记录已清除", QMessageBox.StandardButton.Ok)
            os.remove('password_error.txt')
            
        # 保留cookie设置
        if hasattr(self, 'browser') and self.browser:
            settings = self.browser.page().profile().settings()
            settings.setAttribute(QWebEngineSettings.WebAttribute.PersistentCookies, True)
            
        self.setWindowTitle("GFY浏览器")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1280, 720)
        
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget {
                border: 1px solid #ddd;
                background-color: white;
            }
            QSplitter::handle {
                background-color: #ddd;
                width: 2px;
            }
        """)
        
    def take_screenshot(self):
        """截图当前浏览器窗口并保存为PNG文件"""
        screen = QApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(self.winId())
            
            # 创建screenshot文件夹如果不存在
            screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # 获取保存路径，默认保存到screenshots文件夹
            default_path = os.path.join(screenshot_dir, 'screenshot.png')
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存截图", 
                default_path, 
                "PNG 图片 (*.png);;所有文件 (*)"
            )
            
            if file_path:
                if not file_path.endswith('.png'):
                    file_path += '.png'
                pixmap.save(file_path, 'PNG')
                QMessageBox.information(self, "成功", f"截图已保存到 {file_path}")
        else:
            QMessageBox.warning(self, "错误", "无法获取屏幕信息")
            
    def show_settings_dialog(self):
        from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QCheckBox, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("浏览器设置")
        dialog.resize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-weight: bold;
            }
            QPushButton {
                min-width: 80px;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 起始页设置
        homepage_label = QLabel("起始页URL:")
        self.homepage_edit = QLineEdit(self.homepage_url)
        
        # 下载路径设置
        download_label = QLabel("下载文件夹:")
        self.download_dir_edit = QLineEdit(getattr(self, 'download_dir', 'download'))
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_download_dir)
        
        download_layout = QHBoxLayout()
        download_layout.addWidget(self.download_dir_edit)
        download_layout.addWidget(browse_btn)
        
        # 静音模式设置
        self.mute_checkbox = QCheckBox("静音模式")
        self.mute_checkbox.setChecked(getattr(self, 'is_muted', False))
        
        # 错误日志设置
        error_log_label = QLabel("错误日志:")
        self.error_log_text = QTextEdit()
        self.error_log_text.setReadOnly(True)
        
        error_log_btn_layout = QHBoxLayout()
        view_error_btn = QPushButton("查看错误日志")
        view_error_btn.clicked.connect(lambda: self.show_error_log_window())
        error_log_btn_layout.addWidget(view_error_btn)
        
        # 修改密码设置
        change_pass_btn = QPushButton("修改密码")
        change_pass_btn.clicked.connect(lambda: self.show_change_password_dialog(dialog))
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(lambda: self.save_settings(dialog))
        
        layout.addWidget(homepage_label)
        layout.addWidget(self.homepage_edit)
        layout.addSpacing(10)
        layout.addWidget(download_label)
        layout.addLayout(download_layout)
        layout.addSpacing(10)
        layout.addWidget(self.mute_checkbox)
        layout.addSpacing(10)
        layout.addWidget(error_log_label)
        layout.addWidget(self.error_log_text)
        layout.addLayout(error_log_btn_layout)
        layout.addSpacing(10)
        layout.addWidget(change_pass_btn)
        layout.addWidget(save_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
        
    def show_error_log_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("错误日志")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        try:
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                text_edit.setPlainText(f.read())
        except Exception as e:
            text_edit.setPlainText(f"无法加载错误日志: {e}")
        
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.exec()
        
    def browse_download_dir(self):
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择下载文件夹", self.download_dir_edit.text())
        if dir_path:
            self.download_dir_edit.setText(dir_path)
            
    def show_change_password_dialog(self, parent_dialog):
        dialog = QDialog(self)
        dialog.setWindowTitle("修改密码")
        dialog.resize(300, 200)
        
        layout = QVBoxLayout()
        
        current_pass_label = QLabel("当前密码:")
        self.current_pass_input = QLineEdit()
        self.current_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        new_pass_label = QLabel("新密码:")
        self.new_pass_input = QLineEdit()
        self.new_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        confirm_label = QLabel("确认新密码:")
        self.confirm_pass_input = QLineEdit()
        self.confirm_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        submit_btn = QPushButton("确定")
        submit_btn.clicked.connect(lambda: self.change_password(dialog, parent_dialog))
        
        layout.addWidget(current_pass_label)
        layout.addWidget(self.current_pass_input)
        layout.addWidget(new_pass_label)
        layout.addWidget(self.new_pass_input)
        layout.addWidget(confirm_label)
        layout.addWidget(self.confirm_pass_input)
        layout.addWidget(submit_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
        
    def change_password(self, dialog, parent_dialog):
        # 验证当前密码
        try:
            with open(self.password_file, 'r') as f:
                stored_hash = f.read().strip()
                
            input_hash = hashlib.sha256(self.current_pass_input.text().encode()).hexdigest()
            
            if input_hash != stored_hash:
                QMessageBox.warning(self, "错误", "当前密码错误！")
                return
                
            # 验证新密码
            if self.new_pass_input.text() != self.confirm_pass_input.text():
                QMessageBox.warning(self, "错误", "两次输入的新密码不一致！")
                return
                
            if not self.new_pass_input.text():
                QMessageBox.warning(self, "错误", "新密码不能为空！")
                return
                
            # 更新密码
            new_hash = hashlib.sha256(self.new_pass_input.text().encode()).hexdigest()
            with open(self.password_file, 'w') as f:
                f.write(new_hash)
                
            QMessageBox.information(self, "成功", "密码修改成功！")
            dialog.close()
            parent_dialog.close()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"修改密码时出错: {e}")
        
    def save_settings(self, dialog):
        # 保存起始页
        url = self.homepage_edit.text()
        if not url.startswith('http'):
            url = 'http://' + url
            
        self.homepage_url = url
        
        # 保存下载路径
        download_dir = self.download_dir_edit.text()
        self.download_dir = download_dir
        
        # 保存静音设置
        is_muted = self.mute_checkbox.isChecked()
        self.is_muted = is_muted
        self.browser.page().setAudioMuted(is_muted)
        
        try:
            # 保存起始页配置
            with open('homepage.txt', 'w') as f:
                f.write(url)
                
            # 保存下载路径配置
            with open('download_dir.txt', 'w') as f:
                f.write(download_dir)
                
            # 保存静音配置
            with open('mute.txt', 'w') as f:
                f.write('1' if is_muted else '0')
            
            # 检查当前网址是否已收藏
            try:
                with open('bookmarks.txt', 'r') as f:
                    bookmarks = [line.strip() for line in f]
                    if url in bookmarks:
                        self.bookmark_btn.setText("★")
                    else:
                        self.bookmark_btn.setText("☆")
            except FileNotFoundError:
                self.bookmark_btn.setText("☆")
                
            dialog.close()
        except Exception as e:
            print(f"保存设置时出错: {e}")
            
class WebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化媒体播放器
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        
        # 检查多媒体后端支持
        if not self.media_player.isAvailable():
            print("警告: 系统缺少必要的多媒体后端支持，请安装GStreamer或DirectShow")
        else:
            print("多媒体后端支持正常")
        # 启用安全相关设置
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.HyperlinkAuditingEnabled, False)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.AllowGeolocationOnInsecureOrigins, False)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, False)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, False)
        
        # 保留必要的功能设置
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.WebRTCPublicInterfacesOnly, True)
        
        # 增强HTML5视频播放支持
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.AutoLoadIconsForPage, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        # 媒体源扩展支持已被移除，因当前PyQt6版本不支持该属性
        # 媒体编解码器支持已被移除，因当前PyQt6版本不支持该属性
        # MediaStreamEnabled属性在当前PyQt6版本中不可用
        
        # 设置视频元素处理
        self.page().runJavaScript("""
            document.addEventListener('play', function(e) {
                if(e.target.tagName.toLowerCase() === 'video') {
                    window.videoUrl = e.target.currentSrc;
                }
            });
        """)
        
        # 通过JavaScript监听视频播放事件
        self.page().runJavaScript("""
            document.addEventListener('play', function(e) {
                if(e.target.tagName.toLowerCase() === 'video') {
                    window.videoUrl = e.target.currentSrc;
                    console.log('视频播放:', window.videoUrl);
                }
            });
        """)
        # 启用WebGL支持
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        # 启用视频轨道支持
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        # 启用全屏API
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        # 启用屏幕捕捉API
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
        
        # 错误处理
        self.page().featurePermissionRequested.connect(self.handle_feature_permission)
        self.page().loadFinished.connect(self.on_load_finished)
        
        # 设置下载管理器
        self.page().profile().downloadRequested.connect(self.on_download_requested)
        
        # 初始化静音状态
        try:
            with open('mute.txt', 'r') as f:
                is_muted = f.read().strip() == '1'
                self.page().setAudioMuted(is_muted)
        except FileNotFoundError:
            self.page().setAudioMuted(False)
        
    def on_download_requested(self, download):
        # 获取下载文件名
        file_name = download.url().fileName()
        if not file_name:
            file_name = "download_" + str(int(time.time()))
            
        # 确保下载目录存在
        import os
        try:
            with open('download_dir.txt', 'r') as f:
                download_dir = f.read().strip()
                if not download_dir:
                    download_dir = "download"
        except FileNotFoundError:
            download_dir = "download"
            
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # 设置默认保存路径
        default_path = os.path.join(download_dir, file_name)
        
        # 弹出保存文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", default_path, "All Files (*.*)")
            
        if file_path:
            # 设置保存路径
            download.setPath(file_path)
            # 接受下载
            download.accept()
            
            # 显示下载进度
            download.downloadProgress.connect(lambda bytes_received, bytes_total: 
                print(f"下载进度: {bytes_received}/{bytes_total}"))
            download.finished.connect(lambda: print("下载完成"))
        else:
            download.cancel()
        
    def createWindow(self, type):
        # 处理新窗口/标签页的创建请求
        if type == QWebEnginePage.WebWindowType.WebBrowserTab or \
           type == QWebEnginePage.WebWindowType.WebBrowserWindow:
            # 获取当前浏览器实例
            browser_window = self.parent().parent().parent()
            # 在当前窗口中加载新URL
            return browser_window.browser
        return super().createWindow(type)
        
    def handle_feature_permission(self, securityOrigin, feature):
        # 自动允许媒体相关权限请求
        if feature in [QWebEnginePage.Feature.MediaAudioCapture, 
                     QWebEnginePage.Feature.MediaVideoCapture, 
                     QWebEnginePage.Feature.MediaAudioVideoCapture]:
            self.page().setFeaturePermission(securityOrigin, feature, 
                                           QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
    
    def handle_video_request(self, request):
        """处理视频播放请求(已弃用)"""
        pass
            
    def on_load_finished(self, ok):
        if not ok:
            print(f"页面加载失败，请检查网络连接或URL是否正确")
        # 检查视频元素并打印状态
        self.page().runJavaScript("""
            var videos = document.getElementsByTagName('video');
            for (var i = 0; i < videos.length; i++) {
                console.log('视频状态: ' + videos[i].readyState);
            }
        """)
         


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = Browser()
        window.show()
        app.exec()
    except KeyboardInterrupt:
        print("\n程序被用户中断，正在退出...")