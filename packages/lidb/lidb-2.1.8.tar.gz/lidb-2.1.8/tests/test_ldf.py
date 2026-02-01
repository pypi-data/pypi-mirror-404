# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/12/11 14:52
# Description:
from omegaconf import OmegaConf

import lidb
import polars as pl
from lidb.qdf.lazy import LQDF
from lidb.qdf.lazy2 import LQDF as LQDF2
from lidb.qdf.qdf import QDF as LQDF3
import time
from hydra import main

pl.Config.set_tbl_cols(15)
pl.Config.set_tbl_width_chars(1500)
pl.Config.set_tbl_rows(30)

@main(version_base=None, config_path="./conf", config_name="svc-preds")
def run(cfg):
    quote_tb = lidb.tb_path("mc/stock_tick_cleaned")/ "freq=3s"/ "date=2025-05-06"
    quote = lidb.scan(quote_tb).filter(pl.col("time") <= "09:36:00")
    code_num = 600
    code_list = quote.select("asset").unique(maintain_order=True).collect()["asset"].to_list()
    codes = code_list[:code_num]
    quote = quote.filter(pl.col("asset").is_in(codes))
    start_t = time.time()
    db = LQDF3(quote, align=False, index=("date", "time", "asset"))
    print(f"LQDF elapsed: {(time.time()-start_t):.3f}s")
    # exprs = ["abs(c_ma20_ma30_sd30)", "ts_std(ts_mean(ts_mean(close, 20), 30), 30) as c_ma20_ma30_sd30",]
    # exprs = ["ts_std(ts_mean(ts_mean(close, 20), 30), 30) as c_ma20_ma30_sd30",
    #          "abs(c_ma20_ma30_sd30)",
    #          "volume>0?ts_sum(amount, 30)/ts_sum(volume, 30):null as vwap_30",]
    exprs = OmegaConf.to_container(cfg.exprs)
    # print(exprs)
    start_t = time.time()
    df = db.sql(*exprs, show_progress=True)
    # df = db.data.select(pl.col("close").shift(1).over("asset", order_by=["date", "time"]))
    print(f"Collect elapsed: {(time.time()-start_t):.3f}s")
    print(df)
    # return df

if __name__ == '__main__':
    import os
    # pl.Cojnfig.set_verbose(True)
    # os.environ["POLARS_MAX_THREADS"] = "32"
    # # pl.Config.set_engine_affinity("streaming")
    # # pl.Config.set_engine_affinity("gpu")
    #
    print(f"cpu_num: {os.cpu_count()}")
    print(f"polars.threads: {pl.thread_pool_size()}")
    # # print(f"polars.state: {pl.Config.state()}")
    # res = run(type_=2)
    # print(res)
    run()