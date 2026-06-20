import argparse
from pathlib import Path

from toolbox.text_processing.pdf import convert_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--page", type=int, default=0)
    args = parser.parse_args()

    print(convert_to_markdown(args.pdf_path, pages=[args.page]))


if __name__ == "__main__":
    main()
