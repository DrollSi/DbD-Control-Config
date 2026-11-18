import sys
import os
import stat
import time
import configparser

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QScrollArea, QWidget,
    QMainWindow, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QLineEdit, QGroupBox,
    QMessageBox, QSlider, QComboBox, QPlainTextEdit
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QKeySequence

try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
    MULTIMEDIA_OK = True
except ImportError:
    MULTIMEDIA_OK = False

WARNING_TEXT = f"""<h2 align="center">Предупреждение</h2>

<hr>

<p align="center">Нажимая кнопку «Подтвердить согласие», вы соглашаетесь с тем, что эта<br>
программа может <b>изменять файлы сохранения игры Dead by Daylight</b>.</p>

<hr>

<p align="center"><b>Dead by Daylight не запрещает менять файлы графики и управление,</b><br>
однако неизвестно, не выйдет ли обновление, которое запретит это.<br>
<b>Решение об использовании программы остаётся за вами.</b></p>

<p align="center"><b>Автор программы не несёт ответственности за ваш аккаунт.</b><br>
Все действия вы выполняете на свой страх и риск.</p>

<hr>

<p align="center">Программа распространяется <b>только на официальной странице <a href="https://github.com/DrollSi/DbD-Control-Config">GitHub</a></b> и является<br>
полностью открытой, <b>исходный код доступен каждому.</b></p>

<hr>

<p align="center"><b>Проверяйте, что запускаете файл с официальной страницы:</b><br>
<a href="https://github.com/DrollSi/DbD-Control-Config">https://github.com/DrollSi/DbD-Control-Config</a></p>"""

