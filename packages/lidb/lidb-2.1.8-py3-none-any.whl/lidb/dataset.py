# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/10/27 14:13
# Description:

from __future__ import annotations

import shutil
import sys
import warnings
from collections import defaultdict
from enum import Enum
from functools import partial
from typing import Callable, Literal

import logair
import pandas as pd
import polars as pl
import polars.selectors as cs
import xcals
import ygo
from varname import varname

from .database import put, tb_path, scan, DB_PATH
from .parse import parse_hive_partition_structure
import inspect

DEFAULT_DS_PATH = DB_PATH / "datasets"

class InstrumentType(Enum):
    STOCK = "Stock"  # 股票
    ETF = "ETF"  #
    CB = "ConvertibleBond"  # 可转债


def complete_data(fn, date, save_path, partitions):
    logger = logair.get_logger(__name__)
    try:
        data = fn()
        if data is None:
            # 保存数据的逻辑在fn中实现了
            return
        # 剔除以 `_` 开头的列
        data = data.select(~cs.starts_with("_"))
        if not isinstance(data, (pl.DataFrame, pl.LazyFrame)):
            logger.error(f"{save_path}: Result of dataset.fn must be polars.DataFrame or polars.LazyFrame.")
            return
        if isinstance(data, pl.LazyFrame):
            data = data.collect()
        cols = data.columns
        if "date" not in cols:
            data = data.with_columns(pl.lit(date).alias("date")).select("date", *cols)
        else:
            data = data.cast({"date": pl.Utf8})
        data = data.filter(date=date)
        if "time" in data.columns:
            if data["time"].n_unique() < 2:
                data = data.drop("time")
        put(data, save_path, partitions=partitions)
    except Exception as e:
        logger.error(f"{save_path}: Error when complete data for {date}\n", exc_info=e)


