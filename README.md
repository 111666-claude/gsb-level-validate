# level-validate

关卡数据校验：引用完整性、二级引用与可达性，只用 Python 标准库。

```
python3 -m levelcheck.cli --level sample-a
python3 -m levelcheck.cli --level sample-b
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **错误要收全**：遍历完所有房间与传送门再返回，不能发现第一个错就退出。
  `--level sample-a` 有 5 个问题（3 个坏引用 + 2 个缺钥匙），按口径是 `errors=5`，现在只报 1 个。
- **二级引用也要查**：传送门上的 `key` 必须在关卡的 `keys` 里，缺钥匙单独报一条。
- **可达性按门的方向**：单向门只能单向通行。`--level sample-b`（入口 cave、出口 hall，
  只有 hall → cave 的门）按口径是 `reachable=false`，现在把门当双向，给 `reachable=true`。
- 不变量：同一份关卡重复校验给出同样的错误列表（按房间名、再按传送门序号稳定排序）；
  错误信息里要有房间名与原因；合法关卡零误报。
- 规模：10 万房间 / 50 万传送门 3 秒内校验完，内存 O(房间数 + 门数)；不许对每个房间重扫全表。

## 现在的行为

- `validate` 在第一个坏引用处直接 `return errors`。
- 只看 `portal["to"]`，完全不看 `portal["key"]` 是否在 `level["keys"]` 里。
- `reachable` 建邻接表时补了反向边，门的方向被丢弃。

## 计划新增的能力

```
--level sample-a|sample-b
```

## 输出

```
errors=5
reachable=true
```

## 目录

```
levelcheck/check.py   校验与可达性
levelcheck/cli.py     命令行入口
tests/                unittest 用例
```
