from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class AddressBase:
    street: str
    city: str
    state: str
    zip_code: str
    country: str

@dataclass
class AddressRequest(AddressBase):
    pass

@dataclass
class AddressResponse:
    original_address: AddressBase
    standardized_address: AddressBase
    is_valid: bool
    confidence_score: float
    formatted_address: str
    provider: str
    geocoding: Optional[dict] = None

    def to_json(self):
        # Helper to convert to JSON since dataclasses don't have .json()
        data = asdict(self)
        return data