class Dataset:

    def __init__(self,
                 *depends: Dataset,
                 fn: Callable[..., pl.DataFrame | pl.LazyFrame],
                 tb: str = "",
                 update_time: str = "",
                 window: str = "1d",
                 partitions: list[str] = None,
                 is_hft: bool = False,
                 data_name: str = "",
                 frame: int = 1):
        """

        Parameters
        ----------
        depends: Dataset
            底层依赖数据集
        fn: str
            数据集计算函数。如果要用到底层依赖数据集，则必须显示定义形参 `depend`
        tb: str
            数据集保存表格, 如果没有指定，默认 {lidb.DB_PATH}/datasets/<module>
        update_time: str
            更新时间: 默认没有-实时更新，也就是可以取到当天值
            更新时间只允许三种情况：
            - 1. 盘前时间点：比如 08:00:00, 09:00:00, 09:15:00 ...
            - 2. 盘中时间点：归为实时更新，使用空值 ""
            - 3. 盘后时间点：比如 15:00:00, 16:30:00, 20:00:00 ...
        partitions: list[str]
            分区: 如果指定为 None, 则自动从 fn 参数推断，如果不需要分区，应该将其设定为空列表: []
        is_hft: bool
            是否是高频数据，如果是，则会按照asset进行分区存储，默认 False
            hft定义为：时间步长 < 1min
        window: str
            配合depends使用，在取depends时，会回看window周期，最小单位为`d`。不足 `d` 的会往上取整为`1d`
        data_name: str
            数据名，默认为空，会自动推断，如果指定了，则使用指定名
        frame: int
            用于自动推断 数据名
        """
        self._depends = list(depends)
        self._name = ""
        self.fn = fn
        self.fn_params_sig = ygo.fn_signature_params(fn)
        self._is_depend = "depend" in self.fn_params_sig and len(self._depends) > 0
        self._is_hft = is_hft
        self._frame = frame
        self.data_name = data_name
        if not self.data_name:
            try:
                self.data_name = varname(frame, strict=False)
            except Exception as e:
                pass
        if self.data_name:
            self.data_name = self.data_name.replace('ds_', '')
        fn_params = ygo.fn_params(self.fn)
        self.fn_params = {k: v for (k, v) in fn_params}
        # 更新底层依赖数据集的同名参数
        self._update_depends()

        if pd.Timedelta(window).days < 1:
            window = "1d"
        window_td = pd.Timedelta(window)
        self._window = window
        self._days = window_td.days
        if window_td.seconds > 0:
            self._days += 1
        # 检测是否高频数据：如果是高频数据，则按照标的进行分区，高频的定义为时间差 < 60s
        self._append_partitions = ["asset", "date"] if is_hft else ["date", ]
        if partitions is not None:
            partitions = [k for k in partitions if k not in self._append_partitions]
            partitions = [*partitions, *self._append_partitions]
        else:
            # partitions = self._append_partitions
            exclude_partitions = ["this", "depend"]
            partitions = [k for k in self.fn_params_sig if k not in self._append_partitions and k not in exclude_partitions]
            partitions = [*partitions, *self._append_partitions]
        self.partitions = partitions
        self._type_asset = "asset" in self.fn_params_sig
        mod = inspect.getmodule(fn)
        self._tb = tb
        self.tb = tb if tb else DEFAULT_DS_PATH / mod.__name__ /f"{self.data_name}"
        self.save_path = tb_path(self.tb)
        self.constraints = dict()
        for k in self.partitions[:-len(self._append_partitions)]:
            if k in self.fn_params:
                v = self.fn_params[k]
                if isinstance(v, (list, tuple)) and not isinstance(v, str):
                    v = sorted(v)
                self.constraints[k] = v
                self.save_path = self.save_path / f"{k}={v}"

        if "09:30:00" < update_time < "15:00:00":
            update_time = ""
        # self.update_time = update_time
        # 根据底层依赖调整update_time
        if self._depends:
            has_rt = any([not ds.update_time for ds in self._depends]) # 存在实时依赖
            dep_uts = [ds.update_time for ds in self._depends if ds.update_time]
            max_ut = max(dep_uts) if dep_uts else ""

            if update_time:
                if max_ut:
                    if not has_rt:
                        update_time = max(max_ut, update_time)
                    else:
                        # 存在实时依赖
                        if max_ut >= "15:00:00":
                            update_time = max(max_ut, update_time)
                        else:
                            # 存在实时依赖并且没有盘后依赖
                            if update_time <= "09:30:00":
                                # 修复盘前更新时间
                                update_time = ""
                else:
                    # 依赖都是实时依赖
                    if not has_rt:
                        warnings.warn(f"{self.data_name}:{self.save_path} 更新时间推断错误", UserWarning)
                        sys.exit()
                    else:
                        if update_time <= "09:30:00":
                            # 修复盘前更新时间
                            update_time = ""
            else:
                # 最顶层是实时数据:
                # 需要修复的情况: 存在盘后依赖
                if max_ut >= "15:00:00":
                    # 盘后依赖：修复
                    update_time = max_ut

        self.update_time = update_time
        self.fn = ygo.delay(self.fn)(this=self)

    def _update_depends(self):
        new_deps = list()
        for dep in self._depends:
            new_dep = dep(**self.fn_params).alias(dep._name)
            new_deps.append(new_dep)
        self._depends = new_deps

    def is_empty(self, path) -> bool:
        return not any(path.rglob("*.parquet"))

    def __call__(self, *depends, **fn_kwargs):
        """赋值时也会同步更新底层依赖数据集的同名参数"""
        if "data_name" in fn_kwargs:
            data_name = fn_kwargs.pop("data_name")
        else:
            data_name = self.data_name
        window = fn_kwargs.get("window", self._window)
        fn = ygo.delay(self.fn)(**fn_kwargs)
        depends = depends or self._depends
        ds = Dataset(*depends,
                     fn=fn,
                     tb=self._tb,
                     partitions=self.partitions,
                     update_time=self.update_time,
                     is_hft=self._is_hft,
                     window=window,
                     data_name=data_name,
                     frame=self._frame+1)
        return ds

    def alias(self, new_name: str):
        self._name = new_name
        return self

    def get_value(self,
                  date,
                  eager: bool = True,
                  backend: Literal["threading", "multiprocessing", "loky"] = "loky",
                  **constraints):
        """
        取值: 不保证未来数据
        Parameters
        ----------
        date: str
            取值日期
        eager: bool
        backend:  Literal["threading", "multiprocessing", "loky"]
            获取依赖因子并发后端
        constraints: dict
            取值的过滤条件

        Returns
        -------

        """
        logger = logair.get_logger(f"{__name__}.{self.__class__.__name__}")
        _constraints = {k: v for k, v in constraints.items() if k in self.partitions}
        _limits = {k: v for k, v in constraints.items() if k not in self.partitions}
        search_path = self.save_path
        for k, v in _constraints.items():
            if isinstance(v, (list, tuple)) and not isinstance(v, str):
                v = sorted(v)
            search_path = search_path / f"{k}={v}"
        search_path = search_path / f"date={date}"

        # 处理空文件
        for file_path in search_path.rglob("*.parquet"):
            if file_path.stat().st_size == 0:
                # 删除
                logger.warning(f"{file_path}: Deleting empty file.")
                file_path.unlink()

        if not self.is_empty(search_path):
            lf = scan(search_path).cast({"date": pl.Utf8})
            try:
                schema = lf.collect_schema()
            except:
                logger.warning(f"{search_path}: Failed to collect schema.")
                # 删除该文件夹
                shutil.rmtree(search_path)
                return self.get_value(date=date, eager=eager, **constraints)
            _limits = {k: v for k, v in constraints.items() if schema.get(k) is not None}
            lf = lf.filter(date=date, **_limits)
            if not eager:
                return lf
            data = lf.collect()
            if not data.is_empty():
                return data

        days = self.constraints.get("days", constraints.get("days", self._days))
        if self._depends:
            # 先补齐depend
            _beg_date = date
            if days > 1:
                _beg_date = xcals.shift_tradeday(date, -(days-1))
            _depend_dates = xcals.get_tradingdays(_beg_date, date)
            for depend in self._depends:
                depend.get_history(_depend_dates, eager=False, backend=backend)

        fn = self.fn
        save_path = self.save_path
        if self._is_depend:
            fn = partial(fn, depend=self.get_dependsPIT(date, days=days, backend=backend))
        else:
            fn = partial(fn, date=date)
        if self._type_asset:
            if "asset" in _constraints:
                fn = ygo.delay(self.fn)(asset=_constraints["asset"])
        if len(self.constraints) < len(self.partitions) - len(self._append_partitions):
            # 如果分区指定的字段没有在Dataset定义中指定，需要在get_value中指定
            params = dict()
            for k in self.partitions[:-len(self._append_partitions)]:
                if k not in self.constraints:
                    v = constraints[k]
                    params[k] = v
                    save_path = save_path / f"{k}={v}"
            fn = ygo.delay(self.fn)(**params)

        today = xcals.today()
        now = xcals.now()
        if (date > today) or (date == today and now < self.update_time):
            logger.warning(f"{self.tb}: {date} is not ready, waiting for {self.update_time}")
            return
        complete_data(fn, date, save_path, self._append_partitions)

        lf = scan(search_path).cast({"date": pl.Utf8})
        schema = lf.collect_schema()
        _limits = {k: v for k, v in constraints.items() if schema.get(k) is not None}
        lf = lf.filter(date=date, **_limits)
        if not eager:
            return lf
        return lf.collect()

    def get_pit(self, date: str, query_time: str, eager: bool = True, **contraints):
        """取值：如果取值时间早于更新时间，则返回上一天的值"""
        if not self.update_time:
            return self.get_value(date, **contraints)
        val_date = date
        if query_time < self.update_time:
            val_date = xcals.shift_tradeday(date, -1)
        return self.get_value(val_date, eager=eager, **contraints).with_columns(date=pl.lit(date), )

    def get_history(self,
                    dateList: list[str],
                    n_jobs: int = 11,
                    backend: Literal["threading", "multiprocessing", "loky"] = "loky",
                    eager: bool = True,
                    rep_asset: str = "000001",  # 默认 000001
                    **constraints):
        """获取历史值: 不保证未来数据"""
        _constraints = {k: v for k, v in constraints.items() if k in self.partitions}
        search_path = self.save_path
        for k, v in _constraints.items():
            if isinstance(v, (list, tuple)) and not isinstance(v, str):
                v = sorted(v)
            search_path = search_path / f"{k}={v}"
        if self.is_empty(search_path):
            # 需要补全全部数据
            missing_dates = dateList
        else:
            if not self._type_asset:
                _search_path = self.save_path
                for k, v in _constraints.items():
                    if k != "asset":
                        _search_path = _search_path / f"{k}={v}"
                    else:
                        _search_path = _search_path / f"asset={rep_asset}"
                hive_info = parse_hive_partition_structure(_search_path)
            else:
                hive_info = parse_hive_partition_structure(search_path)
            exist_dates = hive_info["date"].to_list()
            missing_dates = set(dateList).difference(set(exist_dates))
            missing_dates = sorted(list(missing_dates))
        if missing_dates:
            days = self.constraints.get("days", constraints.get("days", self._days))
            # 先逐个补齐 depends
            if self._depends:
                _end_date = max(missing_dates)
                _beg_date = min(missing_dates)
                if days > 1:
                    _beg_date = xcals.shift_tradeday(_beg_date, -(days-1))
                _depend_dates = xcals.get_tradingdays(_beg_date, _end_date)
                for depend in self._depends:
                    depend.get_history(_depend_dates, eager=False, backend=backend)

            fn = self.fn
            save_path = self.save_path

            if self._type_asset:
                if "asset" in _constraints:
                    fn = ygo.delay(self.fn)(asset=_constraints["asset"])

            if len(self.constraints) < len(self.partitions) - len(self._append_partitions):
                params = dict()
                for k in self.partitions[:-len(self._append_partitions)]:
                    if k not in self.constraints:
                        v = constraints[k]
                        params[k] = v
                        save_path = save_path / f"{k}={v}"
                fn = ygo.delay(self.fn)(**params)

            with ygo.pool(n_jobs=n_jobs, backend=backend) as go:
                info_path = self.save_path
                try:
                    info_path = info_path.relative_to(DB_PATH)
                except:
                    pass
                if self._is_depend:
                    with ygo.pool(n_jobs=n_jobs, show_progress=False) as _go:
                        for date in missing_dates:
                            _go.submit(self.get_dependsPIT, job_name="preparing depend")(date=date, days=days, backend=backend)
                        for (date, depend) in zip(missing_dates, _go.do()):
                            fn = partial(fn, depend=depend)
                            go.submit(complete_data,
                                      job_name=f"Completing",
                                      postfix=info_path,
                                      leave=False)(fn=fn,
                                                   date=date,
                                                   save_path=save_path,
                                                   partitions=self._append_partitions, )
                else:
                    for date in missing_dates:
                        fn = partial(fn, date=date)
                        go.submit(complete_data,
                                  job_name=f"Completing",
                                  postfix=info_path,
                                  leave=False)(fn=fn,
                                               date=date,
                                               save_path=save_path,
                                               partitions=self._append_partitions, )
                go.do()
        data = scan(search_path, ).cast({"date": pl.Utf8}).filter(pl.col("date").is_in(dateList), **constraints)
        data = data.sort("date")
        if eager:
            return data.collect()
        return data

    def get_dependsPIT(self,
                       date: str,
                       days: int,
                       backend: Literal["threading", "multiprocessing", "loky"] = "loky",
                       depends: list[Dataset] | None = None) -> pl.LazyFrame | None:
        """获取依赖数据集"""
        if not depends and not self._depends:
            return None
        end_date = date
        beg_date = date
        if days > 1:
            beg_date = xcals.shift_tradeday(beg_date, -(days-1))
        depends = depends or self._depends
        params = {
            "ds_conf": dict(depend=depends),
            "beg_date": beg_date,
            "end_date": end_date,
            "times": [self.update_time, ],
            "show_progress": False,
            "eager": False,
            "n_jobs": 1,
            "backend": backend,
            "process_time": False,  # 不处理时间
        }
        res = load_ds(**params)
        return res["depend"]


