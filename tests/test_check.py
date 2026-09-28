import unittest

from levelcheck.check import reachable, sample_a, sample_b, validate


def simple_level():
    return {"rooms": {"a": {"name": "a", "portals": [{"to": "b"}]},
                      "b": {"name": "b", "portals": []}},
            "start": "a", "exit": "b", "keys": []}


class ValidateTest(unittest.TestCase):
    def test_ok_level(self):
        self.assertEqual(validate(simple_level()), [])

    def test_missing_room_is_reported(self):
        level = {"rooms": {"a": {"name": "a", "portals": [{"to": "nope"}]}},
                 "start": "a", "exit": "a", "keys": []}
        self.assertEqual(len(validate(level)), 1)

    def test_sample_a_reports_something(self):
        self.assertGreaterEqual(len(validate(sample_a())), 1)


class ReachableTest(unittest.TestCase):
    def test_simple_path(self):
        self.assertTrue(reachable(simple_level(), "a", "b"))

    def test_start_equals_goal(self):
        self.assertTrue(reachable(sample_b(), "hall", "hall"))


if __name__ == "__main__":
    unittest.main()
