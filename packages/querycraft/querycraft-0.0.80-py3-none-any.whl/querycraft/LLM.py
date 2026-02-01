# https://github.com/ollama/ollama-python
import os
from datetime import datetime

import colorama
import openai
# https://github.com/Soulter/hugging-chat-api
# from hugchat import hugchat
# from hugchat.login import Login
from ollama import chat, ChatResponse, Client

from querycraft.tools import clear_line, loadCache, saveCache, getAge, getTemplate

# API keys
Ollama_API_KEY = os.environ.get('OLLAMA_API_KEY')  # os.getenv("OLLAMA_API_KEY")
OpenAI_API_KEY = os.getenv("OPENAI_API_KEY")
POE_API_KEY = os.getenv("POE_API_KEY")


# print(f"{Ollama_API_KEY} - {OpenAI_API_KEY} - {POE_API_KEY}")

##########################################################################################################
##########################################################################################################
##########################################################################################################

class LLM():
    def __init__(self, verbose, setHelp, sgbd, modele, bd=None):
        self.prompt = str()
        self.modele = modele
        self.bd = bd
        self.sgbd = sgbd
        self.prompt_systeme = self.__build_prompt_contexte(sgbd, bd)
        self.verbose = verbose
        self.setHelp = setHelp

    def __build_prompt_contexte(self, sgbd, bd=None):
        prompt = getTemplate("systeme_prompt.md")
        return prompt.replace("{{sgbd}}", sgbd).replace("{{database_schema}}", f"{bd}")

    def set_prompt_err(self, erreur, sql_soumis):
        prompt = getTemplate("erreur_prompt.md")
        self.prompt = prompt.replace("{{erreur}}", erreur).replace("{{requete_err}}", f"{sql_soumis}")

    def set_prompt_err2(self, erreur, sql_soumis, sql_attendu):
        prompt = getTemplate("erreur2_prompt.md")
        self.prompt = prompt.replace("{{erreur}}", erreur).replace("{{requete_err}}", f"{sql_soumis}").replace(
            "{{requete}}", f"{sql_attendu}")

    def set_prompt_req(self, sql_attendu):
        prompt = getTemplate("requete_prompt.md")
        self.prompt = prompt.replace("{{requete}}", f"{sql_attendu}")

    def set_prompt_correction(self, sql_soumis, sql_attendu, intention, cmp=None):
        prompt = getTemplate("correction_prompt.md")
        if cmp is None:
            self.prompt = prompt.replace("{{requete}}", f"{sql_soumis}").replace(
                "{{requete_attendue}}", f"{sql_attendu}").replace(
                "{{intention}}", f"{intention}").replace(
                "{{cmp}}", f"")
        else:
            match cmp:
                case 0:
                    txt = f"la requête proposée par l'élève ne donne pas les mêmes données que à la requête correcte.>>"
                case 1:
                    txt = f"la requête proposée par l'élève donne les mêmes données que à la requête correcte, mais l'ordre des colonnes et l'ordre des lignes sont différents."
                case 2:
                    txt = f"la requête proposée par l'élève donne les mêmes données que à la requête correcte, mais l'ordre des lignes est différent."
                case 3:
                    txt = f"la requête proposée par l'élève donne les mêmes données que à la requête correcte, mais l'ordre des colonnes est différent."
                case 4:
                    txt = f"la requête proposée par l'élève donne le même résultat que à la requête correcte."
                case _:
                    txt = "RAS"
            if sql_attendu.com and self.setHelp:
                txt += f"\n\nL'enseignant donne comme aide : « {sql_attendu.com} »"
            self.prompt = prompt.replace(
                "{{requete}}", f"{sql_soumis}").replace(
                "{{requete_attendue}}", f"{sql_attendu}").replace(
                "{{intention}}", f"{intention}").replace(
                "{{cmp}}", txt)

    def set_prompt_db(self):
        self.prompt = getTemplate("database_prompt.md")

    def setPrompt(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
        # print(f"erreur={erreur}, sql_soumis={sql_soumis}, sql_attendu={sql_attendu}, intention={intention}, cmp={cmp}")
        if erreur is not None:  # la requête soumise n'est pas correcte pour le SGBD
            assert (sql_soumis is not None)
            if sql_attendu is None:
                # print("Erreur")
                self.set_prompt_err(erreur, sql_soumis)
            else:
                # print("Erreur2")
                self.set_prompt_err2(erreur, sql_soumis, sql_attendu)
        elif sql_soumis is None:
            if sql_attendu is not None:
                # print("Requête")
                self.set_prompt_req(sql_attendu)
            else:
                # print("Database")
                self.set_prompt_db()
        else:
            assert (sql_soumis is not None and sql_attendu is not None)
            assert (intention is not None and cmp is not None)
            assert (erreur is None)
            # print("Exercice")
            self.set_prompt_correction(sql_soumis, sql_attendu, intention, cmp)
        # clear_line()
        # clear_line()

    def run(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
        return ""

    def set_reponse(self, rep, llm, link, modele, date):
        return (f"{colorama.Fore.GREEN}{rep}{colorama.Style.RESET_ALL}\n---\n"
                + f"{colorama.Fore.BLUE}Source : {llm} ({link}) avec {modele} {colorama.Style.RESET_ALL}"
                + f"{colorama.Fore.BLUE} le {date.date()} à {date.time()}. {colorama.Style.RESET_ALL}\n"
                + f"{colorama.Fore.BLUE}Attention, {llm}/{modele} ne garantit pas la validité de l'aide. "
                + f"Veuillez vérifier la réponse et vous rapprocher de vos enseignants si nécessaire.{colorama.Style.RESET_ALL}\n"
                )


##########################################################################################################
##########################################################################################################
##########################################################################################################

class OllamaLLM(LLM):
    def __init__(self, verbose, setHelp, sgbd, modele="gemma3:1b", bd=None):
        super().__init__(verbose, setHelp, sgbd, modele, bd)

    def run(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
        try:
            self.setPrompt(erreur, sql_soumis, sql_attendu, intention, cmp)
            response: ChatResponse = chat(model=self.modele, options={"temperature": 0.0, "top-p": 0.9}, messages=[
                {'role': 'system', 'content': self.prompt_systeme},
                {'role': 'user', 'content': self.prompt},
            ])
            if self.verbose and False:
                print(f"{colorama.Fore.BLUE}================================")
                print(f"================================")
                print(f"================================")
                print(f"{self.prompt_systeme}")
                print(f"================================")
                print(f"{self.prompt}")
                print(f"================================")
                print(f"================================")
                print(f"================================{colorama.Style.RESET_ALL}")
            return self.set_reponse(response.message.content, "Ollama", "https://ollama.com/",
                                    self.modele, datetime.now())
        except Exception as e:
            print(e)
            return super().run(erreur, sql_attendu, sql_soumis, intention, cmp)


class OllamaAPICloud(OllamaLLM):
    def __init__(self, verbose, setHelp, sgbd, modele, api_key=None, bd=None):
        super().__init__(verbose, setHelp, sgbd, modele, bd)
        self.client = Client(host='https://ollama.com',
                             headers={'Authorization': 'Bearer ' + api_key})

    def run(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
        try:
            self.setPrompt(erreur, sql_soumis, sql_attendu, intention, cmp)
            messages = [
                {'role': 'system', 'content': self.prompt_systeme},
                {'role': 'user', 'content': self.prompt}
            ]
            rep = ""
            for part in self.client.chat(self.modele,
                                         messages=messages,
                                         options={"temperature": 0.0, "top-p": 0.9},
                                         stream=True):
                rep += part.message.content

            if self.verbose and False:
                print(f"{colorama.Fore.BLUE}================================")
                print(f"================================")
                print(f"================================")
                print(f"{self.prompt_systeme}")
                print(f"================================")
                print(f"{self.prompt}")
                print(f"================================")
                print(f"================================")
                print(f"================================{colorama.Style.RESET_ALL}")
            return self.set_reponse(rep, "Ollama Cloud", "https://ollama.com/",
                                    self.modele, datetime.now())
        except Exception as e:
            print(e)
            return super().run(erreur, sql_attendu, sql_soumis, intention, cmp)


##########################################################################################################
##########################################################################################################
##########################################################################################################

class GenericLLM(LLM):
    def __init__(self, verbose, setHelp, sgbd, modele, api_key, base_url, bd=None):
        super().__init__(verbose, setHelp, sgbd, modele, bd)
        self.api_key = api_key
        self.base_url = base_url
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url, )

    def run(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
        try:
            response = self.query(erreur, sql_attendu, sql_soumis, intention, cmp)
            return self.set_reponse(response.choices[0].message.content, "Generic LLM", "API Reference - OpenAI",
                                    self.modele, datetime.now())
        except Exception as e:
            print(e)
            return super().run(erreur, sql_attendu, sql_soumis, intention, cmp)

    def query(self, erreur, sql_attendu, sql_soumis, intention=None, cmp=None):
        try:
            self.setPrompt(erreur, sql_soumis, sql_attendu, intention, cmp)
            response = self.client.chat.completions.create(model=self.modele, temperature=0.0, messages=[
                {'role': 'system', 'content': self.prompt_systeme},
                {'role': 'user', 'content': self.prompt},
            ])
            return response
        except Exception as e:
            print(e)
            return ""


class PoeLLM(GenericLLM):
    def __init__(self, verbose, setHelp, sgbd, modele, api_key, base_url='https://api.poe.com/v1', bd=None):
        super().__init__(verbose, setHelp, sgbd, modele, api_key, 'https://api.poe.com/v1', bd)

    def run(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
        try:
            response = self.query(erreur, sql_attendu, sql_soumis, intention, cmp)
            return self.set_reponse(response.choices[0].message.content, "POE", "https://poe.com/",
                                    self.modele, datetime.now())
        except Exception as e:
            print(e)
            return super().run(erreur, sql_attendu, sql_soumis, intention, cmp)


class GoogleLLM(GenericLLM):
    def __init__(self, verbose, setHelp, sgbd, modele, api_key,
                 base_url='https://generativelanguage.googleapis.com/v1beta/openai/', bd=None):
        super().__init__(verbose, setHelp, sgbd, modele, bd)
        self.api_key = api_key
        self.base_url = base_url
        self.client = openai.OpenAI(api_key=self.api_key)

    def run(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
        try:
            response = self.query(erreur, sql_attendu, sql_soumis, intention, cmp)
            return self.set_reponse(response.choices[0].message.content,
                                    "Google", "https://ai.google.dev/gemini-api/",
                                    self.modele, datetime.now())
        except Exception as e:
            print(e)
            return super().run(erreur, sql_attendu, sql_soumis, intention, cmp)


class OpenaiLLM(GenericLLM):
    def __init__(self, verbose, setHelp, sgbd, modele, api_key, base_url='https://api.openai.com/v1/chat/completions',
                 bd=None):
        super().__init__(verbose, setHelp, sgbd, modele, bd)
        self.api_key = api_key
        self.base_url = base_url
        self.client = openai.OpenAI(api_key=self.api_key)

    def run(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
        try:
            response = self.query(erreur, sql_attendu, sql_soumis, intention, cmp)
            return self.set_reponse(response.choices[0].message.content, "Open AI", "https://openai.com/",
                                    self.modele, datetime.now())
        except Exception as e:
            print(e)
            return super().run(erreur, sql_attendu, sql_soumis, intention, cmp)


# class HuggingLLM(LLM):
#     def __init__(self, verbose, setHelp, sgbd, modele, base_url='https://router.huggingface.co/v1', bd=None):
#         super().__init__(verbose, setHelp, sgbd, modele, bd)
#         self.base_url = base_url
#
#     def run(self, erreur, sql_soumis, sql_attendu, intention=None, cmp=None):
#         try:
#             EMAIL = "emmanuel.desmontils@univ-nantes.fr"
#             PASSWD = ""
#             with importlib.resources.files("querycraft.cookies").joinpath('') as cookie_path_dir:
#                 cpd = str(cookie_path_dir) + '/'
#                 print(cpd)
#                 # cookie_path_dir = "./cookies/"  # NOTE: trailing slash (/) is required to avoid errors
#                 sign = Login(EMAIL, PASSWD)
#                 cookies = sign.login(cookie_dir_path=cpd, save_cookies=True)
#
#                 chatbot = hugchat.ChatBot(cookies=cookies.get_dict())
#
#                 # Create a new conversation with an assistant
#                 ASSISTANT_ID = self.modele  # get the assistant id from https://huggingface.co/chat/assistants
#                 chatbot.new_conversation(assistant=ASSISTANT_ID, switch_to=True)
#
#                 if erreur is not None:
#                     self.set_prompt_err2(erreur, sql_attendu, sql_soumis)
#                 if sql_soumis is None and sql_attendu is not None:
#                     self.set_prompt_req(sql_attendu)
#                 else:
#                     self.set_prompt_db()
#
#                 if self.verbose:
#                     print(f"{CYAN}{self.prompt_systeme}\n\n{self.prompt}{RESET}")
#                 return (f"{GREEN}" + chatbot.chat(self.prompt).wait_until_done() + f"{RESET}\n---\n"
#                         + f"{BLUE}Source : HuggingChat (https://huggingface.co/chat/), assistant Mia-DB (https://hf.co/chat/assistant/{self.modele}) {RESET}\n"
#                         + f"{BLUE}Attention, HuggingChat/Mia-DB ne garantit pas la validité de l'aide. Veuillez vérifier la réponse et vous rapprocher de vos enseignants si nécessaire.{RESET}")
#                 # return self.set_reponse(chatbot.chat(self.prompt).wait_until_done(), "HuggingChat", "https://huggingface.co/chat/", self.modele,
#                 #                        datetime.now())
#         except Exception as e:
#             print(e)
#             return super().run(erreur, sql_attendu, sql_soumis, intention, cmp)  # + f"\nPb HuggingChat : {e}"

##########################################################################################################
##########################################################################################################
##########################################################################################################

def format_ia(rep, titre):
    s = ""
    if rep:
        s += f"\n{colorama.Fore.BLUE}--- {titre} par IA générative ---{colorama.Style.RESET_ALL}\n"
        s += rep + "\n"
    else:
        s += f"{colorama.Fore.BLUE}--- {titre} par IA générative impossible ---{colorama.Style.RESET_ALL}"
    return s


def show_ia(rep, titre):
    print(format_ia(rep, titre))


def buildCacheHint(cache_file, dt, duree):
    return f"{colorama.Fore.BLUE}(From cache file {cache_file[:-5]} - information freshness {int((1 - getAge(dt) / duree) * 100)}%){colorama.Style.RESET_ALL}"


def getCache(cacheName, service, modele, cacheKey, duree):
    cache_file = f"{cacheName}_" + (service + "_" + modele).replace(':', '_')+ ".json"
    cache = loadCache(cache_file, duree)
    if cacheKey in cache:
        (rep, dt) = cache[cacheKey]
        rep += buildCacheHint(cache_file, dt, duree)
    else:
        rep = ""
    return (rep, cache_file, cache)

def manage_ia(cacheName, cfg, verbose, cacheKey, bd, erreur, sql, sol, intention, cmp):
    doCache = cfg['Autre']['cache'] == 'on'
    duree = int(cfg['Autre']['duree-cache'])
    cache_file = (f"{cacheName}_" + (cfg['IA']['service'] + "_" + cfg['IA']['modele']).replace(':', '_')
                  + ".json")
    setHelp = cfg['Autre']['aide'] == 'on'

    if doCache:
        (rep, cache_file, cache)=getCache(cacheName, cfg['IA']['service'], cfg['IA']['modele'], cacheKey, duree)
    else:
        cache = dict()
        rep = ""

    if rep == "":

        if cfg['IA']['service'] == 'ollama':
            rep = OllamaLLM(verbose, setHelp, cfg['Database']['type'], cfg['IA']['modele'],
                            bd.tables2string()).run(erreur, sql, sol, intention, cmp)
        elif cfg['IA']['service'] == 'ollama_cloud':
            if cfg['IA']['api-key']:
                api_key = cfg['IA']['api-key']
            else:
                api_key = Ollama_API_KEY
            rep = OllamaAPICloud(verbose, setHelp, cfg['Database']['type'], cfg['IA']['modele'], api_key=api_key,
                                 bd=bd.tables2string()).run(erreur, sql, sol, intention, cmp)
        elif cfg['IA']['service'] == 'poe':
            if cfg['IA']['api-key']:
                api_key = cfg['IA']['api-key']
            else:
                api_key = POE_API_KEY
            rep = PoeLLM(verbose, setHelp, cfg['Database']['type'], cfg['IA']['modele'], api_key=api_key,
                         base_url='https://api.poe.com/v1',
                         bd=bd.tables2string()).run(erreur, sql, sol, intention, cmp)
        elif cfg['IA']['service'] == 'openai':
            if cfg['IA']['api-key']:
                api_key = cfg['IA']['api-key']
            else:
                api_key = OpenAI_API_KEY
            rep = OpenaiLLM(verbose, setHelp, cfg['Database']['type'], cfg['IA']['modele'], api_key=api_key,
                            base_url='https://api.openai.com/v1/chat/completions',
                            bd=bd.tables2string()).run(erreur, sql, sol, intention, cmp)
        elif cfg['IA']['service'] == 'google':
            rep = GoogleLLM(verbose, setHelp, cfg['Database']['type'], cfg['IA']['modele'],
                            api_key=cfg['IA']['api-key'],
                            base_url='https://generativelanguage.googleapis.com/v1beta/openai/',
                            bd=bd.tables2string()).run(erreur, sql, sol, intention, cmp)
        elif cfg['IA']['service'] == 'generic':
            rep = GenericLLM(verbose, setHelp, cfg['Database']['type'], cfg['IA']['modele'],
                             api_key=cfg['IA']['api-key'],
                             base_url=cfg['IA']['url'],
                             bd=bd.tables2string()).run(erreur, sql, sol, intention, cmp)
        else:
            rep = ""
        if doCache and rep != "": saveCache(cache_file, cache, cacheKey, rep)

    if not rep:
        print("Utilisation de l'IA générative par défaut."
              " ⚠️  Ce service est susceptible d'être coupé à tout moment."
              " Merci d'utiliser votre propre service d'IA. ⚠️")

        if Ollama_API_KEY:
            if doCache:
                (rep, cache_file, cache) = getCache(cacheName, 'ollama_cloud','gpt-oss:120b',
                                                    cacheKey, duree)
            else:
                rep = ""
            if not rep:
                rep = OllamaAPICloud(verbose, setHelp, cfg['Database']['type'],
                                 'gpt-oss:120b', Ollama_API_KEY,
                                 bd.tables2string()).run(erreur, sql, sol, intention, cmp)
                if doCache and rep: saveCache(cache_file, cache, cacheKey, rep)

        if rep == "" and POE_API_KEY:
            if doCache:
                (rep, cache_file, cache) = getCache(cacheName, 'poe', "gpt-5-nano",
                                                    cacheKey, duree)
            else:
                rep = ""
            if not rep:
                # gpt-4.1-nano ; gpt-5-nano ; gpt-5.1-codex
                rep = PoeLLM(verbose, setHelp, cfg['Database']['type'],
                             "gpt-5-nano", POE_API_KEY,
                             "https://api.poe.com/v1",
                             bd.tables2string()).run(erreur, sql, sol, intention, cmp)
                if doCache and rep: saveCache(cache_file, cache, cacheKey, rep)

        if rep == "" and OpenAI_API_KEY:
            if doCache:
                (rep, cache_file, cache) = getCache(cacheName, 'openai', "gpt-5-nano",
                                                    cacheKey, duree)
            else:
                rep = ""
            if not rep:
                rep = OpenaiLLM(verbose, setHelp, cfg['Database']['type'],
                                "gpt-5-nano", api_key=OpenAI_API_KEY,
                                base_url='https://api.openai.com/v1/chat/completions',
                                bd=bd.tables2string()).run(erreur, sql, sol, intention, cmp)
                if doCache and rep: saveCache(cache_file, cache, cacheKey, rep)

        clear_line()
    return rep


def main():
    pass


if __name__ == '__main__':
    main()
