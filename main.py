#!/usr/bin/env python3
"""
osu! to Clone Hero Timing Converter

This script converts timing points from osu! beatmap format to Clone Hero format.
It extracts BPM and time signature changes from an osu! beatmap file and outputs
them in a format compatible with Clone Hero.
"""

import sys
import logging
from typing import List, Tuple

# Constants
DEFAULT_TICK_RATE = 192
DEFAULT_BPM = 120
DEFAULT_TIME_SIGNATURE = 4
DEFAULT_INPUT_FILE = "example_beatmap.osz"
DEFAULT_OUTPUT_FILE = "output.txt"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


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

    # Extract the TimingPoints section
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
    # Get the first actual BPM from the map to use at tick 0
    first_bpm = DEFAULT_BPM
    first_signature = DEFAULT_TIME_SIGNATURE
    
    if timing_points:
        try:
            parts = timing_points[0].split(",")
            if len(parts) >= 8:
                beat_length = float(parts[1])  # in milliseconds
                first_bpm = round(60000 / beat_length)
                first_signature = int(parts[2])
        except (ValueError, IndexError, ZeroDivisionError) as e:
            logger.warning(f"Could not parse first timing point, using default BPM: {str(e)}")
    
    # Start with a timing point at tick 0 with the first BPM from the map
    ch_timing_lines = [[0, first_bpm, first_signature, 0.0]]

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

            # Skip if this is the first timing point and it's at time 0
            if timing == 0 and ch_timing_lines[0][0] == 0:
                continue
                
            # Convert osu! timing (ms) to minutes
            minutes = timing / 60000

            # Calculate ticks based on time elapsed since last timing point
            last_point = ch_timing_lines[-1]
            minutes_elapsed = minutes - last_point[3]
            ticks_elapsed = round(minutes_elapsed * last_point[1] * tick_rate)
            ticks = round(ticks_elapsed + last_point[0])

            # Log information
            logger.info(f"{timing}ms: BPM: {bpm}, Signature: {signature}/4 ({ticks} ticks)")

            # Add the new timing point
            ch_timing_lines.append([ticks, bpm, signature, minutes])
        except (ValueError, IndexError, ZeroDivisionError) as e:
            logger.warning(f"Skipping invalid timing point: {line} - Error: {str(e)}")

    return ch_timing_lines


def write_clone_hero_file(ch_timing_lines: List[Tuple[int, int, int, float]], output_file_path: str) -> None:
    """Write timing points to a Clone Hero format file.

    Format:
    - Time signature lines: {ticks} = TS {signature}
    - BPM lines: {ticks} = B {bpm}000

    Args:
        ch_timing_lines: List of Clone Hero timing points
        output_file_path: Path to the output file
    """
    try:
        with open(output_file_path, "w", encoding="utf-8") as file:
            file.write("// Generated by osu! to Clone Hero Timing Converter\n")
            file.write("// https://github.com/theyadev/osuToChTimings\n")
            file.write("[SyncTrack]\n{\n")
            for ticks, bpm, signature, _ in ch_timing_lines:
                file.write(f"  {ticks} = TS {signature}\n")
                file.write(f"  {ticks} = B {int(bpm)}000\n")
            file.write("}\n")
    except IOError as e:
        logger.error(f"Failed to write output file: {str(e)}")
        raise


def main() -> None:
    """Main function to run the conversion process."""
    try:
        input_file = DEFAULT_INPUT_FILE
        output_file = DEFAULT_OUTPUT_FILE
        tick_rate = DEFAULT_TICK_RATE

        # Handle command-line arguments if provided
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
        if len(sys.argv) > 2:
            output_file = sys.argv[2]

        logger.info(f"Converting {input_file} to {output_file}\n")

        timing_points = extract_timing_points(input_file)
        logger.info(f"Found {len(timing_points)} timing points")

        ch_timing_lines = convert_to_clone_hero_format(timing_points, tick_rate)
        write_clone_hero_file(ch_timing_lines, output_file)

        logger.info(f"\nConversion complete. Output saved to {output_file}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
