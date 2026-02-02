"""Urząd Regulacji Energetyki (URE) Library.

A comprehensive Python library for creating insights from publicly available data
on the Polish Energy Regulatory Office (Urząd Regulacji Energetyki) websites.

Modules:
    - biuletyn_informacji_publicznej_changelog: Public Information Bulletin tracking
    - taryfy_i_inne_decyzje_energia_elektryczna: Electricity tariffs and regulatory decisions
    - rejestr_mioze: Small renewable energy installations registry (MIOZE)
"""

__version__ = "0.0.1"
__author__ = "Wiktor Hawrylik"
__email__ = "wiktor.hawrylik@gmail.com"
__license__ = "GPL-3.0"

from . import biuletyn_informacji_publicznej_changelog, rejestr_mioze, taryfy_i_inne_decyzje_energia_elektryczna

__all__ = [
    "biuletyn_informacji_publicznej_changelog",
    "taryfy_i_inne_decyzje_energia_elektryczna",
    "rejestr_mioze",
]
