# 智能化认知诊断系统 MVP — 设计文档

- 日期：2026-08-20
- 状态：已批准并实现
- 项目路径：`E:\cognitive-diagnosis-mvp`

> **SDD 阶段修订（2026-08-20）**：进入 SDD（Schema-Driven）阶段后，对本文档做如下简化定稿：
> 1. 数据表由 `items` + `item_params` 简化为 `questions` 表 + 固定 slip/guess（`config.py`），移除 `item_params` 表。
> 2. API 路径由 `GET /api/students/{id}/mastery`、`GET /api/students/{id}/suggestion` 调整为 `GET /api/diagnosis/{id}`、`POST /api/suggest`。
> 3. 知识图谱边字段由 `from/to/type` 统一为 `from_kp_id/to_kp_id/edge_type`。
>
> 正文已按最终实现同步更新。

## 1. 背景与目标

构建一个认知诊断系统的最小可用版本（MVP），用于根据学生的答题记录推断其对各个知识点的掌握概率。

- **输入**：学生答题记录 X 矩阵（对/错）、题目-知识点关联 Q 矩阵
- **输出**：每个学生对每个知识点的掌握概率
- **算法**：DINA 模型（简化的固定 slip/guess 变体）
- **数据规模**：5 个知识点 × 20 道题 × 10 个学生
- **存储**：SQLite
- **前端**：最简 Web 页面，选择学生 ID，展示掌握概率雷达图
- **加分项**：用 LLM（DeepSeek）根据诊断结果生成学习建议
- **知识图谱**：构建最小知识图谱结构，展示知识点的前置/后续关系

## 2. 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3 + FastAPI |
| 算法 | numpy（纯计算，无重依赖） |
| 存储 | SQLite（标准库 `sqlite3`） |
| 前端 | 原生 HTML/JS + Chart.js（CDN，无构建） |
| LLM | DeepSeek chat API（OpenAI 兼容） |
| 测试 | pytest + FastAPI TestClient |

## 3. 目录结构

```
E:\cognitive-diagnosis-mvp\
├── app/
│   ├── main.py          # FastAPI 入口 + 路由
│   ├── dina.py          # DINA 推理引擎
│   ├── simulator.py     # 模拟数据生成器（Q矩阵 + 掌握模式 + X + 知识图谱）
│   ├── db.py            # SQLite 访问层
│   ├── llm.py           # DeepSeek 学习建议生成
│   └── config.py        # slip/guess 常量、DB路径、DeepSeek 配置
├── static/
│   └── index.html       # 前端：选学生 + 雷达图 + 知识图谱 + 建议
├── scripts/
│   └── seed.py          # 一键生成模拟数据并写入 SQLite
├── tests/
│   ├── test_dina.py
│   ├── test_simulator.py
│   ├── test_api.py
│   ├── test_e2e.py
│   └── test_llm.py
├── data/
│   └── diagnosis.db     # 生成的 SQLite（gitignore）
├── docs/superpowers/specs/
├── requirements.txt
├── .env.example         # DEEPSEEK_API_KEY 模板
├── .gitignore
└── README.md
```

## 4. DINA 算法设计（核心）

### 4.1 符号

- K = 5 个知识点，J = 20 道题，N = 10 个学生
- Q 矩阵 `Q[j,k] ∈ {0,1}`：题目 j 是否考察知识点 k
- X 矩阵 `X[i,j] ∈ {0,1}`：学生 i 是否答对题目 j
- 掌握向量 `α_i ∈ {0,1}^K`：学生 i 对每个知识点的真实掌握状态（隐变量）

### 4.2 理想作答（合取模型）

`η_ij = ∏_{k: Q[j,k]=1} α_ik`

学生必须掌握题目要求的**所有**知识点，其理想作答才为 1（答对）。

### 4.3 固定题目参数

- 失误率（slip）：`s_j = P(答错 | 本应答对)`，默认 `0.1`
- 猜测率（guess）：`g_j = P(答对 | 本应不会)`，默认 `0.2`

