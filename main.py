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
from typing import List, Tuple

DEFAULT_TICK_RATE = 192
DEFAULT_BPM = 120
DEFAULT_TIME_SIGNATURE = 4
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


def extract_timing_points(osu_file_path: str) -> List[str]:
    """Extract timing points from an osu! beatmap file.

    Only extracts timing points that are actual BPM changes (not inherited points).

    Args:
        osu_file_path: Path to the osu! beatmap file

    Returns:
        List of timing point lines

    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the file doesn't contain timing points section
    """
    try:
        with open(osu_file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file '{osu_file_path}' not found")

    try:
        timing_section_parts = content.split("[TimingPoint")
        if len(timing_section_parts) < 2:
            raise ValueError("No TimingPoints section found in the file")

        timing_section = timing_section_parts[1].split("]")[1].split("\n")

        # Filter out empty lines and inherited timing points (last value before the last is "1")
        timing_points = [
            line for line in timing_section if line.strip() and len(line.split(",")) >= 8 and line.split(",")[-2] == "1"
        ]

        if not timing_points:
            logger.warning("No timing points found in the file")

        return timing_points
    except (IndexError, ValueError) as e:
        raise ValueError(f"Failed to parse the osu! file: {str(e)}")


def convert_to_clone_hero_format(
    timing_points: List[str], tick_rate: int = DEFAULT_TICK_RATE
) -> List[Tuple[int, int, int, float]]:
    """Convert osu! timing points to Clone Hero timing points.

    Args:
        timing_points: List of osu! timing point lines
        tick_rate: Clone Hero tick rate (default: 192)

    Returns:
        List of Clone Hero timing points [ticks, bpm, signature, minutes]
    """
    # Start with a default timing point at tick 0
    ch_timing_lines = [[0, DEFAULT_BPM, DEFAULT_TIME_SIGNATURE, 0.0]]

    for line in timing_points:
        try:
            # Parse osu! timing point values
            parts = line.split(",")
            if len(parts) < 8:
                logger.warning(f"Skipping malformed timing point: {line}")
                continue

            timing = int(parts[0])
            beat_length = float(parts[1])  # in milliseconds
            signature = int(parts[2])

            # Calculate BPM from beat length
            bpm = round(60000 / beat_length)

            # Convert osu! timing (ms) to minutes
            minutes = timing / 60000
            logger.debug(f"Converted time {timing}ms to {minutes:.6f} minutes")

            # Calculate ticks based on time elapsed since last timing point
            last_tick, last_bpm, _, last_minutes = ch_timing_lines[-1]
            minutes_elapsed = minutes - last_minutes
            logger.debug(f"Time elapsed since last point: {minutes_elapsed:.6f} minutes")

            # Calculate ticks elapsed using the formula: minutes * BPM * tick_rate
            ticks_elapsed = round(minutes_elapsed * last_bpm * tick_rate)
            logger.debug(
                f"Tick calculation: {minutes_elapsed:.6f} minutes * {last_bpm} BPM * {tick_rate} ticks/beat ="
                f" {ticks_elapsed} ticks"
            )

            ticks = last_tick + ticks_elapsed
            logger.debug(f"New tick position: {last_tick} (last) + {ticks_elapsed} (elapsed) = {ticks}")

            # Add the new timing point
            ch_timing_lines.append([ticks, bpm, signature, minutes])
            logger.debug(f"Added timing point at tick {ticks}: BPM {bpm}, signature {signature}/4")
        except (ValueError, IndexError, ZeroDivisionError) as e:
            logger.warning(f"Skipping invalid timing point: {line} - Error: {str(e)}")

    logger.debug(f"Total timing points generated: {len(ch_timing_lines)}")
    return ch_timing_lines


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


def generate_clone_hero_output(ch_timing_lines: List[Tuple[int, int, int, float]]) -> str:
    """Generate timing points in Clone Hero format as a string.

    Format:
    - Time signature lines: {ticks} = TS {signature}
    - BPM lines: {ticks} = B {bpm}000

    Args:
        ch_timing_lines: List of Clone Hero timing points

    Returns:
        String containing formatted Clone Hero timing data
    """
    lines = [
        "// Generated by osu! to Clone Hero Timing Converter",
        "// https://github.com/theyadev/osuToChTimings",
        "[SyncTrack]",
        "{",
    ]

    for ticks, bpm, signature, _ in ch_timing_lines:
        lines.append(f"  {ticks} = TS {signature}")
        lines.append(f"  {ticks} = B {int(bpm)}000")

    lines.append("}")

    return "\n".join(lines)


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
