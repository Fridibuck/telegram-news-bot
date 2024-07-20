#created by Fridibuck

import sys
import random
import logging
import requests
import feedparser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QHBoxLayout, QPlainTextEdit, QDoubleSpinBox, QLineEdit,
    QTabWidget, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QObject
from PyQt5.QtGui import QPalette, QColor, QPainter, QPen, QBrush,QIcon
from telegram import Bot, Update
from apscheduler.schedulers.qt import QtScheduler
import asyncio

class ToggleButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setMinimumSize(80, 40)
        self.setMaximumSize(80, 40)
        self.setStyleSheet("border: none;")
        self.setChecked(False)

    def paintEvent(self, event):
        radius = 20
        width = self.width()
        height = self.height()

        bg_color = QColor(0, 150, 0) if self.isChecked() else QColor(150, 0, 0)
        circle_color = QColor(255, 255, 255)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(0, 0, width, height, radius, radius)

        circle_x = width - height if self.isChecked() else 0
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(circle_x, 0, height, height)
        
        painter.setPen(QPen(QColor(255, 255, 255)))
        text = "ON" if self.isChecked() else "OFF"
        painter.drawText(self.rect(), Qt.AlignCenter, text)
        
        painter.end()

# Global değişkenler
new_articles_queue = []
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
shared_articles = set()
fetched_article_count = 0
shared_article_count = 0

def read_rss_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

RSS_FEED_URLS = read_rss_urls('rss.txt')

class BotThread(QThread):
    status_signal = pyqtSignal(str)
    bot_name_signal = pyqtSignal(str)
    fetched_articles_signal = pyqtSignal(str)
    shared_articles_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(BotThread, self).__init__(parent)
        self.running = False
        self.check_interval = 10.0
        self.chat_id = ''
        self.bot_name = ""

    def set_interval(self, seconds):
        self.check_interval = seconds

    def set_chat_id(self, chat_id):
        self.chat_id = chat_id

    async def bot_task(self):
        bot_token = ' BOT TOKEN GİR'
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        self.bot_name = me.username
        self.bot_name_signal.emit(f"{self.bot_name}")

        self.status_signal.emit("Bot çalışıyor")

        while self.running:
            await asyncio.sleep(1)

        self.status_signal.emit("Bot durduruldu")

    async def share_random_article(self):
        global shared_article_count

        if new_articles_queue:
            article = random.choice(new_articles_queue)
            bot_token = 'BOT TOKEN GİR'
            bot = Bot(token=bot_token)

            try:
                await bot.send_message(chat_id=self.chat_id, text=article)
                shared_article_count += 1
                new_articles_queue.remove(article)
                logger.info(f"Makale paylaşıldı: {article}")
                self.shared_articles_signal.emit(f"Paylaşılan makaleler: {shared_article_count}")
            except Exception as e:
                logger.error(f"Mesaj gönderme başarısız: {e}")
        else:
            logger.info("Paylaşılacak yeni makale yok.")

    def run(self):
        self.running = True
        asyncio.run(self.bot_task())

    def stop(self):
        self.running = False
        self.status_signal.emit("Bot durduruluyor...")

