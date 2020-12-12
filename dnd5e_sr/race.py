"""

    dnd5e_sr.race.py
    ~~~~~~~~~~~~~~~~~

    Parse race data from 5e.tools race.json.

    @author: z33k

"""
import json
from pathlib import Path
from pprint import pprint
from typing import List

from dnd5e_sr import BOOKS, Json
from dnd5e_sr.spell import Race as BasicRace


class Race:
    """Race as parsed for spells info from race.json.
    """
    KEYS = ["innate", "expanded"]

    def __init__(self, data: Json) -> None:
        self._json = data
        self.name: str = self._json["name"]
        self.source: str = self._json["source"]

    def parse_spellnames(self) -> List[str]:
        ...


class Subrace(Race):
    """Subrace as parsed for spell info from race.json.
    """
    def __init__(self, data: Json, baserace: BasicRace) -> None:
        super().__init__(data)
        self.baserace = baserace


def parse_races() -> None:
    """Parse races.json for race data.
    """
    source = Path(f"data/5etools/races.json")
    with source.open() as f:
        data = json.load(f)["race"]

    result = [race for race in data
              if race["source"] in BOOKS and "_copy" not in race.keys()]

    result = [race for race in result if (race.get("additionalSpells") is not None
              or (race.get("subraces") is not None
              and any(sr.get("additionalSpells") is not None for sr in race["subraces"])))]

    races = []
    for race in result:
        if race.get("additionalSpells"):
            races.append(race)
        else:
            if race.get("subraces"):
                for subrace in race["subraces"]:
                    if (subrace.get("additionalSpells")
                            and (subrace.get("source") is None
                                 or (subrace.get("source") and subrace["source"] in BOOKS))):
                        races.append((subrace, race["name"], race["source"]))

    for i, item in enumerate(races, start=1):
        print()
        print(f"********** {i} **********")
        print()
        if type(item) == tuple:
            spells = item[0]["additionalSpells"][0]
            pprint((item[0]["name"], spells.get("innate"), spells.get("expanded")))
        else:
            spells = item["additionalSpells"][0]
            pprint((item["name"], spells.get("innate"), spells.get("expanded")))
