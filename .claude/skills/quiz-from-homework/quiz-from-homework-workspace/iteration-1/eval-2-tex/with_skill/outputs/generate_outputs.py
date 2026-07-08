import json
import sys
import os
import re
import difflib
from pathlib import Path

# --- Configuration ---
SUBJECT = "算法设计与分析"
SUBJECT_SLUG = "algorithm-design-analysis"
CHAPTER = "第10章 近似算法"
SOURCE_FILE = "hw8.tex"
OUTPUT_DIR = Path("/Users/semt0/blog/Semt0.github.io/.claude/skills/quiz-from-homework/quiz-from-homework-workspace/iteration-1/eval-2-tex/with_skill/outputs")
QUIZ_YML_PATH = Path("/Users/semt0/blog/Semt0.github.io/docs/note/算法设计与分析/quiz.yml")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Extracted questions from hw8.tex ---
# The tex file contains 4 proof problems (10.1, 10.3, 10.4, 10.5)
# All are short_answer type as they require proof/explanation

questions = [
    {
        "id": "algorithm-design-analysis-ch10-001",
        "type": "short_answer",
        "difficulty": "core",
        "question": "10.1 最小顶点覆盖问题的近似算法 MVC 任取一条边，把这条边的两个端点加入顶点覆盖集，现在改为只把这条边的一个端点加入顶点覆盖集，其余不变。试分析这个修改后的算法的近似性能。",
        "options": [],
        "answer": "",
        "explanation": "修改后的算法不再具有有界的常数近似比，其近似性能可以任意差。考虑星形图实例：中心顶点 c 与 n 个叶子顶点相连。最优解只需选中心顶点 c，大小为 1。但修改后的算法每一步可能不幸选中叶子顶点，需要将所有 n 个叶子顶点都加入覆盖集，输出大小为 n。因此近似比 ALG/OPT = n/1 = n，当 n→∞ 时趋于无穷大。",
        "keywords": ["最小顶点覆盖", "近似算法", "近似比", "星形图", "MVC"],
        "chapter": CHAPTER,
        "source": SOURCE_FILE
    },
    {
        "id": "algorithm-design-analysis-ch10-002",
        "type": "short_answer",
        "difficulty": "core",
        "question": "10.3 装箱问题（优化形式）：任给 n 件物品，物品 j 的重量为 w_j，1≤j≤n。限制每只箱子装入物品的总重量不超过 B，w_j 和 B 都是正整数，且 w_j≤B。要求用最少的箱子装入所有物品。考虑首次适合算法（FF）：按输入顺序装物品，对每一件物品依次检查每只箱子，只要能装下就装入，所有已打开的箱子都装不下时才新开一只箱子。证明：对装箱问题的所有实例 I，FF(I) < 2·OPT(I)。",
        "options": [],
        "answer": "",
        "explanation": "证明思路：先证引理——对任意两只箱子 S_i 和 S_j（i<j），都有 w(S_i)+w(S_j)>B。因为装入 S_j 的第一件物品 x 无法装入当时已打开的 S_i（否则 FF 会把它放入 S_i），故 w(S_i')+w_x>B，而 w(S_i)≥w(S_i')，w(S_j)≥w_x，所以 w(S_i)+w(S_j)>B。由此，m 只箱子两两配对可得 ⌊m/2⌋ 对，每对重量之和>B，故总重量 W > ⌊m/2⌋·B。而 OPT(I) ≥ ⌈W/B⌉ ≥ ⌊m/2⌋+1，于是 2·OPT(I) ≥ 2⌊m/2⌋+2 > m = FF(I)。",
        "keywords": ["装箱问题", "首次适合算法", "FF", "近似比", "OPT", "引理"],
        "chapter": CHAPTER,
        "source": SOURCE_FILE
    },
    {
        "id": "algorithm-design-analysis-ch10-003",
        "type": "short_answer",
        "difficulty": "advanced",
        "question": "10.4 证明：装箱问题不存在近似比 r < 3/2 的多项式时间近似算法，除非 P=NP。",
        "options": [],
        "answer": "",
        "explanation": "采用反证法，从划分问题（Partition）归约。划分问题：给定 n 个正整数 a_1,...,a_n，判定是否存在子集 S 使得 Σ_{i∈S} a_i = Σ_{i∉S} a_i。假设存在近似比 r<3/2 的多项式时间近似算法 A。对划分实例，令 T=Σa_i，若 T 为奇数直接回答否；否则构造装箱实例：n 件物品重量 w_j=a_j，箱子容量 B=T/2。若划分有解，则 OPT=2，A(I)≤2r<3，故 A(I)≤2；若划分无解，则 OPT≥3，此时必有 A(I)≥3（否则 A(I)=2 会给出划分方案，矛盾）。因此划分问题有解当且仅当 A(I)≤2，可在多项式时间内求解划分问题。由于划分问题是 NP-完全的，故除非 P=NP，这样的 A 不存在。",
        "keywords": ["装箱问题", "近似比下界", "P=NP", "划分问题", "NP-完全", "归约"],
        "chapter": CHAPTER,
        "source": SOURCE_FILE
    },
    {
        "id": "algorithm-design-analysis-ch10-004",
        "type": "short_answer",
        "difficulty": "core",
        "question": "10.5 设无向图 G=⟨V,E⟩，V_1∪V_2=V，V_1∩V_2=∅，称 (V_1,V_2)={(u,v)|(u,v)∈E, 且 u∈V_1,v∈V_2} 是 G 的割集。求最大割集问题：任给无向图 G，求边数最多的割集。考虑局部改进算法 MCUT：令 V_1=V，V_2=∅。如果存在顶点 u，在 u 关联的边中非割边多于割边，就把 u 移到另一侧。直到不存在这样的顶点为止。证明：对最大割集问题的每一个实例 I，OPT(I) ≤ 2·MCUT(I)。",
        "options": [],
        "answer": "",
        "explanation": "设 MCUT 终止时割边集为 E_cut，非割边集为 E_non。终止条件：对任意顶点 u，d_non(u) ≤ d_cut(u)。将所有顶点不等式相加得 Σ d_non(u) ≤ Σ d_cut(u)。由于每条非割边两端在同一侧，被左端计数两次，故左端=2|E_non|；每条割边两端分属两侧，被右端计数两次，故右端=2|E_cut|。因此 2|E_non| ≤ 2|E_cut|，即 |E_non| ≤ |E_cut|。总边数 |E| = |E_cut|+|E_non| ≤ 2|E_cut| = 2·MCUT(I)。而 OPT(I) ≤ |E|，故 OPT(I) ≤ 2·MCUT(I)。",
        "keywords": ["最大割集", "局部改进算法", "MCUT", "近似比", "割边", "非割边"],
        "chapter": CHAPTER,
        "source": SOURCE_FILE
    }
]

