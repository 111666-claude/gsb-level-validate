import random
import time
import unittest
from collections import deque

from levelcheck.check import reachable, sample_a, sample_b, validate


def simple_level():
    return {"rooms": {"a": {"name": "a", "portals": [{"to": "b"}]},
                      "b": {"name": "b", "portals": []}},
            "start": "a", "exit": "b", "keys": []}


def reference_errors(level):
    """参考实现：全量扫描，先收集再统一排序。"""
    rooms = level["rooms"]
    keys = set(level.get("keys", []))
    found = []
    for name, room in rooms.items():
        for index, portal in enumerate(room.get("portals", [])):
            if portal.get("to") not in rooms:
                found.append((name, index, "bad_ref"))
            key = portal.get("key")
            if key is not None and key not in keys:
                found.append((name, index, "missing_key"))
    found.sort(key=lambda item: (item[0], item[1]))
    result = ["%s#%d:%s" % item for item in found]
    if not reference_reachable(level, level["start"], level["exit"]):
        result.append("unreachable")
    return result


def reference_reachable(level, start, goal):
    """参考实现：有向 BFS。"""
    if start == goal:
        return True
    rooms = level["rooms"]
    if start not in rooms or goal not in rooms:
        return False
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for portal in rooms[current].get("portals", []):
            target = portal["to"]
            if target in rooms and target not in seen:
                seen.add(target)
                queue.append(target)
    return goal in seen


def normalized_errors(level):
    """把 validate 的错误列表归一成可比对的形式。"""
    rooms = level["rooms"]
    keys = set(level.get("keys", []))
    result = []
    for name in sorted(rooms):
        for index, portal in enumerate(rooms[name].get("portals", [])):
            if portal.get("to") not in rooms:
                result.append("%s#%d:bad_ref" % (name, index))
            key = portal.get("key")
            if key is not None and key not in keys:
                result.append("%s#%d:missing_key" % (name, index))
    if not reachable(level, level["start"], level["exit"]):
        result.append("unreachable")
    return result


def random_level(rng):
    room_count = rng.randint(1, 12)
    names = ["room%02d" % i for i in range(room_count)]
    keys = ["key%d" % i for i in range(rng.randint(0, 3))]
    rooms = {}
    for name in names:
        portals = []
        for _ in range(rng.randint(0, 4)):
            portal = {}
            # 部分指向不存在的房间（坏引用），自然形成环与单向门
            if rng.random() < 0.2:
                portal["to"] = "ghost%d" % rng.randint(0, 3)
            else:
                portal["to"] = rng.choice(names)
            if rng.random() < 0.4:
                if rng.random() < 0.5 and keys:
                    portal["key"] = rng.choice(keys)
                else:
                    portal["key"] = "lost_key%d" % rng.randint(0, 2)
            portals.append(portal)
        rooms[name] = {"name": name, "portals": portals}
    return {"rooms": rooms,
            "start": rng.choice(names),
            "exit": rng.choice(names),
            "keys": keys}


