"""

    DnD 5e spell ratings

    @author: z33k

"""

from dnd5e_sr.spell import parse_spells
from dnd5e_sr.race import parse_races


def run():
    # parse_spells("spells-ai.json")
    # parse_spells("spells-egw.json")
    # parse_spells("spells-ggr.json")
    # parse_spells("spells-idrotf.json")
    # parse_spells("spells-llk.json")
    # parse_spells("spells-phb.json")
    # parse_spells("spells-tce.json")
    # parse_spells("spells-xge.json")

    parse_races()


if __name__ == '__main__':
    run()
