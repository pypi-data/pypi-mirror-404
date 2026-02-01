from querycraft.LLM import *
from querycraft.tools import clear_line
import colorama

class SQLException(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message

    def __unicode__(self):
        return self.message


class SQLQueryException(SQLException):
    cfg = None
    ia_on = False

    @classmethod
    def setCfg(cls, cfg):
        SQLQueryException.cfg = cfg
        SQLQueryException.ia_on = cfg['IA']['mode'] == 'on'

    def __init__(self, verbose, message, sqlhs, sqlok, sgbd, bd=""):
        super().__init__(message)
        self.sqlhs = sqlhs
        self.sqlok = sqlok
        if sqlok is None:
            self.sqloktxt = ""
        else:
            self.sqloktxt = f"{sqlok}"
        self.sgbd = sgbd
        self.verbose = verbose
        self.hints = ""
        self.err = f"{colorama.Fore.RED}Erreur sur la requête SQL avec {self.sgbd} :\n -> Requête proposée : {self.sqlhs}\n -> Message {self.sgbd} :\n{self.message}{colorama.Style.RESET_ALL}\n"  # Affichage de l'erreur de base
        if verbose and SQLQueryException.ia_on:
            # print(f"{SQLQueryException.model},{SQLQueryException.api_key}, {SQLQueryException.url}")
            # input("Appuyez sur Entrée pour avoir une explication de l'erreur par IA ou Ctrl + Z pour quitter.")
            # clear_line()
            print("Construction de l'explication avec l'IA générative. Veuillez patienter.")
            self.hints = manage_ia('error', SQLQueryException.cfg, verbose, f"{self.sqlhs}{self.sqloktxt}", bd,
                                   f"{message}", sqlhs, sqlok, None, None)
            clear_line()

    def __str__(self):
        mssg = self.err
        if self.verbose and SQLQueryException.ia_on :
            mssg +=  format_ia(self.hints,"Explication de l'erreur")
        return mssg

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()