def loader(data_name: str,
           ds: Dataset,
           date_list: list[str],
           prev_date_list: list[str],
           prev_date_mapping: dict[str, str],
           time: str,
           process_time: bool,
           **constraints) -> pl.LazyFrame:
    """
    Parameters
    ----------
    data_name
    ds
    date_list
    prev_date_list
    prev_date_mapping
    time
    process_time: bool
        是否处理源数据的时间: 根据实参 time. 用于应对不同场景
        场景1：依赖因子不处理，底层数据是什么就返回什么
        场景2：zoo.load 用来加载测试日内不同时间点的数据，就应该处理
    constraints

    Returns
    -------

    """
    if time:
        if time < ds.update_time:
            if len(prev_date_list) > 1:
                lf = ds.get_history(prev_date_list, eager=False, **constraints)
            else:
                lf = ds.get_value(prev_date_list[0], eager=False, **constraints)
        else:
            if len(date_list) > 1:
                lf = ds.get_history(date_list, eager=False, **constraints)
            else:
                lf = ds.get_value(date_list[0], eager=False, **constraints)
    else:
        if ds.update_time > "09:30:00":
            # 盘后因子：取上一天的值
            if len(prev_date_list) > 1:
                lf = ds.get_history(prev_date_list, eager=False, **constraints)
            else:
                lf = ds.get_value(prev_date_list[0], eager=False, **constraints)
        else:
            if len(date_list) > 1:
                lf = ds.get_history(date_list, eager=False, **constraints)
            else:
                lf = ds.get_value(date_list[0], eager=False, **constraints)

    schema = lf.collect_schema()
    include_time = schema.get("time") is not None
    if process_time and time:
        if include_time:
            lf = lf.filter(time=time)
        else:
            lf = lf.with_columns(time=pl.lit(time))
    if time < ds.update_time:
        lf = lf.with_columns(date=pl.col("date").replace(prev_date_mapping))
    keep = {"date", "time", "asset"}
    if ds._name:
        columns = lf.collect_schema().names()
        rename_cols = set(columns).difference(keep)
        if len(rename_cols) > 1:
            lf = lf.rename({k: f"{ds._name}.{k}" for k in rename_cols})
        else:
            lf = lf.rename({k: ds._name for k in rename_cols})
    return data_name, lf


