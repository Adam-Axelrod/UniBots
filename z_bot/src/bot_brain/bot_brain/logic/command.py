from dataclasses import dataclass


@dataclass
class Command:
    linear_x: float = 0.0
    angular_z: float = 0.0
