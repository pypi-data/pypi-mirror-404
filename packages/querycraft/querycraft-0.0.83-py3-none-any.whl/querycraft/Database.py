#!/usr/bin/env python3

from pprint import pprint

import mysql.connector
import psycopg2 as pgsql
import sqlite3

from sqlalchemy import MetaData, create_engine
from sqlalchemy.schema import CreateTable

from querycraft.tools import existFile,format_table_1,format_table_2,format_table_3
from querycraft.SQLException import SQLException, SQLQueryException

class Database:
    dblist = dict()

    @classmethod
    def get(cls, dbcon: str, dbtype: str, debug=False, verbose=True):
        dbid = dbtype + '—' + str(dbcon)
        if dbid in cls.dblist:
            return cls.dblist[dbid]
        elif dbtype == 'sqlite':
            db = DBSQLite(dbcon, debug, verbose)
            cls.dblist[dbid] = db
            return db
        elif dbtype == 'pgsql':
            db = DBPGSQL(dbcon, debug, verbose)
            cls.dblist[dbid] = db
            return db
        elif dbtype == 'mysql':
            db = DBMySQL(dbcon, debug, verbose)
            cls.dblist[dbid] = db
            return db
        else:
            raise SQLException("Erreur Database : type de base de données pas défini")

    @classmethod
    def getPGSQLDB(cls, dbcon):
        dbid = 'pgsql' + '—' + dbcon
        if dbid in cls.dblist:
            return cls.dblist[dbid]
        else:
            db = DBPGSQL(dbcon)
            cls.dblist[dbid] = db
            return db

    @classmethod
    def getSQLiteDB(cls, dbcon):
        dbid = 'sqlite' + '—' + dbcon
        if dbid in cls.dblist:
            return cls.dblist[dbid]
        else:
            db = DBSQLite(dbcon)
            cls.dblist[dbid] = db
            return db

    def __init__(self, db=None, dbtype=None, debug=False, verbose=False):
        self.name = None
        self.debug = debug
        self.verbose = verbose
        if db is not None:
            self.setDB(db, dbtype)
        else:
            self.db = None
            self.dbtype = None
            self.dbTables = dict()
            self.dbAttributs = dict()
        self.connection = None

    def getDBTables(self):
        """
        Récupère les tables de la base de données et leurs attributs.
        :return: Un dictionnaire avec les tables en entrée et
        en valeur l'identifiant de la table (s'il existe)
        et les attributs (et s'ils sont dans la clé)
        """
        pass

    def setDB(self, db, type):
        self.db = db
        self.dbtype = type
        self.getDBTables()  # les tables de la base avec leurs attributs

    def getType(self):
        return self.dbtype

    def getDBCon(self):
        return self.db

    def connect(self):
        pass

    def disconnect(self, cursor):
        cursor.close()

    def execute(self, sql):
        try:
            cursor = self.connect()
            cursor.execute(sql)
            desc = cursor.description
            # print(desc)
            data = cursor.fetchall()
            self.disconnect(cursor)
            return (desc, data)
        except Exception as e:
            raise SQLQueryException(self.verbose,e,sql,None,self.name,self)

    def tables2string(self):
        pass

    def tables2string2(self, url):
        engine = create_engine(url)
        metadata = MetaData()
        metadata.reflect(bind=engine)

        s = "```sql\n"
        for table in metadata.sorted_tables:
            s += (f"-- Schéma pour la table \"{table.name}\"")
            #s += "\n"
            s += (str(CreateTable(table).compile(engine)) + ";")
            s += "\n\n"
        return s+"```"

    def tables2string_ter(self):
        s = ""  # self.db+"\n"
        for (t, (id_t, att)) in self.dbTables.items():
            hd = ['Attribut', 'Clé primaire', 'Clé étrangère']

            if self.debug:
                s += f"--- table \"{t}\" - {id_t}  ---"
            else:
                s += f"--- table \"{t}\"  ---"
            s += "\n"
            s += format_table_1(hd, att)
            s += "\n\n"
        return s


    def printDBTables(self):
        print(f"type = {self.dbtype}\n")
        print(self.tables2string_ter())


