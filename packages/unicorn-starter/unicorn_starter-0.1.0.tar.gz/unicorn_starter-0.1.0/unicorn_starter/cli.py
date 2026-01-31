import sys
from pathlib import Path
from importlib.resources import files


def write_template(name, target_name):
    template_path = files("unicorn_starter").joinpath(f"templates/{name}")
    content = template_path.read_text()

    Path(target_name).write_text(content)
    print(f"Создан файл: {target_name}")


def main():
    if len(sys.argv) < 2:
        print("Команды: init-api, init-parser")
        return

    cmd = sys.argv[1]

    if cmd == "init-api":
        write_template("api.py.txt", "api.py")

    elif cmd == "init-parser":
        write_template("parser.py.txt", "parser.py")

    else:
        print("Неизвестная команда")


if __name__ == "__main__":
    main()
