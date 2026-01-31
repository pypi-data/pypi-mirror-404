from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class DataChangeEvent:
    """
    Represents a data change event from Firebase RTDB.
    """

    event_type: Literal["put", "patch"]
    path: str
    data: Any
