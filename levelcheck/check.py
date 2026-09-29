"""关卡数据校验：引用完整性、二级引用、可达性与错误收集。

口径（见 README）：
- 遍历完所有房间与传送门再返回，错误收全；
- 传送门的 key 必须在关卡的 keys 里（二级引用），缺钥匙单独报一条；
- 可达性按门的方向建图，单向门只能单向通行，起点等于终点算可达；
- 错误按房间名、再按传送门序号稳定排序，每条都带房间名与原因；
- 整体复杂度 O(房间数 + 门数)，不对每个房间重扫全表。
"""

from collections import deque


def validate(level):
    """收集全部校验错误，按（房间名, 传送门序号）稳定排序后返回。"""
    rooms = level["rooms"]
    keys = set(level.get("keys", []))
    errors = []
    for name in sorted(rooms):
        for index, portal in enumerate(rooms[name].get("portals", [])):
            target = portal.get("to")
            if target not in rooms:
                errors.append(
                    "房间 %s 的第 %d 号传送门指向不存在的房间 %s" % (name, index, target))
            key = portal.get("key")
            if key is not None and key not in keys:
                errors.append(
                    "房间 %s 的第 %d 号传送门需要不存在的钥匙 %s" % (name, index, key))
    if not reachable(level, level["start"], level["exit"]):
        errors.append("从入口 %s 到不了出口 %s" % (level["start"], level["exit"]))
    return errors


def reachable(level, start, goal):
    """有向 BFS：单向门只沿门的方向通行；起点等于终点算可达。"""
    if start == goal:
        return True
    rooms = level["rooms"]
    if start not in rooms or goal not in rooms:
        return False
    adjacency = {}
    for name, room in rooms.items():
        adjacency[name] = [portal["to"] for portal in room.get("portals", [])
                           if portal.get("to") in rooms]
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for target in adjacency[current]:
            if target == goal:
                return True
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return False


def sample_a():
    """5 个问题：3 个坏引用 + 2 个缺钥匙；正确方向上入口能到出口。"""
    rooms = {
        "hall": {"name": "hall", "portals": [{"to": "cave"}, {"to": "missing1"},
                                             {"to": "missing2", "key": "red"}]},
        "cave": {"name": "cave", "portals": [{"to": "vault", "key": "gold"}, {"to": "missing3"}]},
        "vault": {"name": "vault", "portals": [{"to": "hall", "key": "silver"}]},
    }
    return {"rooms": rooms, "start": "hall", "exit": "vault", "keys": ["red"]}


def sample_b():
    """单向门：hall 能去 cave，cave 回不去；入口在 cave、出口在 hall。"""
    rooms = {
        "hall": {"name": "hall", "portals": [{"to": "cave"}]},
        "cave": {"name": "cave", "portals": []},
    }
    return {"rooms": rooms, "start": "cave", "exit": "hall", "keys": []}
