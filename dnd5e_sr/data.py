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
from typing import List, Optional, Dict, Any

Json = Dict[str, Any]


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
    cost: Optional[int]
    is_consumed: bool


@dataclass
class Components:
    verbal: bool
    somatic: bool
    material: Optional[MaterialComponent]
    royalty: bool


@dataclass
class Duration:
    type: str
    time: Optional[Time]
    concentration: bool
    terminations: List[str]


SCHOOLSMAP = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "E": "Enchantment",
    "I": "Illusion",
    "N": "Necromancy",
    "T": "Transmutation",
    "V": "Evocation",
}


class Spell:
    """Object representing a spell parsed from 5e.tools json data files acquired via
    https://get.5e.tools/ but also available on Github:
    https://github.com/TheGiddyLimit/TheGiddyLimit.github.io/tree/master/data/spells
    """
    def __init__(self, data: Json) -> None:
        """Initialize.

        :param data: an element of the 'spell' list in a spell JSON file
        """
        self._json = data
        self.name: str = self._json["name"]
        self.source: str = self._json["source"]
        self.page: int = self._json["page"]
        self.in_srd: bool = self._json.get("srd") is not None
        self.level: int = self._json["level"]
        self.school: str = SCHOOLSMAP[self._json["school"]]
        self.times: List[Time] = self._gettimes()
        self.range: Range = self._getrange()
        self.is_ritual: bool = self._json.get("meta") is not None
        self.components: Components = self._getcomponents()
        self.durations: List[Duration] = self._getdurations()

    def __repr__(self) -> str:
        return f"{type(self)}(name='{self.name}', source='{self.source}', page='{self.page}', " \
               f"in_srd='{self.in_srd}', level='{self.level}', school='{self.school}', " \
               f"times='{self.times}', range='{self.range}', is_ritual='{self.is_ritual}', " \
               f"components='{self.components}', durations='{self.durations}')"

    def _gettimes(self) -> List[Time]:
        return [Time(time["number"], time["unit"], time.get("condition"), False)
                for time in self._json["time"]]

    def _getrange(self) -> Range:
        range_ = self._json["range"]
        distance = range_.get("distance")
        if distance:
            distance = Distance(distance["type"], distance.get("amount"))

        return Range(range_["type"], distance)

    def _getcomponents(self) -> Components:
        components = self._json["components"]
        verbal = components.get("v") is not None
        somatic = components.get("s") is not None
        royalty = components.get("r") is not None
        material = components.get("m")
        if type(material) is dict:
            material = MaterialComponent(material["text"], material.get("cost"), material.get(
                "consume") is not None)
        return Components(verbal, somatic, material, royalty)

    def _getdurations(self) -> List[Duration]:
        durations = []
        for duration in self._json["duration"]:
            time = duration.get("duration")
            if time:
                time = Time(time["amount"], time["type"], None, time.get("upTo") is not None)
            terminations = duration.get("ends")
            duration = Duration(duration["type"], time, duration.get("concentration") is not None,
                                terminations if terminations is not None else [])

            durations.append(duration)

        return durations


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
        # compnames = [[*spell["components"].keys()] for spell in spells]
        # compnames = [cn for cn in compnames if any(n not in ("v", "s", "m") for n in cn)]
        # times = [(spell["name"], spell["time"]) for spell in spells]
        # ranges = [(spell["name"], spell["range"]) for spell in spells if spell["range"].get(
        #     "distance") is not None and "amount" not in spell["range"]["distance"].keys()]
        # schools = [(spell["name"], spell["school"]) for spell in spells
        #            if spell["school"]]
        # comps = [(spell["name"], spell["components"]) for spell in spells]
        # durations = [(spell["name"], spell["duration"]) for spell in spells]
        # srd = [spell["name"] for spell in spells if spell.get("srd") is None]
        spells = [Spell(spell) for spell in spells]

    # pprint(ranges)
    # pprint(f"Number of parsed spell names: {len(names)}")
    # pprint(compnames)
    # pprint(times)
    # pprint(sorted(ranges, key=lambda r: r[0]))
    # pprint(sorted(schools, key=lambda s: s[1]))
    # pprint(comps)
    # pprint(durations)
    # pprint(srd)
    pprint(spells)
