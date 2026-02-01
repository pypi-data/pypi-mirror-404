from pprint import pprint

from sqlglot import parse_one,exp
from sqlglot.expressions import Select, From, Join, Where, Group, Having, Limit, Offset, Subquery, Table
from querycraft.tools import bold_substring

class SQLParser():

    def __init__(self,sql=None, debug=False):
        self.debug = debug
        if sql : self.setQuery(sql)

    def setQuery(self, sql):
        self.sql = sql
        self.stmt = parse_one(sql)

    def parcoursFrom(self, smt, deep=0):
        return self.__parcoursFrom(smt, deep)

    def __parcoursFrom(self,smt, deep=0):
        if isinstance(smt, Select):
            if self.debug: print('\t'*deep,f"--> Select : {smt}")
            l = []
            l += self.__parcoursFrom(smt.args['from'],deep+1)
            if "joins" in smt.args:
                joins = smt.args["joins"]
                req = f"Select * {smt.args['from']} "
                for j in joins:
                    l += self.__parcoursFrom(j,deep+1)
                    req += f' {j}'
                    l += [f'{req} ; --(Sel)']
            if self.debug: print('\t'*deep,f"<-- Select...{l}")
            return l
        elif isinstance(smt, From): # ok
            if self.debug: print('\t'*deep,f"--> From : {smt}")
            l =self.__parcoursFrom(smt.this,deep+1)
            if self.debug: print('\t'*deep,f"<-- From...{l}")
            return l
        elif isinstance(smt, Table): # ok
            if self.debug: print('\t'*deep,f"--> Table : {smt.this}")
            l = [f'Select * From {smt.this} ; --(Tab)']
            rep = f'Select * From {smt.this}'
            if "joins" in smt.args:
                joins = smt.args["joins"]
                for j in joins:
                    l += self.__parcoursFrom(j, deep + 1)
                    rep += f' {j}'
                    l += [ f'{rep} ; --(Tab-Join)']
            if self.debug: print('\t'*deep,f"<-- Table...{l}")
            return l
        elif isinstance(smt, Join): # ok
            if self.debug: print('\t'*deep,f"--> Join : {smt}")
            l = self.__parcoursFrom(smt.this,deep+1)
            if self.debug: print('\t'*deep,f"<-- Join...{l}")
            return l
        elif isinstance(smt, Subquery):
            if self.debug: print('\t'*deep,f"--> Subquery : {smt.this}")
            l = self.__parcoursFrom(smt.this,deep+1)
            rep =f'Select * From ({smt.this})'
            if "joins" in smt.args:
                joins = smt.args["joins"]
                for j in joins:
                    l += self.__parcoursFrom(j,deep+1)
                    rep += f' {j}'
                    l += [f'{rep} ; --(Sub)']
            if self.debug: print('\t'*deep,f"<-- Subquery...{l}")
            return l
        else:
            if self.debug: print(f"==> Unknown Smt {type(smt)} : {smt} ")

# Exemple d'utilisation
query1 = """SELECT m.codemat, titre, count(*)
FROM matieres m left join ((select * from notes) n join etudiants using (noetu)) on m.codemat = n.codemat 
group by m.codemat, titre
having count(*) >1 ;"""

query2 = """SELECT m.codemat, titre, count(*)
FROM matieres m left join (notes n join etudiants using (noetu)) on m.codemat = n.codemat 
group by m.codemat, titre
having count(*) >1 ;"""
query_list = [query1,query2]
for f in ['test/sql3a.sql']:#,'test/sql1.sql', 'test/sql1b.sql','test/sql2.sql','test/sql2b.sql','test/sql2c.sql','test/sql2d.sql'] :
    query = ''
    with open(f, 'r') as f:
        query += f.read()
    query_list += [query]

for query in query_list:
    print('==================================================================')
    parser = SQLParser(query, True)
    stmt = parser.stmt
    l = parser.parcoursFrom(stmt)
    pprint(l)
    for s in l:
        print(bold_substring(s, s[14:-10]))