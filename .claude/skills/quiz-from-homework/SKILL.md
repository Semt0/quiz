---
name: quiz-from-homework
description: |
  根据用户上传的作业文件自动补充博客复习题库。当用户提到"作业""补充题库""加到题库""生成题库""quiz""复习题""把这道题加进去""作业里的题"或上传 PDF/图片/Markdown/文本作业文件时触发。
  自动推断科目、提取题目、生成解答、校验 schema、检测重复、做 LLM 自洽性检查，最终展示 diff 并经用户确认后写入 data/<subject>/quiz.yml，然后运行 scripts/build_quiz.py 重新构建静态站点。
compatibility: |
  需要 Python 3.13+、uv 以及项目依赖。PDF/图片 OCR 依赖外部工具（优先用已安装的 pymupdf/pdf2image/pytesseract，如无则提示用户安装）。
---

## 1 触发条件

当用户出现以下任一意图时，使用本 skill：

- 上传作业文件并说"把这个加到题库""补充到复习题""整理成 quiz"
- "根据这份作业生成题库"
- "这道题没有解答，帮我补一下"
- "把作业里的错题/好题加入题库"
- 任何涉及"作业" + "题库/quiz/复习"的组合

## 2 整体流程

1. **接收文件**：读取用户提供的作业文件路径。支持 `PDF`、`PNG/JPG`、`Markdown`、`纯文本`。
2. **识别科目**：结合文件路径、文件名和文件内容，自动推断应补充到 `data/<subject>/` 下的哪个科目。如果推断置信度低，询问用户确认。
3. **提取题目**：从作业中抽离题目，尽量保留原题表述，识别题型（单选/多选/判断/填空/简答）。
4. **去重**：**必须**调用 helper 脚本 `quiz_homework_helper.py --check-duplicate`，与目标科目的 `quiz.yml` 现有题目比对，高度相似的题目跳过。
5. **补解答**：若题目缺少 `answer` 或 `explanation`，调用 LLM 生成解答，并做 LLM 自洽性检查。
6. **校验**：**必须**调用 helper 脚本 `quiz_homework_helper.py --validate`，使用项目 schema 校验字段格式。
7. **展示 diff**：**必须**调用 helper 脚本 `quiz_homework_helper.py --preview`，用统一 diff 格式展示即将写入的变更，等待用户确认。
8. **写入并更新**：用户确认后，**必须**调用 helper 脚本 `quiz_homework_helper.py --write` 追加到 `data/<subject>/quiz.yml`，然后运行 `uv run python scripts/build_quiz.py` 重新构建静态站点。

**核心原则：所有确定性的去重、校验、diff、写入操作都必须通过 helper 脚本完成，不要自己重新实现这些逻辑，也不要直接用 Read/Edit/Write 修改 `data/<subject>/quiz.yml`。这样能保证结果一致、可验证、可复现。**

## 3 读取作业文件

根据文件扩展名选择读取方式：

| 扩展名 | 处理方式 |
|--------|----------|
| `.pdf` | 用 `pymupdf` 或 `pdfplumber` 提取文本；若文本为空或太少，改用 OCR（`pdf2image` + `pytesseract`）。 |
| `.png/.jpg/.jpeg/.webp` | 用 `pytesseract` 或视觉模型做 OCR。 |
| `.md/.txt/.tex` | 直接读取文本。 |
| 其他 | 尝试按文本读取，失败时询问用户。 |

提取文本后，保留原始内容用于后续解析。

## 4 科目推断

推断优先级：

1. 若用户在 prompt 中明确说了科目名（如"这是计算方法作业"），直接使用。
2. 若文件路径中包含 `data/<subject>/` 或文件名含科目关键词，优先匹配。
3. 扫描 `data/` 下所有 `quiz.yml` 的 `subject` 字段，计算内容关键词匹配度。
4. 若最高匹配度低于阈值（如 0.3），列出候选科目让用户选择。

## 5 题目提取

把作业文本交给 LLM，要求输出 JSON 数组：

```json
[
  {
    "id": "建议的 id",
    "type": "single_choice|multiple_choice|true_false|fill_blank|short_answer",
    "difficulty": "core|advanced|exam",
    "question": "题目文本（保留 LaTeX）",
    "options": ["选项1", "选项2", ...],
    "answer": "...",
    "explanation": "解析",
    "keywords": ["关键词"],
    "chapter": "章节名",
    "source": "来源文件名"
  }
]
```

### 5.1 id 命名规则（重要）

id 必须参考目标科目现有 `quiz.yml` 的命名风格。通常是：

```
<subject-abbreviation>-<chapter-keyword>-<3-digit-number>
```

例如：
- 算法设计与分析：`algo-dp-001`、`algo-np-011`、`algo-approx-101`
- 计算方法：`compute-error-001`、`compute-interp-002`

生成 id 前，先读取目标科目的 `quiz.yml`，找到该章节已有的最大编号，然后顺序递增。**不要自己创造新的 id 风格**（如 `algorithm-design-analysis-ch10-001` 是不允许的）。

### 5.2 字段填写规则

