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
import sys
from functools import lru_cache
from functools import partial
from pathlib import Path
import inspect

import polars as pl
from polars import selectors as cs
import logair

from .errors import CalculateError, CompileError, PolarsError, FailError
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

class LQDF:

    def __init__(self,
                 data: pl.LazyFrame | pl.DataFrame,
                 index: tuple[str] = ("date", "time", "asset"),
                 align: bool = True, ):
        assert isinstance(data, (pl.LazyFrame, pl.DataFrame)), "data must be a polars DataFrame or LazyFrame"
        self.data: pl.LazyFrame = data.lazy().cast({pl.Decimal: pl.Float64}).fill_nan(None).drop_nulls(subset=index)
        self._index = self.data.select(index).collect()
        self.dims = [self._index[name].n_unique() for name in index]
        if align:
            lev_vals: list[pl.LazyFrame] = [self._index.select(name).unique().lazy() for name in index]
            full_index = lev_vals[0]
            for lev_val in lev_vals[1:]:
                full_index = full_index.join(lev_val, how="cross")
            self.data = full_index.join(self.data, on=index, how='left')
        self.data = self.data.sort(index)
        self.failed = list()
        self._cols = set(self.data.collect_schema().names())
        self._expr_cache = dict()  # type: dict[Expr, str]
        self._cur_expr_cache = dict()
        self._fn_map = dict()

    def __str__(self):
        return self.data.__str__()

    def __repr__(self):
        return self.data.__str__()

    def register_udf(self, func: callable, name: str = None):
        name = name if name is not None else func.__name__
        setattr(module, name, func)

    def _to_pl_expr(self, e: Expr) -> pl.Expr:
        """递归编译"""
        alias = e.alias
        if alias in self._cols:
            return pl.col(alias)
        elif e in self._expr_cache:
            return pl.col(self._expr_cache[e]).alias(alias)
        elif e in self._cur_expr_cache:
            return pl.col(self._cur_expr_cache[e]).alias(alias)
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
                    if arg in self._expr_cache:
                        args.append(pl.col(self._expr_cache[arg]))
                    elif arg in self._cur_expr_cache:
                        args.append(pl.col(self._cur_expr_cache[arg]))
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
                self._cur_expr_cache[e] = alias
                return expr_pl.alias(alias)
            except Exception as error:
                raise CompileError(message=f"{e.fn_name}({', '.join([str(arg) for arg in args])})\n{error}") from error


    def sql(self, *exprs: str, ) -> pl.DataFrame:
        """
        表达式查询
        Parameters
        ----------
        exprs: str
            表达式，比如 "ts_mean(close, 5) as close_ma5"
        Returns
        -------
            polars.LazyFrame
        """
        self.failed = list()
        # exprs_select = list()
        exprs_parsed = list()
        self._cur_expr_cache = {}
        for expr in exprs:
            try:
                # compiled, alias = self._compile_expr(expr)
                e_parsed = Expr(expr)
                exprs_parsed.append(e_parsed)
            except Exception as e:
                self.failed.append(FailError(expr, e))
        if self.failed:
            logger.warning(f"sql failed num：{len(self.failed)}/{len(exprs)}: \n {self.failed}")
        graph, indegree, expr_map = build_dependency_graph(exprs_parsed, self._cols)
        lvls: list[list[Expr]] = topological_sort(graph, indegree, expr_map)
        for batch_exprs in lvls:
            batch_exprs = [self._to_pl_expr(e) for e in batch_exprs]
            self.data = self.data.with_columns(*batch_exprs).fill_nan(None)
        new_expr_cache = dict()
        try:
            current_cols = set(self.data.collect_schema().names())
            # 缓存整理：只保留当前表达式的缓存
            self._expr_cache.update(self._cur_expr_cache)
            for k, v in self._expr_cache.items():
                if v in current_cols:
                    new_expr_cache[k] = v
            self._expr_cache = new_expr_cache
            final_df = self.data.select(*self._index.columns, *[e.alias for e in exprs_parsed])
            return final_df
            # return final_df
        except Exception as e:
            # 缓存整理：只保留当前表达式的缓存
            for k, v in self._expr_cache.items():
                if v in self._cols:
                    new_expr_cache[k] = v
            self._expr_cache = new_expr_cache
            raise PolarsError(message=f"LazyFrame.collect() step error:\n{e}") from e
