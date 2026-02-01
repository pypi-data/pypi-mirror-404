#!/usr/bin/env python3
"""
Propose quelques fonctions et procédures outils pour le projet
"""

import importlib.resources
import json
import os.path
import re
import sys
from configparser import ConfigParser
from datetime import date, datetime

import keyboard

# paramettres des tableaux (affichage des tables)
MAX_TABLE_WIDTH = 160  # Largeur maximale autorisée (bordures comprises)
MIN_COLUMN_WIDTH = 8  # Permet d’afficher au moins « a… »

# ==================================================
# ============ Tools ===============================
# ==================================================

def clear_line():
    # Windows
    if os.name == 'nt':
        os.system('cls')
    # Unix/Linux/MacOS
    else:
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")


def clear_terminal():
    # Windows
    if os.name == 'nt':
        os.system('cls')
    # Unix/Linux/MacOS
    else:
        os.system('clear')

##########################################################################################################
##########################################################################################################
##########################################################################################################

def readConfigFile():
    # lecture du fichier de configuration
    cfg = ConfigParser()
    with importlib.resources.open_text("querycraft.config", "config-sbs.cfg") as fichier:
        cfg.read_file(fichier)
    return cfg


##########################################################################################################
##########################################################################################################
##########################################################################################################

def diff_dates_iso(date_iso1: str, date_iso2: str) -> bool:
    d1 = date.fromisoformat(date_iso1)
    d2 = date.fromisoformat(date_iso2)
    age = abs(d2 - d1).days
    return age

##########################################################################################################
##########################################################################################################
##########################################################################################################

def getTemplate(templatefile: str) -> str:
    try:
        with importlib.resources.open_text("querycraft.templates", templatefile) as fichier:
            return fichier.read()
    except FileNotFoundError:
        print(f"Le fichier '{templatefile}' est introuvable.")
        return ""


##########################################################################################################
##########################################################################################################
##########################################################################################################

def getAge(date_iso: str) -> int:
    age = diff_dates_iso(date_iso, datetime.now().date().isoformat())
    return age


def loadCache(cacheName: str, duree=2) -> dict():
    cache = dict()
    cache2 = dict()
    #print(f"Chargement du cache {cacheName}")
    with importlib.resources.path("querycraft.cache", f"{cacheName}") as file:
        if existFile(file):
            with file.open("r", encoding="utf-8") as fichier:
                cache = json.load(fichier)
            # purge des valeurs trop anciennes
            for k, v in cache.items():
                (sql, date_creation) = v
                if getAge(date_creation) <= duree:
                    cache2[k] = v
                else:
                    pass
    return cache2


def saveCache(cacheName, cache, cle, val):
    #print(f"Sauvegarde du cache {cacheName}")
    cache[cle] = (val, datetime.now().date().isoformat())
    with importlib.resources.path("querycraft.cache", f"{cacheName}") as file:
        with file.open("w", encoding="utf-8") as fichier:
            json.dump(cache, fichier, ensure_ascii=False, indent=2)
    #print(f"Cache {cacheName} sauvegardé")

##########################################################################################################
##########################################################################################################
##########################################################################################################


def loadExos(codeex):
    exos = dict()
    with importlib.resources.path("querycraft.exos", f"{codeex}.json") as file:
        if existFile(file):
            with file.open("r", encoding="utf-8") as fichier:
                exos = json.load(fichier)
        else:
            # print(f"Fichier {file} inexistant")
            print(f"Exo {codeex} introuvable")
    return exos


def getQuestion(codeex, codeq):
    exos = dict()
    with importlib.resources.path("querycraft.exos", f"{codeex}.json") as file:
        if existFile(file):
            with file.open("r", encoding="utf-8") as fichier:
                exos = json.load(fichier)
            if codeq in exos:
                (requete, intention, comment, type, instuctions) = exos[codeq]
                return (requete, intention, comment, type, instuctions)
            else:
                print(f"Question {codeq} introuvable")
                return None
        else:
            # print(f"Fichier {file} inexistant")
            print(f"Exo {codeex} introuvable")
            return None


