## lidb

### 项目简介
lidb 是一个基于 Polars 的数据管理和分析库，专为金融量化研究设计。它提供了高效的数据存储、查询和表达式计算功能，支持多种时间序列和横截面数据分析操作。

### 功能特性
- **多数据源支持**: 本地 Parquet 存储、MySQL、ClickHouse 等数据库连接
- **高效数据存储**: 基于 Parquet 格式的分区存储机制
- **SQL 查询接口**: 支持标准 SQL 语法进行数据查询
- **表达式计算引擎**: 提供丰富的 UDF 函数库，包括时间序列、横截面、维度等分析函数
- **数据集管理**: 自动化数据补全、历史数据加载和 PIT(Point-in-Time)数据处理
- **数据服务**: 异步加载数据，用于数据密集型任务的数据加载(如大量标的的高频数据)

### 安装
```bash
pip install -U lidb
```

### 快速开始

#### 基础数据操作
```python
import lidb
import polars as pl

df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

# 写入数据
lidb.put(df, "my_table")

# sql 查询
res = lidb.sql("select * from my_table;")
```

#### 数据集使用
```python
import lidb
from lidb import Dataset, dataset
import polars as pl

# 定义一个tick级别的高频数据集: 高频成交量
def hft_vol(date: str, num: int) -> pl.DataFrame | pl.LazyFrame | None:
    # 假设上游tick行情表在clickhouse
    quote_query = f"select * from quote where date = '{date}'"
    quote = lidb.read_ck(quote_query, db_conf="databases.ck")
    # 特征计算: 比如过去20根tick的成交量总和, 使用表达式引擎计算
    return lidb.from_polars(quote).sql(f"itd_sum(volume, {num}) as vol_s20")

ds_hft_vol = Dataset(fn=hft_vol, 
                     tb="path/to/hft_vol", 
                     partitions=["num"], # 默认值 None, 会自动识别 num 
                     update_time="", # 实时更新
                     is_hft=True, # 根据asset_id进行分区
                    )(num=20)

# 获取历史数据
history_data = ds_hft_vol.get_history(["2023-01-01", "2023-01-02", ...])

# 更加便捷的创建数据集方式：通过dataset装饰器
@dataset()
def hft_vol(date: str, num: int) -> pl.DataFrame | pl.LazyFrame | None:
    # 假设上游tick行情表在clickhouse
    quote_query = f"select * from quote where date = '{date}'"
    quote = lidb.read_ck(quote_query, db_conf="databases.ck")
    # 特征计算: 比如过去20根tick的成交量总和, 使用表达式引擎计算
    return lidb.from_polars(quote).sql(f"itd_sum(volume, {num}) as vol_s20")

hft_vol.get_value("2025-05-15")
```

#### `Table`
除了 `Dataset` 类用于管理复杂的、可分区的历史数据集之外，lidb 还提供了一个更轻量级的 `Table` 类。
它适用于那些不需要复杂分区逻辑，且通常以单一文件形式存储的表格数据。`Table` 类同样支持基于更新时间的自动化数据管理和加载。
##### 特性
- **简化数据管理**: 专为单表数据设计，无需复杂的分区结构。
- **灵活更新策略**: 
  - **全量更新(`TableMode.F`)**: 每次更新时覆盖旧数据，仅保留最新的数据文件（0.parquet）。
  - **增量更新(`TableMode.I`)**: 每次更新时生成一个新的带时间戳的文件（<uuid>.parquet），保留历史版本。
- **自动更新检查**: 根据设定的 `update_time` 和文件修改时间，自动判断是否需要更新数据。
 
##### 使用示例
```python
from lidb import Table, TableMode
import polars as pl

# 1. 定义一个数据获取函数
def fetch_latest_stock_list() -> pl.DataFrame:
    # 模拟从某个API或数据库获取最新的股票列表
    import time
    time.sleep(1) # 模拟网络延迟
    return pl.DataFrame({
        "symbol": ["AAPL", "GOOGL", "MSFT"],
        "name": ["Apple Inc.", "Alphabet Inc.", "Microsoft Corp."],
        "sector": ["Technology", "Communication Services", "Technology"]
    })

# 2. 创建 Table 实例
# 假设此表每天上午9点更新
stock_list_table = Table(
    fn=fetch_latest_stock_list,
    tb="stock_list",
    update_time="09:00:00",
    mode=TableMode.F # 使用全量更新模式
)

# 3. 更新数据 (可选，get_value 会自动检查并提示更新)
# stock_list_table.update(verbose=True)

# 4. 获取数据
# 如果数据过期，get_value 会打印警告并退出，提示先调用 update()
df = stock_list_table.get_value(date="2023-10-27")
print(df)
```


