from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    source: str
    region: str
    kind: str
    subject: str
    title: str
    url: str
    published: str
    summary: str
