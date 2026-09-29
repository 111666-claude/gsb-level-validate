"""关卡数据校验：引用完整性、二级引用、可达性与错误收集。"""

from collections import deque


def validate(level):
    """遍历完所有房间与传送门，收齐全部错误后再返回。

    错误按房间名、再按传送门序号稳定排序；每条错误带房间名与原因。
    """
    rooms = level["rooms"]
    keys = set(level.get("keys", []))
    errors = []
    for name in sorted(rooms):
        room = rooms[name]
        for index, portal in enumerate(room.get("portals", [])):
            target = portal.get("to")
            if target not in rooms:
                errors.append(
                    "房间 %s 的第 %d 号传送门指向不存在的房间 %s" % (name, index, target))
            key = portal.get("key")
            if key is not None and key not in keys:
                errors.append(
                    "房间 %s 的第 %d 号传送门需要的钥匙 %s 不在关卡钥匙表里"
                    % (name, index, key))
    if not reachable(level, level["start"], level["exit"]):
        errors.append("从入口 %s 到不了出口 %s" % (level["start"], level["exit"]))
    return errors


def reachable(level, start, goal):
    """有向可达性：单向门只能单向通行；起点与终点相同算可达。"""
    if start == goal:
        return True
    rooms = level["rooms"]
    if start not in rooms or goal not in rooms:
        return False
    adjacency = {name: [] for name in rooms}
    for name in rooms:
        for portal in rooms[name].get("portals", []):
            target = portal["to"]
            if target in rooms:
                adjacency[name].append(target)
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for target in adjacency[current]:
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return goal in seen


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
