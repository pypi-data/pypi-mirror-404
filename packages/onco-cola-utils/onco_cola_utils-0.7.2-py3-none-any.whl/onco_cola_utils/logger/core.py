"""ЯДРО"""

import sys

from loguru import logger


logger.remove()

logger.level("WARNING", color="<light-yellow>")  # светло-жёлтый (более яркий)

# Обработчики для всех уровней
for level in ["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR"]:
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <level>{message}</level>",
        level=level,
        filter=lambda record, lvl=level: record["level"].name == lvl,
        colorize=True
    )

# Алиасы
log = logger.debug
loginf = logger.info
logsuc = logger.success
logwarn = logger.warning
logerr = logger.error