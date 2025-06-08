import sqlite3 # Python 内置的数据库模块，非常适合这个项目

# 定义数据库文件的路径
# 它会在项目根目录的 data 文件夹下创建一个名为 todo.db 的文件
DATABASE_PATH = 'data/todo.db'
SCHEMA_PATH = 'todo/schema.sql'

def get_db():
    """
    打开一个数据库连接。
    后续我们会优化这里，实现类似 Flask g 对象的功能。
    但现在，先让它返回一个新连接。
    """
    conn = sqlite3.connect(DATABASE_PATH)
    # 这行让查询结果可以像字典一样通过列名访问，更方便
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    初始化数据库：根据 schema.sql 文件创建表。
    """
    with get_db() as conn:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
    print("数据库已成功初始化！")

def add_todo(content, deadline=None):
    """向数据库中添加一个新的待办事项"""
    # 模板和数据是分开的
    sql = "INSERT INTO todo (content, deadline) VALUES (?, ?);"
    with get_db() as conn:
        conn.execute(sql, (content, deadline))
    print(f"已添加待办事项：'{content}'")

def get_all_todos():
    """从数据库中获取所有的待办事项"""
    sql = "SELECT task_id, content, is_done, created_at, deadline FROM todo ORDER BY created_at DESC;"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        # fetchall() 获取所有查询结果
        results = cursor.fetchall()
        # fetchall() 返回的是一个元组列表，我们把它转成字典列表，方便使用
        return [dict(row) for row in results]

def update_todo_status(task_id, is_done):
    """更新指定ID任务的完成状态"""
    sql = "UPDATE todo SET is_done = ? WHERE task_id = ?;"
    with get_db() as conn:
        conn.execute(sql, (is_done, task_id))
    print(f"已更新任务 {task_id} 的状态。")

def delete_todo(task_id):
    """根据ID删除一个任务"""
    sql = "DELETE FROM todo WHERE task_id = ?;"
    with get_db() as conn:
        conn.execute(sql, (task_id,))
    print(f"已删除任务 {task_id}。")

def edit_todo(task_id, content=None, start_at=None, deadline=None):
    """
    通用的编辑函数，可以修改任务的任意一个或多个字段。
    """
    # 这是一个非常常见的模式：动态构建UPDATE语句
    set_clauses = []
    params = []

    if content is not None:
        set_clauses.append("content = ?")
        params.append(content)
    
    if start_at is not None:
        set_clauses.append("start_at = ?")
        params.append(start_at)

    if deadline is not None:
        set_clauses.append("deadline = ?")
        params.append(deadline)

    # 如果用户什么都没传，就没必要执行更新
    if not set_clauses:
        print("没有提供任何需要修改的内容。")
        return

    # 用逗号把所有 'key = ?' 拼接起来
    sql = f"UPDATE todo SET {', '.join(set_clauses)} WHERE task_id = ?;"
    
    # 别忘了把 task_id 加到参数列表的最后，对应 WHERE id = ?
    params.append(task_id)

    with get_db() as conn:
        conn.execute(sql, tuple(params))
    print(f"任务 {task_id} 已更新。")

# 我们可以创建一个新的 find_todos 函数，或者直接增强 get_all_todos
# 为了清晰，我们先创建一个新的
def find_todos(status=None, text_search=None):
    """
    根据不同条件查找任务。
    status: 0 for 未完成, 1 for 已完成
    text_search: 在 content 字段中进行模糊搜索
    """
    where_clauses = []
    params = []
    
    # 基础查询语句
    sql = "SELECT task_id, content, is_done, created_at, deadline FROM todo"

    if status is not None:
        where_clauses.append("is_done = ?")
        params.append(status)

    if text_search:
        # 使用 LIKE 进行模糊查询
        where_clauses.append("content LIKE ?")
        # 参数需要我们手动加上 %
        params.append(f"%{text_search}%")
    
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    
    sql += " ORDER BY created_at DESC;"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
        return [dict(row) for row in results]
   