MVP 不估计 s/g，二者为可配置常量（`config.py` 中全局可配，可通过环境变量覆盖）。

### 4.4 作答似然

给定掌握模式 α：

- 若 `η_ij = 1`：答对概率 `1 - s_j`，答错概率 `s_j`
- 若 `η_ij = 0`：答对概率 `g_j`，答错概率 `1 - g_j`

### 4.5 掌握后验（关键计算）

1. 枚举全部 `2^K = 32` 种掌握模式 α
2. 每种模式计算似然 `P(X_i | α) = ∏_j P(X_ij | η_ij(α))`
3. 取均匀先验 `P(α) = 1/32`
4. 后验 `P(α | X_i) ∝ P(α) · P(X_i | α)`（归一化）
5. **边际化**得到每个知识点的掌握概率：`P(α_k=1 | X_i) = Σ_{α: α_k=1} P(α | X_i)`

### 4.6 输出

掌握概率矩阵 `M ∈ [0,1]^{N×K}`，`M[i,k]` 即「学生 i 掌握知识点 k 的概率」，直接喂给前端雷达图。

> 说明：固定 slip/guess + 32 种模式穷举后验，是「简化但正确」的 DINA 变体。K=5 时计算量可忽略。

## 5. 数据模型（SQLite）

| 表 | 字段 | 说明 |
|---|---|---|
| `knowledge_points` | id INTEGER PK, name TEXT | 5 行 |
| `questions` | id INTEGER PK, name TEXT | 20 行 |
| `q_matrix` | question_id, kp_id | 题目-知识点关联（每道题考 1~3 个点） |
| `students` | id INTEGER PK, name TEXT | 10 行 |
| `responses` | student_id, question_id, correct INTEGER | 200 行，即 X 矩阵 |
| `kg_edges` | from_kp_id, to_kp_id, edge_type TEXT | 知识图谱边（见下） |

### 5.1 知识图谱表 `kg_edges`

- `from_kp_id`：前置知识点 ID
- `to_kp_id`：后续知识点 ID
- `edge_type`：边类型，当前固定为 `'prerequisite'`（前置关系）

含义：`from_kp_id → to_kp_id` 表示「先掌握 `from_kp_id`，再学 `to_kp_id`」。

默认数据为线性前置链：`KP1 → KP2 → KP3 → KP4 → KP5`。

### 5.2 掌握概率计算方式

掌握概率**按需实时计算**（计算量极小，不做结果缓存，以降低复杂度）。

## 6. API 设计

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 返回 `static/index.html` |
| GET | `/api/students` | 学生列表 |
| GET | `/api/diagnosis/{student_id}` | 跑 DINA，返回该生 5 个知识点掌握概率 |
| POST | `/api/suggest` | 生成学习建议（模板 / DeepSeek） |
| GET | `/api/knowledge-graph` | 返回知识点（节点）与前置/后续关系（边） |

### 6.1 响应示例

`GET /api/diagnosis/3`：

```json
{
  "student_id": 3,
  "mastery": [
    {"kp_id": 1, "kp_name": "分数加法", "probability": 0.91},
    {"kp_id": 2, "kp_name": "分数减法", "probability": 0.74},
    {"kp_id": 3, "kp_name": "分数乘法", "probability": 0.42},
    {"kp_id": 4, "kp_name": "分数除法", "probability": 0.28},
    {"kp_id": 5, "kp_name": "分数混合运算", "probability": 0.13}
  ]
}
```

`GET /api/knowledge-graph`：

```json
{
  "nodes": [
    {"id": 1, "name": "分数加法"},
    {"id": 2, "name": "分数减法"},
    {"id": 3, "name": "分数乘法"},
    {"id": 4, "name": "分数除法"},
    {"id": 5, "name": "分数混合运算"}
  ],
  "edges": [
    {"from_kp_id": 1, "to_kp_id": 2, "edge_type": "prerequisite"},
    {"from_kp_id": 2, "to_kp_id": 3, "edge_type": "prerequisite"},
    {"from_kp_id": 3, "to_kp_id": 4, "edge_type": "prerequisite"},
    {"from_kp_id": 4, "to_kp_id": 5, "edge_type": "prerequisite"}
  ]
}
```

