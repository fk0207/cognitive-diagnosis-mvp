# 核心 Prompt 记录

> 项目：智能化认知诊断系统 MVP（DINA 认知诊断）
> 开发环境：Claude Code（接入 DeepSeek V4 Pro 模型）+ Superpowers 插件
> 仓库：https://github.com/fk0207/cognitive-diagnosis-mvp
>
> 本文记录开发全流程中的核心 Prompt，按「SDD → TDD → 整合/E2E」三个阶段组织。
> 每段 Prompt 后附「意图」与「挑战/纠偏」说明，重点记录当 AI 输出偏离目标时，如何通过 Prompt 将其拉回正轨。

---

## Step 1：SDD 建模阶段（契约/模型驱动）

### Prompt 1 · 需求澄清与架构设计

**Prompt**（节选）：

> 我要做一个智能化认知诊断系统 MVP。业务背景：输入学生答题记录（X 矩阵，对/错）和题目-知识点关联（Q 矩阵）；输出每个学生对每个知识点的掌握概率；算法 DINA 模型；数据 5 个知识点 × 20 道题 × 10 个学生；存储 SQLite；前端最简 Web（选学生 ID，展示雷达图）；加分项用 LLM 根据诊断结果生成学习建议。请帮我先理清需求和架构设计。

**意图**：先不写代码，把业务目标、输入输出、算法、数据规模、存储、前端、加分项一次性说清，让 AI 给出需求理解和架构方案，作为后续所有阶段的「锚点」。

**挑战/纠偏**：这是 Brainstorming 阶段的起点。通过澄清性问题（Python 3 + FastAPI、简化 DINA 用固定 slip/guess、内置数据模拟器、DeepSeek API）把模糊需求收敛为可实现的 MVP 边界，避免一开始就陷入实现细节。

---

### Prompt 2 · 补充知识图谱表（把遗漏需求拉回正轨）

**Prompt**：

> 设计整体 OK，但需要补一个知识图谱表。作业要求里写了「构建最小知识图谱结构，展示知识点的前置/后续关系」…… kg_edges(from_kp_id, to_kp_id, edge_type)…… 同时在 API 里加一个端点 GET /api/knowledge-graph。补上这个表后，设计就完整了。

**意图**：在架构设计被认可后，明确指出 AI 遗漏了「知识图谱」这一硬性需求，要求补表 + 补端点。

**挑战/纠偏**：这是第一次「把 AI 拉回正轨」——初始设计聚焦 DINA 与 Q/X 矩阵，忽略了作业里知识图谱的要求。用户用「作业要求里写了……」锚定到原始需求，AI 据此补上 `kg_edges` 表与对应端点，设计才算完整。

---

### Prompt 3 · 定义 Schema / 契约 / 类型（只定义骨架，不写业务）

**Prompt**（节选）：

> 现在进入 SDD 阶段，请帮我定义：1. SQLite 数据库 Schema（建表语句）… 2. API 接口契约：GET /api/students、GET /api/diagnosis/{student_id}、POST /api/suggest 3. 数据类型定义（Pydantic models）。先不要写业务逻辑代码，只定义骨架。

**意图**：用「契约驱动」先锁定数据库结构与接口契约，为后续代码生成提供明确锚点，抑制大模型自由发挥导致的幻觉。

**挑战/纠偏**：明确指令「先不要写业务逻辑代码，只定义骨架」，防止 AI 越过 SDD 边界提前写实现。此阶段还把初版设计中的 `items` + `item_params` 简化为 `questions` 表 + 固定 slip/guess（去除 `item_params`），是一次合理的简化。

---

## Step 2：TDD 算法与核心逻辑实现阶段

### Prompt 4 · 先写测试（RED）

**Prompt**（节选）：

> 现在进入 TDD 阶段。只写测试，不要写实现代码。创建 tests/test_dina.py、tests/test_api.py、tests/__init__.py。运行 pytest tests/ -v，预期结果：所有测试失败（RED 状态）。不要写任何业务实现代码！

**意图**：对复杂算法（DINA）强制「测试先行」，用失败测试锁定期望行为，再写实现。

**挑战/纠偏**：反复强调「只写测试、预期 RED、不要写实现」，确保 AI 不跳过红绿循环。测试先于实现，保证算法正确性可验证。

---

