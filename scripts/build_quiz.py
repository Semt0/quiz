#!/usr/bin/env python3
"""
自动扫描 data/*/quiz.yml，校验题目 schema，
生成 public/data/manifest.json（科目清单 + 统计）与
public/data/<id>.json（每科目完整题目，前端懒加载）。

移植自旧 scripts/update_quiz.py，复用其 schema 校验与题目解析逻辑，
但产物由 Markdown 改为 JSON，并使用 ASCII 稳定的科目 id。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML 未安装，请运行: uv add pyyaml 或 pip install pyyaml"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
OUT_DIR = REPO_ROOT / "public" / "data"

VALID_TYPES = {"single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"}
VALID_DIFFICULTIES = {"core", "advanced", "exam"}

MANIFEST_VERSION = 1


@dataclass
class Question:
    id: str
    type: str
    difficulty: str
    question: str
    options: list[str] = field(default_factory=list)
    answer: Any = None
    explanation: str = ""
    keywords: list[str] = field(default_factory=list)
    chapter: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "difficulty": self.difficulty,
            "question": self.question,
            "answer": self.answer,
            "explanation": self.explanation,
            "chapter": self.chapter,
            "source": self.source,
        }
        if self.options:
            d["options"] = self.options
        if self.keywords:
            d["keywords"] = self.keywords
        return d


@dataclass
class QuizSubject:
    subject: str
    dir: str
    sid: str
    path: Path
    questions: list[Question] = field(default_factory=list)

    @property
    def question_count(self) -> int:
        return len(self.questions)

    def difficulty_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {"core": 0, "advanced": 0, "exam": 0}
        for q in self.questions:
            if q.difficulty in counts:
                counts[q.difficulty] += 1
        return counts

    def type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {t: 0 for t in VALID_TYPES}
        for q in self.questions:
            if q.type in counts:
                counts[q.type] += 1
        return counts

    def chapter_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for q in self.questions:
            counts[q.chapter] = counts.get(q.chapter, 0) + 1
        return counts


def subject_id(dir_name: str, index: int) -> str:
    """为科目生成 ASCII 稳定 id。ASCII 合法目录名原样使用，否则回退 subject-<index>。"""
    if dir_name.isascii() and dir_name.replace("-", "_").isidentifier():
        return dir_name
    return f"subject-{index}"


def parse_question(raw: dict[str, Any], chapter: str, source: str, path: Path) -> Question | None:
    """解析单个题目，返回 Question 或 None（解析失败时打印警告）。"""
    qid = str(raw.get("id", "")).strip()
    qtype = str(raw.get("type", "")).strip()
    difficulty = str(raw.get("difficulty", "core")).strip()
    question_text = str(raw.get("question", "")).strip()
    answer = raw.get("answer")
    explanation = str(raw.get("explanation", "")).strip()
    keywords = raw.get("keywords", [])
    options = raw.get("options", [])

    warnings: list[str] = []

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
        warnings.append(f"非法 difficulty: {difficulty}，使用 core")
        difficulty = "core"

    options = list(options) if isinstance(options, list) else []
    option_count = len(options)

    if qtype in ("single_choice", "multiple_choice"):
        if not options:
            warnings.append("单选/多选缺少 options 数组")
        if qtype == "single_choice" and answer is not None:
            if not isinstance(answer, int) or answer < 0:
                warnings.append("单选 answer 应为非负整数索引")
            elif option_count and answer >= option_count:
                warnings.append(f"单选 answer 索引越界: {answer} >= {option_count}")
        if qtype == "multiple_choice" and answer is not None:
            if not isinstance(answer, list) or not all(isinstance(a, int) for a in answer):
                warnings.append("多选 answer 应为整数索引数组")
            elif option_count:
                bad = [a for a in answer if a < 0 or a >= option_count]
                if bad:
                    warnings.append(f"多选 answer 索引越界: {bad}")
                # normalize: deduplicate and sort
                uniq = sorted(set(answer))
                if uniq != answer:
                    warnings.append("多选 answer 已去重排序")
                    answer = uniq

    if qtype == "true_false" and answer is not None:
        if answer not in (True, False, "true", "false"):
            warnings.append("判断题 answer 应为 true/false")
        elif isinstance(answer, str):
            answer = answer.lower() == "true"
            warnings.append("判断题 answer 字符串已转为布尔")

    if qtype == "fill_blank" and answer is not None:
        if isinstance(answer, list):
            if not answer:
                warnings.append("填空题 answer 数组为空")
        elif isinstance(answer, str):
            if answer.strip() == "":
                warnings.append("填空题 answer 为空字符串")
        else:
            warnings.append("填空题 answer 应为字符串或字符串数组")

    if qtype == "short_answer":
        if options:
            warnings.append("简答题不应有 options")
        if answer is None or (isinstance(answer, str) and answer.strip() == ""):
            # self-eval path; keep answer as-is
            pass
        elif isinstance(answer, list) and not answer:
            warnings.append("简答题 answer 数组为空")

    if warnings:
        print(f"  [警告] {path.name} 题目 {qid or '(无id)'}: {', '.join(warnings)}")
        if "缺少 id" in warnings or "缺少 type" in warnings or "缺少 question" in warnings:
            return None

    return Question(
        id=qid or "unknown",
        type=qtype or "single_choice",
        difficulty=difficulty,
        question=question_text,
        options=options,
        answer=answer,
        explanation=explanation,
        keywords=list(keywords) if isinstance(keywords, list) else [],
        chapter=chapter,
        source=source,
    )


def load_yaml_quiz(path: Path, index: int) -> QuizSubject:
    """加载单个 quiz.yml 文件。"""
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SystemExit(f"{path} 根节点不是字典")

    dir_name = path.parent.name
    subject = str(data.get("subject", dir_name))
    sid = subject_id(dir_name, index)
    quiz = QuizSubject(subject=subject, dir=dir_name, sid=sid, path=path)

    chapters = data.get("chapters", [])
    if not isinstance(chapters, list):
        raise SystemExit(f"{path} 中 chapters 不是列表")

    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        chapter_name = str(ch.get("chapter", ""))
        source = str(ch.get("source", ""))
        questions = ch.get("questions", [])
        if not isinstance(questions, list):
            continue
        for q_raw in questions:
            if not isinstance(q_raw, dict):
                continue
            q = parse_question(q_raw, chapter_name, source, path)
            if q:
                quiz.questions.append(q)

    return quiz


def collect_quizzes() -> list[QuizSubject]:
    """扫描所有 quiz.yml 文件。"""
    quizzes: list[QuizSubject] = []
    paths = sorted(DATA_ROOT.rglob("quiz.yml"))
    seen_qids: dict[str, tuple[str, Path]] = {}
    for index, quiz_path in enumerate(paths, start=1):
        print(f"加载 {quiz_path.relative_to(REPO_ROOT)} ...")
        quiz = load_yaml_quiz(quiz_path, index)
        for q in quiz.questions:
            if q.id in seen_qids:
                other_sid, other_path = seen_qids[q.id]
                print(f"[错误] 重复 qid {q.id!r}: {quiz_path} 与 {other_path}")
                sys.exit(1)
            seen_qids[q.id] = (quiz.sid, quiz_path)
        quizzes.append(quiz)
    return quizzes


def build_manifest(quizzes: list[QuizSubject]) -> dict[str, Any]:
    """构建 manifest.json 数据。"""
    subjects: list[dict[str, Any]] = []
    all_qids: dict[str, list[str]] = {}
    for quiz in quizzes:
        diff = quiz.difficulty_counts()
        types = quiz.type_counts()
        ch_counts = quiz.chapter_counts()
        chapters = [
            {"name": ch, "count": cnt}
            for ch, cnt in sorted(ch_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
        subjects.append({
            "id": quiz.sid,
            "name": quiz.subject,
            "dir": quiz.dir,
            "questionCount": quiz.question_count,
            "dataFile": f"data/{quiz.sid}.json",
            "chapters": chapters,
            "difficulty": diff,
            "types": types,
        })
        all_qids[quiz.sid] = [q.id for q in quiz.questions]

    return {
        "version": MANIFEST_VERSION,
        "generatedAt": _now_iso(),
        "subjects": subjects,
        "allQids": all_qids,
    }


def _now_iso() -> str:
    """生成 ISO 时间戳（构建时刻）。"""
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    print(f"已生成 {path.relative_to(REPO_ROOT)}")


def build_all() -> list[QuizSubject]:
    quizzes = collect_quizzes()
    if not quizzes:
        print("未找到任何 quiz.yml 文件，退出。")
        sys.exit(1)

    total = sum(q.question_count for q in quizzes)
    print(f"\n共发现 {len(quizzes)} 个科目，{total} 道题目。")

    manifest = build_manifest(quizzes)
    write_json(OUT_DIR / "manifest.json", manifest)

    current_sids = {quiz.sid for quiz in quizzes}
    if OUT_DIR.exists():
        for f in OUT_DIR.glob("*.json"):
            if f.name == "manifest.json":
                continue
            sid = f.stem
            if sid not in current_sids:
                f.unlink()
                print(f"已删除过期数据文件 {f.relative_to(REPO_ROOT)}")

    for quiz in quizzes:
        questions_data = [q.to_dict() for q in quiz.questions]
        write_json(OUT_DIR / f"{quiz.sid}.json", questions_data)

    print("\n生成摘要:")
    for quiz in quizzes:
        diff = quiz.difficulty_counts()
        print(f"  - {quiz.subject} ({quiz.sid}): {quiz.question_count} 题 "
              f"(核心 {diff['core']}, 进阶 {diff['advanced']}, 真题 {diff['exam']})")
    print("\n题库数据生成完成！")
    return quizzes


def watch(poll_interval: float = 1.0) -> None:
    """监听 data/ 下 quiz.yml 变化，重新生成。"""
    print(f"监听 {DATA_ROOT.relative_to(REPO_ROOT)} （每 {poll_interval}s 轮询）...")
    mtimes: dict[Path, float] = {}
    for p in DATA_ROOT.rglob("quiz.yml"):
        mtimes[p] = p.stat().st_mtime

    try:
        while True:
            changed = False
            current_paths = set(DATA_ROOT.rglob("quiz.yml"))
            for p in current_paths:
                m = p.stat().st_mtime
                if mtimes.get(p) != m:
                    mtimes[p] = m
                    changed = True
            # 检测删除
            removed = set(mtimes) - current_paths
            if removed:
                for p in removed:
                    mtimes.pop(p, None)
                changed = True
            if changed:
                print("\n检测到变化，重新生成...")
                try:
                    build_all()
                except Exception as e:  # noqa: BLE001
                    print(f"[错误] 生成失败: {e}")
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n停止监听。")


def main() -> None:
    parser = argparse.ArgumentParser(description="扫描 data/ 生成 public/data/*.json 题库数据")
    parser.add_argument("--watch", action="store_true", help="监听 data/ 变化并重新生成")
    parser.add_argument("--poll", type=float, default=1.0, help="--watch 时的轮询间隔（秒）")
    args = parser.parse_args()

    if args.watch:
        build_all()
        watch(args.poll)
    else:
        build_all()


if __name__ == "__main__":
    main()