class DBPGSQL(Database):

    def __init__(self, db, debug=False, verbose=False):
        self.dbPGID = dict()
        super().__init__(db=db, dbtype='pgsql', debug=debug, verbose=verbose)
        self.name = "PostgreSQL"
        #print("=====>",self.name)
        self.dbname = ""
        self.dbport = "5432"
        self.dbuser = ""
        self.dbpassword = ""
        self.dbhost = "localhost"
        #self.db = f"dbname={self.dbname} user={self.dbuser} password={self.dbpassword} host={self.dbhost} port={self.dbport}"
        for s in db.split():
            if s.startswith("dbname="):
                self.dbname = s.split("=")[1]
            elif s.startswith("user="):
                self.dbuser = s.split("=")[1]
            elif s.startswith("password="):
                self.dbpassword = s.split("=")[1]
            elif s.startswith("host="):
                self.dbhost = s.split("=")[1]
            elif s.startswith("port="):
                self.dbport = s.split("=")[1]

    def tables2string(self):
        url = f"postgresql+psycopg2://{self.dbuser}:{self.dbpassword}@{self.dbhost}:{self.dbport}/{self.dbname}"
        return self.tables2string2(url)

    def connect(self):
        try:
            connection = pgsql.connect(self.db)
            cursor = connection.cursor()
            return cursor
        except Exception as e:
            raise SQLException(f"Erreur PostgreSQL (connect) :\n {e}")

    def getForeignKeys(self, dbcursor, tableName):
        """
        Retrieves foreign key constraints for a given table.

        Parameters:
        dbcursor (cursor): A database cursor object for executing SQL queries.
        tableName (str): The name of the table for which to retrieve foreign key constraints.

        Returns:
        list: A list of tuples, where each tuple represents a foreign key constraint. Each tuple contains:
            - foreign_table_name (str): The name of the foreign table.
            - column_name (str): The name of the column in the original table.
            - foreign_column_name (str): The name of the column in the foreign table.
        """
        query = """
        SELECT 
            tc.constraint_name,
            tc.table_name,
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
        JOIN 
            information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN 
            information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE 
            tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = %s ;
        """
        dbcursor.execute(query, (tableName,))
        lst = dict()
        for att in dbcursor.fetchall():
            lst[att[2]] = (att[3], att[4])
        return lst
        # return [(i[3], i[2], i[4]) for i in lst]

    def getDBTables(self):
        """
        Récupère les tables de la base de données et leurs attributs.
        :return: Un dictionnaire avec les tables en entrée et
        en valeur l'identifiant de la table (s'il existe)
        et les attributs (et s'ils sont dans la clé)
        """
        if self.db is None:
            raise SQLException("La base de donnée n'est pas renseignée.")
        else:
            if self.debug: print('Récupération des informations de la base PostgreSQL')
            self.dbTables = dict()
            self.dbAttributs = dict()
            self.dbPGID = dict()

            dbcursor = self.connect()
            try:
                self.dbTables = dict()
                dbcursor.execute(
                    "SELECT table_name, oid "
                    "FROM information_schema.tables join pg_class on table_name = relname "
                    "WHERE table_schema = 'public';")
                lst = dbcursor.fetchall()
                for tq in lst:
                    t = tq[0]
                    id_t = tq[1]
                    dbcursor.execute(
                        f"SELECT c.column_name, c.data_type, string_agg(tc.constraint_type, ', ') as t "
                        f"FROM  information_schema.columns c LEFT JOIN information_schema.key_column_usage kcu using (table_name,column_name,table_schema) LEFT JOIN information_schema.table_constraints tc using(constraint_name, table_schema) "
                        f"WHERE c.table_schema = 'public' AND c.table_name = '{t}' "
                        f"Group By c.column_name, c.data_type ;")
                    attlst = dbcursor.fetchall()
                    fk = self.getForeignKeys(dbcursor, t)
                    lstatt = []
                    for i in attlst:
                        attname = i[0]
                        if i[2] is not None:
                            lstatt.append((attname, 'PRIMARY KEY' in i[2], fk[attname] if attname in fk else None))
                        else:
                            lstatt.append((attname, False, fk[attname] if attname in fk else None))
                        if attname in self.dbAttributs:
                            self.dbAttributs[attname].append(t)
                        else:
                            self.dbAttributs[attname] = [t]
                    self.dbTables[t] = (id_t, lstatt)
                    self.dbPGID[id_t] = t

                if self.debug:
                    pprint(self.dbTables)
                    pprint(self.dbPGID)
                    pprint(self.dbAttributs)
            except Exception as e:
                raise SQLException(
                    f"Erreur PostgreSQL : Impossible de récupérer les tables de la base de données\n -> {e}")
            finally:
                self.disconnect(dbcursor)