# --- Step 1: Save extracted questions ---
extracted_path = OUTPUT_DIR / "extracted_questions.json"
with open(extracted_path, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print(f"[1] Extracted {len(questions)} questions → {extracted_path}")

# --- Step 2: Load existing quiz.yml for deduplication ---
existing_questions = []
if QUIZ_YML_PATH.exists():
    try:
        import yaml
        with open(QUIZ_YML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and isinstance(data, list):
            existing_questions = data
        elif data and isinstance(data, dict) and "questions" in data:
            existing_questions = data["questions"]
    except Exception as e:
        print(f"    Warning: Could not parse existing quiz.yml: {e}")
        # Fallback: try to read as text and extract question fields
        with open(QUIZ_YML_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        # Simple heuristic: look for question texts
        existing_questions = []

print(f"[2] Loaded {len(existing_questions)} existing questions from quiz.yml")

# --- Step 3: Deduplication ---
def normalize_text(text):
    """Normalize text for comparison."""
    text = str(text)
    # Remove LaTeX commands, extra spaces, punctuation
    text = re.sub(r'\\[a-zA-Z]+\*?(\{[^}]*\})?', '', text)
    text = re.sub(r'[\$\s\n\r\t.,;:!?()\[\]{}]', '', text)
    return text.lower()

def similarity(a, b):
    return difflib.SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

exact_duplicates = []
fuzzy_duplicates = []
kept = []

for q in questions:
    dup_found = False
    for eq in existing_questions:
        eq_text = eq.get("question", "") if isinstance(eq, dict) else str(eq)
        if normalize_text(q["question"]) == normalize_text(eq_text):
            exact_duplicates.append(q)
            dup_found = True
            break
        if similarity(q["question"], eq_text) > 0.85:
            fuzzy_duplicates.append((q, eq))
            dup_found = True
            break
    if not dup_found:
        kept.append(q)

print(f"[3] Deduplication: exact_dup={len(exact_duplicates)}, fuzzy_dup={len(fuzzy_duplicates)}, kept={len(kept)}")

# --- Step 4: Schema validation ---
VALID_TYPES = {"single_choice", "multiple_choice", "true_false", "fill_blank", "short_answer"}
VALID_DIFFICULTIES = {"core", "advanced", "exam"}

validation_errors = []
for q in questions:
    qid = q.get("id", "unknown")
    if q.get("type") not in VALID_TYPES:
        validation_errors.append(f"{qid}: invalid type '{q.get('type')}'")
    if q.get("difficulty") not in VALID_DIFFICULTIES:
        validation_errors.append(f"{qid}: invalid difficulty '{q.get('difficulty')}'")
    if q.get("type") in ("single_choice", "multiple_choice") and not q.get("options"):
        validation_errors.append(f"{qid}: missing options for choice type")
    if q.get("type") == "single_choice":
        ans = q.get("answer")
        opts = q.get("options", [])
        if not isinstance(ans, int) or ans < 0 or (opts and ans >= len(opts)):
            validation_errors.append(f"{qid}: invalid single_choice answer index")
    if q.get("type") == "multiple_choice":
        ans = q.get("answer")
        if not isinstance(ans, list) or not all(isinstance(x, int) for x in ans):
            validation_errors.append(f"{qid}: invalid multiple_choice answer")
    if q.get("type") == "true_false":
        ans = q.get("answer")
        if ans not in (True, False, "true", "false"):
            validation_errors.append(f"{qid}: invalid true_false answer")

validation_passed = len(validation_errors) == 0
print(f"[4] Validation: {'PASSED' if validation_passed else 'FAILED'} ({len(validation_errors)} errors)")
for err in validation_errors:
    print(f"    - {err}")

# --- Step 5: Generate diff preview ---
diff_lines = []
diff_lines.append("=" * 60)
diff_lines.append("DIFF PREVIEW: 即将追加到 docs/note/算法设计与分析/quiz.yml")
diff_lines.append("=" * 60)
diff_lines.append(f"科目: {SUBJECT}")
diff_lines.append(f"章节: {CHAPTER}")
diff_lines.append(f"来源: {SOURCE_FILE}")
diff_lines.append(f"新增题目数: {len(kept)}")
diff_lines.append(f"跳过（重复）: {len(exact_duplicates) + len(fuzzy_duplicates)}")
diff_lines.append("")

for i, q in enumerate(kept, 1):
    diff_lines.append(f"--- 新增题目 {i} ---")
    diff_lines.append(f"  id: {q['id']}")
    diff_lines.append(f"  type: {q['type']}")
    diff_lines.append(f"  difficulty: {q['difficulty']}")
    diff_lines.append(f"  question: {q['question'][:120]}...")
    diff_lines.append(f"  explanation: {q['explanation'][:120]}...")
    diff_lines.append("")

if exact_duplicates:
    diff_lines.append("--- 精确重复（已跳过）---")
    for q in exact_duplicates:
        diff_lines.append(f"  - {q['id']}: {q['question'][:80]}...")
    diff_lines.append("")

if fuzzy_duplicates:
    diff_lines.append("--- 疑似重复（已跳过，待复核）---")
    for q, eq in fuzzy_duplicates:
        diff_lines.append(f"  - {q['id']}: {q['question'][:80]}...")
    diff_lines.append("")

diff_text = "\n".join(diff_lines)
diff_path = OUTPUT_DIR / "diff_preview.txt"
with open(diff_path, "w", encoding="utf-8") as f:
    f.write(diff_text)

print(f"[5] Diff preview → {diff_path}")

# --- Step 6: Generate summary ---
summary_lines = []
summary_lines.append("=" * 60)
summary_lines.append("SUMMARY: quiz-from-homework 执行摘要")
summary_lines.append("=" * 60)
summary_lines.append(f"输入文件: /Users/semt0/Desktop/2026春/算分/hw8/hw8.tex")
summary_lines.append(f"推断科目: {SUBJECT} (置信度: 高 — 文件路径含'算分'，内容标题为'算法设计与分析第八次作业')")
summary_lines.append(f"目标文件: {QUIZ_YML_PATH}")
summary_lines.append("")
summary_lines.append(f"提取题目总数: {len(questions)}")
summary_lines.append(f"  - 题型: 全部为 short_answer（证明题）")
summary_lines.append(f"  - 难度分布: core=3, advanced=1")
summary_lines.append(f"  - 章节: {CHAPTER}")
summary_lines.append("")
summary_lines.append(f"去重结果:")
summary_lines.append(f"  - 精确重复: {len(exact_duplicates)}")
summary_lines.append(f"  - 疑似重复 (fuzzy>0.85): {len(fuzzy_duplicates)}")
summary_lines.append(f"  - 保留待写入: {len(kept)}")
summary_lines.append("")
summary_lines.append(f"校验结果: {'通过' if validation_passed else '未通过'}")
if validation_errors:
    summary_lines.append(f"  错误详情:")
    for err in validation_errors:
        summary_lines.append(f"    - {err}")
summary_lines.append("")
summary_lines.append(f"LLM 自洽性检查: N/A（题目已有完整解答，无需 LLM 生成）")
summary_lines.append("")
summary_lines.append(f"待复核题目: {len(fuzzy_duplicates)}")
if fuzzy_duplicates:
    for q, eq in fuzzy_duplicates:
        summary_lines.append(f"  - {q['id']}: 与现有题目相似度>0.85")
summary_lines.append("")
summary_lines.append(f"输出文件位置: {OUTPUT_DIR}")
summary_lines.append("  - extracted_questions.json")
summary_lines.append("  - diff_preview.txt")
summary_lines.append("  - summary.txt")
summary_lines.append("  - confirmation_prompt.txt")

summary_text = "\n".join(summary_lines)
summary_path = OUTPUT_DIR / "summary.txt"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(summary_text)

print(f"[6] Summary → {summary_path}")

# --- Step 7: Generate confirmation prompt ---
confirmation_lines = []
confirmation_lines.append("=" * 60)
confirmation_lines.append("CONFIRMATION PROMPT")
confirmation_lines.append("=" * 60)
confirmation_lines.append("")
confirmation_lines.append(f"天依已经从作业文件 {SOURCE_FILE} 中提取了 {len(questions)} 道证明题，")
confirmation_lines.append(f"准备追加到 {SUBJECT} 的题库中。")
confirmation_lines.append("")
confirmation_lines.append(f"【科目】{SUBJECT}")
confirmation_lines.append(f"【章节】{CHAPTER}")
confirmation_lines.append(f"【新增】{len(kept)} 题")
confirmation_lines.append(f"【跳过】{len(exact_duplicates) + len(fuzzy_duplicates)} 题（重复/疑似重复）")
confirmation_lines.append("")
confirmation_lines.append("题目列表:")
for i, q in enumerate(kept, 1):
    confirmation_lines.append(f"  {i}. [{q['difficulty']}] {q['question'][:100]}...")
confirmation_lines.append("")
if fuzzy_duplicates:
    confirmation_lines.append("⚠ 以下题目与现有题库疑似重复，请确认是否保留:")
    for q, eq in fuzzy_duplicates:
        confirmation_lines.append(f"   - {q['id']}")
    confirmation_lines.append("")
confirmation_lines.append("请确认是否写入？")
confirmation_lines.append("  - 输入 'yes' 或 '确认' → 追加到 quiz.yml 并运行 update_quiz.py")
confirmation_lines.append("  - 输入 'no' 或 '取消' → 放弃写入，仅保存输出文件")
confirmation_lines.append("  - 输入 'skip <id>' → 跳过特定题目后写入")
confirmation_lines.append("")

confirmation_text = "\n".join(confirmation_lines)
confirmation_path = OUTPUT_DIR / "confirmation_prompt.txt"
with open(confirmation_path, "w", encoding="utf-8") as f:
    f.write(confirmation_text)

print(f"[7] Confirmation prompt → {confirmation_path}")
print("=" * 60)
print("All output files generated successfully!")
print(f"Output directory: {OUTPUT_DIR}")
