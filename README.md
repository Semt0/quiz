# Semt0's Quiz

[![Deploy Quiz](https://github.com/Semt0/quiz/actions/workflows/docs.yml/badge.svg)](https://github.com/Semt0/quiz/actions/workflows/docs.yml)

独立复习题库站点，从博客仓库拆分出来，专门承载各科目的交互式复习题。

**在线地址**: <https://semt0.github.io/quiz/>

## 目录结构

```text
.
├── data/                     # 题库原始数据（按科目分目录的 quiz.yml）
│   ├── 算法设计与分析/
│   └── 计算方法/
├── docs/                     # 由 update_quiz.py 生成的题库页面
│   ├── index.md
│   ├── 算法设计与分析.md
│   ├── 计算方法.md
│   ├── javascripts/quiz.js
│   └── stylesheets/quiz.css
├── scripts/
│   └── update_quiz.py        # 扫描 data/ 下的 quiz.yml 生成 docs/
├── overrides/                # Zensical 主题覆盖（加载 KaTeX 等）
└── .claude/skills/
    └── quiz-from-homework/   # 根据作业自动补充题库的 Claude Skill
```

## 本地开发

```bash
uv sync
uv run python scripts/update_quiz.py
uv run zensical serve
```

## 构建

```bash
uv run python scripts/update_quiz.py
uv run zensical build --clean
```

## 新增题目

1. 将作业或题目整理为符合 schema 的 JSON。
2. 使用 `.claude/skills/quiz-from-homework/scripts/quiz_homework_helper.py` 去重、校验并写入 `data/<subject>/quiz.yml`。
3. 运行 `uv run python scripts/update_quiz.py` 重新生成页面。

## 部署

推送到 `main`/`master` 分支后，GitHub Actions（`.github/workflows/docs.yml`）会自动构建并部署到 GitHub Pages。
