import unittest

from querycraft.SQL import SQL
from querycraft.tools import compare_query_results_raw

class SQLTestCase(unittest.TestCase):
    def test_sim(self):
        a1 = [[6, 9, 7], [1, 2, 4]]
        a2 = [[1, 2, 4], [6, 9, 7]]
        a3 = [[1, 4, 2], [6, 7, 9]]
        a4 = [[1, 2, 4], [6, 8, 7]]

        self.assertEqual(compare_query_results_raw(['a', 'b', 'c'],a1, ['a', 'b', 'c'],a1), 4)
        self.assertEqual(compare_query_results_raw(['a', 'b', 'c'],a1, ['a', 'b', 'c'],a2), 2)
        self.assertEqual(compare_query_results_raw(['a', 'b', 'c'],a2, ['a', 'c', 'b'],a3), 3)
        self.assertEqual(compare_query_results_raw(['a', 'c', 'b'],a3, ['a', 'b', 'c'],a1), 1)
        self.assertEqual(compare_query_results_raw(['a', 'c', 'b'],a3, ['a', 'b', 'c'],a4) , 0)

    def test_sim_SQL(self):
        sql1 = SQL(db='../querycraft/data/cours.db', dbtype='sqlite')
        sql1.load('sql1.sql')
        sql2 = SQL(db='../querycraft/data/cours.db', dbtype='sqlite')
        sql2.load('sql2.sql')
        sql2b = SQL(db='../querycraft/data/cours.db', dbtype='sqlite')
        sql2b.load('sql2b.sql')
        sql2c = SQL(db='../querycraft/data/cours.db', dbtype='sqlite')
        sql2c.load('sql2c.sql')

        self.assertEqual(sql1.similaire(sql2),0)
        self.assertEqual(sql1.similaire(sql1), 4)
        self.assertEqual(sql2.similaire(sql2), 4)
        self.assertEqual(sql2.similaire(sql2b), 2)
        self.assertEqual(sql2b.similaire(sql2c), 3)
        self.assertEqual(sql2.similaire(sql2c), 1)

if __name__ == '__main__':
    unittest.main()