def saveExos(codeex, exos):
    with importlib.resources.path("querycraft.exos", f"{codeex}.json") as file:
        with file.open("w", encoding="utf-8") as fichier:
            json.dump(exos, fichier, ensure_ascii=False, indent=2)
            print(f"Exo {codeex} sauvegardé")


##########################################################################################################
##########################################################################################################
##########################################################################################################

def stopWithEscKey(mssg: str = "Appuyez sur ESC pour arrêter ou sur une autre touche pour continuer.") -> bool:
    print(mssg)
    # return keyboard.read_key() == 'esc'
    stop = False
    while True:
        # Attendre qu'une touche soit pressée
        event = keyboard.read_event()

        # Vérifier si la touche ESC est pressée
        if event.event_type == keyboard.KEY_DOWN:
            stop = event.name == 'esc'
            break
    return stop


##########################################################################################################
##########################################################################################################
##########################################################################################################

def delEntete(string, char):
    first_index = string.find(char)
    if first_index == -1:
        return ''  # Le caractère n'est pas dans la chaîne
    second_index = string.find(char, first_index + 1)
    return string[second_index + 2:]


##########################################################################################################
##########################################################################################################
##########################################################################################################

def existFile(f: str) -> bool:
    return os.path.isfile(f)


def deleteFile(f: str) -> None:
    if existFile(f):
        os.remove(f)


def existDir(d: str) -> bool:
    return os.path.exists(d)


##########################################################################################################
##########################################################################################################
##########################################################################################################


# == changer date d'un fichier
# touch -t 2006010000 tmp/s88581.ics
# ==
def modifDate(f: str) -> date:
    return date.fromtimestamp(os.stat(f).st_mtime)


def daysOld(f: str) -> int:
    """
    Calculate the number of days since the last modification of a file.

    Parameters:
    - f (str): The path to the file.

    Returns:
    - int: The number of days since the last modification.

    This function uses the `modifDate` function to get the last modification date of the file.
    It then calculates the difference between the current date and the modification date using the `date.today()` and `datetime.timedelta` functions.
    Finally, it returns the number of days as an integer.
    """
    n = date.today()
    d = modifDate(f)
    delta = n - d
    return delta.days


def bold_substring(string: str, substring: str) -> str:
    """
    This function takes a string and a substring as input, and returns a new string with the substring
    enclosed in ANSI escape codes for bold formatting.

    Parameters:
    - string (str): The original string.
    - substring (str): The substring to be bolded.

    Returns:
    - str: The new string with the substring bolded.

    "Example:
    ">>> bold_substring("Hello, World!", "World")
    "Hello, #\033[1mWorld\033[0m!"

    Pour les codes (mise en gras) : https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
    Voir aussi :
    - https://emojipedia.org/
    - https://unicode-explorer.com/

    """
    match = re.search(re.escape(substring), rf"{string}", re.IGNORECASE)
    coord = match.span()
    return string[:coord[0]] + " #\033[1m" + substring + "\033[0m# " + string[coord[1]:]


#################################################################################################
## Codes en partie générés par ChatGPT 5.1 Codex nov. 2025
#################################################################################################

from collections import Counter
from typing import Sequence, Iterable, Tuple, Any, List


def normalize_rows(
        columns_ref: Sequence[str],
        columns_src: Sequence[str],
        rows_src: Iterable[Sequence[Any]],
) -> List[Tuple[Any, ...]]:
    """
    Réordonne les lignes de rows_src pour qu'elles suivent columns_ref.
    """
    if len(columns_src) != len(set(columns_src)):
        raise ValueError("Les colonnes doivent être uniques par table.")

    pos_src = {col: idx for idx, col in enumerate(columns_src)}
    try:
        index_map = [pos_src[col] for col in columns_ref]
    except KeyError as missing:
        raise ValueError(f"Colonne absente : {missing.args[0]!r}") from None

    normalized = []
    for ridx, row in enumerate(rows_src):
        if len(row) != len(columns_src):
            raise ValueError(
                f"Ligne {ridx} : attendu {len(columns_src)} valeurs, reçu {len(row)}."
            )
        normalized.append(tuple(row[idx] for idx in index_map))
    return normalized


