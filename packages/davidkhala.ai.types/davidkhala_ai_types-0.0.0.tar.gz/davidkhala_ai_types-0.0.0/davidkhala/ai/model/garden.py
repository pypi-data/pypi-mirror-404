from typing import Protocol


class GardenAlike(Protocol):
    @property
    def models(self) -> list[str]: ...
