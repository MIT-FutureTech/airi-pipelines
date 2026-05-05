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
    parser.add_argument(
        "--input-cost",
        type=float,
        metavar="$/MT",
        help="Input cost in dollars per million tokens",
    )
    parser.add_argument(
        "--output-cost",
        type=float,
        metavar="$/MT",
        help="Output cost in dollars per million tokens",
    )
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

    input_cost_str = ""
    output_cost_str = ""
    total_cost_str = ""
    if args.input_cost is not None and args.output_cost is not None:
        input_cost = input_total * args.input_cost / 1_000_000
        output_cost = output_total * args.output_cost / 1_000_000
        total_cost = input_cost + output_cost
        input_cost_str = f"${input_cost:>8,.4f}"
        output_cost_str = f"${output_cost:>8,.4f}"
        total_cost_str = f"${total_cost:>8,.4f}"

    print(f"API calls:     {count:>12,}")
    print(f"Input tokens:  {input_total:>12,}    {input_cost_str}")
    print(f"Output tokens: {output_total:>12,}    {output_cost_str}")
    print(f"Total tokens:  {total:>12,}    {total_cost_str}")


if __name__ == "__main__":
    main()