class ValidateTest(unittest.TestCase):
    def test_ok_level(self):
        self.assertEqual(validate(simple_level()), [])

    def test_missing_room_is_reported(self):
        level = {"rooms": {"a": {"name": "a", "portals": [{"to": "nope"}]}},
                 "start": "a", "exit": "a", "keys": []}
        self.assertEqual(len(validate(level)), 1)

    def test_sample_a_collects_all_five_errors(self):
        errors = validate(sample_a())
        self.assertEqual(len(errors), 5)
        for entry in errors:
            self.assertIn("房间", entry)

    def test_errors_are_all_collected_not_short_circuited(self):
        level = {"rooms": {
            "a": {"name": "a", "portals": [{"to": "nope1"}, {"to": "nope2"}]},
            "b": {"name": "b", "portals": [{"to": "nope3"}]},
        }, "start": "a", "exit": "a", "keys": []}
        errors = validate(level)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("a" in e and "nope2" in e for e in errors))
        self.assertTrue(any("b" in e and "nope3" in e for e in errors))

    def test_missing_key_is_reported_separately(self):
        level = {"rooms": {
            "a": {"name": "a", "portals": [{"to": "b", "key": "gold"}]},
            "b": {"name": "b", "portals": []},
        }, "start": "a", "exit": "b", "keys": []}
        errors = validate(level)
        self.assertEqual(len(errors), 1)
        self.assertIn("gold", errors[0])
        self.assertIn("a", errors[0])

    def test_bad_ref_and_missing_key_are_two_errors(self):
        level = {"rooms": {
            "a": {"name": "a", "portals": [{"to": "nope", "key": "gold"}]},
        }, "start": "a", "exit": "a", "keys": []}
        self.assertEqual(len(validate(level)), 2)

    def test_errors_sorted_by_room_then_portal_index(self):
        level = {"rooms": {
            "zeta": {"name": "zeta", "portals": [{"to": "nope2"}]},
            "alpha": {"name": "alpha", "portals": [{"to": "nope0"}, {"to": "nope1"}]},
        }, "start": "alpha", "exit": "alpha", "keys": []}
        errors = validate(level)
        self.assertEqual(len(errors), 3)
        self.assertIn("alpha", errors[0])
        self.assertIn("alpha", errors[1])
        self.assertIn("zeta", errors[2])
        self.assertIn("nope0", errors[0])
        self.assertIn("nope1", errors[1])

    def test_validate_is_deterministic(self):
        level = sample_a()
        self.assertEqual(validate(level), validate(level))

    def test_error_count_matches_actual_bad_points(self):
        level = sample_a()
        bad_points = 0
        keys = set(level["keys"])
        for room in level["rooms"].values():
            for portal in room["portals"]:
                if portal["to"] not in level["rooms"]:
                    bad_points += 1
                if "key" in portal and portal["key"] not in keys:
                    bad_points += 1
        self.assertEqual(len(validate(level)), bad_points)


class ReachableTest(unittest.TestCase):
    def test_simple_path(self):
        self.assertTrue(reachable(simple_level(), "a", "b"))

    def test_start_equals_goal(self):
        self.assertTrue(reachable(sample_b(), "hall", "hall"))

    def test_one_way_portal_is_not_traversable_backwards(self):
        self.assertFalse(reachable(sample_b(), "cave", "hall"))
        self.assertTrue(reachable(sample_b(), "hall", "cave"))

    def test_sample_b_exit_unreachable(self):
        level = sample_b()
        self.assertFalse(reachable(level, level["start"], level["exit"]))

    def test_cycle_does_not_hang(self):
        rooms = {name: {"name": name, "portals": [{"to": other}]}
                 for name, other in [("a", "b"), ("b", "c"), ("c", "a")]}
        level = {"rooms": rooms, "start": "a", "exit": "c", "keys": []}
        self.assertTrue(reachable(level, "a", "c"))


class DifferentialTest(unittest.TestCase):
    def test_200_random_levels_match_reference(self):
        rng = random.Random(20260930)
        for case in range(200):
            level = random_level(rng)
            self.assertEqual(normalized_errors(level), reference_errors(level),
                             "case %d 错误列表不一致" % case)
            self.assertEqual(
                reachable(level, level["start"], level["exit"]),
                reference_reachable(level, level["start"], level["exit"]),
                "case %d 可达性不一致" % case)


class PerformanceTest(unittest.TestCase):
    def test_100k_rooms_500k_portals_under_3_seconds(self):
        room_count = 100000
        rooms = {}
        for i in range(room_count):
            name = "r%06d" % i
            portals = [{"to": "r%06d" % ((i + 1) % room_count)},
                       {"to": "r%06d" % ((i * 7 + 3) % room_count)},
                       {"to": "r%06d" % ((i * 13 + 11) % room_count)},
                       {"to": "r%06d" % ((i * 29 + 17) % room_count)},
                       {"to": "nowhere", "key": "ghost_key"}]
            rooms[name] = {"name": name, "portals": portals}
        level = {"rooms": rooms, "start": "r000000",
                 "exit": "r%06d" % (room_count - 1), "keys": []}
        started = time.monotonic()
        errors = validate(level)
        elapsed = time.monotonic() - started
        self.assertEqual(len(errors), room_count * 2)  # 每房间 1 坏引用 + 1 缺钥匙
        self.assertLess(elapsed, 3.0, "校验耗时 %.2fs 超过 3s" % elapsed)


if __name__ == "__main__":
    unittest.main()
