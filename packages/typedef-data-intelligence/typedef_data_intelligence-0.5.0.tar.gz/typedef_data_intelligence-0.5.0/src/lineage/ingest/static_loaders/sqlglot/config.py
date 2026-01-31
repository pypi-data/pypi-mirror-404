from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass(slots=True)
class SqlglotConfig:
    default_dialect: str = "snowflake"
    per_model_dialects: Dict[str, str] = field(default_factory=dict)
    enable_caching: bool = True
    max_cascade_depth: Optional[int] = None

