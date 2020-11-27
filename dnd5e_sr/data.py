"""

    dnd5e_sr.data.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Parse spell data from 5e.tools JSON files.

    @author: z33k

"""

from dataclasses import dataclass
import json
from pathlib import Path
from pprint import pprint  # DEBUG
from typing import List, Optional


# boolean key appears in JSON only if its value is 'true'


@dataclass
class Time:  # works also duration subcomponent of duration in json
    amount: int
    unit: str
    condition: Optional[str]
    up_to: bool


@dataclass
class Distance:
    type: str
    amount: Optional[int]


@dataclass
class Range:
    type: str
    distance: Optional[Distance]


@dataclass
class MaterialComponent:
    text: str
    cost: int
    consumed: bool


@dataclass
class Components:
    verbal: bool
    somatic: bool
    material: MaterialComponent
    royalty: bool


@dataclass
class Duration:
    type: str
    time: Time
    concentration: bool


@dataclass
class Spell:
    name: str
    source: str
    page: int
    srd: bool
    level: int
    school: str
    times: List[Time]
    range: Range
    components: Components
    durations: List[Duration]
    ritual: bool  # if it has "meta" key check will suffice ==> DEBUG


def parse(filename: str) -> None:
    """Parse data from file designated by filename.
    """
    source = Path(f"data/{filename}")

    with source.open() as f:
        spells = json.load(f)["spell"]
        # names = [spell["name"] for spell in spells if len(spell["time"]) == 1
        #          and len(spell["time"][0].keys()) > 2]
        # names = [spell["name"] for spell in spells
        #          if spell["components"].get("m") is not None
        #          and isinstance(spell["components"].get("m"), dict)
        #          and len(spell["components"]["m"].keys()) > 3]
        # names = [(spell["name"], spell["duration"][0]["duration"]) for spell in spells
        #          if len(spell["duration"][0].keys()) > 1
        #          and spell["duration"][0].get("duration") is not None
        #          and len(spell["duration"][0]["duration"].keys()) > 2]
        # names = [(spell["name"], spell["range"]["distance"]) for spell in spells
        #          if len(spell["range"].keys()) == 2]
        # names = [(spell["name"], spell["meta"]) for spell in spells
        #          if spell.get("meta") is not None and [*spell["meta"].keys()][0] == "ritual"]
        compnames = [[*spell["components"].keys()] for spell in spells]
        compnames = [cn for cn in compnames if any(n not in ("v", "s", "m") for n in cn)]

    # pprint(f"Number of parsed spell names: {len(names)}")
    pprint(compnames)