#### 表达式计算
```python
import lidb

date = "2025-05-15"
quote_query = f"select * from quote where date = '{date}'"
quote = lidb.read_ck(quote_query, db_conf="databases.ck")

qdf = lidb.from_polars(quote)

# 使用 QDF 进行表达式计算
res = qdf.sql(
    "ts_mean(close, 5) as c_m5", 
    "cs_rank(volume) as vol_rank", 
)
```

#### 数据服务
lidb 提供了一个名为 `D` 的全局 `DataService` 实例。
用于在后台线程中预加载数据并缓存，从而提升数据密集型任务的性能。
这对于需要提前准备大量数据的应用非常有用，例如回测系统或实时数据处理流水线。
##### 启动数据服务
你可以通过调用 `D.start()` 方法来启动数据服务，指定一个数据加载函数、需要加载的键列表以及迭代配置。
```python
from lidb import D
import polars as pl

# 定义一个模拟的数据加载函数
def mock_data_loader(key: str, iterables: list[str]) -> pl.DataFrame:
  # 模拟耗时操作
  import time
  time.sleep(1)

  # 返回简单的 DataFrame 示例
  return pl.DataFrame({
    "key": [key],
    "value": [sum(len(s) for s in iterables)]
  })

# 启动数据服务
D.start(
  fn=mock_data_loader,
  keys=["2023-01-01", "2023-01-02", "2023-01-03"],
  iter_conf={"data_source_a": ["a", "b"], "data_source_b": ["x", "y"]},
  max_cache_size=3
)
```
##### 消费数据
一旦数据服务启动，你就可以通过 `D.do()` 来消费已加载的数据。
这个方法接受一个消费者函数作为参数，每当有新数据可用时就会被调用。
```python
def data_consumer(data_package: dict):
    print(f"Consumed data for key: {data_package['key']}")
    for name, df in data_package['data'].items():
        print(f"  Data from {name}:")
        print(df)

# 开始消费数据
D.do(consumer=data_consumer, wait_secs=1)
```
##### 停止数据服务
当你需要停止数据服务时，你可以调用 `D.stop()` 方法。
##### 完整示例
以下是一个完整的示例，演示了如何使用 D 进行异步数据加载与消费:
```python
import lidb
from lidb import D
import polars as pl
import time

def fetch_market_data(key: str, iterables: list[str]) -> pl.DataFrame:
    # 模拟网络请求或复杂计算
    time.sleep(0.5)
    return pl.DataFrame({
        "date": [key],
        "symbol_count": [len(iterables)],
        "total_volume": [sum(ord(c) for s in iterables for c in s)]  # Dummy volume
    })

# 启动服务
D.start(
    fn=fetch_market_data,
    keys=["2023-01-01", "2023-01-02", "2023-01-03"],
    iter_conf={"symbols": ["AAPL", "GOOGL", "MSFT"]},
    max_cache_size=2
)

# 消费者函数
def handle_data(data_package: dict):
    print(f"\nReceived data for {data_package['key']}:")
    print(data_package['data']['market_data'])

# 启动消费过程
try:
    D.do(consumer=handle_data, wait_secs=1)
except KeyboardInterrupt:
    print("\nShutting down data service...")
finally:
    D.stop()
```

### 核心模块

#### 数据库操作(`database.py`)
- `put`: 将 `polars.DataFrame` 写入指定表
- `sql`: 执行 `SQL` 查询
- `has`: 检查表是否存在
- `read_mysql`,`write_mysql`: mysql 数据读写
- `read_ck`: clickhouse 数据读取

#### 数据服务(`svc/data.py`)
- `DataService`: 数据服务管理
- `D`: `DataService` 全局实例

#### 数据集管理(`dataset.py`)
- `Dataset`: 数据集定义和管理
- `DataLoader`： 数据加载器

#### 表达式计算(`qdf/`)
- `QDF`: 表达式数据库
- `Expr`: 表达式解析器
- `UDF 函数库`:
    - `base_udf`: 基础运算函数
    - `ts_udf`: 时间序列函数
    - `cs_udf`: 横截面函数
    - `d_udf`: 日期维度函数
    - `itd_udf`: 日内函数

#### 配置管理(`init.py`)
- 自动创建配置文件
- 支持自定义数据存储路径
- `polars` 线程配置
#### 配置说明
首次运行会在 `~/.config/lidb/settings.toml` 创建配置文件:
```toml
[GLOBAL]
path = "~/lidb"  # 数据存储路径

[POLARS]
max_threads = 32  # Polars 最大线程数
```

### 许可证
本项目采用 MIT 许可证, 请在项目根目录下查看

### 联系方式
Zhangyundi - yundi.xxii@outlook.com