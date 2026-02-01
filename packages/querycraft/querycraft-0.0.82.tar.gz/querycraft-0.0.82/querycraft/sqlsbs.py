#!/usr/bin/env python3

import argparse
import importlib.resources
import os
import sys
from configparser import ConfigParser
import json

import colorama

from querycraft.Database import *
from querycraft.LLM import manage_ia, show_ia
from querycraft.LRS import LRS
from querycraft.SQL import SQL,colorize_sql
from querycraft.tools import readConfigFile, clear_line, existFile, deleteFile, saveExos, loadExos, \
    getQuestion

##########################################################################################################
##########################################################################################################
##########################################################################################################

def sbs(sql, cfg, sol=None, verbose=False):
    duree = 0
    if verbose:
        print(f"Bonjour {os.getlogin()} !")
        print('==================================================================================================')
        print('======================================== Requête à analyser ======================================')
        print('==================================================================================================\n')
        print("-------------------------")
        print("--- Schéma de la base ---")
        print("-------------------------")
        sql.printDBTables()
        print("--------------------------")
        print('--- Requête à exécuter ---')
        print("--------------------------")
        print(colorize_sql(f"{sql}"))
        print("\n-----------------------")
        print('--- Table à obtenir ---')
        print("-----------------------")
        # print(sql.getPLTable())
        (hd, rows) = sql.getTable()
        print(format_table_2(hd, rows))
        if cfg['IA']['mode'] == 'on':
            print("Construction de l'explication avec l'IA générative. Veuillez patienter.")
            rep = manage_ia('explain', cfg, verbose, f"{sql}", sql.getDB(), None, None, sql, None, None)
            clear_line()
            show_ia(rep,"Explication de la requête")

        print('==================================================================================================')
        print('========================================== Pas à pas =============================================')
        print('==================================================================================================\n')
    sql.sbs()
    if verbose:
        # Comparaison des résultats
        ok = False
        if sol is not None:
            cmp = sql.similaire(sol)
            ok = cmp == 4
        else:
            ok = False
            cmp = None

        # Analyse des requêtes
        if cfg['IA']['mode'] == 'on' and sol is not None:
            print('==================================================================================================')
            print('========================================== Correction ============================================')
            print(
                '==================================================================================================\n')
            buildStdCorrection(ok, cfg['Autre']['aide'] == 'on', sol, cmp)
            print("Construction de la correction avec l'IA générative. Veuillez patienter.")
            (exo, quest, intention, com, inst) = sol.getExo()
            rep = manage_ia('solution', cfg, verbose, f"{sql} ; {sol}", sql.getDB(), None, sql, sol, intention, cmp)
            clear_line()
            show_ia(rep,"Correction de la requête")
        else:
            buildStdCorrection(ok, cfg['Autre']['aide'] == 'on', sol, cmp)
        print('fin')


def buildStdCorrection(ok, setHelp, sol, cmp):
    if not ok and sol is not None:
        match cmp:
            case 0:
                print(
                    "❌ La requête proposée n'est pas correcte. Elle ne renvoie pas les mêmes résultats que la requête attendue.")
                if setHelp and sol.com :
                    print(f"💡✨ {sol.com}")
            case 1:
                print(
                    "⚠️ La requête renvoie les mêmes résultats que la requête attendue, mais lignes et colonnes ne sont pas dans le même ordre.")
            case 2:
                print(
                    "⚠️ La requête renvoie les mêmes résultats que la requête attendue, mais les lignes ne sont pas dans le même ordre.")
            case 3:
                print(
                    "⚠️ La requête renvoie les mêmes résultats que la requête attendue, mais les colonnes ne sont pas dans le même ordre.")
        # switch = input("Voulez-vous voir la requête attendue ? (o/n) ")
        # if switch == 'o':
        #    print(f"\n{BLUE}--- Requête attendue ---{RESET}")
        #    print(sol.getQuery())
    elif ok and sol is not None:
        print(
            "✅ La requête renvoie les mêmes résultats que la requête attendue.\n ⚠️ Vérifiez que la requête répond bien à la demande.")
    else:
        pass  # print("⚠️ Pas de correction disponible pour cette requête.")


