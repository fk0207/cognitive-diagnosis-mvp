# 智能化认知诊断系统 MVP

基于 **DINA 模型**（Deterministic Inputs, Noisy "And" gate）的认知诊断最小可用系统：输入学生答题记录（X 矩阵，对/错）与题目-知识点关联（Q 矩阵），输出每个学生对每个知识点的掌握概率，并提供知识图谱展示与 LLM 学习建议。

## 功能特性

- **DINA 诊断**：根据答题记录推断学生对 5 个知识点的掌握概率
- **数据模拟器**：内置可复现的模拟数据生成（5 知识点 × 20 题 × 10 学生）
- **知识图谱**：展示知识点前置/后续关系（线性链）
- **LLM 学习建议**：接入 DeepSeek，未配置 Key 或调用失败时自动降级为模板建议
- **Web 可视化**：学生下拉选择 + 掌握概率雷达图 + 知识图谱 + 学习建议

## 技术栈

Python 3.9+（推荐 3.11） · FastAPI · SQLite · numpy · Chart.js · DeepSeek API · pytest

## 项目结构

```
.
├── app/
│   ├── config.py       # 全局配置（DB 路径、slip/guess、DeepSeek 参数）
│   ├── schema.sql      # SQLite 建表语句（6 张表）
│   ├── schemas.py      # Pydantic 类型定义
│   ├── simulator.py    # 数据模拟器
│   ├── dina.py         # DINA 算法核心
│   ├── db.py           # SQLite 数据访问层
│   ├── llm.py          # DeepSeek 学习建议（含降级）
│   └── main.py         # FastAPI 路由 + 静态资源
├── scripts/
│   └── seed.py         # 种子脚本（生成并写入模拟数据）
├── static/
│   └── index.html      # 前端页面
├── tests/              # 测试（53 个用例）
├── docs/               # PRD、ER 图、API 契约、设计文档
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 环境要求

- Python 3.9+（推荐 3.11）
- 注意：Windows 下若 `python` 指向 3.6 等旧版本，请统一使用 `py -3`

### 2. 安装依赖

```bash
pip install -r requirements.txt
# 如需清华镜像加速：
# pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 初始化数据

```bash
python scripts/seed.py
# 生成 5 知识点 × 20 题 × 10 学生的模拟数据，写入 data/diagnosis.db
```

### 4. 启动服务

```bash
python -m uvicorn app.main:app --reload
```

浏览器打开 http://127.0.0.1:8000 即可使用。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DIAGNOSIS_DB` | `data/diagnosis.db` | SQLite 数据库路径 |
| `DINA_SLIP` | `0.1` | 失误率（本应答对却答错） |
| `DINA_GUESS` | `0.2` | 猜测率（本应不会却答对） |
| `DEEPSEEK_API_KEY` | 空 | DeepSeek API Key；留空则学习建议走模板降级 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek 接口地址 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | DeepSeek 模型名 |

Windows（PowerShell）示例：

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."
```

Git Bash 示例：

```bash
export DEEPSEEK_API_KEY="sk-..."
```

（`.env.example` 为参考模板，可复制为 `.env` 后按需加载。）

## API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/students` | 学生列表 |
| GET | `/api/diagnosis/{student_id}` | 某学生的掌握概率（不存在返回 404） |
| POST | `/api/suggest` | 生成学习建议（body：`{student_id, mastery}`） |
| GET | `/api/knowledge-graph` | 知识点节点 + 前置关系 |

交互式 API 文档：http://127.0.0.1:8000/docs

## DINA 模型简介

DINA 是一种认知诊断模型，采用「合取」假设：题目 j 的理想作答 η_ij 为 1，当且仅当学生 i 掌握了题目 j 要求的所有知识点：

```
η_ij = ∏_{k: Q[j,k]=1} α_ik
```

本 MVP 采用简化版本：固定 slip/guess（0.1/0.2）、均匀先验 + 后验边缘化，得到每个知识点的掌握概率 P(α_ik=1|X)。

## 测试

```bash
pytest tests/ -v
```

53 个测试覆盖：DINA 算法、API 接口、数据模拟器、端到端流程。测试通过环境变量 `DIAGNOSIS_DB` 指向临时数据库，自包含、不污染本地数据。

## 文档

- `docs/PRD.md` — 产品需求文档
- `docs/er-diagram.md` — ER 图（Mermaid）
- `docs/api-contract.md` — API 契约
- `docs/superpowers/specs/` — 设计文档
