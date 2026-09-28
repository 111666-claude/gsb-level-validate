"""命令行入口：跑关卡校验样例。"""

import argparse

from .check import reachable, sample_a, sample_b, validate


def build_parser():
    parser = argparse.ArgumentParser(prog="level-validate", description="关卡数据校验")
    parser.add_argument("--level", default="sample-a", help="sample-a / sample-b")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    level = sample_a() if args.level == "sample-a" else sample_b()
    errors = validate(level)
    print("errors=%d" % len(errors))
    for entry in errors:
        print("error %s" % entry)
    print("reachable=%s" % reachable(level, level["start"], level["exit"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