def load_ds(ds_conf: dict[str, list[Dataset]],
            beg_date: str,
            end_date: str,
            times: list[str],
            n_jobs: int = 11,
            backend: Literal["threading", "multiprocessing", "loky"] = "loky",
            show_progress: bool = True,
            eager: bool = False,
            process_time: bool = True,
            **constraints) -> dict[str, pl.DataFrame | pl.LazyFrame]:
    """
    加载数据集
    Parameters
    ----------
    ds_conf: dict[str, list[Dataset]]
        数据集配置: key-data_name, value-list[Dataset]
    beg_date: str
        开始日期
    end_date: str
        结束日期
    times: list[str]
        取值时间
    n_jobs: int
        并发数量
    backend: str
    show_progress: bool
    eager: bool
        是否返回 DataFrame
        - True: 返回DataFrame
        - False: 返回LazyFrame
    process_time: bool
        是否处理源数据的时间: 根据实参 time. 用于应对不同场景
        场景1：依赖因子不处理，底层数据是什么就返回什么
        场景2：zoo.load 用来加载测试日内不同时间点的数据，就应该处理
    constraints
        限制条件，比如 asset='000001'
    Returns
    -------
    dict[str, polars.DataFrame | polars.LazyFrame]
        - key: data_name
        - value: polars.DataFrame

    """
    if beg_date > end_date:
        raise ValueError("beg_date must be less than end_date")
    date_list = xcals.get_tradingdays(beg_date, end_date)
    beg_date, end_date = date_list[0], date_list[-1]
    prev_date_list = xcals.get_tradingdays(xcals.shift_tradeday(beg_date, -1),
                                           xcals.shift_tradeday(end_date, -1))
    prev_date_mapping = {prev_date: date_list[i] for i, prev_date in enumerate(prev_date_list)}
    results = defaultdict(list)
    index = ("date", "time", "asset")
    _index = ("date", "asset")
    with ygo.pool(n_jobs=n_jobs,
                  backend=backend,
                  show_progress=show_progress) as go:
        for data_name, ds_list in ds_conf.items():
            for ds in ds_list:
                _data_name = f"{data_name}:{ds.tb}"
                if ds._name:
                    _data_name += f".alias({ds._name})"
                for time in times:
                    go.submit(loader,
                              job_name="Loading",
                              postfix=data_name, )(data_name=_data_name,
                                                   ds=ds,
                                                   date_list=date_list,
                                                   prev_date_list=prev_date_list,
                                                   prev_date_mapping=prev_date_mapping,
                                                   time=time,
                                                   process_time=process_time,
                                                   **constraints)
        for name, lf in go.do():
            results[name].append(lf)
    # _LFs = {
    # name: (pl.concat(lfList, )
    # .select(*index,
    # cs.exclude(index))
    # )
    # for name, lfList in results.items()}
    _LFs_with_time = {}
    _LFs_without_time = {}
    for name, lfList in results.items():
        lf = pl.concat(lfList)
        # print(lf)
        if "time" not in lf.collect_schema().names():
            _LFs_without_time[name] = lf
        else:
            _LFs_with_time[name] = lf
    LFs_with_time = defaultdict(list)
    LFs_without_time = defaultdict(list)
    for name, lf in _LFs_with_time.items():
        dn, _ = name.split(":")
        LFs_with_time[dn].append(lf)
    for name, lf in _LFs_without_time.items():
        dn, _ = name.split(":")
        LFs_without_time[dn].append(lf)
    LFs_with_time = {
        name: (pl.concat(lfList, how="align")
               .sort(index)
               .select(*index,
                       cs.exclude(index))
               )
        for name, lfList in LFs_with_time.items()}
    LFs_without_time = {
        name: (pl.concat(lfList, how="align")
               .sort(_index)
               .select(*_index,
                       cs.exclude(_index))
               )
        for name, lfList in LFs_without_time.items()}
    dns = list(LFs_with_time.keys()) if LFs_with_time else list(LFs_without_time.keys())
    LFs = dict()
    for dn in dns:
        _lf_with_time = LFs_with_time.get(dn)
        _lf_without_time = LFs_without_time.get(dn)
        if _lf_with_time is not None:
            LFs[dn] = _lf_with_time
            if _lf_without_time is not None:
                LFs[dn] = LFs[dn].join(_lf_without_time, on=["date", "asset"], how="left")
        else:
            LFs[dn] = _lf_without_time
    if not eager:
        return LFs
    return {
        name: lf.collect()
        for name, lf in LFs.items()
    }

