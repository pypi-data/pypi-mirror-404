from dataclasses import dataclass


@dataclass
class MoyskladAPIServer:
    url: str


PRODUCTION = MoyskladAPIServer(
    url="https://api.moysklad.ru/api/remap/1.2",
)
