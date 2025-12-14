from __future__ import annotations

from enum import Enum


class RoleType(Enum):
    QUARANTINE_SPECIALIST   = 1
    EMERGENCY_EXPERT        = 2
    DISPATCHER              = 3
    SCIENTIST               = 4
    DOCTOR                  = 5
    RESEARCHER              = 6
    ENGINEER                = 7

class ColorType(Enum):
    red     = 1
    yellow  = 2
    blue    = 3
    black   = 4


class CardType(Enum):
    CITY     = 1
    EVENT    = 2
    EPIDEMIC = 3


class GameStatus(Enum):
    waiting  = 1
    active   = 2
    finished = 3
    aborted  = 4

class Difficult(Enum):
    easy    = 4
    medium  = 5
    hard    = 6