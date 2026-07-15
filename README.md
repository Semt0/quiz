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
├── public/                   # 静态资源（含 build_quiz.py 生成的题库 JSON）
│   ├── data/manifest.json
│   └── data/subject-*.json
├── scripts/
│   └── build_quiz.py         # 扫描 data/ 下的 quiz.yml，生成 public/data/*.json
├── src/                      # Vite + Svelte 5 源码
│   ├── components/
│   ├── pages/
│   └── lib/
├── index.html
├── package.json
├── vite.config.js
└── .claude/skills/
    └── quiz-from-homework/   # 根据作业自动补充题库的 Claude Skill
```

## 本地开发

```bash
python3 scripts/build_quiz.py   # 生成 public/data/*.json
npm install
npm run dev                     # http://localhost:5173/
```

## 生产构建

```bash
python3 scripts/build_quiz.py
npm run build:prod
npm run preview:prod            # http://localhost:4173/quiz/
```

## 新增题目

1. 将作业或题目整理为符合 schema 的 JSON。
2. 使用 `.claude/skills/quiz-from-homework/scripts/quiz_homework_helper.py` 去重、校验并写入 `data/<subject>/quiz.yml`。
3. 运行 `python3 scripts/build_quiz.py` 重新生成题库数据。

## 部署

推送到 `main`/`master` 分支后，GitHub Actions（`.github/workflows/docs.yml`）会自动构建并部署到 GitHub Pages。
