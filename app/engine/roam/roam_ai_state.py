from dataclasses import dataclass
from typing import Tuple, ClassVar
from enum import Enum, auto
from app.engine.objects.unit import UnitObject
from app.engine.objects.region import RegionObject

class AIAction(Enum):
    NONE = auto()
    MOVE = auto()
    WAIT = auto()
    INTERACT = auto()

@dataclass
class AIStruct():
    unit: UnitObject
    mtype: ClassVar[AIAction] = AIAction.NONE

@dataclass
class Wait(AIStruct):
    unit: UnitObject
    time: int
    mtype: ClassVar[AIAction] = AIAction.WAIT

@dataclass
class MoveTo(AIStruct):
    unit: UnitObject
    target: Tuple[int, int]
    desired_proximity: float
    mtype: ClassVar[AIAction] = AIAction.MOVE

@dataclass
class Interact(AIStruct):
    unit: UnitObject
    region: RegionObject
    desired_proximity: float
    mtype: ClassVar[AIAction] = AIAction.INTERACT
