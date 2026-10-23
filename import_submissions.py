# RU: Используем команду, определённую в пакете.
# EN: Use the command defined in the package.
from school_lab.cli import main


# RU: Передаём операционной системе код завершения команды.
# EN: Pass the command's exit code to the operating system.
if __name__ == "__main__":
    raise SystemExit(main())
