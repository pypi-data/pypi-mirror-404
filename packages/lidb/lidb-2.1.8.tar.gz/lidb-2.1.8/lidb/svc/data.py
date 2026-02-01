# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/10/11 11:01
# Description:

import queue
import time
from collections.abc import Callable

import polars as pl
import threading
import logair

class DataService:

    def __init__(self, cache_size: int = 5):
        self._max_cache_size = cache_size
        self._cache = queue.Queue(maxsize=self._max_cache_size)
        self._cache_dict: dict[str, dict[str, pl.DataFrame]] = dict()  # 用于快速查找的字典
        self.stop_event = threading.Event()
        self._data_thread = None
        self.is_running = False
        self._fn = None

    def put_data(self, key: str, data: dict[str, pl.DataFrame]):
        self._cache.put(key)
        self._cache_dict[key] = data

    def get_data(self) -> pl.DataFrame:
        try:
            key = self._cache.get_nowait()
            data = self._cache_dict.pop(key)
            return key, data, False
        except queue.Empty:
            return "", None, True

    def _data_loading_worder(self,
                             keys: list[str],
                             iter_conf: dict[str, list[str]],):
        logger = logair.get_logger(f"{__name__}.{self.__class__.__name__}.worker")
        logger.info(f"Data loading worker started for {len(keys)} keys.")

        def worker(key, work_id: int):
            result = dict()
            try:
                for name, iters in iter_conf.items():
                    data = self._fn(key=key, iterables=iters)
                    result[name] = data
                self.put_data(key, result)
                logger.info(f"{key}(WorkerID: {work_id}) Loaded data.")
            except Exception as e:
                logger.warning(f"Failed to load data for {key}(WorkerID: {work_id}): {e}")

        for i, k in enumerate(keys):
            worker(key=k, work_id=i + 1)
        self.stop_event.set()

    def start(self,
              fn: Callable,
              keys: list[str],
              iter_conf: dict[str, list[str]],
              max_cache_size: int,):
        """

        Parameters
        ----------
        fn: 获取数据的函数，参数为 key 和 iterables 以及其它参数
        keys
        iter_conf
        max_cache_size

        Returns
        -------

        """
        logger = logair.get_logger(f"{__name__}.{self.__class__.__name__}")
        self._fn = fn
        self._max_cache_size = max_cache_size
        # 先确保之前的服务已经完全停止
        if self.is_running:
            logger.warning("DataService is already running")
            self.stop()
            # return
        # 重新初始化缓存和 stop_event
        self._cache = queue.Queue(maxsize=self._max_cache_size)
        self._cache_dict.clear()
        self.stop_event.clear()

        logger.info(f"Starting DataService({self._max_cache_size}) for {len(keys)} key...")
        # 启动后台数据加载线程
        self._data_thread = threading.Thread(
            target=self._data_loading_worder,
            args=(keys,
                  iter_conf,),
            daemon=True,  # 设置为守护线程，主程序退出时自动结束
        )
        self.is_running = True
        self._data_thread.start()
        logger.info("DataService started successfully.")

    def stop(self):
        """停止数据服务"""
        logger = logair.get_logger(f"{__name__}.{self.__class__.__name__}")
        if not self.is_running:
            logger.warning("Data service is not running")
            return
        logger.info("Stopping data service...")
        self.stop_event.set()
        if self._data_thread and self._data_thread.is_alive():
            self._data_thread.join(timeout=10)
        self.is_running = False
        logger.info("Data service stopped")

    def do(self, consumer: callable, wait_secs: float = 3):
        """
        消费数据
        Parameters
        ----------
        consumer:
        wait_secs

        Returns
        -------

        """
        while self.is_running:
            key, data, is_empty = self.get_data()
            if is_empty:
                if self.stop_event.is_set():
                    self.stop()
                    break
                else:
                    time.sleep(wait_secs)
                    continue
            consumer(dict(key=key, data=data))


D = DataService()