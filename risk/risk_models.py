# Intentionally kept light, as models/alert_models.py handles the core schemas.
# Could be used for internal risk computation schemas if the project grows.
from pydantic import BaseModel

class RiskComputationContext(BaseModel):
    location_name: str
    latitude: float
    longitude: float
