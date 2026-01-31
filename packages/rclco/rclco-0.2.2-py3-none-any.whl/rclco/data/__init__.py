"""
Data access layer for RCLCO.

Provides pre-built queries and helpers for common datasets.

Modules:
    demographics: Esri demographic data (population, income, housing, etc.)

Example:
    from rclco.data.demographics import Esri

    esri = Esri()
    df = esri.demographics(state="NC", geo_unit="tract", year=2024)
"""

from rclco.data import demographics

__all__ = ["demographics"]