def app_dir():
    """Папка, где лежит программа: у exe или у исходника."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(app_dir(), "config.cfg")

# Название программы (используется во всех окнах и заголовках)
APP_NAME = "DbD Control Config"

# Раздел конфига с общими настройками программы (согласие, путь к игре)
GENERAL_SECTION = "General"

LOCKED_MODE = "Неизменяемые привязки"


# Вкладки программы
MODES = [
    "Убийца",
    "Выживший",
    "Режим зрителя",
]

# Список доступных действий по режимам
ACTIONS = {
    "Убийца": [
        "Вперёд",
        "Назад",
        "Влево",
        "Вправо",
        "Атаковать",
        "Использовать силу",
        "Вторичная сила",
        "Активировать способность 1",
        "Активировать способность 2",
        "Активировать способность события",
        "Бросить выжившего",
        "Взаимодействие / Поднять выжившего",
        "Повернуть направо",
        "Повернуть налево",
        "Посмотреть вверх",
        "Посмотреть вниз",
    ],
    "Выживший": [
        "Вперёд",
        "Назад",
        "Влево",
        "Вправо",
        "Бежать",
        "Пригнуться",
        "Использовать предмет",
        "Бросить предмет",
        "Поднять предмет / Взаимодействие",
        "Действие",
        "Вспомогательные действие / Проверки реакции",
        "Активировать способность 1",
        "Активировать способность 2",
        "Активировать способность события",
        "Дернуться вправо",
        "Дернуться влево",
        "Повернуть направо",
        "Повернуть налево",
        "Посмотреть вверх",
        "Посмотреть вниз",
        "Указать на что-либо",
        "За мной / Иди сюда",
        "Открыть круг намерений",
    ],
    "Режим зрителя": [
        "Выживший 1",
        "Выживший 2",
        "Выживший 3",
        "Выживший 4",
        "Выживший 5",
        "Выживший 6",
        "Выживший 7",
        "Выживший 8",
        "Убийца 1",
        "Убийца 2",
        "Выбор влево",
        "Выбор вправо",
        "Верхняя панель наблюдателя",
    ],
}

# Как наше действие превращается в бинды игры.
# ("тип строки", "имя маппинга", "Scale")
# type = "axis"   -> AxisMappings, Scale из слайдера (со знаком)
# type = "action" -> ActionMappings, Scale нет - слайдер не показываем
ACTION_BINDS = {
    "Убийца": {
        "Вперёд": ("axis",   "MoveForwardKiller",   1.0),
        "Назад":  ("axis",   "MoveForwardKiller",  -1.0),
        "Влево":  ("axis",   "MoveRightKiller",    -1.0),
        "Вправо": ("axis",   "MoveRightKiller",     1.0),
        "Атаковать": ("action", "Attack_Slasher",      None),
        "Использовать силу": ("action", "ItemUse_Slasher", None),
        "Вторичная сила": ("action", "Action_Slasher",  None),
        "Активировать способность 1": ("action", "AbilityOne_Killer", None),
        "Активировать способность 2": ("action", "AbilityTwo_Killer", None),
        "Активировать способность события": ("action", "EventAbility_Killer", None),
        "Бросить выжившего": ("action", "ItemDrop_Slasher", None),
        "Взаимодействие / Поднять выжившего": ("action", "Interact_Slasher", None),
        "Повернуть направо": ("axis", "TurnConstantKiller",   1.0),
        "Повернуть налево": ("axis",  "TurnConstantKiller",  -1.0),
        "Посмотреть вверх": ("axis",  "LookUpConstantKiller", 1.0),
        "Посмотреть вниз": ("axis",   "LookUpConstantKiller",-1.0),
    },
    "Выживший": {
        "Вперёд": ("axis",   "MoveForwardSurvivor",          1.0),
        "Назад":  ("axis",   "MoveForwardSurvivor",         -1.0),
        "Влево":  ("axis",   "MoveRightSurvivor",           -1.0),
        "Вправо": ("axis",   "MoveRightSurvivor",            1.0),
        "Бежать": ("action", "Run_Camper",                   None),
        "Пригнуться": ("action", "Crouch",                   None),
        "Использовать предмет": ("action", "ItemUse_Camper", None),
        "Бросить предмет": ("action", "ItemDrop_Camper",     None),
        "Поднять предмет / Взаимодействие": ("action", "Interact_Camper", None),
        "Действие": ("action", "FastInteract_Camper",        None),
        "Вспомогательные действие / Проверки реакции": ("action", "SecondaryAction_Camper", None),
        "Активировать способность 1": ("action", "Action_Camper", None),
        "Активировать способность 2": ("action", "AbilityTwo_Camper", None),
        "Активировать способность события": ("action", "EventAbility_Survivor", None),
        "Дернуться вправо": ("action", "WiggleRight_Camper", None),
        "Дернуться влево": ("action", "WiggleLeft_Camper",   None),
        "Повернуть направо": ("axis", "TurnConstantSurvivor",   1.0),
        "Повернуть налево": ("axis",  "TurnConstantSurvivor",  -1.0),
        "Посмотреть вверх": ("axis",  "LookUpConstantSurvivor", 1.0),
        "Посмотреть вниз": ("axis",   "LookUpConstantSurvivor",-1.0),
        "Указать на что-либо": ("action", "Gesture01",       None),
        "За мной / Иди сюда": ("action", "Gesture02",        None),
        "Открыть круг намерений": ("action", "QuickCommsWheelOpen", None),
    },
    "Режим зрителя": {
        "Выживший 1": ("action", "Spectate_Survivor1", None),
        "Выживший 2": ("action", "Spectate_Survivor2", None),
        "Выживший 3": ("action", "Spectate_Survivor3", None),
        "Выживший 4": ("action", "Spectate_Survivor4", None),
        "Выживший 5": ("action", "Spectate_Survivor5", None),
        "Выживший 6": ("action", "Spectate_Survivor6", None),
        "Выживший 7": ("action", "Spectate_Survivor7", None),
        "Выживший 8": ("action", "Spectate_Survivor8", None),
        "Убийца 1": ("action", "Spectate_Killer1", None),
        "Убийца 2": ("action", "Spectate_Killer2", None),
        "Выбор влево": ("action", "Spectate_Previous", None),
        "Выбор вправо": ("action", "Spectate_Next", None),
        "Верхняя панель наблюдателя": ("action", "Spectate_TopBar", None),
    },
}

# Неизменяемые привязки. Пишутся в Input.ini всегда.
# Формат: (тип, имя маппинга, базовый Scale, клавиша движка, отображаемое действие)
# тип = "axis"   -> AxisMappings, Scale = базовый знак * сила со слайдера
# тип = "action" -> ActionMappings, Scale нет, слайдера тоже нет
LOCKED_BINDS = [
    ("axis",   "Turn",                  1.0,  "MouseX",           "Навести / Смотреть"),
    ("axis",   "LookUp",               -1.0,  "MouseY",           "Навести / Смотреть"),
    ("action", "SecondaryAction_Slasher", None, "RightMouseButton", "Неизвестно"),
    ("action", "Cheat",                 None, "Q",                "Неизвестно"),
    ("action", "DirectionalInputLeft",  None, "A",                "Неизвестно"),
    ("action", "DirectionalInputRight", None, "D",                "Неизвестно"),
    ("action", "Gesture03",             None, "Three",            "Неизвестно"),
    ("action", "Gesture04",             None, "Four",             "Неизвестно"),
    ("action", "Mash_Camper",           None, "SpaceBar",         "Неизвестно"),
    ("action", "PushToTalk",            None, "Q",                "Неизвестно"),
]

# Сканкоды -> английские имена клавиш (независимо от раскладки)
SCANCODE_MAP = {
    0x02: "1", 0x03: "2", 0x04: "3", 0x05: "4", 0x06: "5",
    0x07: "6", 0x08: "7", 0x09: "8", 0x0A: "9", 0x0B: "0",
    0x10: "Q", 0x11: "W", 0x12: "E", 0x13: "R", 0x14: "T",
    0x15: "Y", 0x16: "U", 0x17: "I", 0x18: "O", 0x19: "P",
    0x1E: "A", 0x1F: "S", 0x20: "D", 0x21: "F", 0x22: "G",
    0x23: "H", 0x24: "J", 0x25: "K", 0x26: "L",
    0x2C: "Z", 0x2D: "X", 0x2E: "C", 0x2F: "V", 0x30: "B",
    0x31: "N", 0x32: "M",
    0x39: "Space",
    0x0C: "-", 0x0D: "=", 0x2B: "\\", 0x29: "~",
    0x0E: "Backspace", 0x0F: "Tab", 0x1C: "Enter", 0x2A: "Shift",
    0x36: "RShift", 0x1D: "Ctrl", 0x38: "Alt", 0x3A: "CapsLock",
    0xC7: "Home", 0xC8: "PageUp", 0xC9: "PageDown", 0xCF: "End",
    0xD1: "Pause", 0xD2: "Insert", 0xD3: "Delete",
    0x1A: "[", 0x1B: "]", 0x27: ";", 0x28: "'",
    0x33: ",", 0x34: ".", 0x35: "/",
    # Расширенные сканкоды (с префиксом 0xE0) на случай, если система отдаёт их так
    0x1CD: "Enter", 0x11D: "Ctrl", 0x138: "Alt",
    0x14B: "Left", 0x147: "Home", 0x152: "Insert", 0x153: "Delete",
    0x148: "Up", 0x150: "Down", 0x149: "PageUp", 0x151: "PageDown",
    0x14D: "Right", 0x14F: "End",   
}

# Кнопки мыши (как отображаем в интерфейсе)
MOUSE_BUTTONS = {
    Qt.LeftButton: "ЛКМ",
    Qt.RightButton: "ПКМ",
    Qt.MiddleButton: "СКМ",
    Qt.XButton1: "M4",
    Qt.XButton2: "M5",
}

# Запрещённые клавиши: нельзя назначать, захват просто игнорирует их
BLOCKED_KEYS = {
    Qt.Key_Meta: "клавиша Windows",
    Qt.Key_Print: "PrintScreen",
    Qt.Key_ScrollLock: "ScrollLock",
}

# Нормализация имён клавиш: Qt отдаёт некоторые имена в сокращённом виде,
# приводим их к полным (движок ожидает именно их).
NAME_NORMALIZE = {
    "Del": "Delete",
    "Ins": "Insert",
    "PgUp": "PageUp",
    "PgDown": "PageDown",
    "PgDn": "PageDown",
    "Esc": "Escape",
    "Ret": "Enter",
    "Ё": "~",
    "ё": "~",
    "`": "~",
}

# Перевод наших названий клавиш в те, что понимает движок игры
KEY_TO_UE = {
    "1": "One", "2": "Two", "3": "Three", "4": "Four",
    "5": "Five", "6": "Six", "7": "Seven", "8": "Eight",
    "9": "Nine", "0": "Zero",
    "-": "Hyphen",
    "=": "Equals",
    "~": "Tilde",
    "\\": "Backslash",
    "ЛКМ": "LeftMouseButton",
    "ПКМ": "RightMouseButton",
    "СКМ": "MiddleMouseButton",
    "Колесо вверх": "MouseScrollUp",
    "Колесо вниз": "MouseScrollDown",
    "M4": "ThumbMouseButton",
    "M5": "ThumbMouseButton2",
    "Space": "SpaceBar",
    "Shift": "LeftShift",
    "RShift": "RightShift",
    "Ctrl": "LeftControl",
    "Alt": "LeftAlt",
    "Enter": "Enter",
    "Tab": "Tab",
    "Backspace": "BackSpace",
    "CapsLock": "CapsLock",
    "[": "LeftBracket",
    "]": "RightBracket",
    ";": "Semicolon",
    "'": "Apostrophe",
    ",": "Comma",
    ".": "Period",
    "/": "Slash",
}

# Обратный перевод: имя движка -> как показываем в программе.
# Нужен при загрузке config.cfg, где клавиши хранятся в движковых именах.
UE_TO_DISPLAY = {}
for _disp, _ue in KEY_TO_UE.items():
    UE_TO_DISPLAY.setdefault(_ue, _disp)

DEFAULT_FORCE = 1.0
MIN_FORCE = 0.1   # ниже 0.1 нельзя
FORCE_STEP = 0.1  # шаг слайдера 0.1

# Шапка, которая всегда пишется в начало Input.ini
INI_HEADER = (
    ";METADATA=(Diff=true, UseCommands=true)\n"
    "[/Script/EnhancedInput.EnhancedPlayerInput]\n"
)


def normalize_key_name(name):
    """Приводит имя клавиши к полному виду (Del -> Delete и т.д.)."""
    return NAME_NORMALIZE.get(name, name)


def make_config_parser():
    """ConfigParser без интерполяции: процент и слэш в путях не ломают чтение."""
    return configparser.ConfigParser(interpolation=None)


def load_general_settings():
    """Читает из config.cfg согласие пользователя и путь к папке игры."""
    config = make_config_parser()
    if not config.read(CONFIG_FILE, encoding="utf-8"):
        return False, ""
    agreed = config.get(GENERAL_SECTION, "agreed", fallback="false").lower() == "true"
    game_path = config.get(GENERAL_SECTION, "game_path", fallback="")
    return agreed, game_path


def save_general_settings(agreed, game_path):
    """Сохраняет согласие и путь, не трогая остальной конфиг."""
    config = make_config_parser()
    config.read(CONFIG_FILE, encoding="utf-8")
    config[GENERAL_SECTION] = {
        "agreed": "true" if agreed else "false",
        "game_path": game_path,
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)


def load_tutorial_seen():
    """Читает из конфига флаг «туториал уже показан»."""
    config = make_config_parser()
    if not config.read(CONFIG_FILE, encoding="utf-8"):
        return False
    return config.get(GENERAL_SECTION, "tutorial_seen", fallback="false").lower() == "true"


def save_tutorial_seen():
    """Помечает в конфиге, что туториал уже показан."""
    config = make_config_parser()
    config.read(CONFIG_FILE, encoding="utf-8")
    if GENERAL_SECTION not in config:
        config[GENERAL_SECTION] = {}
    config[GENERAL_SECTION]["tutorial_seen"] = "true"
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)


class WarningDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - Предупреждение")
        self.resize(520, 460)

        root = QVBoxLayout(self)

        # ---------- Текст предупреждения ----------
        text = QLabel(WARNING_TEXT)
        text.setWordWrap(True)
        text.setTextFormat(Qt.RichText)
        text.setOpenExternalLinks(True)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(QWidget())
        scroll.widget().setLayout(QVBoxLayout())
        scroll.widget().layout().addWidget(text)
        scroll.widget().layout().addStretch()

        root.addWidget(scroll, 1)

        # ---------- Кнопка ----------
        btn_row = QHBoxLayout()
        self.btn_agree = QPushButton("Подтвердить согласие")
        btn_row.addWidget(self.btn_agree)
        root.addLayout(btn_row)

        self.btn_agree.clicked.connect(self.accept)


if MULTIMEDIA_OK:
    class VideoWidget(QVideoWidget):
        """QVideoWidget, который ловит Esc и передаёт его туториалу."""
        tutorial = None

        def keyPressEvent(self, event):
            if event.key() == Qt.Key_Escape and self.tutorial is not None:
                self.tutorial.exit_fullscreen()
                event.accept()
                return
            super().keyPressEvent(event)
else:
    VideoWidget = None


class TutorialDialog(QDialog):
    """Окно туториала: заголовок, чёрный плеер, кнопки управления."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Обучающий видеоурок")
        self.resize(860, 560)
        self.setMinimumSize(640, 420)

        self.player = None
        self.video_started = False

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # ---------- Заголовок ----------
        title = QLabel("Посмотреть видеоурок?")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        root.addWidget(title)

        # ---------- Плеер: всегда виден, чёрный фон ----------
        if MULTIMEDIA_OK:
            self.video_page = VideoWidget()
            self.video_page.tutorial = self
            self.video_page.setFocusPolicy(Qt.StrongFocus)
            self.video_page.setStyleSheet("background-color: black;")
            self.video_page.setMinimumSize(620, 340)
            root.addWidget(self.video_page, 1)
        else:
            self.video_page = None
            warn = QLabel(
                "Плеер\n\nМодуль PySide6-Multimedia не установлен - видео недоступно.\n"
            )
            warn.setAlignment(Qt.AlignCenter)
            warn.setStyleSheet(
                "background-color: black; color: gray;"
                "font-size: 14px; min-height: 340px;"
            )
            root.addWidget(warn, 1)

        # ---------- Кнопки управления видео ----------
        controls_row = QHBoxLayout()
        controls_row.addStretch(1)

        self.btn_pause = QPushButton("Пауза")
        self.btn_pause.setFixedWidth(120)
        self.btn_pause.clicked.connect(self.on_pause)
        controls_row.addWidget(self.btn_pause)

        self.btn_replay = QPushButton("Повторить")
        self.btn_replay.setFixedWidth(120)
        self.btn_replay.clicked.connect(self.on_replay)
        controls_row.addWidget(self.btn_replay)

        self.btn_fullscreen = QPushButton("Полный экран")
        self.btn_fullscreen.setFixedWidth(140)
        self.btn_fullscreen.clicked.connect(self.on_fullscreen)
        controls_row.addWidget(self.btn_fullscreen)

        controls_row.addStretch(1)
        root.addLayout(controls_row)

        # Кнопки управления показываем только когда видео играет
        self.btn_pause.hide()
        self.btn_replay.hide()
        self.btn_fullscreen.hide()

        # ---------- Кнопки выбора ----------
        choice_row = QHBoxLayout()
        choice_row.addStretch(1)
        self.btn_watch = QPushButton("Да, я готов посмотреть")
        self.btn_skip = QPushButton("Нет, я уже знаю")
        choice_row.addWidget(self.btn_watch)
        choice_row.addWidget(self.btn_skip)
        choice_row.addStretch(1)
        root.addLayout(choice_row)

        self.btn_watch.clicked.connect(self.on_watch)
        self.btn_skip.clicked.connect(self.accept)

        if MULTIMEDIA_OK:
            # Без QAudioOutput Qt6-плеер может не начать проигрывание
            self.audio_output = QAudioOutput()
            self.audio_output.setVolume(1.0)

            self.player = QMediaPlayer()
            self.player.setAudioOutput(self.audio_output)
            self.player.setVideoOutput(self.video_page)
            self.player.setSource(QUrl.fromLocalFile(self.video_path()))

            self.player.mediaStatusChanged.connect(self.on_media_status)
            self.player.errorOccurred.connect(self.on_error)

    def video_path(self):
        """Ищет tutorial.mp4: рядом с exe, во временной папке onefile,
        рядом с исходником и в текущей папке."""
        candidates = []
        if getattr(sys, "frozen", False):
            candidates.append(os.path.join(os.path.dirname(sys.executable), "tutorial.mp4"))
            candidates.append(os.path.join(getattr(sys, "_MEIPASS", ""), "tutorial.mp4"))
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tutorial.mp4"))
        candidates.append("tutorial.mp4")
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return candidates[0]

    # ---------- Кнопки выбора ----------
    def on_watch(self):
        if not MULTIMEDIA_OK:
            QMessageBox.warning(
                self,
                "Видео недоступно",
                "Не установлен модуль PySide6-Multimedia."
            )
            self.accept()
            return

        if not os.path.exists(self.video_path()):
            QMessageBox.warning(
                self,
                "Файл не найден",
                f"Рядом с программой нет файла tutorial.mp4.\n"
                f"Искал тут: {self.video_path()}\n"
                f"Папка программы: {app_dir()}\n\n"
                "Положите ролик в одну папку с программой под именем tutorial.mp4."
            )
            self.accept()
            return

        # Прячем выбор, показываем управление и запускаем ролик
        self.btn_watch.hide()
        self.btn_skip.hide()
        self.btn_pause.show()
        self.btn_replay.show()
        self.btn_fullscreen.show()
        self.video_started = True

        # Ролик всегда начинается с нуля - важно для повторного просмотра
        self.player.setPosition(0)
        self.player.play()

    # ---------- Кнопки управления ----------
    def on_pause(self):
        if self.player is None:
            return
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_pause.setText("Продолжить")
        else:
            self.player.play()
            self.btn_pause.setText("Пауза")

    def on_replay(self):
        if self.player is None:
            return
        self.player.setPosition(0)
        self.player.play()
        self.btn_pause.setText("Пауза")

    def on_fullscreen(self):
        """Полный экран у всего окна туториала: видео растягивается,
        кнопки остаются доступны."""
        if self.video_page is None:
            return
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.showFullScreen()
            self.btn_fullscreen.setText("Выйти")
            self.video_page.setFocus()

    def exit_fullscreen(self):
        """Возврат из полного экрана в обычное окно."""
        if self.isFullScreen():
            self.showNormal()
        if self.video_page is not None and self.video_page.isFullScreen():
            self.video_page.setFullScreen(False)
        self.btn_fullscreen.setText("Полный экран")
        self.setFocus()

    def keyPressEvent(self, event):
        # Esc в полном экране возвращает обычный режим, а не закрывает окно
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.exit_fullscreen()
            event.accept()
            return
        super().keyPressEvent(event)

    # ---------- Состояние плеера ----------
    def on_media_status(self, status):
        # Ролик доиграл до конца - выходим из полного экрана, прячем
        # управление и показываем «Посмотреть ещё раз» и «Продолжить»
        if self.player is not None and status == QMediaPlayer.EndOfMedia:
            self.exit_fullscreen()

            self.btn_pause.hide()
            self.btn_replay.hide()
            self.btn_fullscreen.hide()

            self.btn_watch.setText("Посмотреть ещё раз")
            self.btn_watch.show()

            self.btn_skip.setText("Продолжить")
            self.btn_skip.show()

    def on_error(self, error, error_string):
        path = self.video_path()
        QMessageBox.critical(
            self,
            "Ошибка воспроизведения",
            f"Не удалось проиграть видео: {error_string}\n\n"
            f"Путь: {path}\n"
            f"Файл существует: {os.path.exists(path)}\n\n"
            "Можно открыть tutorial.mp4 любым видеоплеером вручную."
        )
        self.accept()


