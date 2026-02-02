"""This module contains utility functions for analyzing tariffs and other decisions."""


def calculate_annual_cost(tariff_rate: float, annual_consumption_kwh: float) -> float:
    """Calculate annual cost for given tariff.

    Args:
        tariff_rate: Tariff rate in PLN/MWh
        annual_consumption_kwh: Annual consumption in kWh

    Returns:
        Annual cost in PLN
    """
    # Convert kWh to MWh and multiply by rate
    return (annual_consumption_kwh / 1000) * tariff_rate


def parse_tariff_code(code: str) -> dict:
    """Parse tariff code to extract information.

    Args:
        code: Tariff code (e.g., G11, B23)

    Returns:
        Dictionary with parsed code information
    """
    # Placeholder implementation
    return {}
