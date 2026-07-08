#!/usr/bin/env python3
"""
quiz-from-homework skill 的辅助脚本。

负责读取现有 quiz.yml、加载新题目 JSON、执行去重、schema 校验、
生成 diff 预览以及写入文件。
"""

from __future__ import annotations

import argparse
import json
import sys
from difflib import SequenceMatcher, unified_diff
from pathlib import Path
from typing import Any

# 尝试导入 PyYAML，若未安装则给出友好提示
try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML 未安装，请运行: uv add pyyaml"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"

VALID_TYPES = {"single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"}
VALID_DIFFICULTIES = {"core", "advanced", "exam"}


def load_quiz(subject_slug: str) -> dict[str, Any]:
    """加载指定科目的 quiz.yml。"""
    path = DATA_ROOT / subject_slug / "quiz.yml"
    if not path.exists():
        raise FileNotFoundError(f"未找到 {path}")
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} 根节点不是字典")
    return data


def save_quiz(subject_slug: str, data: dict[str, Any]) -> None:
    """保存 quiz.yml。"""
    path = DATA_ROOT / subject_slug / "quiz.yml"
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
        newline="\n",
    )


def normalize_question_text(q: dict[str, Any]) -> str:
    """把题目文本和选项合并为一个无空白字符串，用于去重比较。"""
    parts = [str(q.get("question", ""))]
    for opt in q.get("options", []):
        parts.append(str(opt))
    return "".join(parts).replace(" ", "").replace("\n", "").replace("\t", "")


def find_duplicates(
    existing: list[dict[str, Any]],
    new: list[dict[str, Any]],
    threshold: float = 0.85,
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[tuple[dict[str, Any], dict[str, Any], float]]]:
    """返回 (精确重复列表, 疑似重复列表)。"""
    existing_norms = [normalize_question_text(q) for q in existing]
    exact: list[tuple[dict[str, Any], dict[str, Any]]] = []
    fuzzy: list[tuple[dict[str, Any], dict[str, Any], float]] = []

    for nq in new:
        nq_norm = normalize_question_text(nq)
        matched_exact = False
        for idx, eq_norm in enumerate(existing_norms):
            if nq_norm == eq_norm:
                exact.append((nq, existing[idx]))
                matched_exact = True
                break
            ratio = SequenceMatcher(None, nq_norm, eq_norm).ratio()
            if ratio >= threshold:
                fuzzy.append((nq, existing[idx], ratio))
        # 精确重复的题目不再参与 fuzzy 比较；上面 break 已处理
        _ = matched_exact

    return exact, fuzzy


def validate_question(q: dict[str, Any]) -> list[str]:
    """校验单道题目是否符合项目 schema。"""
    warnings: list[str] = []
    qid = str(q.get("id", "")).strip()
    qtype = str(q.get("type", "")).strip()
    difficulty = str(q.get("difficulty", "core")).strip()
    question_text = str(q.get("question", "")).strip()
    answer = q.get("answer")
    options = q.get("options", [])

    if not qid:
        warnings.append("缺少 id")
    if not qtype:
        warnings.append("缺少 type")
    elif qtype not in VALID_TYPES:
        warnings.append(f"非法 type: {qtype}")
    if not question_text:
        warnings.append("缺少 question")
    if answer is None and qtype != "short_answer":
        warnings.append("缺少 answer")
    if difficulty not in VALID_DIFFICULTIES:
        warnings.append(f"非法 difficulty: {difficulty}")

    if qtype in ("single_choice", "multiple_choice"):
        if not options or not isinstance(options, list):
            warnings.append("单选/多选缺少 options 数组")
        if qtype == "single_choice" and answer is not None:
            if not isinstance(answer, int) or answer < 0:
                warnings.append("单选 answer 应为非负整数索引")
        if qtype == "multiple_choice" and answer is not None:
            if not isinstance(answer, list) or not all(isinstance(a, int) for a in answer):
                warnings.append("多选 answer 应为整数索引数组")

    if qtype == "true_false" and answer is not None:
        if answer not in (True, False, "true", "false"):
            warnings.append("判断题 answer 应为 true/false")

    if qtype == "fill_blank" and answer is not None:
        if not isinstance(answer, (str, list)):
            warnings.append("填空题 answer 应为字符串或字符串数组")

    if qtype == "short_answer" and (answer is None or str(answer).strip() == ""):
        warnings.append("简答题/证明题 answer 不应为空，应填写核心结论")

    return warnings


