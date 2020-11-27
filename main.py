"""

    DnD 5e spell ratings

    @author: z33k

"""

from dnd5e_sr.data import parse


def run():
    parse("spells-ai.json")
    parse("spells-egw.json")
    parse("spells-ggr.json")
    parse("spells-idrotf.json")
    parse("spells-llk.json")
    parse("spells-phb.json")
    parse("spells-tce.json")
    parse("spells-xge.json")


if __name__ == '__main__':
    run()
