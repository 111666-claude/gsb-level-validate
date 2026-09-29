import unittest
import random
import time
from collections import deque

from levelcheck.check import reachable, sample_a, sample_b, validate


def simple_level():
    return {"rooms": {"a": {"name": "a", "portals": [{"to": "b"}]},
                      "b": {"name": "b", "portals": []}},
            "start": "a", "exit": "b", "keys": []}


def reference_errors(level):
    """参考实现：全量扫描，返回 (房间名, 传送门序号, 类别) 列表。"""
    rooms = level["rooms"]
    keys = set(level.get("keys", []))
    errors = []
    for name in sorted(rooms):
        for index, portal in enumerate(rooms[name].get("portals", [])):
            if portal.get("to") not in rooms:
                errors.append((name, index, "bad-ref"))
            key = portal.get("key")
            if key is not None and key not in keys:
                errors.append((name, index, "missing-key"))
    return errors


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
            target = portal.get("to")
            if target in rooms and target not in seen:
                if target == goal:
                    return True
                seen.add(target)
                queue.append(target)
    return False


def random_level(rng):
    """随机关卡：含坏引用、缺钥匙、单向门与环。"""
    room_count = rng.randint(2, 30)
    names = ["room-%d" % i for i in range(room_count)]
    key_pool = ["key-%d" % i for i in range(rng.randint(0, 4))]
    keys = [key for key in key_pool if rng.random() < 0.7]
    rooms = {}
    for name in names:
        portals = []
        for _ in range(rng.randint(0, 4)):
            portal = {}
            if rng.random() < 0.15:
                portal["to"] = "missing-%d" % rng.randint(0, 5)
            else:
                portal["to"] = rng.choice(names)
            if rng.random() < 0.4:
                if rng.random() < 0.3 or not key_pool:
                    portal["key"] = "ghost-key-%d" % rng.randint(0, 3)
                else:
                    portal["key"] = rng.choice(key_pool)
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
        # 错误收全：3 个坏引用 + 2 个缺钥匙，一条都不能漏。
        errors = validate(sample_a())
        self.assertEqual(len(errors), 5)
        self.assertEqual(sum("指向不存在的房间" in e for e in errors), 3)
        self.assertEqual(sum("需要不存在的钥匙" in e for e in errors), 2)

    def test_missing_key_is_reported(self):
        # 二级引用：to 合法但 key 不在关卡 keys 里，也要单独报一条。
        level = {"rooms": {"a": {"name": "a", "portals": [{"to": "b", "key": "gold"}]},
                           "b": {"name": "b", "portals": []}},
                 "start": "a", "exit": "b", "keys": []}
        errors = validate(level)
        self.assertEqual(len(errors), 1)
        self.assertIn("gold", errors[0])
        self.assertIn("a", errors[0])

    def test_known_key_is_not_an_error(self):
        level = {"rooms": {"a": {"name": "a", "portals": [{"to": "b", "key": "gold"}]},
                           "b": {"name": "b", "portals": []}},
                 "start": "a", "exit": "b", "keys": ["gold"]}
        self.assertEqual(validate(level), [])

    def test_error_mentions_room_and_reason(self):
        level = {"rooms": {"hall": {"name": "hall", "portals": [{"to": "nowhere"}]}},
                 "start": "hall", "exit": "hall", "keys": []}
        (error,) = validate(level)
        self.assertIn("hall", error)
        self.assertIn("nowhere", error)

    def test_errors_sorted_by_room_then_portal_index(self):
        rooms = {
            "b-room": {"name": "b-room", "portals": [{"to": "x1"}, {"to": "x2"}]},
            "a-room": {"name": "a-room", "portals": [{"to": "x3"}]},
        }
        level = {"rooms": rooms, "start": "a-room", "exit": "a-room", "keys": []}
        errors = validate(level)
        self.assertEqual([e.split(" ")[1] for e in errors],
                         ["a-room", "b-room", "b-room"])
        self.assertIn("x3", errors[0])
        self.assertIn("x1", errors[1])
        self.assertIn("x2", errors[2])

    def test_validate_is_deterministic(self):
        level = sample_a()
        self.assertEqual(validate(level), validate(level))

    def test_unreachable_exit_is_reported(self):
        errors = validate(sample_b())
        self.assertEqual(len(errors), 1)
        self.assertIn("cave", errors[0])
        self.assertIn("hall", errors[0])


class ReachableTest(unittest.TestCase):
    def test_simple_path(self):
        self.assertTrue(reachable(simple_level(), "a", "b"))

    def test_start_equals_goal(self):
        self.assertTrue(reachable(sample_b(), "hall", "hall"))

    def test_one_way_portal_is_not_traversable_backwards(self):
        # 单向门：hall -> cave 存在，但 cave 到不了 hall。
        self.assertFalse(reachable(sample_b(), "cave", "hall"))
        self.assertTrue(reachable(sample_b(), "hall", "cave"))

    def test_sample_b_exit_unreachable(self):
        self.assertFalse(reachable(sample_b(), sample_b()["start"], sample_b()["exit"]))


class FuzzTest(unittest.TestCase):
    def test_matches_reference_on_200_random_levels(self):
        for seed in range(200):
            rng = random.Random(seed)
            level = random_level(rng)
            with self.subTest(seed=seed):
                expected = reference_errors(level)
                errors = validate(level)
                ref_reach = reference_reachable(level, level["start"], level["exit"])
                # 不可达时 validate 额外追加一条“到不了出口”。
                self.assertEqual(len(errors), len(expected) + (0 if ref_reach else 1))
                for (name, index, _kind), error in zip(expected, errors):
                    self.assertIn(name, error)
                    self.assertIn("第 %d 号" % index, error)
                self.assertEqual(reachable(level, level["start"], level["exit"]),
                                 ref_reach)
                # 不变量：重复校验结果相同。
                self.assertEqual(validate(level), errors)


class ScaleTest(unittest.TestCase):
    def test_100k_rooms_500k_portals_under_3_seconds(self):
        room_count = 100000
        portals_per_room = 5
        rooms = {}
        for i in range(room_count):
            rooms["r%d" % i] = {
                "name": "r%d" % i,
                "portals": [{"to": "r%d" % ((i * 7 + j + 1) % room_count)}
                            for j in range(portals_per_room)],
            }
        level = {"rooms": rooms, "start": "r0",
                 "exit": "r%d" % (room_count - 1), "keys": []}
        began = time.monotonic()
        errors = validate(level)
        self.assertTrue(reachable(level, level["start"], level["exit"]))
        elapsed = time.monotonic() - began
        self.assertEqual(errors, [])
        self.assertLess(elapsed, 3.0, "校验耗时 %.2fs 超过 3s" % elapsed)


if __name__ == "__main__":
    unittest.main()
