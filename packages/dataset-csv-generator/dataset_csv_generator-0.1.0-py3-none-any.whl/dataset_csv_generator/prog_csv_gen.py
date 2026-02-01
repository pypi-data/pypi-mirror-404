#!/usr/bin/env python3

import argparse
from pathlib import Path
import WorkingWithFiles as rnfunc


def main():
    parser = argparse.ArgumentParser(
        description="Generate CSV labels from directory structure"
    )

    parser.add_argument(
        "--output-csv-file",
        default="test_labels.csv",
        help="Output CSV file name"
    )

    parser.add_argument(
        "--input-base-dir",
        required=True,
        help="Base directory with images"
    )

    parser.add_argument(
        "--input-format",
        action="append",
        help="Image format (can be used multiple times, e.g. --input-format .png)"
    )

    args = parser.parse_args()

    base_dir = Path(args.input_base_dir)

    if not base_dir.exists():
        parser.error(f"Base directory does not exist: {base_dir}")

    format_set = set(args.input_format) if args.input_format else {".png"}

    print("\nConfiguration:")
    print("  csv_file :", args.output_csv_file)
    print("  base_dir :", base_dir)
    print("  formats  :", format_set)
    print()

    rnfunc.generate_csv_file_from_dir_structure(
        str(base_dir),
        list(format_set),
        args.output_csv_file
    )


if __name__ == "__main__":
    main()

