from dataclasses import dataclass
from .list import LockedList

@dataclass
class Fixed(LockedList):
  ...