def compare_query_results_raw(
        columns1: Sequence[str],
        rows1: Iterable[Sequence[Any]],
        columns2: Sequence[str],
        rows2: Iterable[Sequence[Any]],
) -> int:
    """
    Compare deux tables de résultats SQL.

    :return: code {0,1,2,3,4}
        0 : différences de contenu
        1 : mêmes données, ordre des lignes ET des colonnes différent
        2 : mêmes données, même ordre des colonnes, ordre des lignes différent
        3 : mêmes données, même ordre des lignes, ordre des colonnes différent
        4 : mêmes données, même ordre des colonnes et des lignes
    """
    cols1 = list(columns1)
    cols2 = list(columns2)

    # Vérifications structurelles minimales
    if len(cols1) != len(cols2):
        return 0
    if set(cols1) != set(cols2):
        return 0

    rows1 = list(rows1)
    rows2 = list(rows2)
    if len(rows1) != len(rows2):
        return 0

    same_col_order = cols1 == cols2

    norm_rows1 = normalize_rows(cols1, cols1, rows1)
    norm_rows2 = normalize_rows(cols1, cols2, rows2)

    same_row_order = norm_rows1 == norm_rows2
    if same_row_order:
        return 4 if same_col_order else 3

    # Égalité en ignorant l’ordre des lignes (multiset de tuples)
    # Hypothèse : chaque cellule est hashable (types SQL usuels).
    if Counter(norm_rows1) != Counter(norm_rows2):
        return 0

    return 2 if same_col_order else 1


#################################################################################################


def format_table_1(headers, rows, padding=2, inter=False, table_size=MAX_TABLE_WIDTH, min_col_width=MIN_COLUMN_WIDTH):
    # Calcule la largeur maximale pour chaque colonne
    col_widths = [
        max(len(str(value)) for value in column)
        for column in zip(headers, *rows)
    ]
    col_widths = [w + padding for w in col_widths]

    def format_row(row):
        return "│ " + " ┆ ".join(
            str(value if value is not None else "").replace("\n", " ").ljust(width) for value, width in
            zip(row, col_widths)
        ) + " │"

    def format_row_hd(row):
        return "│ " + " ┆ ".join(
            "\033[1m" + str(value).replace("\n", " ").ljust(width) + "\033[0m" for value, width in zip(row, col_widths)
        ) + " │"

    # Construire la ligne séparatrice
    separator0 = "┌─" + "─┬─".join("─" * width for width in col_widths) + "─┐"
    separator = "╞═" + "═╪═".join("═" * width for width in col_widths) + "═╡"
    separator2 = "├─" + "─┼─".join("─" * width for width in col_widths) + "─┤"
    separator3 = "└─" + "─┴─".join("─" * width for width in col_widths) + "─┘"

    # Générer le tableau complet
    lines = [separator0, format_row_hd(headers), separator]
    for row in rows[:-1]:
        lines.append(format_row(row))
        if inter: lines.append(separator2)
    if rows: lines.append(format_row(rows[-1]))
    lines.append(separator3)

    return "\n".join(lines)


#################################################################################################


def fit_text(text, width):
    """Ajuste le texte à la largeur demandée en ajoutant éventuellement une ellipse."""
    text = str(text)
    if len(text) <= width:
        return text.ljust(width)
    if width == 1:
        return "…"
    if width == 2:
        return text[0] + "…"
    return text[:width - 1] + "…"


def clamp_widths(widths, max_data_width, table_size=MAX_TABLE_WIDTH, min_col_width=MIN_COLUMN_WIDTH):
    """Réduit les largeurs de colonnes jusqu’à rentrer dans la contrainte globale."""
    total = sum(widths)
    if total <= max_data_width:
        return widths

    reducible = sum(max(0, w - min_col_width) for w in widths)
    deficit = total - max_data_width
    if reducible < deficit:
        raise ValueError(
            f"Impossible de faire tenir le tableau dans {table_size} caractères "
            "(trop de colonnes ou contenus trop larges)."
        )

    widths = widths[:]
    while deficit > 0:
        for idx in sorted(range(len(widths)), key=lambda i: widths[i], reverse=True):
            if widths[idx] > min_col_width:
                widths[idx] -= 1
                deficit -= 1
                if deficit == 0:
                    break
    return widths


