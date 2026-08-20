-- 认知诊断系统 MVP — SQLite 建表语句
-- 说明：slip/guess 为固定常量（见 app/config.py），故不再单独建 item_params 表。

PRAGMA foreign_keys = ON;

-- 知识点
CREATE TABLE IF NOT EXISTS knowledge_points (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 题目
CREATE TABLE IF NOT EXISTS questions (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- 学生
CREATE TABLE IF NOT EXISTS students (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

-- 题目-知识点关联（Q 矩阵）
CREATE TABLE IF NOT EXISTS q_matrix (
    question_id INTEGER NOT NULL REFERENCES questions(id),
    kp_id       INTEGER NOT NULL REFERENCES knowledge_points(id),
    PRIMARY KEY (question_id, kp_id)
);

-- 学生作答记录（X 矩阵）
CREATE TABLE IF NOT EXISTS responses (
    student_id  INTEGER NOT NULL REFERENCES students(id),
    question_id INTEGER NOT NULL REFERENCES questions(id),
    correct     INTEGER NOT NULL CHECK (correct IN (0, 1)),
    PRIMARY KEY (student_id, question_id)
);

-- 知识图谱边（前置关系）
CREATE TABLE IF NOT EXISTS kg_edges (
    from_kp_id INTEGER NOT NULL REFERENCES knowledge_points(id),
    to_kp_id   INTEGER NOT NULL REFERENCES knowledge_points(id),
    edge_type  TEXT NOT NULL DEFAULT 'prerequisite' CHECK (edge_type = 'prerequisite'),
    PRIMARY KEY (from_kp_id, to_kp_id)
);

-- 常用查询索引
CREATE INDEX IF NOT EXISTS idx_responses_student ON responses(student_id);
CREATE INDEX IF NOT EXISTS idx_q_matrix_kp ON q_matrix(kp_id);