class KeyCaptureButton(QPushButton):
    """Кнопка: клик -> режим захвата -> записывает клавишу или кнопку мыши.

    Фактическая клавиша хранится в self.key_value, а не в тексте кнопки:
    текст "-" - это только плейсхолдер пустой привязки.
    """
    EMPTY_TEXT = "-"

    def __init__(self, key_text="", parent=None):
        super().__init__(key_text or self.EMPTY_TEXT, parent)
        self.capturing = False
        self.key_value = key_text or ""
        self.clicked.connect(self.start_capture)

    def start_capture(self):
        self.capturing = True
        self.setText("Нажмите клавишу...")
        self.setStyleSheet("color: gray;")
        self.grabKeyboard()
        self.grabMouse()

    def keyPressEvent(self, event):
        if not self.capturing:
            return super().keyPressEvent(event)

        key = event.key()
        if key == Qt.Key_Escape:
            # Отмена захвата - привязка не меняется
            self.stop_capture()
            return

        # Системные клавиши нельзя - отменяем захват без изменения
        if key in BLOCKED_KEYS:
            self.stop_capture()
            return

        # Backspace - очистить привязку (как в игре): станет пустой
        if key == Qt.Key_Backspace:
            self.clear_key()
            self.stop_capture()
            return

        # Сначала пробуем определить клавишу по сканкоду (независимо от раскладки)
        name = SCANCODE_MAP.get(event.nativeScanCode())
        if name is None:
            name = QKeySequence(key).toString() or f"Key {key}"

        name = normalize_key_name(name)
        self.key_value = name
        self.setText(name)
        self.stop_capture()

    def mousePressEvent(self, event):
        if self.capturing:
            name = MOUSE_BUTTONS.get(event.button())
            if name:
                self.key_value = name
                self.setText(name)
                self.stop_capture()
            event.accept()
            return
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        """Захват прокрутки колёсика: вверх или вниз."""
        if not self.capturing:
            return super().wheelEvent(event)

        delta = event.angleDelta().y()
        if delta > 0:
            self.key_value = "Колесо вверх"
            self.setText(self.key_value)
            self.stop_capture()
            event.accept()
        elif delta < 0:
            self.key_value = "Колесо вниз"
            self.setText(self.key_value)
            self.stop_capture()
            event.accept()
        # если delta == 0 (наклон колеса в сторону) - игнорируем, ждём дальше

    def stop_capture(self):
        self.capturing = False
        self.releaseKeyboard()
        self.releaseMouse()
        self.setStyleSheet("")
        # Возвращаем текст кнопки к реальному значению привязки
        self.setText(self.key_value or self.EMPTY_TEXT)

    def clear_key(self):
        """Очищает привязку: в интерфейсе пусто, в конфигах тоже пусто."""
        self.key_value = ""
        self.setText(self.EMPTY_TEXT)

    def key_text(self):
        return self.key_value