def format_table_2(headers, rows, padding=1, inter=False, table_size=MAX_TABLE_WIDTH, min_col_width=MIN_COLUMN_WIDTH):
    n_cols = len(headers)
    max_data_width = table_size - (3 * n_cols + 1)
    if max_data_width < n_cols * min_col_width:
        raise ValueError(f"Trop de colonnes pour une largeur de {table_size} caractères.")

    # Largeurs brutes (en tenant compte du padding)
    raw_widths = [
        max(len(str(value).replace("\n", " ")) for value in column) + padding
        for column in zip(headers, *rows)
    ]

    col_widths = clamp_widths(raw_widths, max_data_width, table_size, min_col_width)

    def format_row(row):
        cells = [
            fit_text(str(value if value is not None else "").replace("\n", " "), width) for value, width in
            zip(row, col_widths)
        ]
        return "│ " + " ┆ ".join(cells) + " │"

    def format_row_hd(row):
        cells = [
            "\033[1m" + fit_text(str(value).replace("\n", " "), width) + "\033[0m" for value, width in
            zip(row, col_widths)
        ]
        return "│ " + " ┆ ".join(cells) + " │"

    separator0 = "┌─" + "─┬─".join("─" * width for width in col_widths) + "─┐"
    separator = "╞═" + "═╪═".join("═" * width for width in col_widths) + "═╡"
    separator2 = "├─" + "─┼─".join("─" * width for width in col_widths) + "─┤"
    separator3 = "└─" + "─┴─".join("─" * width for width in col_widths) + "─┘"

    lines = [separator0, format_row_hd(headers), separator]
    for row in rows[:-1]:
        lines.append(format_row(row))
        if inter: lines.append(separator2)
    if rows: lines.append(format_row(rows[-1]))
    lines.append(separator3)

    return "\n".join(lines)


#################################################################################################

import textwrap


def wrap_cell(text, width):
    """Retourne une liste de lignes de longueur ≤ width pour le contenu donné."""
    text = str(text)
    if not text:
        return [""]
    lines = []
    for raw_line in text.splitlines() or [""]:
        wrapped = textwrap.wrap(
            raw_line,
            width=width,
            drop_whitespace=False,
            replace_whitespace=False,
            break_long_words=True,
        )
        lines.extend(wrapped or [""])
    return lines


def format_table_3(headers, rows, padding=1, inter=False, table_size=MAX_TABLE_WIDTH, min_col_width=MIN_COLUMN_WIDTH):
    n_cols = len(headers)
    if n_cols == 0:
        return ""

    # Largeur disponible pour les seules données (sans bordures ni espaces)
    max_data_width = table_size - (3 * n_cols + 1)
    if max_data_width < n_cols * min_col_width:
        raise ValueError(f"Trop de colonnes pour une largeur totale de {table_size} caractères.")

    raw_widths = [
        max(len(str(value)) for value in column) + padding
        for column in zip(headers, *rows)
    ]
    col_widths = clamp_widths(raw_widths, max_data_width)

    def format_physical_lines(row):
        wrapped_cells = [wrap_cell(value, width) for value, width in zip(row, col_widths)]
        row_height = max(len(cell) for cell in wrapped_cells)
        physical_lines = []
        for line_idx in range(row_height):
            cells = [
                (cell[line_idx] if line_idx < len(cell) else "").ljust(width)
                for cell, width in zip(wrapped_cells, col_widths)
            ]
            physical_lines.append("│ " + " ┆ ".join(cells) + " │")
        return physical_lines

    def format_physical_lines_hd(row):
        wrapped_cells = [wrap_cell(value, width) for value, width in zip(row, col_widths)]
        row_height = max(len(cell) for cell in wrapped_cells)
        physical_lines = []
        for line_idx in range(row_height):
            cells = [
                "\033[1m" + (cell[line_idx] if line_idx < len(cell) else "").ljust(width) + "\033[0m"
                for cell, width in zip(wrapped_cells, col_widths)
            ]
            physical_lines.append("│ " + " ┆ ".join(cells) + " │")
        return physical_lines

    separator0 = "┌─" + "─┬─".join("─" * width for width in col_widths) + "─┐"
    separator = "╞═" + "═╪═".join("═" * width for width in col_widths) + "═╡"
    separator2 = "├─" + "─┼─".join("─" * width for width in col_widths) + "─┤"
    separator3 = "└─" + "─┴─".join("─" * width for width in col_widths) + "─┘"

    lines = [separator0]
    lines.extend(format_physical_lines_hd(headers))
    lines.append(separator)
    for row in rows[:-1]:
        lines.extend(format_physical_lines(row))
        if inter: lines.append(separator2)
    if rows:
        lines.extend(format_physical_lines(rows[-1]))
    lines.append(separator3)

    return "\n".join(lines)