def getQuery(args):
    if args.file and existFile(args.file):
        sqlTXT = ''
        with open(args.file, 'r') as f:
            sqlTXT += f.read()
    elif args.sql:
        sqlTXT = args.sql
    else:
        sqlTXT = ''
    return sqlTXT


##########################################################################################################
##########################################################################################################
##########################################################################################################

def stdArgs(parser, def_db):
    if def_db:
        parser.add_argument('-d', '--db', help=f'database name (by default {def_db})', default=def_db)
    else:
        parser.add_argument('-d', '--db', help=f'database name', required=True)

    parser.add_argument('-v', '--verbose', help='verbose mode', action='store_true', default=False)
    parser.add_argument('-nsbs', '--step_by_step', help='step by step mode off', action='store_false', default=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-b', '--describe', help='DB Schema', action='store_true', default=False)
    group.add_argument('-f', '--file', help='sql file')
    group.add_argument('-s', '--sql', type=str, help='sql string')

    group = parser.add_argument_group(title='exercice')
    group.add_argument('-e', '--exercice', help="code de l'exercice", default=None)
    group.add_argument('-q', '--question', help="code de la question", default=None)

    return parser


def ctrlStdArgs(parser, args):
    if (args.exercice is None) ^ (args.question is None):
        parser.error("Les options -e et -q doivent être fournies ensemble ou aucune des deux.")


def dbConnectArgs(parser, defaultPort, defaultHost='localhost', defaultUser='desmontils-e'):
    parser.add_argument('-u', '--user', help=f'database user (by default {defaultUser})',
                        default=defaultUser)  # 'desmontils-e')
    parser.add_argument('-p', '--password', help='database password', default=None)
    parser.add_argument('--host', help=f'database host (by default {defaultHost})', default=defaultHost)  # 'localhost')
    parser.add_argument('--port', help=f'database port (by default {defaultPort})', default=defaultPort)  # '5432')


def doSBS(db, dbtype, dbname, sqlTXT, debug, verbose, step_by_step, exo=None, quest=None, lrs=None):
    # clear_terminal()
    try:
        cfg = readConfigFile()
        SQLQueryException.setCfg(cfg)

        # LRS configuration
        if lrs:
            lrs.setContextSBS()
        sql = SQL(db=db, dbtype=dbtype, debug=debug, verbose=verbose, step_by_step=step_by_step)
        sql.setSQL(sqlTXT)
        if lrs: lrs.sendSBSExecute(dbtype, dbname, sqlTXT)

        # Lancement du programme
        try:
            if exo is not None and quest is not None:
                q = getQuestion(exo, quest)
                if q is not None:
                    (requete, intention, com, type, inst) = q
                    sol = SQL(db=db, dbtype=dbtype, debug=debug, verbose=verbose, step_by_step=step_by_step)
                    sol.setSQL(requete)
                    sol.setExo(intention, exo, quest, com, type, inst)
                else:
                    sol = None
            else:
                sol = None

            sbs(sql, cfg, sol, verbose)  # Pas à pas

            if lrs: lrs.sendSBSpap(dbtype, dbname, sqlTXT)
        except Exception as e:
            # LRS : envoie du statement
            if lrs: lrs.sendSBSpap(dbtype, dbname, sqlTXT, error=e)
            print(f'Erreur SBS : {e}')
    except Exception as e:
        print(f"{e}")
        # LRS : envoie du statement
        if lrs: lrs.sendSBSExecute(dbtype, dbname, sqlTXT, error=e)
        exit()

def doDescribe(cfg, sgbd, verbose=False):
    if verbose and (cfg['IA']['mode'] == 'on'):
        # print(f"Description de la base de données {sgbd.dbname} ({sgbd.dbtype})")
        print("Construction de l'explication avec l'IA générative. Veuillez patienter.")
        rep = manage_ia('describe', cfg, verbose, f"{sgbd.dbtype}-{sgbd.db}", sgbd, None, None, None, None, None)
        clear_line()
        show_ia(rep, "Description de la base de données")
    print(f"\nDetail de la base de données")
    print(sgbd.tables2string())
    exit(0)

##########################################################################################################
##########################################################################################################
##########################################################################################################
def mysql():
    cfg = readConfigFile()
    parser = argparse.ArgumentParser(
        description="Effectue l'exécution pas à pas d'une requête sur MySQL\n (c) E. Desmontils, Nantes Université, 2024")
    if cfg['Database']['type'] == "mysql":
        port = cfg['Database']['port']
        host = cfg['Database']['host']
        user = cfg['Database']['username']
        password = cfg['Database']['password']
        db = cfg['Database']['database']
        dbConnectArgs(parser, defaultPort=port, defaultHost=host, defaultUser=user)
    else:
        port = 3306
        host = 'localhost'
        user = 'desmontils-e'
        password = ''
        db = None
        dbConnectArgs(parser, defaultPort=port, defaultHost=host, defaultUser=user)

    stdArgs(parser, db)
    args = parser.parse_args()
    ctrlStdArgs(parser, args)

    port = args.port
    host = args.host
    user = args.user
    db = args.db

    if (args.password is None) and (args.port == cfg['Database']['port']) and (
            args.host == cfg['Database']['host']) and (args.user == cfg['Database']['username']) and (
            args.db == cfg['Database']['database']):
        password = cfg['Database']['password']
    else:
        if args.password is None:
            password = ''
        else:
            password = args.password

    debug = False
    # debug = cfg.getboolean('Autre', 'debug') or args.debug
    verbose = cfg.getboolean('Autre', 'verbose') or args.verbose

    # if debug:
    #    print('Infos BD : ', type, args.user, args.password, args.host, args.port, args.db)
    if args.describe:
        # Affichage des tables de la BD
        try:
            doDescribe(cfg,
                       DBMySQL(db=(user, password, host, db), debug=False, verbose=verbose), args.verbose)
        except Exception as e:
            print(f'Erreur Describe MySQL : {e}')
            exit(1)

    # xAPI configuration
    onLRS = cfg['LRS']['mode'] == 'on'
    if onLRS:
        lrs = LRS(cfg['LRS']['endpoint'], cfg['LRS']['username'], cfg['LRS']['password'], debug=debug)
    else:
        lrs = None

    sqlTXT = getQuery(args)
    if (args.exercice is not None) and (args.question is not None):
        exo = args.exercice
        quest = args.question
    else:
        exo = None
        quest = None

    if onLRS:
        doSBS((user, password, host, db), 'mysql', db, sqlTXT, debug, verbose, args.step_by_step, exo, quest, lrs)
    else:
        doSBS((user, password, host, db), 'mysql', db, sqlTXT, debug, verbose, args.step_by_step, exo, quest)


##########################################################################################################
##########################################################################################################
##########################################################################################################
def pgsql():
    cfg = readConfigFile()
    parser = argparse.ArgumentParser(
        description="Effectue l'exécution pas à pas d'une requête sur PostgreSQL\n (c) E. Desmontils, Nantes Université, 2024")
    if cfg['Database']['type'] == "pgsql":
        port = cfg['Database']['port']
        host = cfg['Database']['host']
        user = cfg['Database']['username']
        password = cfg['Database']['password']
        db = cfg['Database']['database']
        dbConnectArgs(parser, defaultPort=port, defaultHost=host, defaultUser=user)
    else:
        port = 5432
        host = 'localhost'
        user = 'desmontils-e'
        db = None
        dbConnectArgs(parser, defaultPort=port, defaultHost=host, defaultUser=user)

    stdArgs(parser, db)
    args = parser.parse_args()
    ctrlStdArgs(parser, args)

    port = args.port
    host = args.host
    user = args.user
    db = args.db

    if (args.password is None) and (args.port == cfg['Database']['port']) and (
            args.host == cfg['Database']['host']) and (args.user == cfg['Database']['username']) and (
            args.db == cfg['Database']['database']):
        password = cfg['Database']['password']
    else:
        if args.password is None:
            password = ''
        else:
            password = args.password

    debug = False
    # debug = cfg.getboolean('Autre', 'debug') or args.debug
    verbose = cfg.getboolean('Autre', 'verbose') or args.verbose

    if args.describe:
        # Affichage des tables de la BD
        try:
            doDescribe(cfg,
                       DBPGSQL(db=f"dbname={db} user={user} password={password} host={host} port={port}", debug=debug,
                               verbose=verbose), args.verbose)
        except Exception as e:
            print(f'Erreur Describe PostgreSQL : {e}')
            exit(1)

    # xAPI configuration
    onLRS = cfg['LRS']['mode'] == 'on'
    if onLRS:
        lrs = LRS(cfg['LRS']['endpoint'], cfg['LRS']['username'], cfg['LRS']['password'], debug=debug)
    else:
        lrs = None

    sqlTXT = getQuery(args)
    if (args.exercice is not None) and (args.question is not None):
        exo = args.exercice
        quest = args.question
    else:
        exo = None
        quest = None

    if onLRS:
        doSBS(f"dbname={db} user={user} password={password} host={host} port={port}", 'pgsql',
              db, sqlTXT, debug, verbose, args.step_by_step, exo, quest, lrs)
    else:
        doSBS(f"dbname={db} user={user} password={password} host={host} port={port}", 'pgsql',
              db, sqlTXT, debug, verbose, args.step_by_step, exo, quest)


##########################################################################################################
##########################################################################################################
##########################################################################################################
def sqlite():
    cfg = readConfigFile()
    parser = argparse.ArgumentParser(
        description="Effectue l'exécution pas à pas d'une requête sur SQLite\n (c) E. Desmontils, Nantes Université, 2024")

    if cfg['Database']['type'] == "sqlite":
        db = cfg['Database']['database']
    else:
        db = None

    parser = stdArgs(parser, db)
    args = parser.parse_args()
    ctrlStdArgs(parser, args)

    debug = False
    # debug = cfg.getboolean('Autre', 'debug') or args.debug
    verbose = cfg.getboolean('Autre', 'verbose') or args.verbose

    db = args.db

    if not (existFile(db)):
        if args.verbose: print(f'database file not found : {db}')
        package_files = importlib.resources.files("querycraft.data")
        if args.verbose: print(f'trying to search in default databases')
        if not (existFile(package_files / db)):
            print(f'database file not found')
            exit(1)
        else:
            db = package_files / db
            if args.verbose: print('database exists')
    else:
        if args.verbose: print('database exists')
    # if args.debug:
    #    print('Infos BD : ', type, args.user, args.password, args.host, args.port, args.db)
    if args.describe:
        # Affichage des tables de la BD
        try:
            doDescribe(cfg, DBSQLite(db=str(db), debug=debug, verbose=verbose), args.verbose)
        except Exception as e:
            print(f'Erreur Describe SQLite : {e}')
            exit(1)

    # xAPI configuration
    onLRS = cfg['LRS']['mode'] == 'on'
    if onLRS:
        lrs = LRS(cfg['LRS']['endpoint'], cfg['LRS']['username'], cfg['LRS']['password'], debug=debug)
    else:
        lrs = None

    sqlTXT = getQuery(args)
    if (args.exercice is not None) and (args.question is not None):
        exo = args.exercice
        quest = args.question
    else:
        exo = None
        quest = None
    if onLRS:
        doSBS(db, 'sqlite', db, sqlTXT, debug, verbose, args.step_by_step, exo, quest, lrs)
    else:
        doSBS(db, 'sqlite', db, sqlTXT, debug, verbose, args.step_by_step, exo, quest)


##########################################################################################################
##########################################################################################################
##########################################################################################################
def parse_assignment(assignment: str):
    """
    Transforme une chaîne 'Section.clef=valeur' en ses composantes.
    """
    try:
        section_key, value = assignment.split("=", 1)
        section, key = section_key.split(".", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Format invalide pour --set '{assignment}'. "
            "Utiliser Section.clef=valeur."
        ) from exc
    return section.strip(), key.strip(), value.strip()


def afficher_config(config: ConfigParser) -> None:
    if not config.sections():
        print("Le fichier ne contient aucune section.")
        return

    largeur_section = max(len(section) for section in config.sections())
    largeur_cle = max(
        len(key)
        for section in config.sections()
        for key in config[section].keys()
    )
    # print(largeur_cle)
    for section in config.sections():
        print(f"\n{colorama.Fore.GREEN}{colorama.Style.BRIGHT}[{section}]{colorama.Style.RESET_ALL}")
        tab = []
        for key, value in config[section].items():
            # print(f"  {key.ljust(largeur_cle)} : {value}")
            tab.append([key, value])
        print(format_table_2(headers=['Clé', 'Valeur'], rows=tab, table_size=50, min_col_width=largeur_cle))
        if section == "IA":
            print(f"Services reconnus : ollama, poe, openai et generic")


def admin() -> None:
    parser = argparse.ArgumentParser(
        description="Met à jour des paramètres du fichier de configuration."
    )
    parser.add_argument(
        "--set",
        nargs="+",
        required=False,
        help="Assignments au format Section.clef=valeur."
    )
    args = parser.parse_args()
    with importlib.resources.path("querycraft.config", "config-sbs.cfg") as config_path:
        config = ConfigParser()
        config.optionxform = str  # respecte la casse des clefs
        config.read(config_path, encoding="utf-8")

        if args.set:
            for assignment in args.set:
                section, key, value = parse_assignment(assignment)
                if section not in config:
                    print(f"Erreur : section '{section}' absente dans {config_path.name}.", file=sys.stderr)
                    sys.exit(1)
                if key not in config[section]:
                    print(f"Erreur : clef '{key}' absente dans la section '{section}'.", file=sys.stderr)
                    sys.exit(1)
                config[section][key] = value

            with config_path.open("w", encoding="utf-8") as config_file:
                config.write(config_file)

            print(f"✅ Fichier de configuration mis à jour avec succès.")
        else:
            print("Aucune assignation à traiter.")
            afficher_config(config)


##########################################################################################################
##########################################################################################################
##########################################################################################################


def build_parser_exos() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Gestion d'exercices et questions."
    )
    sub = p.add_subparsers(dest="command", required=True)

    c1 = sub.add_parser("create-ex", help="Créer un exercice")
    c1.add_argument("code", help="Code de l'exercice")

    c2 = sub.add_parser("delete-ex", help="Supprimer un exercice")
    c2.add_argument("code", help="Code de l'exercice")

    c3a = sub.add_parser("add-q", help="Ajouter une question à un exercice")
    c3a.add_argument("code", help="Code de l'exercice")
    c3a.add_argument("numero", help="Numéro de la question")
    c3a.add_argument("requete", help="Requête SQL")
    c3a.add_argument("-i","--intention", help="Intention de la requête", default="")
    c3a.add_argument("-e","--explication", help="Explication/aide de la requête", default="")
    c3a.add_argument("-t","--type", help="Type", choices=["I->R", "R->I"], default="I->R")
    c3a.add_argument("-r", "--instruction", help="Instruction selon le type de la requête", default="")

    c3b = sub.add_parser("add-q2", help="Ajouter un groupe de questions à un exercice. Si un numéro de question existe déjà, le processus est stoppé et l'exercice reste inchangé.")
    c3b.add_argument("code", help="Code de l'exercice")
    c3b.add_argument("file", help="Fichier JSON contenant les questions")

    c4 = sub.add_parser("delete-q", help="Supprimer une question")
    c4.add_argument("code", help="Code de l'exercice")
    c4.add_argument("numero", help="Numéro de la question")

    c5 = sub.add_parser("show-ex", help="Afficher un exercice")
    c5.add_argument("code", help="Code de l'exercice")

    return p


