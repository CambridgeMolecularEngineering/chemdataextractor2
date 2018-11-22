# -*- coding: utf-8 -*-
"""
test_relex_entity
~~~~~~~~~~~~~~~~~

Test creation of entity object

"""

from chemdataextractor.relex.entity import Relationship, Entity
import unittest


class TestEntity(unittest.TestCase):
    """ Tests creation of entity objects"""

    def test_entity(self):

        cem = Entity('TiO2', 'cem', 1 ,2 )
        spec = Entity('Curie Temperature', 'specifier', 2,3)
        val = Entity('123', 'value', 3,4)
        unit = Entity('K', 'unit', 4,5)

        rel = Relationship({cem.tag: cem, spec.tag: spec, val.tag: val, unit.tag : unit})
        print(rel.cem)
        print(rel.value)


