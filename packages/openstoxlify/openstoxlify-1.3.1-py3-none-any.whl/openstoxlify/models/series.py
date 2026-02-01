from dataclasses import dataclass
from datetime import datetime
from utcnow import utcnow

from .enum import ActionType


@dataclass
class FloatSeries:
    timestamp: datetime
    value: float

    def to_dict(self):
        return {
            "timestamp": utcnow.get(self.timestamp.isoformat()),
            "value": self.value,
        }


@dataclass
class ActionSeries:
    timestamp: datetime
    action: ActionType
    amount: float = 0.0

    def to_dict(self):
        return {
            "timestamp": utcnow.get(self.timestamp.isoformat()),
            "action": self.action.value,
            "amount": self.amount,
        }