class DataLoader:

    def __init__(self, name: str):
        self._name = name
        self._index: tuple[str] = ("date", "time", "asset")
        self._df: pl.LazyFrame | pl.DataFrame = None
        self._all_df: pl.LazyFrame | pl.DataFrame = None
        # self._db: QDF = None

    def get(self,
            ds_list: list[Dataset],
            beg_date: str,
            end_date: str,
            times: list[str],
            eager: bool = False,
            n_jobs: int = -1,
            backend: Literal["threading", "multiprocessing", "loky"] = "loky",
            **constraints):
        """
        添加数据集
        Parameters
        ----------
        ds_list: list[Dataset]
        beg_date: str
        end_date: str
        times: list[str]
            加载的时间列表
        eager: bool
        n_jobs: int
        backend: str
        constraints

        Returns
        -------

        """
        lf = load_ds(ds_conf={self._name: ds_list},
                     beg_date=beg_date,
                     end_date=end_date,
                     n_jobs=n_jobs,
                     backend=backend,
                     times=times,
                     eager=eager,
                     process_time=True,
                     **constraints)
        self._df = lf[self._name]
        self.add_data(self._df)

    @property
    def name(self) -> str:
        return self._name

    @property
    def data(self) -> pl.DataFrame | None:
        """返回数据"""
        if isinstance(self._df, pl.LazyFrame):
            self._df = self._df.collect()
        return self._df

    @property
    def all_data(self) -> pl.DataFrame | None:
        if isinstance(self._all_df, pl.LazyFrame):
            self._all_df = self._all_df.collect()
        return self._all_df

    def add_data(self, df: pl.DataFrame | pl.LazyFrame):
        """添加dataframe, index 保持为原有的 _df.index"""
        if self._all_df is None:
            self._all_df = df
        else:
            self._all_df = pl.concat([self._all_df.lazy(), df.lazy()], how="align").sort(self._index)