def create_exercice(code):
    exo = dict()
    with importlib.resources.path("querycraft.exos", f"{code}.json") as file:
        if existFile(file):
            print(f"L'exercice {code} existe déjà.")
            return False
        else:
            saveExos(code, exo)
            return True


def delete_exercice(code):
    with importlib.resources.path("querycraft.exos", f"{code}.json") as file:
        if existFile(file):
            deleteFile(file)
            print(f"L'exercice {code} a été supprimé.")
            return True
        else:
            print(f"L'exercice {code} n'existe pas.")
            return False


def add_question(codeex, numero, requete, intention, type):
    exo = loadExos(codeex)
    if numero in exo:
        print(f"La question {numero} existe déjà.")
        return False
    else:
        exo[numero] = [requete, intention, type]
        saveExos(codeex, exo)
        return True

def add_question_list(codex, file) :
    '''
    À partir d'un fichier JSON, ajoute des questions à un exercice.
    Le fichier JSON doit être de la forme :
    {"no_question": ["requete", "intention", "commentaire", "type", "instruction"], ...}
    '''
    exo = loadExos(codex)
    with open(file, 'r') as f:
        questions = json.load(f)
        for q, infos in questions.items():
            if q in exo:
                print(f"La question {q} existe déjà.")
                return False
        for q, (requete, intention, comment, type, instuction) in questions.items():
            exo[q] = [requete, intention, comment, type, instuction]
        saveExos(codex, exo)
        return True

