# Copyright (c) ZhangYundi.
# Licensed under the MIT License. 
# Created on 2025/12/11 10:41
# Description:

from collections import defaultdict, deque
from lidb.qdf.expr import Expr

def build_dependency_graph(exprs: list[Expr], avail_cols: set[str]) -> tuple[dict, dict, dict]:
    """
    构建表达式的依赖图
    Parameters
    ----------
    exprs: list[Expr]
    avail_cols: set[str]

    Returns
    -------
    tuple[dict, dict]
        - graph: {expr_alias: [依赖的 expr_alias]}
        - indegree: {expr_alias: indegree}
        - expr_map: {expr_alias: Expr}

    """

    graph = defaultdict(list)
    indegree = defaultdict(int)
    expr_map = {}

    def collect_deps(e: Expr):
        alias = e.alias
        expr_map[alias] = e
        for arg in e.args:
            if isinstance(arg, Expr):
                graph[arg.alias].append(alias)
                indegree[alias] += 1
                collect_deps(arg)
            elif isinstance(arg, str) and arg.lower() != "null":
                if arg not in avail_cols:
                    graph[arg].append(alias)
                    indegree[alias] += 1
    for expr in exprs:
        # parsed = parse_expr(expr) if isinstance(expr, str) else expr
        collect_deps(expr)

    for alias in expr_map:
        if alias not in indegree:
            indegree[alias] = 0

    return graph, indegree, expr_map

def topological_sort(graph: dict, indegree: dict, expr_map: dict) -> list[list[str]]:
    """
    返回按照层级划分的表达式执行顺序(每层内部没有依赖)
    """
    queue = deque([k for k in expr_map if indegree[k] == 0])
    levels = []
    while queue:
        level_size = len(queue)
        current_level = []
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(expr_map[node])
            for neighbor in graph[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        levels.append(current_level)
    return levels

if __name__ == '__main__':
    exprs = ["high",
             "ma(close, 10) as ma_10",
             "ma(ma_10, 20) as ma_10_20",
             "std(osd_10, 30) as osd_10_30",
             "std(open, 10) as osd_10",
             "std(std(mean(close, 10), 30), 50) as c_ma10_sd30_sd50",
             "vol>0?amt/vol:null as vwap"]
    exprs = [Expr(e) for e in exprs]
    graph, indegree, expr_map = build_dependency_graph(exprs, avail_cols={"open", "high", "close", "vol", "amt"})
    print(graph)
    print(indegree)
    print(expr_map)
    lvl = topological_sort(graph, indegree, expr_map)
    print(lvl)