class QTextEditLogger(logging.Handler, QObject):
    new_log_signal = pyqtSignal(str)

    def __init__(self, text_edit):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.text_edit = text_edit
        self.new_log_signal.connect(self.append_log)
        self.connected = True

    def emit(self, record):
        msg = self.format(record)
        self.new_log_signal.emit(msg)

    def append_log(self, msg):
        self.text_edit.appendPlainText(msg)

    def flush(self):
        pass

    def close(self):
        if self.connected:
            self.new_log_signal.disconnect(self.append_log)
            self.connected = False
        super().close()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.bot_thread = BotThread(self)
        self.scheduler = QtScheduler()
        self.bot_thread.status_signal.connect(self.update_status)
        self.bot_thread.bot_name_signal.connect(self.update_bot_name)
        self.bot_thread.fetched_articles_signal.connect(self.update_fetched_articles)
        self.bot_thread.shared_articles_signal.connect(self.update_shared_articles)
        self.log_handler = QTextEditLogger(self.log_terminal)
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.INFO)

    def initUI(self):
        self.setWindowTitle('Telegram Haber Botu v1')
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#FFFFFF"))
        self.setPalette(palette)

        icon_path = 'tt1.png'
        app_icon = QIcon(icon_path)
        self.app = QApplication(sys.argv)
        self.setWindowIcon(app_icon)

        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        status_layout = QHBoxLayout()

        self.toggle_button = ToggleButton()
        self.toggle_button.toggled.connect(self.toggle_bot)
        button_layout.addWidget(self.toggle_button)
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.article_fetch_button = QPushButton("Makale Çek")
        self.article_fetch_button.clicked.connect(self.fetch_articles)
        self.article_share_button = QPushButton("Makale Paylaş")
        self.article_share_button.clicked.connect(self.share_articles)

        for btn in [self.article_fetch_button, self.article_share_button]:
            btn.setFixedSize(100, 40)
            btn.setStyleSheet("background-color: #87CEEB; color: white; border-radius: 10px;")
            btn.setCheckable(True)
            btn.clicked.connect(self.on_button_toggled)

        button_layout.addWidget(self.article_fetch_button)
        button_layout.addWidget(self.article_share_button)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                background: #FFFFFF;
            }
            QTabBar::tab {
                background: #DDDDDD;
                color: black;
                padding: 10px;
                border: 1px solid #CCCCCC;
                border-bottom-color: #FFFFFF;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                margin-bottom: -1px;
            }
            QTabBar::tab:hover {
                background: #EEEEEE;
            }
        """)
        self.tabs.addTab(self.create_settings_tab(), "Ayarlar")
        self.tabs.addTab(self.create_terminal_tab(), "Terminal")
        self.tabs.addTab(self.create_commands_tab(), "Komutlar")
        self.tabs.addTab(self.create_help_tab(), "Yardım")

        self.status_label = QLabel("Durum:")
        self.bot_name_label = QLabel("Bot Adı:")
        self.fetched_articles_label = QLabel('Alınan: 0')
        self.shared_articles_label = QLabel('Paylaşılan: 0')

        for lbl in [self.status_label, self.bot_name_label, self.fetched_articles_label, self.shared_articles_label]:
            lbl.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            lbl.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.bot_name_label)
        status_layout.addWidget(self.fetched_articles_label)
        status_layout.addWidget(self.shared_articles_label)

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(status_layout)

        self.setLayout(main_layout)

    def on_button_toggled(self):
        sender = self.sender()
        if sender.isChecked():
            sender.setStyleSheet("background-color: #32CD32; color: white; border-radius: 10px;")
        else:
            sender.setStyleSheet("background-color: #87CEEB; color: white; border-radius: 10px;")

    def create_settings_tab(self):
        settings_tab = QWidget()
        settings_tab.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout()

        self.chat_id_label = QLabel('ID:', self)
        self.chat_id_label.setStyleSheet("color: black;")
        self.chat_id_input = QLineEdit(self)
        self.chat_id_input.setPlaceholderText("Sohbet/Grup ID'si girin")
        self.chat_id_input.setText('')
        self.chat_id_input.textChanged.connect(self.update_chat_id)

        self.interval_label = QLabel('Kontrol Aralığı (saniye):', self)
        self.interval_label.setStyleSheet("color: black;")
        self.interval_spinbox = QDoubleSpinBox(self)
        self.interval_spinbox.setRange(0.1, 3600.0)
        self.interval_spinbox.setValue(10.0)
        self.interval_spinbox.setSingleStep(0.1)
        self.interval_spinbox.valueChanged.connect(self.update_interval)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_spinbox)

        chat_id_layout = QHBoxLayout()
        chat_id_layout.addWidget(self.chat_id_label)
        chat_id_layout.addWidget(self.chat_id_input)

        layout.addLayout(chat_id_layout)
        layout.addLayout(interval_layout)
        settings_tab.setLayout(layout)
        return settings_tab

    def create_terminal_tab(self):
        terminal_tab = QWidget()
        terminal_tab.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout()

        self.log_terminal = QPlainTextEdit(self)
        self.log_terminal.setReadOnly(True)
        self.log_terminal.setStyleSheet("background-color: #F0F0F0; color: black;")

        layout.addWidget(self.log_terminal)
        terminal_tab.setLayout(layout)
        return terminal_tab

    def create_commands_tab(self):
        commands_tab = QWidget()
        commands_tab.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout()
        
        command_list = QLabel("Kullanılabilir Komutlar:\n/start - Botu başlat\n/rss <url> - Yeni bir RSS feed URL ekle\n \n \n \n \n \n \n \n \n \n \n \n \n \n \n", self)
        command_list.setStyleSheet("color: black;")
        layout.addWidget(command_list)
        
        commands_tab.setLayout(layout)
        return commands_tab

    def create_help_tab(self):
        help_tab = QWidget()
        help_tab.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout()
        
        help_text = QLabel("Telegram Haber Botu:\n1. created by Fridibuck\n \n \n \n \n \n \n \n \n \n \n \n \n", self)
        help_text.setStyleSheet("color: black;")
        layout.addWidget(help_text)
        
        help_tab.setLayout(layout)
        return help_tab

    def toggle_bot(self):
        if self.toggle_button.isChecked():
            self.bot_thread.set_chat_id(self.chat_id_input.text())
            self.bot_thread.start()
            self.status_label.setText("Durum: <span style='color: green;'>Çalışıyor</span>")
        else:
            self.bot_thread.stop()
            self.bot_thread.quit()
            self.status_label.setText("Durum: <span style='color: red;'>Durduruldu</span>")

    def fetch_articles(self):
        global fetched_article_count
        if self.article_fetch_button.isChecked():
            self.scheduler.add_job(self._fetch_articles_job, 'interval', seconds=10, id='fetch_articles_job')
            if not self.scheduler.running:
                self.scheduler.start()
            self.article_fetch_button.setStyleSheet("color: green;")
            logger.info("Makaleler çekilmeye başlandı.")
        else:
            self.scheduler.remove_job('fetch_articles_job')
            self.article_fetch_button.setStyleSheet("color: red;")
            logger.info("Makale çekme işlemi durduruldu.")

    def _fetch_articles_job(self):
        global fetched_article_count
        url = random.choice(RSS_FEED_URLS)
        response = requests.get(url)
        feed = feedparser.parse(response.content)
        fetched_article_count += len(feed.entries)

        for entry in feed.entries:
            title = entry.title
            link = entry.link
            if link not in shared_articles:
                new_articles_queue.append(f"{title}\n{link}")
                shared_articles.add(link)

        self.fetched_articles_label.setText(f'Alınan: {fetched_article_count}')
        logger.info(f"{len(feed.entries)} makale çekildi.")

    def share_articles(self):
        if self.article_share_button.isChecked():
            self.scheduler.add_job(self._share_articles_job, 'interval', seconds=self.interval_spinbox.value(), id='share_articles_job')
            if not self.scheduler.running:
                self.scheduler.start()
            self.article_share_button.setStyleSheet("color: green;")
            logger.info("Makaleler paylaşılmaya başlandı.")
        else:
            self.scheduler.remove_job('share_articles_job')
            self.article_share_button.setStyleSheet("color: red;")
            logger.info("Makale paylaşma işlemi durduruldu.")

    def _share_articles_job(self):
        asyncio.run(self.bot_thread.share_random_article())

    def update_status(self, status):
        if "Çalışıyor" in status:
            status = status.replace("Çalışıyor", "<span style='color: green;'>Çalışıyor</span>")
        elif "Bekliyor" in status:
            status = status.replace("Bekliyor", "<span style='color: yellow;'>Bekliyor</span>")
        elif "Durduruluyor" in status:
            status = status.replace("Durduruluyor", "<span style='color: red;'>Durduruluyor</span>")
        elif "Durduruldu" in status:
            status = status.replace("Durduruldu", "<span style='color: red;'>Durduruldu</span>")
        self.status_label.setText(f"Durum: {status}")

    def update_bot_name(self, name):
        self.bot_name_label.setText(f'Bot Adı: {name}')

    def update_fetched_articles(self, count):
        self.fetched_articles_label.setText(f'Alınan: {count}')

    def update_shared_articles(self, count):
        self.shared_articles_label.setText(f'Paylaşılan: {count}')

    def update_interval(self):
        if self.bot_thread.isRunning():
            self.bot_thread.set_interval(self.interval_spinbox.value())

    def update_chat_id(self, chat_id):
        if self.bot_thread.isRunning():
            self.bot_thread.set_chat_id(chat_id)

    def closeEvent(self, event):
        logger.removeHandler(self.log_handler)  # Handler'ı logger'dan kaldırın
        self.log_handler.close()  # QTextEditLogger'ı kapatın
        event.accept()
        logging.shutdown()  # Loglama işlemlerini kapatın


async def check_and_share_new_articles():
    global fetched_article_count
    logger.info("Yeni makaleler kontrol ediliyor...")
    url = random.choice(RSS_FEED_URLS)
    response = requests.get(url)
    feed = feedparser.parse(response.content)
    fetched_article_count += len(feed.entries)

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        logger.info(f"Makale bulundu: {title} - {link}")

        if link not in shared_articles:
            new_articles_queue.append(f"{title}\n{link}")
            shared_articles.add(link)
            logger.info(f"Yeni makale eklendi: {title} - {link}")

async def start(update: Update, context):
    await update.message.reply_text('Bot çalışıyor ve yeni makaleleri kontrol ediyor!')

    async def add_rss(self, update: Update, context):
        new_rss_url = context.args[0]
        if new_rss_url not in RSS_FEED_URLS:
            RSS_FEED_URLS.append(new_rss_url)
            with open('rss.txt', 'a') as file:
                file.write(new_rss_url + '\n')
            await update.message.reply_text(f"Yeni RSS bağlantısı eklendi: {new_rss_url}")
            logger.info(f"Yeni RSS bağlantısı eklendi: {new_rss_url}")

            # RSS_FEED_URLS listesini güncelle
            self.update_rss_urls()
        else:
            await update.message.reply_text("Bu RSS bağlantısı zaten mevcut.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    try:
        sys.exit(app.exec_())
    except:
        logging.shutdown()
