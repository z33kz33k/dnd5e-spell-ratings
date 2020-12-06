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
from enum import Enum
import json
from pathlib import Path
from random import randint
from typing import List, Optional, Dict, Any, Tuple, Union

# boolean key appears in JSON only if its value is 'true'
Json = Dict[str, Any]


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

AOE_TAGS_MAP = {
    "C": "cube",
    "H": "hemisphere",
    "L": "line",
    "MT": "multiple targets",
    "N": "cone",
    "Q": "square",
    "R": "circle",
    "S": "sphere",
    "ST": "single target",
    "W": "wall",
    "Y": "cylinder",
}

MISC_TAGS_MAP = {
    "HL": "healing",
    "MAC": "modifies AC",
    "PRM": "permanent effects",
    "SCL": "scaling effects",
    "SGT": "requires sight",
    "SMN": "summons creature",
    "THP": "grants temporary hit points",
    "TP": "teleportation",
}

ATTRIBUTES = ["name", "source", "page", "srd", "level", "school", "time", "range", "components",
              "duration", "meta", "entries", "entriesHigherLevel", "scalingLevelDice",
              "conditionInflict", "damageInflict", "damageResist", "damageImmune",
              "damageVulnerable", "savingThrow", "spellAttack", "abilityCheck", "miscTags",
              "areaTags", "classes", "races", "backgrounds", "eldritchInvocations", "otherSources"]


class AttackType(Enum):
    NONE = 0
    MELEE = 1
    RANGED = 2


@dataclass
class Time:  # works also for duration subcomponent of JSON duration
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

    def _validate_input(self) -> None:
        try:
            index = self._formula.index(self.DIE_CHAR)
        except ValueError:
            raise ValueError(f"No '{self.DIE_CHAR}' in dice formula: '{self._formula}'")

        if index == len(self._formula) or not self._formula[index + 1].isdigit():
            raise ValueError(f"Invalid formula: '{self._formula}'")

        if self._formula.count(self.DIE_CHAR) > 1:
            raise ValueError(f"More than one '{self.DIE_CHAR}' in dice formula: '{self._formula}'")

    def _parse(self) -> Tuple[Optional[int], int, Optional[str], Optional[int]]:
        """Parse the input formula for an multiplier, a die, an operator and a modifier.
        """
        self._validate_input()

        multiplier, die = self._formula.split(self.DIE_CHAR)

        if multiplier and "{" in multiplier:
            multiplier = "multiplier"
        else:
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
        if self.multiplier == "multiplier":
            multiplier = f"{self.multiplier}*"
        else:
            multiplier = self.multiplier if self.multiplier else ""
        operator = self.operator if self.operator else ""
        modifier = self.modifier if self.modifier else ""
        if self.operator and not self.modifier:
            modifier = "modifier"

        return f"{multiplier}{self.DIE_CHAR}{self.die}{operator}{modifier}"

    @property
    def roll_results(self) -> List[int]:
        """Return list of roll results.
        """
        multiplier = 0 if not self.multiplier or self.multiplier == "multipier" else self.multiplier
        return [randint(1, self.die) for _ in range(multiplier)]

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

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self.formula}')"

    def __str__(self) -> str:
        return self.formula


@dataclass
class ScalingDice:
    label: str
    scalingmap: Dict[int, Union[Dice, str]]