#################################################################################################

from collections import OrderedDict
from typing import Sequence, Iterable, Any


def group_table_as_rows(
        columns: Sequence[str],
        data_rows: Iterable[Sequence[Any]],
        group_cols: Sequence[str] | None = None,
):
    """
    Regroupe des lignes (listes/tuples) et renvoie une liste de lignes.

    - `columns` : noms des colonnes (ordre fixe).
    - `data_rows` : lignes alignées sur `columns`.
    - `group_cols` : colonnes servant de clé (scalaires dans le résultat).
      Les autres colonnes deviennent des listes de valeurs.

    Retour :
        list[list[Any]]
    """
    cols = list(columns)
    rows = [list(row) for row in data_rows]
    if not rows:
        return []

    group_cols = list(group_cols or [])
    col_index = {col: idx for idx, col in enumerate(cols)}

    # Vérifications simples
    for col in group_cols:
        if col not in col_index:
            raise ValueError(f"Colonne inconnue pour le regroupement : {col!r}")

    grouped = OrderedDict()  # clé -> listes de lignes complètes
    for ridx, row in enumerate(rows):
        if len(row) != len(cols):
            raise ValueError(
                f"Ligne {ridx} : attendu {len(cols)} valeurs, reçu {len(row)}."
            )
        key = tuple(row[col_index[col]] for col in group_cols)
        grouped.setdefault(key, []).append(row)

    result = []
    for key, matching_rows in grouped.items():
        out_row = []
        for col in cols:
            idx = col_index[col]
            if col in group_cols:
                # valeur scalaire (issue de la clé)
                out_row.append(key[group_cols.index(col)])
            else:
                # liste de toutes les valeurs correspondantes
                out_row.append([r[idx] for r in matching_rows])
        result.append(out_row)

    return result


#################################################################################################
#################################################################################################
#################################################################################################


if __name__ == "__main__":
    headers = ["Produit", "Quantité", "Prix (€)", "Description"]
    rows = [
        ["Pommes", 12, 3.40, "Variété Gala, croquante et très sucrée. Idéale pour les tartes et compotes."],
        ["Oranges", 8, 4.10, "Riche en vitamine C.\nConvient bien pour les jus frais."],
        ["Bananes", 15, 2.80, "Origine Guadeloupe. Bien mûres, parfaites pour les smoothies ou les desserts."],
    ]

    print(format_table_1(headers, rows))
    print(format_table_2(headers, rows))
    print(format_table_3(headers, rows, inter=True))

    cols = ["ville", "jour", "ventes", "devise"]
    data = [
        ["Paris", "Lundi", 12, "EUR"],
        ["Paris", "Mardi", 18, "EUR"],
        ["Lyon", "Lundi", 9, "EUR"],
        ["Paris", "Mercredi", 22, "EUR"],
        ["Lyon", "Mardi", 11, "EUR"],
    ]

    rows = group_table_as_rows(cols, data, group_cols=["ville"])
    print(format_table_3(headers, rows))
    # for line in rows:
    #    print(line)

    cols_a = ["id", "nom", "age"]
    rows_a = [
        (1, "Ana", 30),
        (2, "Ben", 41),
    ]
    cols_b = ["id", "age", "nom"]
    rows_b = [
        (2, 41, "Ben"),
        (1, 30, "Ana"),
    ]

    print(compare_query_results_raw(cols_a, rows_a, cols_a, rows_a))  # -> 2