class NoWheelComboBox(QComboBox):
    """Комбобокс, который не листается колёсиком мыши."""
    def wheelEvent(self, event):
        event.ignore()


class NoWheelSlider(QSlider):
    """Слайдер, который не меняется колёсиком мыши."""
    def wheelEvent(self, event):
        event.ignore()


class ForceWidget(QWidget):
    """Слайдер силы нажатия + числовое значение (0.1 - 1.0, шаг 0.1)."""
    def __init__(self, initial=DEFAULT_FORCE):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        # ... дальше всё как было

        self.slider = NoWheelSlider(Qt.Horizontal)
        self.slider.setRange(int(MIN_FORCE * 100), 100)
        self.slider.setSingleStep(10)
        self.slider.setPageStep(10)

        initial = round(initial / FORCE_STEP) * FORCE_STEP
        if initial < MIN_FORCE:
            initial = MIN_FORCE
        self.slider.setValue(int(initial * 100))

        self.label = QLabel(f"{initial:.1f}")
        self.label.setFixedWidth(36)

        self.slider.valueChanged.connect(self._update)
        layout.addWidget(self.slider)
        layout.addWidget(self.label)
        self._update()

    def _update(self):
        # Округляем к сетке 0.1: при перетаскивании мышью Qt выдаёт
        # промежуточные значения (например, 33), а нам нужны только десятые
        snapped = round(self.slider.value() / 10) * 10
        if snapped != self.slider.value():
            self.slider.blockSignals(True)
            self.slider.setValue(snapped)
            self.slider.blockSignals(False)

        self.label.setText(f"{snapped / 100:.1f}")

    def value(self):
        return round(self.slider.value() / 10) * 10 / 100


