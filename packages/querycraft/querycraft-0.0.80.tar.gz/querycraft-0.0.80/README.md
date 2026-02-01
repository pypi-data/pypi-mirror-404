# QueryCraft

[TOC]


## Le nom ?

Un nom en anglais qui évoque l'idée de "façonner" ou "construire" des requêtes SQL de manière intuitive, parfait pour une approche pédagogique. (GPT 4o ;-) )

## Objectifs

L'objectif de cette bibliothèque est de proposer des classes Python permettant de manipuler des requêtes SQL. 
Elle propose aussi des applications pour décomposer l'exécution d'une requête SQL sur une base de données PostgreSQL, MySQL ou SQLite.

## Fonctionnalités

- **Analyse de requêtes SQL** : Analysez et comprenez la structure de vos requêtes SQL.
- **Décomposition de requêtes** : Décomposez vos requêtes SQL en étapes simples pour une meilleure compréhension.
- **Support multi-SGBD** : Compatible avec PostgreSQL, MySQL et SQLite.
- **Interface en ligne de commande** : Utilisez l'application en ligne de commande pour analyser et décomposer vos requêtes SQL.
- **Aide de l'IA** : Comprenez vos erreurs SQL grâce à l'aide de l'IA.

## Limitations

### Limitations liées à SQL et aux SGBD

- **Opérateurs SQL non couverts** : Certains opérateurs SQL avancés peuvent ne pas être entièrement pris en charge, en particulier les opérateurs ensemblistes. 
                                    Par exemple, les opérateurs `INTERSECT`, `EXCEPT` et `UNION` ne sont pas pris en charge.
                                    Les sous-requêtes dans le 'From' sont prises en charges, mais pas les sous-requêtes dans le 'Where' et le 'Having' (pas de pas à pas possible).
- **Support limité des fonctions SQL** : Certaines fonctions SQL avancées peuvent ne pas être entièrement prises en charge.
- **Compatibilité avec les versions de SGBD** : La compatibilité avec les versions spécifiques de PostgreSQL, MySQL et SQLite peut varier.

### Problème avec la version de Python

QueryCraft fonctionne avec Python 3.11. A ce jour (13/03/2025), une bibliothèque (psycopg2) pose des problèmes avec Python 3.12. Il est donc préférable de rester pour l'instant sur la version 3.11.


## Installation 

### Après téléchargement depuis Gitlab :

```shell
git clone https://gitlab.univ-nantes.fr/ls2n-didactique/querycraft.git
cd querycraft
pip install -e .
```

### Sans téléchargement depuis Gitlab :

```shell
pip install querycraft
```

## Mise à jour

```shell
pip install --upgrade querycraft  
```

## Usage

**Pour voir les commandes et comprendre l'utilisation avec exemples voir : [HOW_TO_USE](HOW_TO_USE.md)**
La requête devra être écrite entre double quotes " ".

### PostgreSQL

```shell
usage: pgsql-sbs [-h] [-u USER] [-p PASSWORD] [--host HOST] [--port PORT] -d DB [-v] [-nsbs] (-b | -f FILE | -s SQL)

Effectue l'exécution pas à pas d'une requête sur PostgreSQL (c) E. Desmontils, Nantes Université, 2024

options:
  -h, --help            show this help message and exit
  -u USER, --user USER  database user (by default desmontils-e)
  -p PASSWORD, --password PASSWORD
                        database password
  --host HOST           database host (by default localhost)
  --port PORT           database port (by default 5432)
  -d DB, --db DB        database name
  -v, --verbose         verbose mode
  -nsbs, --step_by_step
                        step by step mode
  -b, --describe        DB Schema
  -f FILE, --file FILE  sql file
  -s SQL, --sql SQL     sql string
```

### SQLite

```shell
usage: sqlite-sbs [-h] [-d DB] [-v] [-nsbs] (-b | -f FILE | -s SQL)

Effectue l'exécution pas à pas d'une requête sur SQLite (c) E. Desmontils, Nantes Université, 2024

options:
  -h, --help            show this help message and exit
  -d DB, --db DB        database name (by default cours.db)
  -v, --verbose         verbose mode
  -nsbs, --step_by_step
                        step by step mode
  -b, --describe        DB Schema
  -f FILE, --file FILE  sql file
  -s SQL, --sql SQL     sql string
```

### MySQL

