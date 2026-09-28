"""关卡数据校验：引用完整性、二级引用、可达性与错误收集。

缺陷：发现第一个错误就 return（后面的全漏报）、不检查传送门需要的钥匙是否存在、
可达性把单向门当双向。
"""


def validate(level):
    """缺陷：第一个坏引用就返回，其余问题全部漏报。"""
    rooms = level["rooms"]
    errors = []
    for name in sorted(rooms):
        room = rooms[name]
        for portal in room.get("portals", []):
            if portal["to"] not in rooms:
                errors.append("房间 %s 的传送门指向不存在的房间 %s" % (name, portal["to"]))
                return errors  # 缺陷
    if not reachable(level, level["start"], level["exit"]):
        errors.append("从入口 %s 到不了出口 %s" % (level["start"], level["exit"]))
    return errors


def reachable(level, start, goal):
    """缺陷：邻接表不带方向，单向门被当成双向。"""
    rooms = level["rooms"]
    adjacency = {name: set() for name in rooms}
    for name in rooms:
        for portal in rooms[name].get("portals", []):
            target = portal["to"]
            if target in rooms:
                adjacency[name].add(target)
                adjacency[target].add(name)  # 缺陷：反向也连上了
    seen = {start}
    queue = [start]
    while queue:
        current = queue.pop(0)
        for target in sorted(adjacency[current]):
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