class ModeTab(QWidget):
    """Одна вкладка режима: таблица действий + кнопки."""
    save_requested = Signal()

    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.mode = mode

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        # ---------- Список действий ----------
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Действие", "Клавиша", "Сила нажатия"])
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 170)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        root.addWidget(self.table)

        # ---------- Кнопки ----------
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("+ Добавить действие")
        self.btn_del = QPushButton("- Удалить")
        self.btn_save = QPushButton("Сохранить")
        self.lbl_save_hint = QLabel("")
        self.lbl_save_hint.setStyleSheet("color: #c0392b;")

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_del)
        btn_row.addStretch()
        btn_row.addWidget(self.lbl_save_hint)
        btn_row.addWidget(self.btn_save)
        root.addLayout(btn_row)

        self.btn_add.clicked.connect(self.on_add)
        self.btn_del.clicked.connect(self.on_del)
        self.table.itemSelectionChanged.connect(self.update_del_button)
        self.btn_save.clicked.connect(self.save_requested)

    # ---------- Помощники ----------
    def bind_for(self, action_name):
        """Возвращает бинд действия в этом режиме или None."""
        return ACTION_BINDS.get(self.mode, {}).get(action_name)

    def has_scale(self, action_name):
        bind = self.bind_for(action_name)
        return bind is not None and bind[2] is not None

    # ---------- Работа со списком ----------
    def add_row(self, action_name="Вперёд", key_text="", force=DEFAULT_FORCE):
        row = self.table.rowCount()
        self.table.insertRow(row)

        combo_action = NoWheelComboBox()
        combo_action.addItems(ACTIONS.get(self.mode, []))
        if action_name in ACTIONS.get(self.mode, []):
            combo_action.setCurrentText(action_name)
        combo_action.currentTextChanged.connect(
            lambda text, r=row: self.on_action_changed(r, text)
        )
        self.table.setCellWidget(row, 0, combo_action)

        self.table.setCellWidget(row, 1, KeyCaptureButton(key_text))

        # Слайдер силы - только для действий, у которых есть Scale
        if self.has_scale(combo_action.currentText()):
            self.table.setCellWidget(row, 2, ForceWidget(force))
        else:
            self.table.setCellWidget(row, 2, None)

    def on_action_changed(self, row, text):
        """При смене действия перестраиваем колонку силы."""
        old = self.table.cellWidget(row, 2)
        if old is not None:
            self.table.removeCellWidget(row, 2)

        if self.has_scale(text):
            self.table.setCellWidget(row, 2, ForceWidget(DEFAULT_FORCE))
        else:
            self.table.setCellWidget(row, 2, None)

        self.update_del_button()

    def on_add(self):
        self.add_row()

    def on_del(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
        self.update_del_button()

    def update_del_button(self):
        """Кнопка удаления показывает, что именно будет удалено."""
        row = self.table.currentRow()
        if row < 0:
            self.btn_del.setText("- Удалить")
            return

        combo = self.table.cellWidget(row, 0)
        key_btn = self.table.cellWidget(row, 1)
        if combo is None or key_btn is None:
            self.btn_del.setText("- Удалить")
            return

        name = combo.currentText()
        key = key_btn.key_text() or "клавиша не задана"
        self.btn_del.setText(f"- Удалить: {name} [{key}]")

    # ---------- Подсказка у кнопки Сохранить ----------
    def set_save_hint(self, text):
        """Красная надпись причины блокировки сохранения (или пустая строка)."""
        self.lbl_save_hint.setText(text)

    # ---------- Данные для конфига ----------
    def rows_data(self):
        """Список строк (действие, клавиша, сила).

        Пустая клавиша сохраняется как пустая: в конфиге будет "Действие||сила",
        в Input.ini - Key= без значения.
        """
        result = []
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 0)
            key_btn = self.table.cellWidget(row, 1)
            force_w = self.table.cellWidget(row, 2)
            force = force_w.value() if force_w is not None else None
            result.append((combo.currentText(), key_btn.key_text(), force))
        return result

    def set_rows(self, rows):
        """Заливает в таблицу список строк (действие, клавиша, сила).

        Пустая клавиша - валидная строка: кнопка покажет "-", конфиг - пустое значение.
        """
        self.table.setRowCount(0)
        for action, key, force in rows:
            if action not in ACTIONS.get(self.mode, []):
                continue
            if force is None or force == "":
                force = DEFAULT_FORCE
            try:
                force = float(force)
            except (TypeError, ValueError):
                force = DEFAULT_FORCE
            if force < MIN_FORCE:
                force = MIN_FORCE
            self.add_row(action, key, force)


