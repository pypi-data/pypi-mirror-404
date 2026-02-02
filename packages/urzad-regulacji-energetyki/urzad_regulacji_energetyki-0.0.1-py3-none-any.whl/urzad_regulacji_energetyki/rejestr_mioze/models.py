"""Data models for MIOZE registry entries."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MIOZEStatus(str, Enum):
    """Status of MIOZE installation."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEREGISTERED = "deregistered"
    SUSPENDED = "suspended"


class MIOZESource(str, Enum):
    """Type of energy source for MIOZE installation."""

    PHOTOVOLTAIC = "photovoltaic"
    WIND = "wind"
    HYDRO = "hydro"
    BIOMASS = "biomass"
    GEOTHERMAL = "geothermal"
    HYBRID = "hybrid"


class MIOZEEntry(BaseModel):
    """Model representing a MIOZE registry entry."""

    registration_id: str = Field(..., description="Unique registration ID in MIOZE")
    owner_name: str = Field(..., description="Name of the installation owner")
    owner_type: str = Field(..., description="Type of owner (individual, business, etc.)")
    energy_source: MIOZESource = Field(..., description="Type of energy source")
    installed_power_kw: float = Field(..., description="Installed power in kW")
    location_voivodeship: str = Field(..., description="Voivodeship where installation is located")
    location_gmina: str = Field(..., description="Gmina (municipality) where installation is located")
    status: MIOZEStatus = Field(..., description="Current status of the installation")
    registration_date: datetime = Field(..., description="Date of MIOZE registration")
    deregistration_date: Optional[datetime] = Field(None, description="Date of deregistration if applicable")
    connection_type: str = Field(..., description="Type of grid connection")
    feed_in_type: str = Field(..., description="Type of feed-in (net metering, etc.)")
    annual_production_estimate_kwh: Optional[float] = Field(None, description="Estimated annual production in kWh")

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True


class RegionalStatistics(BaseModel):
    """Statistics for a region."""

    voivodeship: str = Field(..., description="Voivodeship name")
    total_installations: int = Field(..., description="Total number of installations")
    total_capacity_kw: float = Field(..., description="Total installed capacity in kW")
    active_installations: int = Field(..., description="Number of active installations")
    by_source: dict[str, int] = Field(default_factory=dict, description="Breakdown by energy source")
