from . import ui
from . import db
def main():
    print("欢迎使用 TodoList 应用！")
    db.init_db()
    ui.main_loop()


if __name__ == '__main__':
    main()
