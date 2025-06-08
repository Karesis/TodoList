-- 在开发阶段，每次初始化都重建数据表，确保结构最新
DROP TABLE IF EXISTS todo;

CREATE TABLE todo (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    is_done INTEGER NOT NULL DEFAULT 0, -- 0 for false, 1 for true
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 新增的弹性时间字段，允许为空
    start_at TIMESTAMP NULL,
    deadline TIMESTAMP NULL
);
