"""

    dnd5e_sr.data.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Parse spell data from 5e.tools JSON files.

    @author: z33k

"""

# DEBUG
from pprint import pprint
from itertools import count


from dataclasses import dataclass
import json
from pathlib import Path
from random import randint
from typing import List, Optional, Dict, Any, Tuple, Union

Json = Dict[str, Any]


# boolean key appears in JSON only if its value is 'true'


@dataclass
class Time:  # works also for duration subcomponent of JSOn duration
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


# spell description is called 'entries' in JSON and is a list of paragraphs that can be either: a
# string, a list of strings (called 'items' and rendered as bullet points on the page), a quote (
# having an author and its own paragraphs), a subsection (having a name and its own paragraphs) or
# a table (having a caption, a list of column labels and a list of rows (each a list of strings)


@dataclass
class DescriptionQuote:
    paragraphs: List[str]
    by: str


@dataclass
class DescriptionSubsection:
    name: str
    paragraphs: List[str]


@dataclass
class DescriptionTable:
    caption: Optional[str]
    col_labels: List[str]
    rows: List[List[str]]


Description = Union[str, List[str], DescriptionQuote, DescriptionTable, DescriptionTable]


class Dice:
    """A dice formula that can roll itself.
    """
    DIE_CHAR = "d"

    def __init__(self, formula: str) -> None:
        self._formula = formula
        self.multiplier, self.die, self.operator, self.modifier = self._parse()

    def _parse(self) -> Tuple[Optional[int], int, Optional[str], Optional[int]]:
        """Parse the input formula for an multiplier, a die, an operator and a modifier.
        """
        if self._formula.count(self.DIE_CHAR) != 1:
            raise ValueError(f"Not one '{self.DIE_CHAR}' in dice formula: '{self._formula}'")
        multiplier, die = self._formula.split(self.DIE_CHAR)
        multiplier = int(multiplier) if multiplier else None

        if "+" in die:
            operator = "+"
            die, modifier = die.split(operator)
        elif "-" in die:
            operator = "-"
            die, modifier = die.split(operator)
        else:
            operator, modifier = None, None

        die = int(die.strip())

        if modifier:
            if "{" in modifier:
                modifier = None
            else:
                modifier = int(modifier.strip())

        return multiplier, die, operator, modifier

    @property
    def formula(self) -> str:
        """Return formula as parsed.
        """
        operator = self.operator if self.operator else ""
        modifier = self.modifier if self.modifier else ""
        if self.operator and not self.modifier:
            modifier = "modifier"

        return f"{self.multiplier}{self.DIE_CHAR}{self.die}{operator}{modifier}"

    @property
    def roll_results(self) -> List[int]:
        """Return list of roll results.
        """
        return [randint(1, self.die) for _ in range(self.multiplier)]

    def roll(self) -> int:
        """Roll a numerical result of the formula of this dice.
        """
        result = sum(self.roll_results)
        if self.operator and self.operator == "+":
            return result + (self.modifier if self.modifier else 0)
        elif self.operator and self.operator == "-":
            return result - (self.modifier if self.modifier else 0)
        else:
            return result

    def roll_as_text(self) -> str:
        """Roll a textual result of the formula of this dice.
        """
        results = self.roll_results
        total = sum(results)
        text_results = f"+".join([f"[{result}]" for result in results])
        roll = f"{total} ({text_results})"
        if self.modifier:
            if self.operator and self.operator == "+":
                total += self.modifier
                roll = f"{total} ({text_results} + {self.modifier})"
            elif self.operator and self.operator == "-":
                total -= self.modifier
                roll = f"{total} ({text_results} - {self.modifier})"

        return roll


# areaTags: S (sphere), N (cone), ST (single target), MT (multi target), H (hemisphere),
# L (line), W (wall)
# miscTags: SGT (seeing target), SCL (scalable), HL (healing influencing), SMN (summon),
# PRM (permanent), TP (teleportation)

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
        self.descriptions: List[Description] = self._getdescriptions()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name='{self.name}', source='{self.source}', " \
               f"page='{self.page}', in_srd='{self.in_srd}', level='{self.level}', " \
               f"school='{self.school}', times='{self.times}', range='{self.range}', " \
               f"is_ritual='{self.is_ritual}', components='{self.components}', " \
               f"durations='{self.durations}'), descriptions='{self.descriptions}'"

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

    def _getdescriptions(self) -> List[Description]:
        descs = []
        for entry in self._json["entries"]:
            if type(entry) is str:
                descs.append(entry)

            else:  # it's dict then
                if entry["type"] == "list":
                    descs.append(entry["items"])
                elif entry["type"] == "quote":
                    descs.append(DescriptionQuote(entry["entries"], entry["by"]))
                elif entry["type"] == "entries":
                    descs.append(DescriptionSubsection(entry["name"], entry["entries"]))
                elif entry["type"] == "table":
                    descs.append(DescriptionTable(
                        entry.get("caption"), entry["colLabels"], entry["rows"]))

        return descs


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
        # entries = [(spell["name"], spell["entries"]) for spell in spells
        #            if any(type(e) is dict for e in spell["entries"])]
        # entries = [(spell["name"], [n for n in spell["entries"]
        #             if type(n) is dict and n["type"] == "table"])
        #            for spell in spells
        #            if any(type(e) is dict for e in spell["entries"])]

        counter = count(start=1)
        comps = [(next(counter), spell["name"], spell["scalingLevelDice"]) for spell in spells
                 if spell.get("scalingLevelDice")]

        # spells = [Spell(spell) for spell in spells]

    # pprint(ranges)
    # pprint(f"Number of parsed spell names: {len(names)}")
    # pprint(compnames)
    # pprint(times)
    # pprint(sorted(ranges, key=lambda r: r[0]))
    # pprint(sorted(schools, key=lambda s: s[1]))
    # pprint(durations)
    # pprint(srd)
    # pprint(entries)
    pprint(comps)

    # pprint(spells)
