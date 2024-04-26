"""
Reads a version string from stdin and writes a python script which exports it
to stdout.
"""

import argparse
import pathlib


def main():
    parser = argparse.ArgumentParser(
        description="Hard codes the version number reported by odoo_sort"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        default=pathlib.Path("src/odoo_sort/_version.py"),
        help="Where to write the frozen version number",
    )
    parser.add_argument(
        "version",
        type=str,
        help="The new version number to write",
    )

    args = parser.parse_args()

    output = f"""\"\"\"
Generated by `scripts/freeze_version.py`.  Do not edit directly.
\"\"\"

VERSION = {args.version!r}
"""

    args.output.write_text(output)


if __name__ == "__main__":
    main()
