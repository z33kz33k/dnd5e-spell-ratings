"""

    dnd5e_sr.parse_data.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Parse spell data from 5e.tools JSON files.

    @author: z33k

"""

import json
from pathlib import Path
from pprint import pprint  # DEBUG


def parse():
    """Parse data.
    """
    source = Path("data/spells-phb.json")

    with source.open() as f:
        spells = json.load(f)["spell"]
        names = [spell["name"] for spell in spells]

    pprint(f"Number of parsed spell names: {len(names)}")
    pprint(names)

