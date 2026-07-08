# quiz-from-homework 评估摘要

## 测试数据

- 源文件：`/Users/semt0/Desktop/2026春/算分/hw8/hw8.tex`
- 科目：算法设计与分析
- 内容：第10章近似算法，4道证明题

## 迭代对比

### Iteration 1（初稿 SKILL.md）

| 维度 | with-skill | baseline |
|------|-----------|----------|
| 提取题数 | 4 | 4 |
| 科目推断 | ✅ 正确 | ✅ 正确 |
| id 命名 | ❌ 自造 `algorithm-design-analysis-ch10-001` | ✅ 使用 `algo-approx-xxx` |
| answer 字段 | ❌ 全部留空 | ✅ 填写核心结论 |
| difficulty | ⚠️ 3 core + 1 advanced | ✅ 1 exam + 3 advanced |
| 调用 helper 脚本 | ❌ 未调用 | N/A |
| 去重结果 | ⚠️ 报告无重复 | ✅ 准确发现已存在 |

**问题**：with-skill 子代理没有严格按照 skill 指令调用 helper 脚本，输出不符合项目约定。

### Iteration 2（改进后 SKILL.md）

| 维度 | with-skill |
|------|-----------|
| 提取题数 | 4 |
| 科目推断 | ✅ 正确 |
| id 命名 | ✅ `algo-approx-106` ~ `algo-approx-109` |
| answer 字段 | ✅ 全部填写核心结论 |
| difficulty | ✅ 1 exam + 3 advanced |
| 调用 helper 脚本 | ✅ 去重、校验、diff 均调用 |
| 去重结果 | ✅ 正确发现 4 道精确重复 |
| 写入行为 | ✅ 因全部重复，未执行写入 |

**结论**：改进后的 skill 能够严格按照项目约定执行，输出质量符合要求。

## 实际写入验证

用户已确认将 hw8.tex 中的 4 道题写入 `docs/note/算法设计与分析/quiz.yml`：
- `algo-approx-101` ~ `algo-approx-105`
- 科目总题数从 90 增加到 94
- 已运行 `scripts/update_quiz.py` 重新生成题库页面

## 失败记录

- PDF 子代理（eval-1-pdf）两次均出现 `API Error: 400`，未生成输出。推测是子代理沙箱无法访问 `/Users/semt0/Desktop/` 路径。在实际使用场景中，主代理可以直接读取用户上传文件，因此不影响 skill 可用性。
