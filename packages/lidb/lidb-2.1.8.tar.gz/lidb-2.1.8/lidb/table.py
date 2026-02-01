# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/11/10 13:43
# Description: 只有一张表单，没有分区的dataset特例, 所有数据都在一张表中

from __future__ import annotations

import sys
from collections.abc import Callable
from enum import Enum

import xcals
from functools import partial
import polars as pl
from datetime import datetime
import logair
import uuid
from .database import tb_path, scan

import ygo


class TableMode(Enum):

    F = "full" # 全量更新
    I = "increment" # 增量更新

class Table:

    def __init__(self,
                 fn: Callable[..., pl.DataFrame],
                 tb: str,
                 update_time: str,
                 mode: TableMode = TableMode.F):
        self.fn = fn
        self.tb = tb
        self.update_time = update_time
        self._data_dir = tb_path(self.tb)
        self.logger = logair.get_logger(__name__)
        self.verbose = False
        self.mode = mode

    def __call__(self, *args, **kwargs):
        fn = partial(self.fn, *args, **kwargs)
        table = Table(fn,
                      tb=self.tb,
                      update_time=self.update_time,
                      mode=self.mode)
        return table

    def _log(self, msg: str, lvl: str = "info"):
        """统一日志输出方法"""
        if self.verbose:
            getattr(self.logger, lvl)(f"{self.tb}: {msg}")

    def _do_job(self):
        """获取数据并且保存数据"""
        data = ygo.delay(self.fn)(this=self)()
        if data is None:
            self.logger.error(f"{self.tb}: No data.")
            return
        if data.is_empty():
            self.logger.warning(f"{self.tb}: No data.")
            return
        if self.mode == TableMode.I:
            time_uuid = uuid.uuid1()
            data_file = self._data_dir / f"{time_uuid}.parquet"
            data.write_parquet(data_file)
        elif self.mode == TableMode.F:
            data_file = self._data_dir / "0.parquet"
            data.write_parquet(data_file)
        else:
            self.logger.error(f"Invalid table mode: {self.mode}")


    def update(self, verbose: bool = False):
        """更新最新数据: 全量更新, 覆盖旧数据"""
        self.verbose = verbose
        if self._need_update(date=xcals.today()):
            self._log("Updating.", "info")
            self._do_job()

    def _need_update(self, date: str) -> bool:
        """是否需要更新"""
        existed = self._data_dir.exists()
        if not existed:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            return True
        else:
            modified_time = self.modified_time
            if modified_time is not None:
                modified_datetime = modified_time.strftime("%Y-%m-%d %H:%M:%S")
                modified_d, modified_t = modified_datetime.split(" ")
                if self._updated(date, data_date=modified_d, data_time=modified_t):
                    return False
            return True

    def get_value(self, date: str, eager: bool = True) -> pl.DataFrame | pl.LazyFrame:
        """获取数据"""
        # self.update(verbose=True)
        if not date:
            date = xcals.today()
        self.verbose = True
        if self._need_update(date):
            self._log("Update first plz.", "warning")
            sys.exit()

        df = scan(self._data_dir)
        if eager:
            return df.collect()
        return df

    def _updated(self, date: str, data_date: str, data_time: str) -> bool:
        """判断是否已经更新数据"""
        recent_tradeday = xcals.get_recent_tradeday(date)
        prev_tradeday = xcals.shift_tradeday(recent_tradeday, -1)
        now = xcals.now()
        latest_update_date = recent_tradeday if now >= self.update_time else prev_tradeday
        return f"{data_date} {data_time}" >= f"{latest_update_date} {self.update_time}"

    @property
    def latest_file(self):
        if not self._data_dir.exists():
            return
        parquet_files = list(self._data_dir.glob("*.parquet"))
        if not parquet_files:
            return
        latest_file = max(parquet_files, key=lambda x: x.stat().st_mtime)
        return latest_file

    @property
    def modified_time(self):
        """获取文件修改时间"""
        latest_file = self.latest_file
        if latest_file is None:
            return
        mtime = self.latest_file.stat().st_mtime
        return datetime.fromtimestamp(mtime)