```shell
usage: mysql-sbs [-h] [-u USER] [-p PASSWORD] [--host HOST] [--port PORT] -d DB [-v] [-nsbs] (-b | -f FILE | -s SQL)

Effectue l'exécution pas à pas d'une requête sur MySQL (c) E. Desmontils, Nantes Université, 2024

options:
  -h, --help            show this help message and exit
  -u USER, --user USER  database user (by default desmontils-e)
  -p PASSWORD, --password PASSWORD
                        database password
  --host HOST           database host (by default localhost)
  --port PORT           database port (by default 3306)
  -d DB, --db DB        database name
  -v, --verbose         verbose mode
  -nsbs, --step_by_step
                        step by step mode
  -b, --describe        DB Schema
  -f FILE, --file FILE  sql file
  -s SQL, --sql SQL     sql string
```

## Paramétrage

Il est possible de modifier certains paramètre de l'outil à travers l'application "admin-sbs".

```shell
usage: admin-sbs [-h] [--set SET [SET ...]]

Met à jour des paramètres du fichier de configuration.

options:
  -h, --help           show this help message and exit
  --set SET [SET ...]  Assignments au format Section.clef=valeur.
```

L'absence de paramètres permet d'afficher les paramètres courants :

```shell
% admin-sbs
Aucune assignation à traiter.

[Database]
┌───────────┬───────────┐
│ Clé       ┆ Valeur    │
╞═══════════╪═══════════╡
│ type      ┆ sqlite    │
│ database  ┆ cours.db  │
│ username  ┆ None      │
│ password  ┆ None      │
│ host      ┆ None      │
│ port      ┆ None      │
└───────────┴───────────┘

[LRS]
┌──────────┬─────────────────────────────────────┐
│ Clé      ┆ Valeur                              │
╞══════════╪═════════════════════════════════════╡
│ endpoint ┆ http://local.veracity.it/querycraf… │
│ username ┆ toto                                │
│ password ┆ toto                                │
│ mode     ┆ off                                 │
└──────────┴─────────────────────────────────────┘

[IA]
┌──────────────┬────────────┐
│ Clé          ┆ Valeur     │
╞══════════════╪════════════╡
│ modele       ┆ gemma3:4b  │
│ service      ┆ ollama     │
│ api-key      ┆ None       │
│ url          ┆ None       │
│ mode         ┆ on         │
└──────────────┴────────────┘
Services reconnus : ollama, poe, openai et generic

[Autre]
┌──────────────┬─────────┐
│ Clé          ┆ Valeur  │
╞══════════════╪═════════╡
│ debug        ┆ False   │
│ verbose      ┆ False   │
│ duree-cache  ┆ 2       │
└──────────────┴─────────┘
```

Cela permet, par exemple de spécifier la base de données par défaut. Par exemple :
```shell
admin-sbs --set Database.type=sqlite Database.database=em.db
```

Du coup, dans "sqlite-sbs", l'option "-d" devient optionnelle.

Pour les services de LLM sur le Cloud, pour des questions de sécurité, il est préférable de mettre les clés d'API en variables d'environnement plutôt que dans le fichier de configuration.
Par exemple :
```shell
export POE_API_KEY=...
export OPENAI_API_KEY=...
export OLLAMA_API_KEY=...
```

## LRS

L'outil peut être interfacé avec un LRS compatible XAPI (testé avec Veracity  ; https://lrs.io/home ; https://lrs.io/home/download).  
L'activation et les paramètres du service sont à renseigner dans la section LRS des paramètres.

## Aide de l'IA

Il est possible d'activer ou désactiver l'aide par IA, ainsi que de choisir le service d'IA générative à utiliser. L'appel au service d'IA générative n'est fait que dans le mode "verbose" (option "-v").

