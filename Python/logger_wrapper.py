"""
Настройка централизованного логирования для всего проекта.

Класс LoggerWrapper предоставляет готовый экземпляр loguru-логгера с преднастроенными
обработчиками для файла и консоли.

Основные особенности:
- Ежедневная ротация логов (новый файл создаётся каждый день в 00:00)
- Автоматическое архивирование (zip) файлов старше 7 дней
- Хранение последних 45 дней логов (можно изменить через retention)
- Одновременная запись в файл и в консоль (цветная)
- Формат сообщений оптимизирован для читаемости и отладки
- Используются проектные константы: APP_NAME и LOGS_PATH

Пример использования:
    from config.logger import logger

    logger.debug("Подробная отладочная информация")
    logger.info(f"Запущен модуль {__name__}")
    logger.warning("Что-то подозрительное")
    logger.error("Критическая ошибка", exc_info=True)

Настройки можно переопределить при необходимости, создав собственный экземпляр
класса LoggerWrapper с другими параметрами.
"""

import sys
from pathlib import Path

from loguru import logger

from src.config.constants import APP_NAME
from src.config.paths import LOGS_PATH


class LoggerWrapper:
    """
    Обёртка над loguru.Logger для централизованной настройки логирования проекта.
    """

    # ─── Параметры по умолчанию (можно переопределить в наследнике или экземпляре) ───
    DEFAULT_APP_NAME = APP_NAME  # Имя приложения
    DEFAULT_LOGS_DIR = Path(LOGS_PATH)  # Путь к директории логов

    DEFAULT_LEVEL_FILE = "DEBUG"  # Уровень логирования для файлов
    DEFAULT_LEVEL_CONSOLE = "INFO"  # Уровень логирования для консоли

    DEFAULT_RETENTION = "45 days"  # Срок хранения логов
    DEFAULT_ROTATION = "00:00"  # полночь → новый файл каждый день
    DEFAULT_COMPRESSION_DELAY = 7  # архивировать файлы старше 7 дней
    DEFAULT_ENQUEUE = True  # очередь — безопасно для потоков и процессов

    FILE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name: <35} | {function: <20} | {line: >4} | "
        "{message}"
    )

    CONSOLE_FORMAT = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    def __init__(self):
        """
        Инициализация логгера.

        Все параметры опциональны — используются значения по умолчанию класса.
        """
        self.logger = logger

        # Удаляем стандартный обработчик
        self.logger.remove()

        # Подготовка и настройка
        self._ensure_logs_directory()
        self._configure_file_handler()
        self._configure_console_handler()

    def _ensure_logs_directory(self) -> None:
        """Создаёт директорию для логов, если она ещё не существует."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _configure_file_handler(self) -> None:
        """Настраивает файловый обработчик с ротацией и архивированием."""
        file_path = self.logs_dir / f"{self.app_name}_{{time:YYYY-MM-DD}}.log"

        self.logger.add(
            sink=str(file_path),
            rotation=self.DEFAULT_ROTATION,
            retention=self.DEFAULT_RETENTION,
            compression="zip",
            compression_delay=self.DEFAULT_COMPRESSION_DELAY,
            level=self.DEFAULT_LEVEL_FILE,
            encoding="utf-8",
            enqueue=self.DEFAULT_ENQUEUE,
            backtrace=True,
            diagnose=False,
            format=self.FILE_FORMAT,
        )

    def _configure_console_handler(self) -> None:
        """Настраивает цветной консольный вывод."""
        self.logger.add(
            sink=sys.stderr,
            level=self.DEFAULT_LEVEL_CONSOLE,
            colorize=True,
            format=self.CONSOLE_FORMAT,
        )

    def __getattr__(self, name):
        """Проксируем все методы и атрибуты к внутреннему loguru-логгеру."""
        return getattr(self.logger, name)


# Глобальный экземпляр для удобного импорта
logger = LoggerWrapper()
