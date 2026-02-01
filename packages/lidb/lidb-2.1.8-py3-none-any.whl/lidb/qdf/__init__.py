# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2025/3/5 21:40
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""
from __future__ import annotations

from .qdf import QDF
from .lazy import LQDF
from .expr import Expr
from typing import TYPE_CHECKING
from pathlib import Path
from ..dataset import scan

if TYPE_CHECKING:
    import polars as pl



def from_polars(df: pl.DataFrame | pl.LazyFrame | Path | str, index: tuple[str] = ("date", "time", "asset"), align: bool = False, ) -> QDF:
    """polars dataframe 转为 表达式数据库"""
    if isinstance(df, (Path, str)):
        df = scan(df)
    return QDF(df, index, align,)

# def to_lazy(df: pl.DataFrame | pl.LazyFrame | Path | str, index: tuple[str] = ("date", "time", "asset"), align: bool = False, ) -> LQDF:
#     """polars dataframe/lazy frame/table path 转为 表达式数据库"""
#     if isinstance(df, (Path, str)):
#         df = scan(df)
#     return LQDF(df, index, align,)

