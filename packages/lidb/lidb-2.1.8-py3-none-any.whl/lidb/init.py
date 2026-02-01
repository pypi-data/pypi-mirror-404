# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/7/17 14:40
# Description:

from pathlib import Path
from dynaconf import Dynaconf
import logair
import os


USERHOME = Path("~").expanduser() # 用户家目录
NAME = "lidb"
DB_PATH = USERHOME / NAME
CONFIG_PATH = USERHOME / ".config" / NAME / "settings.toml"

logger = logair.get_logger(NAME)


if not CONFIG_PATH.exists():
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create settings file: {e}")
    with open(CONFIG_PATH, "w") as f:
        template_content = f'[GLOBAL]\npath="{DB_PATH}"\n\n[POLARS]\nmax_threads=32\n'
        f.write(template_content)
    logger.info(f"Settings file created: {CONFIG_PATH}")

def get_settings():
    try:
        return Dynaconf(settings_files=[CONFIG_PATH])
    except Exception as e:
        logger.error(f"Read settings file failed: {e}")
        return {}

# 读取配置文件覆盖
_settiings = get_settings()
if _settiings is not None:
    setting_db_path = _settiings.get(f"global.path", "")
    # 配置 polars
    setting_polars_threads = _settiings.get("polars.max_threads", 32)
    os.environ["POLARS_MAX_THREADS"] = str(setting_polars_threads)
    if setting_db_path:
        DB_PATH = Path(setting_db_path)
