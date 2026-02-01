import time
from datetime import timedelta
from typing import Optional

from ..logger import log, loginf


class ProgressMessage:
    """
    Генератор строки прогресса с метриками: процент завершения, скорость обработки,
    прошедшее и оставшееся время. Поддерживает управляемый лог через log_me().
    """
    
    def __init__(
        self,
        total: int,
        processed: int = 0,
        start_time: Optional[float] = None,
        every: Optional[timedelta] = None,
    ) -> None:
        if total <= 0:
            raise ValueError("Общее количество должно быть положительным целым числом")
        self.total = total
        self.processed = max(0, processed)
        self.start_time = start_time or time.time()
        if not isinstance(every, timedelta):
            raise TypeError("Объект every должен быть timedelta с указанием периодичности")
        self._every_seconds = every.total_seconds() if every is not None else None
        self._last_log_time = self.start_time
        
        # Логируем режим работы
        if self._every_seconds is None:
            loginf("Логирование в режиме каждого вызова")
        else:
            loginf(f"Логирование в режиме периодического вызова ({self._every_seconds:.1f} сек.)")
    
    def update(self, processed: int) -> None:
        self.processed = max(0, min(processed, self.total))
    
    def _duration_str(self, seconds: float) -> str:
        if not isinstance(seconds, (int, float)) or seconds != seconds:  # NaN
            return "∞"
        if seconds == float('inf'):
            return "∞"
        total_seconds = int(seconds)
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}ч{m:02d}м{s:02d}с"
    
    @property
    def msg(self) -> str:
        elapsed = time.time() - self.start_time
        if elapsed <= 0:
            speed = 0.0
            remaining_time = float('inf')
        else:
            speed = self.processed / elapsed
            remaining = self.total - self.processed
            remaining_time = remaining / speed if speed > 0 else float('inf')
        
        percent = (self.processed / self.total) * 100
        remain = self.total - self.processed
        
        percent_str = f"{percent:5.2f}%"
        spd_str = f"{speed:6.3f}"
        et_str = self._duration_str(elapsed)
        rt_str = self._duration_str(remaining_time)
        
        return f" || {self.processed}/{self.total}//{remain} || {percent_str} || IPS: {spd_str} || ET: {et_str} || RT: {rt_str}"
    
    def log_me(self, template: str = "{log}") -> None:
        """
        Логирует сообщение прогресса по заданному шаблону.

        Подстрока `{log}` заменяется на актуальное значение self.msg.
        Логирование происходит:
          - всегда, если processed == total (финальное сообщение),
          - иначе — только если прошло достаточно времени (согласно `every`).

        :param template: Строка, содержащая `{log}`. По умолчанию — "{log}".
        """
        now = time.time()
        is_complete = (self.processed >= self.total)
        
        should_log = (
            is_complete  # Финальное сообщение — обязательно!
            or self._every_seconds is None  # Логировать каждый раз
            or (now - self._last_log_time) >= self._every_seconds  # Прошёл интервал
        )
        
        if should_log:
            message = template.replace("{log}", self.msg)
            log(message)
            self._last_log_time = now
