# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2025/3/5 21:40
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""
from __future__ import annotations

import importlib.util
import inspect
import sys
from functools import partial
from pathlib import Path

import logair
import polars as pl
from tqdm.auto import tqdm

from .errors import CompileError, FailError
from .expr import Expr
from .expr import build_dependency_graph, topological_sort

# 动态加载模块
module_name = "udf"
module_path = Path(__file__).parent / "udf" / "__init__.py"
spec = importlib.util.spec_from_file_location(module_name, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[module_name] = module
spec.loader.exec_module(module)

logger = logair.get_logger(__name__)


class QDF:

    def __init__(self,
                 data: pl.LazyFrame | pl.DataFrame,
                 index: tuple[str] = ("date", "time", "asset"),
                 align: bool = True, ):
        assert isinstance(data, (pl.LazyFrame, pl.DataFrame)), "data must be a polars DataFrame or LazyFrame"
        self.data: pl.LazyFrame = (data
                                   .lazy()
                                   .cast({pl.Decimal: pl.Float64})
                                   .fill_nan(None)
                                   .drop_nulls(subset=index)
                                   .sort(index))
        self.data: pl.DataFrame = self.data.collect()

        self._index: pl.DataFrame = self.data.select(index)
        self.dims = [self._index[name].n_unique() for name in index]

        index_greater_than_one = [index[i] for i, dim in enumerate(self.dims) if dim > 1]
        index_one = [index[i] for i, dim in enumerate(self.dims) if dim == 1]

        if align:
            lev_vals: list[pl.DataFrame] = [self._index.select(name).unique(maintain_order=True) for name in
                                            index_greater_than_one]
            full_index = lev_vals[0]
            for lev_val in lev_vals[1:]:
                full_index = full_index.join(lev_val, how="cross", maintain_order="left")
            self.data = full_index.join(self.data, on=index_greater_than_one, how='left', maintain_order="left")
            if index_one:
                self.data = self.data.with_columns(*[pl.lit(self._index[name][0]).alias(name) for name in index_one])

        self.failed = list()
        self._cols = set(self.data.columns)
        self._expr_cache = dict()  # {expr: pl.col(expr.alias)}
        self._cur_batch_expr_cache = dict()
        # self._alias_expr_map = defaultdict(pl.Expr) # {alias: pl.col(ref:alias)}
        self._fn_map = dict()

    def __str__(self):
        return self.data.__str__()

    def __repr__(self):
        return self.data.__str__()

    def register_udf(self, func: callable, name: str = None):
        name = name if name is not None else func.__name__
        setattr(module, name, func)

    def _to_pl_expr(self, e: Expr) -> pl.Expr:
        alias = e.alias
        if alias in self._cols:
            return pl.col(alias)
        elif e in self._expr_cache:
            return self._expr_cache[e].alias(alias)
        else:
            func = self._fn_map.get(e.fn_name)
            if func is None:
                func = getattr(module, e.fn_name)
                _params = sorted(list(inspect.signature(func).parameters.keys()))
                if "dims" in _params:
                    func = partial(func, dims=self.dims)
                self._fn_map[e.fn_name] = func
            args = list()
            kwargs = dict()
            for arg in e.args:
                if isinstance(arg, Expr):
                    args.append(self._expr_cache[arg])
                    # else:
                    # 拓扑解析依赖结构出错
                elif isinstance(arg, dict):
                    kwargs.update(arg)
                elif isinstance(arg, str):
                    if arg.lower() == "null":
                        args.append(None)
                    else:
                        args.append(pl.col(arg))
                else:
                    args.append(arg)  # or args.append(pl.lit(arg))
            try:
                expr_pl: pl.Expr = func(*args, **kwargs)
                self._cur_batch_expr_cache[e] = pl.col(alias)
                return expr_pl.alias(alias)
            except Exception as error:
                raise CompileError(message=f"{e.fn_name}({', '.join([str(arg) for arg in args])})\n{error}") from error

    def sql(self, *exprs: str, show_progress: bool = False, leave: bool = False) -> pl.DataFrame:
        """
        表达式查询
        Parameters
        ----------
        exprs: str
            表达式，比如 "ts_mean(close, 5) as close_ma5"
        show_progress: bool
            是否展示进度条
        leave: bool
            是否保留进度条
        Returns
        -------
            polars.DataFrame
        """
        self.failed = list()
        exprs_parsed = list()
        for expr in exprs:
            try:
                e_parsed = Expr(expr)
                exprs_parsed.append(e_parsed)
            except Exception as e:
                self.failed.append(FailError(expr, e))
        if self.failed:
            logger.warning(f"sql failed num：{len(self.failed)}/{len(exprs)}: \n {self.failed}")
        graph, indegree, expr_map = build_dependency_graph(exprs_parsed, self._cols)
        lvls: list[list[Expr]] = topological_sort(graph, indegree, expr_map)
        pbar = None
        lvl_num = len(lvls)
        if show_progress:
            pbar = tqdm(total=lvl_num, desc=f"{len(exprs)}", leave=leave)
        for i, batch_exprs in enumerate(lvls):
            if show_progress:
                pbar.set_postfix_str(f"level-{i + 1}:{len(batch_exprs)}")
            batch_exprs = [self._to_pl_expr(e) for e in batch_exprs]
            self.data = self.data.with_columns(*batch_exprs).fill_nan(None)
            self._cols = set(self.data.columns)
            self._expr_cache.update(self._cur_batch_expr_cache)
            if show_progress:
                pbar.update(1)

        final_df = self.data.select(*self._index.columns, *[e.alias for e in exprs_parsed])
        return final_df