def get_existing_questions(data: dict[str, Any]) -> list[dict[str, Any]]:
    """收集 quiz.yml 中所有现有题目。"""
    qs: list[dict[str, Any]] = []
    for ch in data.get("chapters", []):
        qs.extend(ch.get("questions", []))
    return qs


def find_or_create_chapter(
    data: dict[str, Any], chapter_name: str, source: str = ""
) -> dict[str, Any]:
    """在 quiz.yml 中查找章节，不存在则创建。"""
    for ch in data.get("chapters", []):
        if ch.get("chapter") == chapter_name:
            return ch
    new_ch: dict[str, Any] = {
        "chapter": chapter_name,
        "source": source,
        "questions": [],
    }
    data.setdefault("chapters", []).append(new_ch)
    return new_ch


def generate_diff_text(old_data: dict[str, Any], new_data: dict[str, Any]) -> str:
    """生成 quiz.yml 的统一 diff。"""
    old_text = yaml.safe_dump(old_data, sort_keys=False, allow_unicode=True)
    new_text = yaml.safe_dump(new_data, sort_keys=False, allow_unicode=True)
    return "".join(
        unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile="a/quiz.yml",
            tofile="b/quiz.yml",
        )
    )


def merge_questions_into_data(
    data: dict[str, Any], new_questions: list[dict[str, Any]]
) -> dict[str, Any]:
    """把新题目合并到 quiz.yml 数据中，返回新的数据副本。"""
    merged = json.loads(json.dumps(data, ensure_ascii=False))
    for q in new_questions:
        ch_name = q.get("chapter") or "未分类"
        source = q.get("source", "")
        ch = find_or_create_chapter(merged, ch_name, source)
        ch["questions"].append(q)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="quiz-from-homework 辅助脚本")
    parser.add_argument("--subject", required=True, help="科目目录 slug，例如 计算方法")
    parser.add_argument(
        "--questions", required=True, help="新题目 JSON 文件路径（数组）"
    )
    parser.add_argument(
        "--check-duplicate", action="store_true", help="检查与现有题目是否重复"
    )
    parser.add_argument("--validate", action="store_true", help="校验题目 schema")
    parser.add_argument(
        "--preview", action="store_true", help="生成合并后的 diff 预览"
    )
    parser.add_argument("--write", action="store_true", help="确认后写入 quiz.yml")
    args = parser.parse_args()

    data = load_quiz(args.subject)
    existing = get_existing_questions(data)

    with open(args.questions, encoding="utf-8") as f:
        new_questions = json.load(f)
    if not isinstance(new_questions, list):
        raise SystemExit("questions JSON 应为数组")

    exit_code = 0

    if args.validate:
        all_pass = True
        for q in new_questions:
            warns = validate_question(q)
            if warns:
                print(f"[校验失败] {q.get('id', '(无id)')}: {', '.join(warns)}")
                all_pass = False
                exit_code = 1
        if all_pass:
            print("所有新题目 schema 校验通过。")

    if args.check_duplicate:
        exact, fuzzy = find_duplicates(existing, new_questions)
        if exact:
            print(f"[精确重复] 发现 {len(exact)} 道：")
            for nq, eq in exact:
                print(f"  - {nq.get('id', '(无id)')} 与 {eq.get('id', '(无id)')}")
            exit_code = 1
        if fuzzy:
            print(f"[疑似重复] 发现 {len(fuzzy)} 道：")
            for nq, eq, ratio in fuzzy:
                print(
                    f"  - {nq.get('id', '(无id)')} 与 {eq.get('id', '(无id)')} "
                    f"(相似度 {ratio:.2f})"
                )
        if not exact and not fuzzy:
            print("未发现重复题目。")

    if args.preview:
        preview_data = merge_questions_into_data(data, new_questions)
        diff = generate_diff_text(data, preview_data)
        if diff:
            print(diff)
        else:
            print("（无变更）")

    if args.write:
        if exit_code != 0:
            print("校验或去重未通过，已取消写入。请先修复上面的问题。")
            sys.exit(1)
        merged = merge_questions_into_data(data, new_questions)
        save_quiz(args.subject, merged)
        print(f"已写入 {DATA_ROOT / args.subject / 'quiz.yml'}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
