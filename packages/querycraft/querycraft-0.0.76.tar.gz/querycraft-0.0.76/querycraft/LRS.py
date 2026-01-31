import os
import uuid

from tincan import (
    RemoteLRS,
    Statement,
    Agent,
    Verb,
    Activity,
    Context,
    Result,
    LanguageMap, ActivityDefinition, Extensions,
)


class LRS(object):
    def __init__(self, lrs_endpoint, lrs_username, lrs_password, debug=False):
        self.debug = debug
        resp = self.lrs = RemoteLRS(
            version='1.0.3',
            endpoint=lrs_endpoint,
            username=lrs_username,
            password=lrs_password
        )
        resp = self.lrs.about()
        if not resp.success:
            self.lrs = None
            self.actor = None
            self.context = None
            if debug: print('Problème d''accès au LRS server')
        else:
            if self.debug: print('LRS ok')
            actorName = os.getlogin()
            self.actor = Agent(
                name=actorName,
                mbox=f"mailto:{actorName}@example.com",
            )
            self.context = None

    def setContextSBS(self):
        self.context = Context(
            platform='QueryCraft-SBS',
            registration=uuid.uuid4(),
            instructor=Agent(
                name='QueryCraft-SBS',
                mbox='mailto:desmontils-e@univ-nantes.fr', ),
        )

    def sendSBSExecute(self, type: str, dbname: str, sqlTXT: str, error=None):
        verb = Verb(id='http://univ-nantes.fr/querycraft/xapi/verbs/execute',
                    display=LanguageMap({'fr': 'Exécuter'}), )
        object = Activity(id='http://univ-nantes.fr/querycraft/xapi/activities/execute-sql',
                          definition=ActivityDefinition(
                              name=LanguageMap({'fr': 'Exécution SQL', 'en': 'Execute a SQL query'}),
                              description=LanguageMap(
                                  {'fr': 'Execute une requête SQL', 'en': 'Execute a SQL query'}),
                          ), )
        self.context.extensions = Extensions({'http://univ-nantes.fr/querycraft/xapi/terms/sql': sqlTXT,
                                              'http://univ-nantes.fr/querycraft/xapi/terms/dbtype': type,
                                              'http://univ-nantes.fr/querycraft/xapi/terms/dbname': dbname})
        if error is None:
            resultat = Result(success=True, completion=True)
        else:
            resultat = Result(success=False,
                              completion=False,
                              extensions={'http://univ-nantes.fr/querycraft/xapi/terms/error': str(error)})
        stmt = Statement(context=self.context,
                         object=object,
                         actor=self.actor,
                         verb=verb,
                         result=resultat)
        if self.lrs is not None:
            stat = self.lrs.save_statement(stmt)
            if self.debug:
                if stat:
                    print('Envoi du statement vers le LRS réussi')
                else:
                    print('Echec de l\'envoi vers le LRS')

    def sendSBSpap(self, type: str, dbname: str, sqlTXT: str, error=None):
        verb = Verb(id='http://univ-nantes.fr/querycraft/xapi/verbs/sbsed',
                    display=LanguageMap({'fr': 'Effectuer Pas à pas ', 'en': 'Do step by step'}), )
        object = Activity(id='http://univ-nantes.fr/querycraft/xapi/activities/sbs-sql',
                          definition=ActivityDefinition(
                              name=LanguageMap({'fr': 'Pas à Pas', 'en': 'Step by step'}),
                              description=LanguageMap(
                                  {'fr': 'Affiche pas à pas pour une requête SQL'}),
                          ), )
        self.context.extensions = Extensions({'http://univ-nantes.fr/querycraft/xapi/terms/sql': sqlTXT,
                                              'http://univ-nantes.fr/querycraft/xapi/terms/dbtype': type,
                                              'http://univ-nantes.fr/querycraft/xapi/terms/dbname': dbname})
        if error is None:
            resultat = Result(success=True, completion=True)
        else:
            resultat = Result(success=False,
                              completion=False,
                              extensions={'http://univ-nantes.fr/querycraft/xapi/terms/error': str(error)})

        stmt = Statement(context=self.context,
                         object=object,
                         actor=self.actor,
                         verb=verb,
                         result=resultat)

        if self.lrs is not None:
            stat = self.lrs.save_statement(stmt)
            if self.debug:
                if stat:
                    print('Envoi du statement vers le LRS réussi')
                else:
                    print('Echec de l\'envoi vers le LRS')
