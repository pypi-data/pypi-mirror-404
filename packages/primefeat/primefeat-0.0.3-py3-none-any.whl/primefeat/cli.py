from typer import Typer
from typing import List


app = Typer()


@app.command()
def main() -> None:
    print("Welcome to PrimeFeat CLI!")


if __name__ == "__main__":
    main()
