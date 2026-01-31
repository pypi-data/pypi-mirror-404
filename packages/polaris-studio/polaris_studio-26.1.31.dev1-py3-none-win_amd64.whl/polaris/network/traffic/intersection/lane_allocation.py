# Copyright (c) 2026, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from typing import List

import numpy as np

from polaris.network.traffic.intersection.approximation import Approximation


def lane_allocation(single_approx: Approximation, list_approx: List[Approximation]) -> List[List[int]]:
    """
    Allocate incoming lanes to outgoing movements proportionally.

    Args:
        single_approx: The incoming approximation (link arriving at intersection)
        list_approx: List of outgoing approximations (destination links)

    Returns:
        List of [start_lane, end_lane] pairs (0-based, inclusive) for each outgoing link.
        Lanes at boundaries may be shared between adjacent movements when necessary.
    """
    incoming_lanes = single_approx.total_lanes()

    # Edge case: no outgoing links
    if len(list_approx) == 0:
        return []

    # Edge case: single outgoing link gets all lanes
    if len(list_approx) == 1:
        return [[0, incoming_lanes - 1]]

    # Get outgoing lane counts
    targets = np.array([approx.total_lanes() for approx in list_approx], dtype=float)
    total_outgoing = targets.sum()

    # Compute proportional allocation (fractional)
    proportions = targets / total_outgoing
    fractional_allocation = incoming_lanes * proportions

    # Compute cumulative boundaries
    cumulative = np.cumsum(fractional_allocation)

    # Determine lane boundaries
    # Each movement spans from previous boundary to current boundary
    # We need to convert fractional boundaries to integer lane indices

    result = []
    prev_end = 0.0

    for i, curr_end in enumerate(cumulative):
        # Start lane is the ceiling of previous end (or 0 for first)
        if i == 0:
            start_lane = 0
        else:
            # Start from where previous ended, but allow overlap if needed
            start_lane = int(np.floor(prev_end))

        # End lane is floor of current cumulative - 1, but at least start_lane
        # For the last movement, ensure we reach the final lane
        if i == len(cumulative) - 1:
            end_lane = incoming_lanes - 1
        else:
            end_lane = int(np.ceil(curr_end)) - 1

        # Ensure each movement gets at least one lane
        end_lane = max(end_lane, start_lane)

        # Ensure we don't exceed available lanes
        end_lane = min(end_lane, incoming_lanes - 1)
        start_lane = min(start_lane, incoming_lanes - 1)

        result.append([start_lane, end_lane])
        prev_end = curr_end

    # Post-process to minimize unnecessary overlaps
    # Only allow overlap when strictly necessary (more movements than lanes)
    if incoming_lanes >= len(list_approx):
        # We have enough lanes, so minimize overlaps
        for prev,curr in zip(result[:-1], result[1:]):
            # If current start overlaps with previous end, shift if possible
            if curr[0] <= prev[1]:
                # Check if we can shift current start forward
                if curr[0] < curr[1]:
                    curr[0] = prev[1] + 1
                # Otherwise, check if we can shift previous end backward
                elif prev[0] < prev[1]:
                    prev[1] = curr[0] - 1

    # Ensure all lanes are covered and boundaries are valid
    result[0][0] = 0
    result[-1][1] = incoming_lanes - 1

    return result
