# run command -> python -m myproj
from myproj import add, greet


def main() -> None:
    print(add(10, 5))
    print(greet("Nishant"))


if __name__ == "__main__":
    main()
