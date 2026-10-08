# SPDX-License-Identifier: MIT
# T5 hidden acceptance test, refactor-inflection. The refactor must not change
# behaviour: PINS holds the output of pluralize and singularize at the
# upstream commit for every uncountable word in several shapes, where the two
# functions' uncountable checks differ. The structural test checks that both
# functions now go through _inflect and no longer loop over a rule list.
import ast
import inspect
import textwrap

import pytest

import inflection

PINS = {
    '': ('', ''),
    ' ': (' s', ' '),
    'equipment': ('equipment', 'equipment'),
    'Equipment': ('Equipment', 'Equipment'),
    'EQUIPMENT': ('EQUIPMENT', 'EQUIPMENT'),
    'old equipment': ('old equipments', 'old equipment'),
    'CamelEquipment': ('CamelEquipments', 'CamelEquipment'),
    'my_equipment': ('my_equipments', 'my_equipment'),
    'subequipment': ('subequipments', 'subequipment'),
    'fish': ('fish', 'fish'),
    'Fish': ('Fish', 'Fish'),
    'FISH': ('FISH', 'FISH'),
    'old fish': ('old fishes', 'old fish'),
    'CamelFish': ('CamelFishes', 'CamelFish'),
    'my_fish': ('my_fishes', 'my_fish'),
    'subfish': ('subfishes', 'subfish'),
    'information': ('information', 'information'),
    'Information': ('Information', 'Information'),
    'INFORMATION': ('INFORMATION', 'INFORMATION'),
    'old information': ('old informations', 'old information'),
    'CamelInformation': ('CamelInformations', 'CamelInformation'),
    'my_information': ('my_informations', 'my_information'),
    'subinformation': ('subinformations', 'subinformation'),
    'jeans': ('jeans', 'jeans'),
    'Jeans': ('Jeans', 'Jeans'),
    'JEANS': ('JEANS', 'JEANS'),
    'old jeans': ('old jeans', 'old jeans'),
    'CamelJeans': ('CamelJeans', 'CamelJean'),
    'my_jeans': ('my_jeans', 'my_jean'),
    'subjeans': ('subjeans', 'subjean'),
    'money': ('money', 'money'),
    'Money': ('Money', 'Money'),
    'MONEY': ('MONEY', 'MONEY'),
    'old money': ('old moneys', 'old money'),
    'CamelMoney': ('CamelMoneys', 'CamelMoney'),
    'my_money': ('my_moneys', 'my_money'),
    'submoney': ('submoneys', 'submoney'),
    'rice': ('rice', 'rice'),
    'Rice': ('Rice', 'Rice'),
    'RICE': ('RICE', 'RICE'),
    'old rice': ('old rices', 'old rice'),
    'CamelRice': ('CamelRices', 'CamelRice'),
    'my_rice': ('my_rices', 'my_rice'),
    'subrice': ('subrices', 'subrice'),
    'series': ('series', 'series'),
    'Series': ('Series', 'Series'),
    'SERIES': ('SERIES', 'SERIES'),
    'old series': ('old series', 'old series'),
    'CamelSeries': ('CamelSeries', 'CamelSeries'),
    'my_series': ('my_series', 'my_series'),
    'subseries': ('subseries', 'subseries'),
    'sheep': ('sheep', 'sheep'),
    'Sheep': ('Sheep', 'Sheep'),
    'SHEEP': ('SHEEP', 'SHEEP'),
    'old sheep': ('old sheeps', 'old sheep'),
    'CamelSheep': ('CamelSheeps', 'CamelSheep'),
    'my_sheep': ('my_sheeps', 'my_sheep'),
    'subsheep': ('subsheeps', 'subsheep'),
    'species': ('species', 'species'),
    'Species': ('Species', 'Species'),
    'SPECIES': ('SPECIES', 'SPECIES'),
    'old species': ('old species', 'old species'),
    'CamelSpecies': ('CamelSpecies', 'CamelSpecy'),
    'my_species': ('my_species', 'my_specy'),
    'subspecies': ('subspecies', 'subspecy'),
}


@pytest.mark.parametrize(("word", "plural", "singular"),
                         [(w, p, s) for w, (p, s) in PINS.items()])
def test_behaviour_unchanged(word: str, plural: str, singular: str) -> None:
    assert inflection.pluralize(word) == plural
    assert inflection.singularize(word) == singular


@pytest.mark.parametrize("name", ["pluralize", "singularize"])
def test_uses_the_shared_helper(name: str) -> None:
    assert callable(getattr(inflection, "_inflect", None))
    tree = ast.parse(textwrap.dedent(inspect.getsource(getattr(inflection, name))))
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "_inflect"]
    loops = [n for n in ast.walk(tree)
             if isinstance(n, ast.For) and isinstance(n.iter, ast.Name)
             and n.iter.id in ("PLURALS", "SINGULARS")]
    assert calls, f"{name} does not call _inflect"
    assert not loops, f"{name} still loops over its rule list itself"