def delete_question(codeex, numero):
    exo = loadExos(codeex)
    if numero not in exo:
        print(f"La question {numero} n'existe pas.")
        return False
    else:
        del exo[numero]
        saveExos(codeex, exo)
        return True


def show_exercice(codeex):
    exo = loadExos(codeex)
    if exo:
        for q, (requete, intention, comment, type, instuctions) in exo.items():
            print(f"- Question {q}")
            print(f"  Requête SQL : {requete}")
            print(f"  Intention   : {intention}")
            print(f"  Commentaire : {comment}")
            print(f"  Type        : {type}")
            print(f"  Instructions : {instuctions}")
        return True
    else:
        print("Aucune question dans cet exercice.")
        return False


def exos() -> None:
    parser = build_parser_exos()
    args = parser.parse_args()
    ok = False
    try:
        if args.command == "create-ex":
            ok = create_exercice(args.code)
        elif args.command == "delete-ex":
            ok = delete_exercice(args.code)
        elif args.command == "add-q":
            ok = add_question(args.code, args.numero, args.requete, args.intention, args.type)
        elif args.command == "add-q2":
            ok = add_question_list(args.code, args.file)  # args.type)
        elif args.command == "delete-q":
            ok = delete_question(args.code, args.numero)
        elif args.command == "show-ex":
            ok = show_exercice(args.code)
        else:
            parser.error("Commande inconnue.")
        if ok:
            print("✅ Opération réussie.")
        else:
            print(f"❌ Échec de l'opération")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)