## 7. 前端设计

单个 `static/index.html`，原生 JS + Chart.js（CDN 引入，无构建步骤）。

页面包含四块：

1. **学生选择器**：下拉框列出 10 个学生 ID。
2. **掌握概率雷达图**：5 个轴 = 知识点，0~1 刻度 = 掌握概率，选择学生后自动刷新。
3. **知识图谱**：调用 `/api/knowledge-graph`，用简单的 SVG/列表展示知识点前置链（`KP1 → KP2 → …`）。
4. **学习建议**：按钮「生成学习建议」，POST `/api/suggest`，展示文本。

## 8. LLM 学习建议（DeepSeek）

`app/llm.py` 提供 `generate_suggestion(student_id, mastery_vec)`：

1. 将掌握概率分档：`< 0.4` 未掌握 / `0.4~0.7` 部分掌握 / `> 0.7` 已掌握，挑出薄弱知识点。
2. 结合知识图谱前置链，构造 prompt（学生画像 + 薄弱点 + 建议学习路径）。
3. 调 DeepSeek chat 接口（OpenAI 兼容 endpoint `https://api.deepseek.com`，模型 `deepseek-chat`）。

**降级策略**：`DEEPSEEK_API_KEY` 未配置或调用失败时，自动回退到模板化建议（如「你在『分数除法』上掌握度仅 28%，建议先复习前置知识点『分数乘法』」），保证功能永远可用。

## 9. 数据模拟

`scripts/seed.py` 调用 `app/simulator.py` 生成数据：

1. 生成 Q 矩阵（20×5，每道题随机考 1~3 个知识点）。
2. 生成知识图谱：线性前置链 `KP1 → KP2 → KP3 → KP4 → KP5`，写入 `kg_edges`。
3. 生成学生真实掌握模式 `α_i`（遵循前置约束：掌握 KP_k 必先掌握其前置）。
4. 用 slip/guess 模拟作答，生成 X 矩阵。
5. 全部写入 SQLite。

数据生成使用固定随机种子，保证可复现。

## 10. 错误处理

| 场景 | 处理 |
|---|---|
| 学生 ID 不存在 | 返回 404 + 明确错误信息 |
| DB 未初始化（表不存在/为空） | 返回明确提示「请先运行 `python scripts/seed.py`」 |
| DeepSeek 未配置或调用失败 | 降级为模板化建议，不阻断 |
| 非法参数 | 返回 422/400 |

## 11. 测试（pytest）

- `test_dina.py`：
  - 手算用例验证后验数学（全答对某知识点的题目 → 该知识点概率 ≈ 1）
  - 后验概率和为 1
  - `s = g = 0.5`（无信息）时后验退化为先验
- `test_simulator.py`：
  - Q/X 维度正确（20×5 / 10×20）
  - 每道题至少考 1 个知识点，X 取值均为 0/1
  - 知识图谱边正确（5 个知识点，线性前置链）
- `test_api.py`（FastAPI TestClient）：
  - `/api/students` 返回 200 + 学生列表
  - `/api/diagnosis/{id}` 返回 5 个知识点概率，概率 ∈ [0,1]
  - `/api/knowledge-graph` 返回节点 + 边结构正确
  - 不存在的学生 ID 返回 404

## 12. 依赖（requirements.txt）

```
fastapi
uvicorn
numpy
requests
pytest
httpx          # TestClient 依赖
```

## 13. 范围外（非目标）

- 不做 slip/guess 参数估计（EM/MCMC）
- 不做真实题库/学生数据接入（仅内置模拟器）
- 不做用户认证、多用户权限
- 不做掌握结果持久化缓存
- 不做前端构建工程（不引入 npm/打包器）