def make_gamepad_placeholder():
    """Подвкладка Джостик - заглушка, функционала нет и не планируется."""
    gp = QWidget()
    gp_root = QVBoxLayout(gp)
    gp_root.setContentsMargins(8, 8, 8, 8)

    table = QTableWidget(0, 3)
    table.setHorizontalHeaderLabels(["Действие", "Клавиша", "Сила нажатия"])
    table.verticalHeader().setVisible(False)

    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.Stretch)
    header.setSectionResizeMode(1, QHeaderView.Fixed)
    header.setSectionResizeMode(2, QHeaderView.Stretch)
    table.setColumnWidth(1, 170)
    table.setEditTriggers(QTableWidget.NoEditTriggers)

    # Строка-заглушка на всю ширину таблицы
    table.insertRow(0)
    placeholder = QTableWidgetItem("Планируется в следущих обновлениях")
    placeholder.setTextAlignment(Qt.AlignCenter)
    table.setSpan(0, 0, 1, 3)
    table.setItem(0, 0, placeholder)

    gp_root.addWidget(table)
    return gp


class LockedTab(QWidget):
    """Вкладка неизменяемых привязок.

    Строки создаются один раз из LOCKED_BINDS. Действие и клавишу менять
    нельзя. Слайдер силы есть только у строк типа axis (Turn / LookUp),
    у строк типа action (Неизвестно) силы нет вообще.
    Добавлять/удалять строки нельзя.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Действие", "Клавиша", "Сила нажатия"])
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 170)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        root.addWidget(self.table)

        # Строим фиксированные строки
        for btype, mapping, base_scale, ue_key, action_name in LOCKED_BINDS:
            self.add_locked_row(btype, mapping, base_scale, ue_key, action_name)

    def add_locked_row(self, btype, mapping, base_scale, ue_key, action_name):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Действие - просто текст, без выпадающего списка
        label = QTableWidgetItem(action_name)
        label.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table.setItem(row, 0, label)

        # Клавиша - неактивная кнопка, захват невозможен
        key_btn = QPushButton(ue_key)
        key_btn.setEnabled(False)
        self.table.setCellWidget(row, 1, key_btn)

        # Слайдер - только у строк с Scale (axis)
        if btype == "axis":
            self.table.setCellWidget(row, 2, ForceWidget(DEFAULT_FORCE))
        else:
            self.table.setCellWidget(row, 2, None)

    def rows_data(self):
        """Список строк (тип, маппинг, клавиша движка, сила)."""
        result = []
        for row, (btype, mapping, base_scale, ue_key, action_name) in enumerate(LOCKED_BINDS):
            force_w = self.table.cellWidget(row, 2)
            force = force_w.value() if force_w is not None else None
            result.append((btype, mapping, ue_key, force))
        return result

    def set_forces(self, forces):
        """Применяет сохранённые силы к строкам типа axis по порядку."""
        for row, force in enumerate(forces):
            if row >= self.table.rowCount():
                break
            if force is None or force == "":
                continue
            try:
                force = float(force)
            except (TypeError, ValueError):
                continue
            if force < MIN_FORCE:
                force = MIN_FORCE
            force_w = self.table.cellWidget(row, 2)
            if force_w is not None:
                force_w.slider.setValue(int(force * 100))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(720, 560)

        # ---------- Вкладки режимов ----------
        self.tabs = QTabWidget()
        self.mode_tabs = {}
        for mode in MODES:
            page = QWidget()
            page_root = QVBoxLayout(page)
            page_root.setContentsMargins(4, 4, 4, 4)

            sub_tabs = QTabWidget()
            tab = ModeTab(mode)
            tab.save_requested.connect(self.save_to_input_ini)
            sub_tabs.addTab(tab, "Клавиатура")
            sub_tabs.addTab(make_gamepad_placeholder(), "Джостик")

            page_root.addWidget(sub_tabs)
            self.tabs.addTab(page, mode)
            self.mode_tabs[mode] = tab

        # ---------- Неизменяемые привязки ----------
        self.locked_tab = LockedTab()
        locked_page = QWidget()
        locked_root = QVBoxLayout(locked_page)
        locked_root.setContentsMargins(4, 4, 4, 4)

        locked_sub_tabs = QTabWidget()
        locked_sub_tabs.addTab(self.locked_tab, "Клавиатура")
        locked_sub_tabs.addTab(make_gamepad_placeholder(), "Джостик")
        locked_root.addWidget(locked_sub_tabs)

        self.tabs.addTab(locked_page, LOCKED_MODE)

        # ---------- Настройки ----------
        self.tabs.addTab(self._make_settings_tab(), "Настройки")
        self.setCentralWidget(self.tabs)

        self.load_config()
        self.refresh_save_hints()
        self.log("DbD Control Config (1.4.0) запущена.")

    # ---------- Вкладка настроек ----------
    def _make_settings_tab(self):
        """Вкладка настроек: путь до папки WindowsClient, возврат к
        стандартным биндам, сброс программы и лог событий."""
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # ---------- Блок с папкой игры ----------
        box = QGroupBox("Папка конфигурации игры")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(12, 8, 12, 12)

        hint = QLabel(
            "Обычно она находится по пути:\n"
            "C:/Users/ВашеИмя/AppData/Local/DeadByDaylight/Saved/Config/WindowsClient"
        )
        hint.setStyleSheet("color: gray;")
        box_layout.addWidget(hint)

        # Поле с путём: можно копировать, вручную менять нельзя
        self.ed_path = QLineEdit()
        self.ed_path.setPlaceholderText("Путь не выбран - нажмите «Обзор...»")
        self.ed_path.setReadOnly(True)

        btn_browse = QPushButton("Обзор...")
        btn_browse.setFixedWidth(110)
        btn_browse.clicked.connect(self.on_browse)

        path_row = QHBoxLayout()
        path_row.addWidget(self.ed_path, 1)
        path_row.addWidget(btn_browse)
        box_layout.addLayout(path_row)

        root.addWidget(box)

        # ---------- Возврат к стандартным биндам ----------
        ro_box = QGroupBox("Возврат к стандартным биндам")
        ro_layout = QVBoxLayout(ro_box)
        ro_layout.setContentsMargins(12, 8, 12, 12)

        ro_hint = QLabel(
            "Если вы снимете галочку «Только чтение» с файла Input.ini,\n"
            "то при заходе в игру ваши бинды слетят до стандартных.\n"
            "(Нужно только чтобы вернуть всё как было)"
        )
        ro_hint.setStyleSheet("color: gray;")
        ro_hint.setWordWrap(True)
        ro_layout.addWidget(ro_hint)

        self.btn_unread = QPushButton("Снять «Только чтение» с Input.ini")
        self.btn_unread.clicked.connect(self.on_remove_readonly)
        ro_layout.addWidget(self.btn_unread)

        root.addWidget(ro_box)

        # ---------- Сброс программы ----------
        reset_box = QGroupBox("Сброс программы")
        reset_layout = QVBoxLayout(reset_box)
        reset_layout.setContentsMargins(12, 8, 12, 12)

        reset_hint = QLabel(
            "Полная очистка config.cfg: стираются согласие с правилами,\n"
            "путь к папке игры, все бинды и отметка о просмотре туториала.\n"
            "После очистки программа перезапустится и снова покажет\n"
            "предупреждение и обучающий ролик."
        )
        reset_hint.setStyleSheet("color: gray;")
        reset_hint.setWordWrap(True)
        reset_layout.addWidget(reset_hint)

        btn_clear = QPushButton("Очистить config.cfg")
        btn_clear.clicked.connect(self.on_clear_config)
        reset_layout.addWidget(btn_clear)

        root.addWidget(reset_box)

        root.addStretch()

        # ---------- Лог программы ----------
        log_box = QGroupBox("Лог программы")
        log_layout = QVBoxLayout(log_box)
        log_layout.setContentsMargins(12, 8, 12, 12)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(140)
        self.log_text.setPlaceholderText("Здесь появятся события программы")
        log_layout.addWidget(self.log_text)

        root.addWidget(log_box)

        return tab

    # ---------- Лог ----------
    def log(self, message):
        """Пишет событие в панель лога (только внутри программы)."""
        self.log_text.appendPlainText(f"[{time.strftime('%H:%M:%S')}] {message}")

    def on_browse(self):
        """Выбор папки WindowsClient. Диалог открывается в папке AppData."""
        user_home = os.path.expanduser("~")  # например: C:\Users\DrollSi
        start_dir = os.path.join(user_home, "AppData")

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку WindowsClient",
            start_dir
        )
        if folder:
            # Проверяем, что последняя папка в пути - именно WindowsClient
            if os.path.basename(folder.rstrip("\\/")).lower() != "windowsclient":
                QMessageBox.warning(
                    self,
                    APP_NAME,
                    f"Выбрана папка: «{os.path.basename(folder)}»\n\n"
                    "Путь должен заканчиваться папкой WindowsClient.\n"
                    "Обычно он выглядит так:\n"
                    "C:/Users/ВашеИмя/AppData/Local/DeadByDaylight/Saved/Config/WindowsClient"
                )
                self.log(f"Отклонён путь (не WindowsClient): {folder}")
                return

            self.ed_path.setText(folder)
            # Путь сразу запоминаем в конфиг, чтобы не выбирать каждый раз
            save_general_settings(True, folder)
            self.log(f"Выбран путь: {folder}")
            self.refresh_save_hints()

    # ---------- Возврат к стандартным биндам ----------
    def on_remove_readonly(self):
        """Снимает атрибут «Только чтение» с Input.ini, чтобы игра при
        следующем запуске перезаписала файл стандартными биндами."""
        path = self.ed_path.text().strip()
        if path == "":
            QMessageBox.warning(
                self,
                APP_NAME,
                "Сначала выберите папку WindowsClient на этой вкладке."
            )
            self.log("Снятие «Только чтение» отменено: путь не выбран")
            return

        ini_path = os.path.join(path, "Input.ini")
        if not os.path.exists(ini_path):
            QMessageBox.information(
                self,
                APP_NAME,
                "Файл Input.ini не найден в выбранной папке.\n"
                "Игра создаст его со стандартными биндами при первом запуске."
            )
            self.log("Снятие «Только чтение»: файл Input.ini не найден")
            return

        if os.access(ini_path, os.W_OK):
            QMessageBox.information(
                self,
                APP_NAME,
                "Галочка «Только чтение» уже снята.\n"
                "При следующем заходе в игру бинды вернутся к стандартным."
            )
            self.log("Снятие «Только чтение»: галочка уже снята")
            return

        try:
            os.chmod(ini_path, stat.S_IWRITE)
        except OSError as e:
            QMessageBox.critical(self, APP_NAME, f"Не удалось изменить файл:\n{e}")
            self.log(f"Ошибка снятия «Только чтение»: {e}")
            return

        self.log(f"Снят атрибут «Только чтение»: {ini_path}")
        QMessageBox.information(
            self,
            APP_NAME,
            "Атрибут «Только чтение» снят.\n"
            "При следующем заходе в игру бинды слетят до стандартных."
        )

    # ---------- Сброс программы ----------
    def on_clear_config(self):
        """Полная очистка config.cfg с последующим перезапуском программы."""
        answer = QMessageBox.question(
            self,
            APP_NAME,
            "Точно очистить config.cfg?\n\n"
            "Сотрутся: согласие с правилами, путь к папке игры,\n"
            "все бинды и отметка о просмотре туториала.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self.log("Очистка config.cfg отменена")
            return

        config = make_config_parser()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)

        self.log("config.cfg очищен - перезапуск программы")
        # Закрываем процесс и запускаем программу заново (работает и для .exe)
        os.execl(sys.executable, *sys.argv)

    # ---------- Подсказки у кнопок Сохранить ----------
    def save_block_reason(self):
        """Возвращает причину блокировки сохранения или пустую строку."""
        path = self.ed_path.text().strip()
        if path == "":
            return "Путь не выбран (вкладка \"Настройки\")"
        if os.path.basename(path.rstrip("\\/")).lower() != "windowsclient":
            return "Папка не похожа на WindowsClient"
        return ""

    def refresh_save_hints(self):
        """Обновляет красные надписи у всех кнопок Сохранить."""
        reason = self.save_block_reason()
        for tab in self.mode_tabs.values():
            tab.set_save_hint(reason)

    # ---------- Сохранение биндов в Input.ini ----------
    def save_to_input_ini(self):
        """Пишет бинды в Input.ini выбранной папки WindowsClient."""
        # Проверка пути в момент нажатия
        if self.ed_path.text().strip() == "":
            QMessageBox.warning(
                self,
                APP_NAME,
                "Сначала выберите папку WindowsClient на вкладке «Настройки»."
            )
            self.log("Сохранение отменено: путь не выбран")
            return

        # Проверка, что путь похож на WindowsClient
        path = self.ed_path.text().strip()
        if os.path.basename(path.rstrip("\\/")).lower() != "windowsclient":
            QMessageBox.warning(
                self,
                APP_NAME,
                "Папка не похожа на WindowsClient.\n"
                "Выберите правильную папку на вкладке «Настройки»."
            )
            self.log("Сохранение отменено: папка не похожа на WindowsClient")
            return

        ini_path = os.path.join(self.ed_path.text().strip(), "Input.ini")

        # Подтверждение перед изменением файла игры
        answer = QMessageBox.question(
            self,
            "Подтверждение",
            f"Изменить файл?\n{ini_path}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            self.log("Сохранение отменено пользователем")
            return

        try:
            # Если файл только для чтения - снимаем атрибут, чтобы можно было писать
            if os.path.exists(ini_path):
                os.chmod(ini_path, stat.S_IWRITE)

            # Шапка + неизменяемые привязки + сгенерированные бинды режимов
            content = INI_HEADER
            content += f"; ===== {LOCKED_MODE} =====\n"
            content += "\n".join(self.build_locked_lines())
            content += "\n\n"
            content += "\n".join(self.build_ini_lines())

            with open(ini_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Снова ставим параметр «только для чтения»
            os.chmod(ini_path, stat.S_IREAD)

        except PermissionError:
            QMessageBox.critical(
                self,
                APP_NAME,
                "Нет прав на запись в файл.\n"
                "Закройте игру и попробуйте ещё раз."
            )
            self.log("Ошибка сохранения: нет прав на запись")
            return
        except OSError as e:
            QMessageBox.critical(self, APP_NAME, f"Не удалось изменить файл:\n{e}")
            self.log(f"Ошибка сохранения: {e}")
            return

        self.log(f"Бинды сохранены: {ini_path}")
        QMessageBox.information(
            self,
            APP_NAME,
            "Клавиши сохранены. Можете запускать Dead by Daylight."
        )

    # ---------- Сборка строк Input.ini ----------
    def build_locked_lines(self):
        """Строки неизменяемых привязок. Пишутся всегда."""
        lines = []
        for (btype, mapping, ue_key, force) in self.locked_tab.rows_data():
            base = next(b for b in LOCKED_BINDS if b[1] == mapping)
            base_scale = base[2]

            if btype == "axis":
                scale = base_scale * (force if force is not None else DEFAULT_FORCE)
                lines.append(
                    f'AxisMappings=(AxisName="{mapping}",Scale={scale:.6f},Key={ue_key})'
                )
            else:
                lines.append(
                    f'ActionMappings=(ActionName="{mapping}",bShift=False,bCtrl=False,'
                    f'bAlt=False,bCmd=False,Key={ue_key})'
                )
        return lines

    def build_ini_lines(self):
        """Собирает строки биндов по всем режимам."""
        lines = []
        for mode in MODES:
            binds = ACTION_BINDS.get(mode, {})
            rows = self.mode_tabs[mode].rows_data()

            mode_lines = []
            for action, key, force in rows:
                bind = binds.get(action)
                if bind is None:
                    continue
                btype, name, base_scale = bind
                ue_key = KEY_TO_UE.get(key, key)  # наши M5/ЛКМ/Space -> имена движка

                if btype == "axis":
                    scale = base_scale * (force if force is not None else DEFAULT_FORCE)
                    mode_lines.append(
                        f'AxisMappings=(AxisName="{name}",Scale={scale:.6f},Key={ue_key})'
                    )
                else:
                    mode_lines.append(
                        f'ActionMappings=(ActionName="{name}",bShift=False,bCtrl=False,'
                        f'bAlt=False,bCmd=False,Key={ue_key})'
                    )

            lines.append(f"; ===== {mode} =====")
            if mode_lines:
                lines.extend(mode_lines)
            else:
                lines.append("; (нет назначенных клавиш)")
            lines.append("")

        return lines

    # ---------- Сохранение / загрузка конфига ----------
    def save_config(self):
        config = make_config_parser()

        # Общие настройки: согласие и путь
        config[GENERAL_SECTION] = {
            "agreed": "true",
            "game_path": self.ed_path.text().strip(),
            "tutorial_seen": "true" if load_tutorial_seen() else "false",
        }

        # Неизменяемые привязки: силы строк axis (у action силы нет)
        config[LOCKED_MODE] = {}
        for i, (btype, mapping, ue_key, force) in enumerate(self.locked_tab.rows_data()):
            force_str = "" if force is None else f"{force:.1f}"
            config[LOCKED_MODE][f"row_{i}"] = f"{btype}|{mapping}|{ue_key}|{force_str}"

        # Обычные режимы
        for mode, tab in self.mode_tabs.items():
            config[mode] = {}
            for i, (action, key, force) in enumerate(tab.rows_data()):
                # В конфиг клавиша пишется движковым именем (M5 -> ThumbMouseButton2)
                key_ue = KEY_TO_UE.get(key, key)
                force_str = "" if force is None else f"{force:.1f}"
                config[mode][f"row_{i}"] = f"{action}|{key_ue}|{force_str}"

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)

    def load_config(self):
        config = make_config_parser()
        if not config.read(CONFIG_FILE, encoding="utf-8"):
            return

        # Путь к папке игры из прошлого запуска
        if GENERAL_SECTION in config:
            game_path = config.get(GENERAL_SECTION, "game_path", fallback="")
            if game_path:
                self.ed_path.setText(game_path)
                self.log(f"Загружен сохранённый путь: {game_path}")

        # Неизменяемые привязки: восстанавливаем силы строк axis
        if LOCKED_MODE in config:
            forces = []
            for name in config[LOCKED_MODE]:
                try:
                    btype, mapping, key_ue, force = config[LOCKED_MODE][name].split("|", 3)
                except ValueError:
                    continue
                forces.append(force)
            self.locked_tab.set_forces(forces)

        # Обычные режимы
        for mode, tab in self.mode_tabs.items():
            rows = []
            if mode in config:
                for name in config[mode]:
                    try:
                        action, key_ue, force = config[mode][name].split("|", 2)
                    except ValueError:
                        continue
                    # Движковое имя обратно в то, что показываем в программе
                    key = UE_TO_DISPLAY.get(key_ue, key_ue)
                    rows.append((action, key, force if force else None))
            tab.set_rows(rows)

    def closeEvent(self, event):
        self.save_config()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    agreed, _game_path = load_general_settings()

    if agreed:
        # Согласие уже было - предупреждение не показываем
        if load_tutorial_seen():
            # Туториал уже видели - сразу основное окно
            win = MainWindow()
            win.show()
            sys.exit(app.exec())
        else:
            tut = TutorialDialog()
            tut.exec()
            save_tutorial_seen()
            win = MainWindow()
            win.show()
            sys.exit(app.exec())
    else:
        dialog = WarningDialog()
        if dialog.exec() == QDialog.Accepted:
            save_general_settings(True, _game_path)
            # После согласия показываем туториал (если ещё не показывали)
            if not load_tutorial_seen():
                tut = TutorialDialog()
                tut.exec()
                save_tutorial_seen()
            win = MainWindow()
            win.show()
            sys.exit(app.exec())
        else:
            print("Пользователь закрыл окно без согласия")
            sys.exit(0)
