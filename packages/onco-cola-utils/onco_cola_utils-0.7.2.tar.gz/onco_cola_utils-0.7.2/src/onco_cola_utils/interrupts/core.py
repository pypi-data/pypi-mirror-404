import sys
from typing import Optional

from ..logger.core import logerr, logsuc


def halt(msg: Optional[str] = "Принудительный выход"):
    """Грубое прерывание хода программы"""
    logerr("")
    logerr(msg)
    logerr("")
    sys.exit(0)


def quiet(msg: Optional[str] = "Успешное завершение программы") -> None:
    """Тихое завершение кода программы"""
    logsuc("")
    logsuc(msg)
    logsuc("")
    sys.exit(0)
