#!/usr/bin/env python3
"""
Beatmap to Chart Converter - Core Functions

This module contains the core functions for converting osu! beatmap timing points
to Clone Hero format, extracted from the main.py script for use in the web application.
"""

import logging
from typing import List, Tuple

# Constants
DEFAULT_TICK_RATE = 192
DEFAULT_BPM = 120
DEFAULT_TIME_SIGNATURE = 4

# Configure logging
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

    for i, line in enumerate(timing_points):
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
            bpm = 60000 / beat_length

            # Round to 3 decimal places to avoid floating point precision issues
            # If the BPM is very close to a whole number (within 0.0001), round to integer
            if abs(round(bpm) - bpm) < 0.0001:
                bpm = round(bpm)
            else:
                bpm = round(bpm, 3)

            while timing < 0:
                timing += beat_length

            if i == 0:
                if new_bpm := round((60000 / timing) * 4, 2) <= 999:
                    ch_timing_lines[0][1] = new_bpm

            # Convert osu! timing (ms) to minutes
            minutes = timing / 60000
            # Calculate ticks based on time elapsed since last timing point
            last_tick, last_bpm, _, last_minutes = ch_timing_lines[-1]
            minutes_elapsed = minutes - last_minutes

            # Calculate ticks elapsed using the formula: minutes * BPM * tick_rate
            ticks_elapsed = round(minutes_elapsed * last_bpm * tick_rate)

            ticks = last_tick + ticks_elapsed

            # Add the new timing point
            ch_timing_lines.append([ticks, bpm, signature, minutes])
        except (ValueError, IndexError, ZeroDivisionError) as e:
            logger.warning(f"Skipping invalid timing point: {line} - Error: {str(e)}")

    return ch_timing_lines


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
        "[SyncTrack]",
        "{",
    ]

    for ticks, bpm, signature, _ in ch_timing_lines:
        lines.append(f"  {ticks} = TS {signature}")

        # Convert BPM to the format expected by Clone Hero
        # For example, 120 BPM becomes 120000, 234.23 BPM becomes 234230
        # Ensure we don't have floating point precision issues
        bpm_float = float(bpm)
        if abs(round(bpm_float) - bpm_float) < 0.0001:
            bpm_float = round(bpm_float)
        else:
            bpm_float = round(bpm_float, 3)

        bpm_value = int(bpm_float * 1000)
        lines.append(f"  {ticks} = B {bpm_value}")

    lines.append("}")

    return "\n".join(lines)
