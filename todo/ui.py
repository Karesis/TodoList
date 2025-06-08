# todo/ui.py

# 从我们的 db 模块中导入所有需要的函数
from . import db
import time

def _print_tasks(tasks):
    """美观地打印任务列表的辅助函数"""
    if not tasks:
        print("太棒了！当前没有待办事项。")
        return

    print("\n--- 任务列表 ---")
    for task in tasks:
        # 根据 is_done 状态显示不同的标记
        status_icon = "[x]" if task['is_done'] else "[ ]"
        
        # 如果有截止日期，就格式化显示
        deadline_str = f" (截止日期: {task['deadline']})" if task['deadline'] else ""
        
        print(f"{status_icon} ID: {task['task_id']:<3} | {task['content']}{deadline_str}")
    print("------------------")


def print_menu():
    """打印主菜单"""
    print("\n===== 待办事项列表 =====")
    print("1. 查看所有任务")
    print("2. 添加新任务")
    print("3. 标记/取消标记任务")
    print("4. 删除任务")
    print("5. 退出")
    print("========================")


def main_loop():
    """程序的主循环"""
    while True:
        print_menu()
        choice = input("请输入你的选择 (1-5): ")

        if choice == '1':
            print("\n正在获取所有任务...")
            all_tasks = db.get_all_todos()
            _print_tasks(all_tasks)

        elif choice == '2':
            print("\n--- 添加新任务 ---")
            content = input("请输入任务内容: ")
            if not content:
                print("错误：内容不能为空！")
                continue

            deadline = input("请输入截止日期 (格式: YYYY-MM-DD HH:MM:SS)，或直接回车跳过: ")
            if not deadline:
                deadline = None # 如果用户直接回车，就设置为 None
            
            db.add_todo(content, deadline)
            print("任务已成功添加！")

        elif choice == '3':
            print("\n--- 标记任务 ---")
            try:
                task_id = int(input("请输入要标记的任务ID: "))
                status = int(input("输入 '1' 标记为完成, '0' 标记为未完成: "))
                if status not in [0, 1]:
                    raise ValueError("状态只能是 0 或 1")
                db.update_todo_status(task_id, status)
                print("状态更新成功！")
            except ValueError as e:
                print(f"输入无效，请确保ID和状态都是正确的数字。错误: {e}")

        elif choice == '4':
            print("\n--- 删除任务 ---")
            try:
                task_id = int(input("请输入要删除的任务ID: "))
                db.delete_todo(task_id)
                print("任务删除成功！")
            except ValueError:
                print("输入无效，请输入正确的任务ID数字。")

        elif choice == '5':
            print("感谢使用，再见！")
            break
        else:
            print("无效输入，请重新输入。")
        
        # 在很多操作后，重新显示列表是一个好习惯
        if choice in ['2', '3', '4']:
            print("\n更新后的任务列表：")
            all_tasks = db.get_all_todos()
            _print_tasks(all_tasks)

        # 暂停一下，让用户可以看清操作结果
        time.sleep(2)


