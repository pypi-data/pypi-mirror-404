"""Utility functions for the MIOZE registry."""

from typing import Optional


def calculate_total_capacity(entries: list, source_filter: Optional[str] = None) -> float:
    """Calculate total installed capacity from MIOZE entries.

    Args:
        entries: List of MIOZE entries
        source_filter: Optional filter by energy source

    Returns:
        Total capacity in kW
    """
    total = 0.0
    for entry in entries:
        if source_filter is None or entry.energy_source == source_filter:
            total += entry.installed_power_kw
    return total


def aggregate_by_voivodeship(entries: list) -> dict:
    """Aggregate MIOZE statistics by voivodeship.

    Args:
        entries: List of MIOZE entries

    Returns:
        Dictionary with aggregated statistics
    """
    # Placeholder implementation
    return {}


def calculate_penetration_rate(total_entries: int, active_entries: int) -> float:
    """Calculate MIOZE penetration rate.

    Args:
        total_entries: Total number of registered entries
        active_entries: Number of active entries

    Returns:
        Penetration rate as percentage
    """
    if total_entries == 0:
        return 0.0
    return (active_entries / total_entries) * 100
