# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/12/31 10:58
# Description:

from .dataset import Dataset
from typing import Callable, TypeVar, cast

F = TypeVar('F', bound=Callable)

def dataset(*depends: Dataset,
            tb: str = "",
            update_time: str = "",
            window: str = "1d",
            partitions: list[str] = None,
            is_hft: bool = False) -> Callable[[F], Dataset]:
    """
    装饰器：将函数转换为Dataset对象

    Parameters
    ----------
    depends: Dataset
        底层依赖数据集
    tb: str
        数据集保存表格, 如果没有指定，默认 {DEFAULT_DS_PATH}/
    update_time: str
        更新时间: 默认没有-实时更新，也就是可以取到当天值
    window: str
        配合depends使用，在取depends时，会回看window周期，最小单位为`d`。不足 `d` 的会往上取整为`1d`
    partitions: list[str]
        分区: 如果指定为 None, 则自动从 fn 参数推断，如果不需要分区，应该将其设定为空列表: []
    is_hft: bool
        是否是高频数据，如果是，则会按照asset进行分区存储，默认 False
        hft定义为：时间步长 < 1min
    """
    def decorator(fn: F):
        # 创建Dataset实例
        ds = Dataset(
            *depends,
            fn=fn,
            tb=tb,
            update_time=update_time,
            window=window,
            partitions=partitions,
            is_hft=is_hft,
            data_name=fn.__name__,
            frame=1
        )
        return ds
    return decorator
