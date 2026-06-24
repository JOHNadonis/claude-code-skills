#!/usr/bin/env python3
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
CASES = json.loads((ROOT / "evals" / "trigger_cases.json").read_text(encoding="utf-8"))

work_terms = [
    "职场", "同事", "领导", "老板", "客户", "下属", "跨部门", "办公室", "项目", "工作", "加班"
]
eq_terms = [
    "高情商", "情商", "拒绝", "说不", "边界", "边界感", "共情", "关系", "价值", "话术", "沟通", "老好人", "吐槽", "抢功", "甩给我"
]
block_terms = [
    "伴侣", "孩子", "抑郁", "next.js", "python", "csv", "涨停", "a 股", "小红书",
    "pua", "背锅", "性骚扰", "骚扰", "仲裁", "婆媳", "暧昧", "报复", "威胁", "sql", "心理咨询"
]


def routes(text: str) -> bool:
    low = text.lower()
    if any(term.lower() in low for term in block_terms):
        return False
    work_hit = any(term in text for term in work_terms)
    eq_hits = sum(1 for term in eq_terms if term in text)
    return work_hit and eq_hits >= 1


def main() -> int:
    errors = []
    for text in CASES["should_trigger"]:
        if not routes(text):
            errors.append({"case": text, "expected": True, "actual": False})
    for text in CASES["should_not_trigger"]:
        if routes(text):
            errors.append({"case": text, "expected": False, "actual": True})

    required = [
        "description:",
        "Do Not Use",
        "Safety Routing",
        "Workflow",
        "Output Templates",
        "Manipulation requests"
    ]
    for term in required:
        if term not in SKILL:
            errors.append({"missing_in_skill": term})

    result = {
        "status": "fail" if errors else "pass",
        "trigger_cases": len(CASES["should_trigger"]),
        "negative_cases": len(CASES["should_not_trigger"]),
        "errors": errors
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