# areaTags: S (sphere), N (cone), ST (single target), MT (multi target), H (hemisphere),
# L (line), W (wall)
# miscTags: SGT (seeing target), SCL (scalable), HL (healing influencing), SMN (summon),
# PRM (permanent), TP (teleportation)


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
        self.higher_lvl_desc: Optional[DescriptionSubsection] = self._get_higher_lvl_desc()
        self.scaling_dice: List[ScalingDice] = self._get_scaling_dice()
        self.misc_tags: List[str] = self._get_misc_tags()
        self.aoe_tags: List[str] = self._get_aoe_tags()
        self.inflicted_conditions: List[str] = self._get_inflicted_conditions()
        self.dmg_types_inflicted: List[str] = self._get_dmg_types_inflicted()
        self.dmg_types_resisted: List[str] = self._get_dmg_types_resisted()
        self.dmg_types_vulnerable: List[str] = self._get_dmg_types_vulnerable()
        self.dmg_types_immune: List[str] = self._get_dmg_types_immune()
        self.saving_throws: List[str] = self._get_saving_throws()
        self.attack_type: AttackType = self._get_attack_type()
        self.ability_checks: List[str] = self._get_ability_checks()

    def __repr__(self) -> str:
        result = f"{type(self).__name__}(name='{self.name}', source='{self.source}', " \
               f"page='{self.page}', in_srd='{self.in_srd}', level='{self.level}', " \
               f"school='{self.school}', times='{self.times}', range='{self.range}', " \
               f"is_ritual='{self.is_ritual}', components='{self.components}', " \
               f"durations='{self.durations}'), descriptions='{self.descriptions}'"
        if self.higher_lvl_desc:
            result += f", higher_lvl_desc={self.higher_lvl_desc}"
        if self.scaling_dice:
            result += f", scaling_dice={self.scaling_dice}"
        if self.misc_tags:
            result += f", misc_tags={self.misc_tags}"
        if self.aoe_tags:
            result += f", aoe_tags={self.aoe_tags}"
        if self.inflicted_conditions:
            result += f", inflicted_conditions={self.inflicted_conditions}"
        if self.dmg_types_inflicted:
            result += f", dmg_types_inflicted={self.dmg_types_inflicted}"
        if self.dmg_types_resisted:
            result += f", dmg_types_resisted={self.dmg_types_resisted}"
        if self.dmg_types_vulnerable:
            result += f", dmg_types_vulnerable={self.dmg_types_vulnerable}"
        if self.dmg_types_immune:
            result += f", dmg_types_immune={self.dmg_types_immune}"
        if self.saving_throws:
            result += f", saving_throws={self.saving_throws}"
        if self.attack_type is not AttackType.NONE:
            result += f", attack_type={self.attack_type}"
        if self.ability_checks:
            result += f", ability_checks={self.ability_checks}"

        return result + ")"

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

    def _get_higher_lvl_desc(self) -> Optional[DescriptionSubsection]:
        desc = self._json.get("entriesHigherLevel")
        if desc:
            desc = desc[0]
            desc = DescriptionSubsection(desc["name"], desc["entries"])
        return desc

    def _get_scaling_dice(self) -> List[ScalingDice]:
        def getdice(json_dict: Json) -> ScalingDice:
            resultdict = {}
            for k, v in json_dict["scaling"].items():
                try:
                    dice = Dice(v)
                except ValueError:
                    dice = "modifier"
                resultdict.update({k: dice})

            return ScalingDice(json_dict["label"], resultdict)

        scaling_dice = self._json.get("scalingLevelDice")
        results = []
        if scaling_dice:
            if type(scaling_dice) is list:
                for die in scaling_dice:
                    results.append(getdice(die))
            else:
                results.append(getdice(scaling_dice))

        return results

    def _get_misc_tags(self) -> List[str]:
        tags = self._json.get("miscTags")
        return [] if not tags else [MISC_TAGS_MAP[tag] for tag in tags]

    def _get_aoe_tags(self) -> List[str]:
        tags = self._json.get("areaTags")
        return [] if not tags else [AOE_TAGS_MAP[tag] for tag in tags]

    def _get_inflicted_conditions(self) -> List[str]:
        conditions = self._json.get("conditionInflict")
        return conditions if conditions else []

    def _get_dmg_types_inflicted(self) -> List[str]:
        dmg_types_inflicted = self._json.get("damageInflict")
        return dmg_types_inflicted if dmg_types_inflicted else []

    def _get_dmg_types_resisted(self) -> List[str]:
        dmg_types_resisted = self._json.get("damageResist")
        return dmg_types_resisted if dmg_types_resisted else []

    def _get_dmg_types_vulnerable(self) -> List[str]:
        dmg_types_vulnerable = self._json.get("damageVulnerable")
        return dmg_types_vulnerable if dmg_types_vulnerable else []

    def _get_dmg_types_immune(self) -> List[str]:
        dmg_types_immune = self._json.get("damageImmune")
        return dmg_types_immune if dmg_types_immune else []

    def _get_saving_throws(self) -> List[str]:
        throws = self._json.get("savingThrow")
        return throws if throws else []

    def _get_attack_type(self) -> AttackType:
        attack = self._json.get("spellAttack")
        if attack is not None:
            if attack[0] == "M":
                return AttackType.MELEE
            else:
                return AttackType.RANGED
        else:
            return AttackType.NONE

    def _get_ability_checks(self) -> List[str]:
        checks = self._json.get("abilityCheck")
        return checks if checks else []


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
        #
        # counter = count(start=1)
        # result = [(next(counter), spell["name"], spell["scalingLevelDice"]) for spell in spells
        #           if spell.get("scalingLevelDice")
        #           and type(spell["scalingLevelDice"]) is not dict]
        # counter = count(start=1)
        # result = [(next(counter), spell["name"], spell["areaTags"]) for spell in spells
        #          if spell.get("areaTags")
        #          and any(tag not in AOE_TAGS_MAP.keys() for tag in spell["areaTags"])]

        # counter = count(start=1)
        # result = [(next(counter), spell["name"], spell["miscTags"]) for spell in spells
        #           if spell.get("miscTags")
        #           and any(tag not in MISC_TAGS_MAP.keys() for tag in spell["miscTags"])]

        # counter = count(start=1)
        # result = [(next(counter), spell["name"], spell["entriesHigherLevel"][0]) for spell in
        # spells
        #           if spell.get("entriesHigherLevel")
        #           and any(key not in ("entries", "name", "type") for key
        #                   in spell["entriesHigherLevel"][0].keys())]

        # counter = count(start=1)
        # result = [(next(counter), spell["name"], spell["abilityCheck"]) for spell in spells
        #           if spell.get("abilityCheck")]
        #
        spells = [Spell(spell) for spell in spells]

    # pprint(result)
    #
    pprint(spells)