class DBSQLite(Database):
    def __init__(self, db, debug, verbose=False):
        super().__init__(db=db, dbtype='sqlite', debug=debug, verbose=verbose)
        if not existFile(db):
            raise SQLException(f"(SQLite) La base de donnée {db} n'existe pas.")
        self.name = "SQLite"
        #print(db)

    def tables2string(self):
        url = f"sqlite:///{self.db}"
        #print(url)
        return self.tables2string2(url)

    def connect(self):
        try:
            connection = sqlite3.connect(self.db, uri=True)
            cursor = connection.cursor()
            return cursor
        except Exception as e:
            raise SQLException(f"Erreur SQLite (connect) :\n {e}")

    def getForeignKeys(self, dbcursor, tableName):
        """
        Retrieves a list of foreign keys for a given table.

        Parameters:
        dbcursor (sqlite3.Cursor): A database cursor object to execute SQL queries.
        tableName (str): The name of the table to retrieve foreign keys for.

        Returns:
        list: A list of tuples, where each tuple represents a foreign key. Each tuple contains:
            - The name of the referencing column.
            - The name of the referenced column.
            - The name of the referenced table.
        """
        query = dbcursor.execute(f"PRAGMA foreign_key_list('{tableName}');")
        lst = dict()
        for att in query.fetchall():
            if att[4] is None:
                lst[att[3]] = (att[2], att[3])
            else:
                lst[att[3]] = (att[2], att[4])
        return lst
        # return [(i[2], i[3],i[4]) for i in query.fetchall()]

    def getDBTables(self):
        """
        Récupère les tables de la base de données et leurs attributs.
        :return: Un dictionnaire avec les tables en entrée et
        en valeur l'identifiant de la table (s'il existe)
        et les attributs (et s'ils sont dans la clé)
        """
        if self.db is None:
            raise SQLException("La base de donnée n'est pas renseignée.")
        elif not existFile(self.db):
            raise SQLException("(SQLite) La base de donnée n'existe pas.")
        else:
            if self.debug: print('Récupération des informations de la base SQLite')
            self.dbTables = dict()
            self.dbAttributs = dict()

            try:
                dbcursor = self.connect()
                query = dbcursor.execute("SELECT name FROM sqlite_master where type='table';")
                lst = query.fetchall()
                for tq in lst:
                    t = tq[0]
                    query = dbcursor.execute(f"PRAGMA table_info('{t}');")
                    attlst = query.fetchall()
                    if self.debug:  print(attlst)
                    # pprint(self.getForeignKeys(dbcursor, t))
                    fk = self.getForeignKeys(dbcursor, t)
                    lstatt = []
                    for i in attlst:
                        attname = i[1]
                        pk_member = i[5] != 0

                        lstatt.append((attname, pk_member, fk[attname] if attname in fk else None))
                        if attname in self.dbAttributs:
                            self.dbAttributs[attname].append(t)
                        else:
                            self.dbAttributs[attname] = [t]
                    self.dbTables[t] = (None, lstatt)
                if self.debug:
                    pprint(self.dbTables)
                    pprint(self.dbAttributs)
                self.disconnect(dbcursor)
            except sqlite3.Error as error:
                raise SQLException(f"Erreur SQLite :\n -> {error}")