##########################################################################################################
##########################################################################################################
##########################################################################################################
def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--lrs', help='use en Veracity lrs', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', help='verbose mode', action='store_true', default=False)
    parser.add_argument('--debug', help='debug mode', action='store_true', default=False)
    parser.add_argument('-d', '--db', help='database file (sqlite) or name (others)', default=None)
    parser.add_argument('-nsbs', '--step_by_step', help='step by step mode', action='store_false', default=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', help='sql file')
    group.add_argument('-s', '--sql', type=str, help='sql string', default="")
    group.add_argument('-b', '--describe', help='DB Schema', action='store_true', default=False)

    args = parser.parse_args()
    sqlTXT = getQuery(args)

    # ==================================================
    # === Gestion de la configuration =================
    # ==================================================

    cfg = readConfigFile()

    # Debug ?
    debug = cfg.getboolean('Autre', 'debug') or args.debug
    verbose = cfg.getboolean('Autre', 'verbose') or args.verbose
    if debug:
        print("Mode debug activé")
    package_files = importlib.resources.files("querycraft.data")
    # Database configuration
    if args.db:
        if args.db.endswith('.db'):
            if not (existFile(args.db)):
                if args.verbose:
                    print(f'database file not found : {args.db}')
                    print(f'trying to search in default databases')
                if not (existFile(package_files / args.db)):
                    print(f'database file not found')
                    exit(1)
                else:
                    args.db = package_files / args.db
                    if args.verbose: print('database exists')
            else:
                if args.verbose: print('database exists')
            database = args.db
            if debug: print(f"SQLite database from parameter : {database}")
            type = 'sqlite'
            username = None
            password = None
            host = None
            port = None
        else:
            database = args.db
            if debug: print(f"PGSQL database from parameter : {database}")
            type = 'pgsql'  # Database configuration
            username = 'postgres'
            password = ''
            host = 'localhost'
            port = '5432'
    else:
        type = cfg['Database']['type']
        if type == 'sqlite':
            if debug: print(f"SQLite database from config file : {cfg['Database']['database']}")
            database = package_files / cfg['Database'][
                'database']  # importlib.resources.resource_filename("querycraft.data", cfg['Database']['database'])
            username = None
            password = None
            host = None
            port = None
        else:
            if debug: print(f"{type} database from config file : {cfg['Database']['database']}")
            username = cfg['Database']['username']
            password = cfg['Database']['password']
            host = cfg['Database']['host']
            port = cfg['Database']['port']
            database = cfg['Database']['database']

    # xAPI configuration
    onLRS = cfg['LRS']['mode'] == 'on'
    if onLRS:
        lrs = LRS(cfg['LRS']['endpoint'], cfg['LRS']['username'], cfg['LRS']['password'], debug=debug)
        lrs.setContextSBS()

    if debug:
        print('Infos BD : ', type, username, password, host, port, database)

    try:
        try:
            if type is None:
                raise Exception("Configuration non fournie")
            if type == 'sqlite':
                if args.describe:
                    # Affichage des tables de la BD
                    try:
                        db = DBSQLite(db=database, debug=False, verbose=args.verbose)
                        print(f"{type}\n{db.tables2string()}")
                        exit(0)
                    except Exception as e:
                        print(f"Erreur Describe SQLite : {e}")
                        exit(1)
                sql = SQL(db=database, dbtype='sqlite', debug=debug, verbose=verbose, step_by_step=args.step_by_step)
            elif type == 'pgsql':  # f"dbname={database} user={username} password={password} host={host} port={port}"
                if args.describe:
                    # Affichage des tables de la BD
                    try:
                        db = DBPGSQL(
                            db=f"dbname={database} user={username} password={password} host={host} port={port}",
                            debug=False, verbose=args.verbose)
                        print(f"{type}\n{db.tables2string()}")
                        exit(0)
                    except Exception as e:
                        print(f"Erreur Describe PostgreSQL : {e}")
                        exit(1)
                sql = SQL(f"dbname={database} user={username} password={password} host={host} port={port}",
                          dbtype='pgsql', debug=debug, verbose=verbose, step_by_step=args.step_by_step)
            elif type == 'mysql':  # (username, password, host ,database) # port ????
                if args.describe:
                    # Affichage des tables de la BD
                    try:
                        db = DBMySQL(db=(username, password, host, database), debug=False, verbose=args.verbose)
                        print(f"{type}\n{db.tables2string()}")
                        exit(0)
                    except Exception as e:
                        print(f"Erreur Describe MySQL : {e}")
                        exit(1)
                sql = SQL(db=(username, password, host, database), dbtype='mysql', debug=debug, verbose=verbose,
                          step_by_step=args.step_by_step)
            else:
                raise Exception("Base de données non supportée")

            sql.setSQL(sqlTXT)

            # LRS : envoie du statement
            if onLRS: lrs.sendSBSExecute(type, database, sqlTXT)

        except Exception as e:
            pprint(e)
            # LRS : envoie du statement
            if onLRS: lrs.sendSBSExecute(type, database, sqlTXT, error=e)
            exit()

        sbs(sql, cfg, verbose)  # Pas à pas

        if onLRS: lrs.sendSBSpap(type, database, sqlTXT)

    except Exception as e:
        # LRS : envoie du statement
        if onLRS: lrs.sendSBSpap(type, database, sqlTXT, e)
        print(f'Erreur SBS : {e}')


if __name__ == '__main__':
    main()
