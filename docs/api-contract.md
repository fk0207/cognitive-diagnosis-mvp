# API 接口契约

基础路径：`/api`。所有响应均为 `application/json`。

## 1. GET /api/students

获取学生列表。

**响应** `200`：

```json
[
  {"id": 1, "name": "学生1"},
  {"id": 2, "name": "学生2"}
]
```

## 2. GET /api/diagnosis/{student_id}

获取某学生的诊断结果（各知识点掌握概率）。

**路径参数**：`student_id`（int）

**响应** `200`：

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

**错误**：`404`（学生不存在）

## 3. POST /api/suggest

根据诊断结果生成学习建议（加分项）。

**请求体**：

```json
{
  "student_id": 3,
  "mastery": [
    {"kp_id": 4, "kp_name": "分数除法", "probability": 0.28},
    {"kp_id": 5, "kp_name": "分数混合运算", "probability": 0.13}
  ]
}
```

**响应** `200`：

```json
{
  "student_id": 3,
  "suggestion": "你在『分数除法』上掌握度仅 28%，建议先复习前置知识点『分数乘法』。"
}
```

> 说明：`/api/suggest` 无状态，直接消费诊断结果；DeepSeek 未配置或失败时降级为模板化建议。

## 4. GET /api/knowledge-graph

获取知识点节点与前置/后续关系。

**响应** `200`：

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

> 注：本端点对应 `kg_edges` 表，为上一轮要求的知识图谱展示接口。