class DBMySQL(Database):

    def __init__(self, db, debug,verbose=False):
        # self.dbPGID = dict()
        (user, password, host, database) = db
        self.user = user
        self.password = password
        self.host = host
        self.database = database
        self.connection = None
        super().__init__(db=db, dbtype='mysql', debug=debug, verbose=verbose)
        self.name = "MySQL"

    def tables2string(self):
        url = f"mysql+mysqlconnector://{self.user}:{self.password}@{self.host}/{self.database}"
        return self.tables2string2(url)

    def connect(self):
        try:
            (user, password, host, database) = self.db
            # print(self.db)
            self.connection = mysql.connector.connect(user=user, password=password, host=host, database=database)
            cursor = self.connection.cursor()
            return cursor
        except Exception as e:
            raise SQLException(f"Erreur MySQL (connect) :\n {e}")

    def disconnect(self, cursor):
        self.connection.close()

    def getForeignKeys(self, dbcursor, tableName):
        """
        Retrieves foreign key constraints for a given table.

        Parameters:
        dbcursor (cursor): A database cursor object for executing SQL queries.
        tableName (str): The name of the table for which to retrieve foreign key constraints.

        Returns:
        list: A list of tuples, where each tuple represents a foreign key constraint. Each tuple contains:
            - foreign_table_name (str): The name of the foreign table.
            - column_name (str): The name of the column in the original table.
            - foreign_column_name (str): The name of the column in the foreign table.
        """
        query = f"""
    SELECT
        CONSTRAINT_NAME,
        COLUMN_NAME,
        REFERENCED_TABLE_NAME,
        REFERENCED_COLUMN_NAME
    FROM
        INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE
        TABLE_NAME = %s
        AND REFERENCED_TABLE_NAME IS NOT NULL
    """
        dbcursor.execute(query, (tableName,))
        lst = dict()
        for att in dbcursor.fetchall():
            lst[att[1]] = (att[2], att[3])
        return lst
        # return [(i[3], i[2], i[4]) for i in lst]

    def getDBTables(self):
        """
        Récupère les tables de la base de données et leurs attributs.
        :return: Un dictionnaire avec les tables en entrée et
        en valeur l'identifiant de la table (s'il existe)
        et les attributs (et s'ils sont dans la clé)
        """
        if self.db is None:
            raise SQLException("La base de donnée n'est pas renseignée.")
        else:
            if self.debug: print('Récupération des informations de la base MySQL')
            self.dbTables = dict()
            self.dbAttributs = dict()

            dbcursor = self.connect()
            try:
                self.dbTables = dict()
                dbcursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                                 (self.database,))
                lst = dbcursor.fetchall()
                #pprint(lst)
                for tq in lst:
                    t = tq[0]
                    id_t = None
                    dbcursor.execute(f"Describe {t}")
                    attlst = dbcursor.fetchall()
                    fk = self.getForeignKeys(dbcursor, t)
                    lstatt = []
                    for i in attlst:
                        attname = i[0]
                        if i[3] is not None:
                            lstatt.append((attname, 'PRI' in i[3], fk[attname] if attname in fk else None))
                        else:
                            lstatt.append((attname, False, fk[attname] if attname in fk else None))
                        if attname in self.dbAttributs:
                            self.dbAttributs[attname].append(t)
                        else:
                            self.dbAttributs[attname] = [t]
                    self.dbTables[t] = (id_t, lstatt)

                if self.debug:
                    pprint(self.dbTables)
                    pprint(self.dbAttributs)
            except Exception as e:
                raise SQLException(
                    f"Erreur MySQL : Impossible de récupérer les tables de la base de données\n -> {e}")
            finally:
                self.disconnect(dbcursor)


# ======================================================================================================================
# ======================================================================================================================
