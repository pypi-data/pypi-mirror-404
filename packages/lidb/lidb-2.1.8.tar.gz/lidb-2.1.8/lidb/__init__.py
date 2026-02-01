# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 

from .init import (
    NAME,
    DB_PATH,
    CONFIG_PATH,
    get_settings,
)

from .database import (
    sql,
    put,
    has,
    tb_path,
    read_mysql,
    write_mysql,
    execute_mysql,
    read_ck,
    scan,
)

from .table import Table, TableMode
from .dataset import Dataset, DataLoader
from .decorator import dataset
from .qdf import from_polars, Expr
from .svc import DataService, D

from .parse import parse_hive_partition_structure

__version__ = "2.1.8"
