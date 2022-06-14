from typing import List
import unittest
from unittest.mock import MagicMock, patch, call
from app.data.items import ItemCatalog
from app.data.klass import ClassCatalog
from app.data.units import UnitCatalog

import app.editor.lib.csv.csv_exporter as csv

class CsvExporterTests(unittest.TestCase):
    def setUp(self):
        from app.data.database import Database
        self.db = Database()
        self.db.load('testing_proj.ltproj')

    def tearDown(self) -> None:
        pass

    def test_unit_dump(self):
        unit_db = UnitCatalog()
        # test shortened version
        for i in range(2):
            unit_db.append(self.db.units[i])
        dmp = csv.unit_db_to_csv(unit_db)
        self.assertEqual(dmp,
"""NAME,NID,HP_base,STR_base,MAG_base,SKL_base,SPD_base,LCK_base,DEF_base,CON_base,MOV_base,RES_base,HP_growth,STR_growth,MAG_growth,SKL_growth,SPD_growth,LCK_growth,DEF_growth,CON_growth,MOV_growth,RES_growth,Sword,Lance,Axe,Bow,Staff,Light,Anima,Dark,Default
Eirika,Eirika,16,4,2,8,9,5,3,5,5,1,70,40,20,60,60,60,30,0,0,30,1,0,0,0,0,0,0,0,0,
Seth,Seth,30,14,7,13,12,13,11,11,8,8,90,50,25,45,45,25,40,0,0,30,181,181,0,0,0,0,0,0,0,
""")

    def test_klass_dump(self):
        klass_db = ClassCatalog()
        # shorten
        for i in range(2):
            klass_db.append(self.db.classes[i])
        dmp = csv.klass_db_to_csv(klass_db)
        self.assertEqual(dmp,
"""NAME,NID,HP_base,STR_base,MAG_base,SKL_base,SPD_base,LCK_base,DEF_base,CON_base,MOV_base,RES_base,LEAD_base,HP_growth,STR_growth,MAG_growth,SKL_growth,SPD_growth,LCK_growth,DEF_growth,CON_growth,MOV_growth,RES_growth,LEAD_growth,Sword,Lance,Axe,Bow,Staff,Light,Anima,Dark,Default
Citizen,Citizen,10,0,0,0,0,0,0,5,5,0,0,65,0,0,0,0,0,0,0,0,0,0,False,False,False,False,False,False,False,False,False,
Lord,Eirika_Lord,16,4,2,8,9,0,3,5,5,0,0,90,45,22,40,45,40,15,0,0,20,0,True,False,False,False,False,False,False,False,False,
"""
)

    def test_item_dmp(self):
        item_db = ItemCatalog()
        # shorten
        for i in range(2):
            item_db.append(self.db.items[i])
        dmp = csv.item_db_to_csv(item_db)
        self.assertEqual(dmp,
"""NAME,NID,HIT,CRIT,MIGHT,TYPE,RANK,WEIGHT,USES,MIN_RANGE,MAX_RANGE,VALUE
Iron Sword,Iron Sword,90,0,5,Sword,E,5,46,1,1,460
Slim Sword,Slim Sword,100,5,3,Sword,E,2,30,1,1,480
""")

if __name__ == '__main__':
    unittest.main()
