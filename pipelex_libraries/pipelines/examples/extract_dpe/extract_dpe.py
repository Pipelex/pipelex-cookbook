from datetime import datetime
from typing import Optional

from pipelex.core.stuff_content import StructuredContent
from pipelex.types import StrEnum


class IndexScale(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"


class Dpe(StructuredContent):
    address: Optional[str] = None
    date_of_issue: Optional[datetime] = None
    date_of_expiration: Optional[datetime] = None
    energy_efficiency_class: Optional[IndexScale] = None
    per_year_per_m2_consumption: Optional[float] = None
    co2_emission_class: Optional[IndexScale] = None
    per_year_per_m2_co2_emissions: Optional[float] = None
    yearly_energy_costs: Optional[float] = None