### Prompt 5 · 实现 DINA 让测试转绿

**Prompt**（节选）：

> 现在实现 app/dina.py，让 tests/test_dina.py 的 12 个测试通过。需要实现：compute_ideal_response、compute_likelihood、compute_posterior、compute_mastery_probability、compute_all_students_mastery。

**意图**：以测试为验收标准，逐个实现 DINA 的合取理想作答、似然、后验、边缘化。

**挑战/纠偏**：AI 严格按函数签名实现，实现完成后跑测试确认 12 个用例从 RED 转 GREEN。

---

### Prompt 6 · 实现数据访问层与 API 路由

**Prompt**（节选）：

> 创建 app/db.py，实现 SQLite 数据访问层（get_all_students、get_student、get_q_matrix、get_student_responses、get_kg_edges…）；现在更新 app/main.py，将 stub 替换为真实实现。

**意图**：把 SDD 阶段定义的契约落地为可运行的数据库访问与 API 路由。

**挑战/纠偏**：实现需与 Schema/契约严格一致（表名、字段名、端点路径），AI 依据 SDD 骨架填充，避免偏离契约。

---

### Prompt 7 · 删除冗余 app/seed.py（纠偏：遏制过度设计）

**Prompt**：

> 有 app/seed.py 又有 scripts/seed.py，应该删除 app/seed.py。

**意图**：纠正 AI 的一次「过度设计」——AI 为在脚本与测试间复用种子逻辑，把逻辑抽到了 `app/seed.py`，导致与 `scripts/seed.py` 重复。

**挑战/纠偏**：用户点明冗余，AI 把逻辑合并回 `scripts/seed.py`（单一来源），删除 `app/seed.py` 及多余的 `scripts/__init__.py`，并确认测试仍通过。这体现 YAGNI 原则——不为复用而复用。

---

## Step 3：整合与 E2E 端到端测试阶段

### Prompt 8 · 前端可视化

**Prompt**（节选）：

> 现在实现前端可视化界面。创建 static/index.html 并更新 app/main.py（启用静态文件服务、加首页路由）。

**意图**：补齐展现层——学生选择器 + 掌握概率雷达图（Chart.js）+ 知识图谱 + 学习建议。

**挑战/纠偏**：AI 完成后用 TestClient 冒烟验证首页、静态资源、各 API 均 200，确保前后端联通。

---

### Prompt 9 · 接入 LLM 学习建议（加分项）

**Prompt**（节选）：

> 阶段 1：创建 app/llm.py（DeepSeek API 学习建议，降级策略：无 Key 或失败时返回模板建议）；更新 app/main.py 的 /api/suggest 端点改为调用 llm.generate_suggestion()。

**意图**：实现加分项，并把降级策略作为第一公民——无 Key / 异常时不影响前端。

**挑战/纠偏**：AI 用三层降级（无 Key / 非 200 / 异常）保证健壮性；随后补 `tests/test_llm.py` 用 mock 覆盖降级与成功路径，避免真实网络依赖。

---

### Prompt 10 · 端到端集成测试（契约纠偏）

**Prompt**（节选）：

> 现在补充端到端集成测试。创建 tests/test_e2e.py（完整流程：获取学生列表 → 诊断 → 验证结果；知识图谱；学习建议；异常处理）。

**意图**：用 E2E 测试保障整体链路（数据层 → 算法 → API → 前端数据流）的可靠性。

**挑战/纠偏**：用户提供的测试草稿里，`/api/suggest` 被写成了 GET、知识图谱边字段写成 `from_id`/`to_id`，与真实契约（`POST /api/suggest`、`from_kp_id`/`to_kp_id`）不符。AI 识别出这些契约偏差并修正测试，而不是照抄让测试「假绿」——这正体现了「AI 输出偏离契约时被拉回正轨」的掌控力。

---

## 阶段小结

| 阶段 | 范式 | 核心动作 |
|---|---|---|
| Step 1 | SDD | 需求澄清 → 架构设计 → 补知识图谱 → 定义 Schema/契约/类型 |
| Step 2 | TDD | 先写失败测试 → 实现 DINA 算法 → 数据层 + API → 冗余纠偏 |
| Step 3 | 整合/E2E | 前端可视化 → LLM 建议 → E2E 测试 + 契约纠偏 |
