"""Data models for electricity tariffs and regulatory decisions."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TariffType(str, Enum):
    """Types of electricity tariffs."""

    HOUSEHOLD = "household"  # Gospodarstwa domowe
    BUSINESS = "business"  # Przedsiębiorstwa
    INDUSTRIAL = "industrial"  # Przemysł
    STREET_LIGHTING = "street_lighting"  # Oświetlenie ulic
    TEMPORARY = "temporary"  # Tymczasowe


class Tariff(BaseModel):
    """Model representing an electricity tariff."""

    tariff_id: str = Field(..., description="Unique identifier of the tariff")
    tariff_code: str = Field(..., description="Official tariff code (e.g., G11, G12, B23)")
    tariff_name: str = Field(..., description="Name of the tariff")
    tariff_type: TariffType = Field(..., description="Type of tariff")
    operator_name: str = Field(..., description="Name of the distribution operator")
    valid_from: datetime = Field(..., description="Date when tariff becomes valid")
    valid_until: Optional[datetime] = Field(None, description="Date when tariff expires")
    base_rate: float = Field(..., description="Base rate in PLN/MWh")
    peak_rate: Optional[float] = Field(None, description="Peak rate in PLN/MWh")
    off_peak_rate: Optional[float] = Field(None, description="Off-peak rate in PLN/MWh")
    description: Optional[str] = Field(None, description="Detailed description")
    url: Optional[str] = Field(None, description="URL to official tariff decision")

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True


class Decision(BaseModel):
    """Model representing a regulatory decision regarding electricity."""

    decision_id: str = Field(..., description="Unique identifier of the decision")
    decision_number: str = Field(..., description="Official decision number")
    title: str = Field(..., description="Title of the decision")
    date_issued: datetime = Field(..., description="Date when decision was issued")
    valid_from: datetime = Field(..., description="Date when decision becomes valid")
    valid_until: Optional[datetime] = Field(None, description="Date when decision expires")
    content: str = Field(..., description="Full text of the decision")
    url: Optional[str] = Field(None, description="URL to official decision document")
    operator_name: Optional[str] = Field(None, description="Operator the decision applies to")
    tags: list[str] = Field(default_factory=list, description="Tags for classification")

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True
