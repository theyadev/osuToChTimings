#!/usr/bin/env python3
"""
osu! to Clone Hero Timing Converter

This script converts timing points from osu! beatmap format to Clone Hero format.
It extracts BPM and time signature changes from an osu! beatmap file and outputs
them in a format compatible with Clone Hero.
"""

import sys
import logging
import argparse

from src.conversion import extract_timing_points, convert_to_clone_hero_format, generate_clone_hero_output

DEFAULT_TICK_RATE = 192
DEFAULT_INPUT_FILE = "example_beatmap.osu"

logger = logging.getLogger(__name__)


def setup_logging(debug_mode: bool) -> None:
    """Configure the logging level based on the debug mode.

    Args:
        debug_mode: Whether to show debug logs
    """
    if debug_mode:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")


def setup_parser() -> argparse.Namespace:
    """Set up and configure the argument parser for command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Convert osu! beatmap timing points to Clone Hero format")
    parser.add_argument(
        "input_file",
        nargs="?",
        default=DEFAULT_INPUT_FILE,
        help=f"Path to the osu! beatmap file (default: {DEFAULT_INPUT_FILE})",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        help="Path to save the output file (if not specified, output to terminal only)",
    )
    parser.add_argument(
        "-t",
        "--tick-rate",
        dest="tick_rate",
        type=int,
        default=DEFAULT_TICK_RATE,
        help=f"Clone Hero tick rate (default: {DEFAULT_TICK_RATE})",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def write_clone_hero_file(output: str, output_file_path: str) -> None:
    """Write the generated output to a file.

    Args:
        output: The string content to write
        output_file_path: Path to the output file
    """
    try:
        with open(output_file_path, "w", encoding="utf-8") as file:
            file.write(output)
    except IOError as e:
        logger.error(f"Failed to write output file: {str(e)}")
        raise


def main() -> None:
    """Main function to run the conversion process."""
    args = setup_parser()
    setup_logging(args.debug)

    logger.info(f"Converting {args.input_file}")
    timing_points = extract_timing_points(args.input_file)
    logger.debug(f"Found {len(timing_points)} timing points")
    ch_timing_lines = convert_to_clone_hero_format(timing_points, args.tick_rate)
    output = generate_clone_hero_output(ch_timing_lines)

    if args.output_file:
        write_clone_hero_file(output, args.output_file)
        logger.info(f"Conversion complete. Output saved to {args.output_file}")
    else:
        print("\n" + output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)
