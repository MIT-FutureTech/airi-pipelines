#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

USAGE_PATTERN = re.compile(r"Usage: ({.*?}) \[")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize token usage totals from a log file.",
    )
    parser.add_argument("log_file", type=Path)
    args = parser.parse_args()

    log_path: Path = args.log_file
    input_total = 0
    output_total = 0
    count = 0

    for line in log_path.read_text().splitlines():
        match = USAGE_PATTERN.search(line)
        if not match:
            continue
        usage = json.loads(match.group(1))
        input_total += usage["input_tokens"]
        output_total += usage["output_tokens"]
        count += 1

    total = input_total + output_total
    print(f"API calls:     {count:>12,}")
    print(f"Input tokens:  {input_total:>12,}")
    print(f"Output tokens: {output_total:>12,}")
    print(f"Total tokens:  {total:>12,}")


if __name__ == "__main__":
    main()