Pour bénéficier de l'aide de l'IA, il faut, par exemple, installer Ollama (https://ollama.com/), récupérer le modèle de langage "codellama:7b" puis lancer le serveur Ollama.
Soit :
```shell
ollama pull codellama:7b
ollama serve
```

Puis, l'activer dans l'outil :
```shell
admin-sbs --set IA.service=ollama IA.modele=codellama:7b IA.mode=on
```

Pour désactiver l'IA :
```shell
admin-sbs --set IA.mode=off
```

Le service IA possède un système de cache pour ne pas effectuer plusieurs fois la même requête à l'IAg. Les informations dans ce cache ont une durée de vie limitée. Le paramètre "duree-cache" fixe cette durée en nombre de jours.

Les services IA générative disponibles sont :
- ollama (IA.service=ollama IA.modele=codellama:7b IA.url=None IA.api-key=None ; pas de IA.url car l'API vise http://localhost:11434)
- poe (IA.service=poe IA.modele=gpt-4.1-nano IA.url=None IA.api-key=xxxxxxx ; pas de IA.url car l'API vise https://api.poe.com/v1)
- openai (IA.service=openai IA.modele=gpt-3.5-turbo IA.url=None IA.api-key=xxxxxxx ; pas de IA.url car l'API vise https://api.openai.com/v1/chat/completions)
- google (IA.service=google IA.modele=gemini-pro IA.url=None IA.api-key=xxxxxxx ; pas de IA.url car l'API vise https://generativelanguage.googleapis.com/v1beta/openai/)
- generic (IA.service=generic IA.modele=gpt-3.5-turbo IA.url=https://xxxxx IA.api-key=xxxxxxx) pour un service compatible avec l'API d'Open AI

Le service d'IA générative est appelé dans trois situations :
- en cas d'erreur générée par le SGBD pour aider l'élève ou l'étudiant à comprendre son erreur ;
- lors de la description de la base de données (option "--describe") pour expliquer la base de données ;
- lors de l'exécution d'une requête pour expliquer la structure de la requête.

Attention, le service d'IA générative ne garantit pas la validité de l'aide. Il faut que les étudiant ou élèves vérifient la réponse et se rapprochent des enseignants si nécessaire.

## Gestion des exercices

Depuis la version 0.0.65, QueryCraft propose une gestion des exercices par la commande :
```shell
exos-sbs -h
usage: exos-sbs [-h] {create-ex,delete-ex,add-q,delete-q,show-ex} ...

Gestion d'exercices et questions.

positional arguments:
  {create-ex,delete-ex,add-q,delete-q,show-ex}
    create-ex           Créer un exercice
    delete-ex           Supprimer un exercice
    add-q               Ajouter une question de type I->R à un exercice
    delete-q            Supprimer une question
    show-ex             Afficher un exercice

options:
  -h, --help            show this help message and exit
```

### Créer un exercice

```shell
% exos-sbs create-ex -h
usage: exos-sbs create-ex [-h] code

positional arguments:
  code        Code de l'exercice

options:
  -h, --help  show this help message and exit
```

### Ajouter une question à un exercice

```shell
exos-sbs add-q -h    
usage: exos-sbs add-q [-h] code numero requete intention

positional arguments:
  code        Code de l'exercice
  numero      Numéro de la question
  requete     Requête SQL
  intention   Intention de la requête

options:
  -h, --help  show this help message and exit
```

NB : pour avoir des explications sur l'intention, voir l'article [1].

### Supprimer une question d'un exercice

```shell
 % exos-sbs delete-q -h
usage: exos-sbs delete-q [-h] code numero

positional arguments:
  code        Code de l'exercice
  numero      Numéro de la question

options:
  -h, --help  show this help message and exit
```

### Supprimer un exercice

```shell
% exos-sbs delete-ex -h
usage: exos-sbs delete-ex [-h] code

positional arguments:
  code        Code de l'exercice

options:
  -h, --help  show this help message and exit
```

### Afficher un exercice

```shell
exos-sbs show-ex -h 
usage: exos-sbs show-ex [-h] code

positional arguments:
  code        Code de l'exercice

options:
  -h, --help  show this help message and exit
```

### Exécuter un exercice

```shell
% sqlite-sbs -d cours.db -s 'SELECT m.codemat, titre FROM matieres m left join notes n on m.codemat = n.codemat inner join etudiants using (noetu) group by m.codemat, titre having count(*) > 1 ;' -v -e exos1 -q q1 -nsbs
```

## Article de recherche et conférences

1- Emmanuel Desmontils, Laura Monceaux. **Enseigner SQL en NSI**. Atelier « Apprendre la Pensée Informatique de la Maternelle à l'Université », dans le cadre de la conférence Environnements Informatiques pour l'Apprentissage Humain (EIAH), Jun 2023, Brest, France. pp.17-24. 
https://hal.science/hal-04144210 
https://apimu.gitlabpages.inria.fr/site/ateliers/pdf-apimu23/APIMUEIAH_2023_paper_3.pdf

2- Emmanuel Desmontils. Enseigner SQL en NSI : typologie et cas de la jointure. Journée des enseignants de SNT et de NSI 2024, Académie de la Réunion et IREMI de La Réunion, Dec 2024, Saint-Denis (La Réunion), France.
https://hal.science/hal-05030037v1

## Génération de la documentation

```shell
pdoc3 --html --force -o doc querycraft
```

## Remerciements

- Wiktoria SLIWINSKA, étudiante ERASMUS en licence Informatique à l'Université de Nantes en 2023-2024, pour son aide à la conception du POC initial. 
- Baptiste GIRARD, étudiant en licence Informatique à l'Université de Nantes en 2024-2025, pour son aide à la fiabilisation de l'outil.

## Autres sites

Sur PyPi : https://pypi.org/project/querycraft/

HAL (pour citer dans une publication) : https://hal.science/hal-04964895 

## Licence

(C) E. Desmontils, Nantes Université, 2024, 2025

Ce logiciel est distribué sous licence GPLv3.