- `type`：单选 `single_choice`，多选 `multiple_choice`，判断 `true_false`，填空 `fill_blank`，简答/证明 `short_answer`。
- `difficulty`：根据题目难度选择 `core`（基础概念/简单计算）、`advanced`（需要推理/证明）、`exam`（真题/高难度）。默认 `core`。
- `question`：保留原题文本，包括 LaTeX 公式。如果原题很长，保留核心陈述，不要过度压缩。
- `options`：单选/多选必填，其他题型可为空数组。
- `answer`：
  - 单选：非负整数索引（0-based）
  - 多选：整数索引数组
  - 判断：`true` 或 `false`
  - 填空：字符串或字符串数组
  - 简答/证明：**必须**填写核心结论或答案要点，不能为空字符串。如果原解答很长，把核心结论放在 `answer`，详细推导放在 `explanation`。
- `explanation`：详细解析、证明过程、推导步骤。如果原题有 solution，尽量提取完整内容。
- `keywords`：3-5 个核心关键词，便于检索。
- `chapter`：尽量从作业中的章节标题提取（如"近似算法"、"动态规划"）。若无法提取，使用"未分类"并告知用户。
- `source`：来源文件名（如 `hw8.tex`、`homework.pdf`）。

### 5.3 证明题 / short_answer 题特殊处理

证明题虽然需要完整推导，但 `answer` 字段**不能留空**。处理方式：
- `answer`：一句话概括核心结论或关键引理
- `explanation`：完整证明过程

例如：
```json
{
  "type": "short_answer",
  "question": "证明：对装箱问题的所有实例 I，FF(I) < 2·OPT(I)。",
  "answer": "关键引理：任意两只已打开箱子的重量之和大于 B。由此推出 2·OPT > FF。",
  "explanation": "完整证明：设 FF 打开 m 只箱子 S1,...,Sm。对 i<j，Sj 中第一件物品 x 装入时 Si 已打开且装不下 x，故 w(Si)+w(Sj)>B。将所有箱子两两配对得总重量 W > ⌊m/2⌋·B，于是 OPT ≥ ⌈W/B⌉ ≥ ⌊m/2⌋+1，因此 FF = m < 2·OPT。"
}
```

## 6 去重

**必须**调用 helper 脚本：

```bash
uv run python .claude/skills/quiz-from-homework/scripts/quiz_homework_helper.py \
  --subject <slug> \
  --questions <new_questions.json> \
  --check-duplicate
```

去重策略由 helper 脚本实现：
- 先用题目文本的精确匹配去重。
- 再用 fuzzy 匹配（difflib.SequenceMatcher ratio > 0.85）标记疑似重复。

**如果检测到精确重复，必须跳过这些题目，不要写入。** 如果是疑似重复，展示给用户，询问是否保留。**不要自己写代码去重，也不要用肉眼判断。**

## 7 补充解答与 LLM 自洽性检查

对每道缺少 `answer` 或 `explanation` 的题目：

1. 让 LLM 基于题目和科目知识生成 `answer` 和 `explanation`。
2. 自洽性检查：让另一个独立的 LLM（用不同 prompt）仅根据题目重新回答，再与生成答案比对。若不一致，标记为"待复核"，不自动写入。
3. 对数学/算法题，优先用符号推理或代码验证；无法验证时明确告知用户"此题为 LLM 生成，请复核"。

## 8 校验与写入

**必须**按顺序调用 helper 脚本：

### 8.1 校验

```bash
uv run python .claude/skills/quiz-from-homework/scripts/quiz_homework_helper.py \
  --subject <slug> \
  --questions <new_questions.json> \
  --validate
```

校验内容：
- `type` 在允许集合内。
- `difficulty` 在允许集合内。
- 单选/多选必须有 `options`。
- 单选 `answer` 是合法索引。
- 多选 `answer` 是整数数组。
- 判断 `answer` 是 `true`/`false`。
- 填空 `answer` 是字符串或字符串数组。
- 简答题 `answer` 不能为空字符串。

### 8.2 预览 diff

```bash
uv run python .claude/skills/quiz-from-homework/scripts/quiz_homework_helper.py \
  --subject <slug> \
  --questions <new_questions.json> \
  --preview
```

把 diff 输出展示给用户，并明确询问："是否确认写入？" 等待用户回答"是"/"确认"/"写入"。

### 8.3 写入

用户确认后：

```bash
uv run python .claude/skills/quiz-from-homework/scripts/quiz_homework_helper.py \
  --subject <slug> \
  --questions <new_questions.json> \
  --write
```

最后运行：

```bash
uv run python scripts/build_quiz.py
```

## 9 错误处理

- 任何一步失败都要清楚告知用户失败原因，不偷偷写入。
- 若作业文件无法解析，询问用户是否需要手动粘贴文本。
- 若科目推断失败，列出候选科目让用户选择。
- 若 LLM 自洽性检查发现可疑答案，单独列出这些题目，让用户决定是否跳过、修改或手动补充。
- 若 helper 脚本报告校验失败或重复，必须停止写入，让用户确认如何处理。

## 10 示例

**用户**："帮我把这份 PDF 作业里的题加到算法题库"

**处理**：
1. 读取 PDF 文本。
2. 推断科目为"算法设计与分析"。
3. 提取 5 道题，其中 2 道无解答。
4. 生成解答并做自洽性检查，全部通过。
5. 调用 helper 脚本去重、校验、生成 diff。
6. 展示 diff，用户确认。
7. 调用 helper 脚本写入 `data/算法设计与分析/quiz.yml`。
8. 运行 `build_quiz.py`。
9. 报告：成功添加 5 题，跳过 0 题，待复核 0 题。
