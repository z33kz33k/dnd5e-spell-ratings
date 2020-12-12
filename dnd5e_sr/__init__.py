"""

    dnd5e_sr
    ~~~~~~~~~

    DnD 5e spell ratings based on community guides' grades.

    @author: z33k

"""
from random import randint
from typing import Any, Dict, List, Optional, Tuple


Json = Dict[str, Any]


__author__ = "z33k"
__contact__ = "zeek@int.pl"
__version__ = "0.1.2.dev0"
__description = f"{__name__} is a script that groks DnD 5e spell ratings from available " \
                f"community guides"


BOOKS = ["PHB", "MM", "DMG", "SCAG", "AL", "VGM", "XGE", "MTF", "GGR", "AI", "ERLW", "RMR", "EGW",
         "MOT", "TCE"]


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
        """Parse the input formula for a multiplier, a die, an operator and a modifier.
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
                modifier = "modifier"
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
            return result + (0 if not self.modifier or self.modifier == "modifier"
                             else self.modifier)
        elif self.operator and self.operator == "-":
            return result - (0 if not self.modifier or self.modifier == "modifier"
                             else self.modifier)
        else:
            return result

    def roll_as_text(self) -> str:
        """Roll a textual result of the formula of this dice.
        """
        results = self.roll_results
        total = sum(results)
        text_results = f"+".join([f"[{result}]" for result in results])
        roll = f"{total} ({text_results})"
        if self.modifier and self.modifier != "modifier":
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
