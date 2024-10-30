### pip install requests
### pip install selenium
### pip install chromedriver_autoinstaller

import requests
import json
import time
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

def file_exists(filename):
    return os.path.isfile(filename)

def directory_exists(directory_name):
    return os.path.isdir(directory_name)

def create_directory(directory_name):
    try:
        os.makedirs(directory_name, exist_ok=True)
    except Exception as e:
        show_error(f'Erreur lors de la création du dossier "{directory_name}": {e}')

def show_loading_animation(msg):
    states = [msg, msg+".", msg+"..", msg+"..."]
    for element in states:
        state = element
        sys.stdout.write('\r' + state)
        sys.stdout.flush()
        time.sleep(1)

def show_error(msg):
    print("")
    print(msg)
    exit()

def get_request_with_cookie(url, cookie):
    session = requests.Session()
    session.cookies.update(cookie)
    response = session.get(url)
    return response

def save_dict_to_json(dict_data, file_name):
    json_formatted_str = json.dumps(dict_data, indent=2)
    with open(file_name, "w") as msgs:
        msgs.write(json_formatted_str)

def concatenate_json_threads(api_threads_list):
    final_json = {"EntityArray":[]}
    final_json["Total"] = api_threads_list[0]["Total"]
    for threads in api_threads_list:
        for thread in threads["EntityArray"]:
            final_json["EntityArray"].append(thread)
    return final_json

def get_threads_ids(json_content):
    threads_dict = {}
    for element in json_content["EntityArray"]:
        if element["Type"] == "OneToOne":
            threads_dict[element["InstantMessageThreadId"]] = {"lastMsgId": element["LastMessage"]["MessageId"], "name": element["Participants"][0]["FullName"]+", "+element["Participants"][1]["FullName"]}
        elif element["Type"] == "Group" and element["Name"] == "":
            threads_dict[element["InstantMessageThreadId"]] = {"lastMsgId": element["LastMessage"]["MessageId"], "name": str([element["FullName"].replace(",", "") for element in element["Participants"]]).replace("[", "").replace("]", "").replace("'", "")}
        else:
            threads_dict[element["InstantMessageThreadId"]] = {"lastMsgId": element["LastMessage"]["MessageId"], "name": element["Name"]}
    return threads_dict

def get_cookie_from_file():
    with open("credentials.txt", "r") as credentials:
        return credentials.read()

def get_authenticated_cookies(login_url, next_page_indicator):
    driver = webdriver.Chrome()
    try:
        driver.get(login_url)
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, next_page_indicator))
        )
        cookies = driver.get_cookies()
        return cookies
    finally:
        driver.quit()

def convert_cookies_to_requests_format(cookies):
    session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
    return session_cookies

def list_thread_files():
    files = os.listdir('.')
    thread_files = [f for f in files if os.path.isfile(f) and f.startswith('thread') and f.endswith('.jon') and 'threads_list' not in f]
    return thread_files

def load_content_from_json_file(finename):
    with open(finename, "r") as json_file_raw:
        json_file = json_file_raw.read()
        return json.loads(json_file)

def download_file_with_cookie(url, cookie, thread_id, attachment_name):
    directory = os.path.join('attachments', thread_id)
    os.makedirs(directory, exist_ok=True)
    session = requests.Session()
    session.cookies.update(cookie)
    response = session.get(url)
    if response.status_code == 200:
        filename = attachment_name
        filepath = os.path.join(directory, filename)
        with open(filepath, 'wb') as file:
            file.write(response.content)
    else:
        show_error(f'Erreur lors du téléchargement du fichier : {response.status_code}')

def display_progress_bar(percentage):
    bar_length = 50
    block = int(round(bar_length * percentage / 100))
    progress_bar = '=' * block + ' ' * (bar_length - block)
    progress_message = f'[{progress_bar}] {percentage}%'
    print(f'\r{progress_message}', end='')

BASE_URL = "https://elyco.itslearning.com"

# Installing chromedriver
print("\nPréparation de l'environnement...\n")
chromedriver_autoinstaller.install()

# Getting cookie
print("********** PHASE 1 : RÉCUPÉRATION DU COOKIE DE CONNEXION\n")

print("Connectez-vous à votre espace dans la fenêtre qui s'ouvre. Ne la fermez pas, le programme va s'en charger tout seul.")
input("Appuyez sur ENTRÉE pour commencer.")

login_url = BASE_URL
next_page_indicator = '#pm-user-status-image'
cookies = get_authenticated_cookies(login_url, next_page_indicator)
session_cookies = convert_cookies_to_requests_format(cookies)
cookie = ""
for element in session_cookies:
    cookie += str(element)+"="+session_cookies[element]+"; "
request_headers = {'session_id': cookie}

print("********** PHASE 1 : SUCCÈS\n")

# Creating working directory
saving_directory = "pytslearning_backup"+datetime.today().strftime("%Y%m%d%H") # %Y%m%d%H%M%S
create_directory(saving_directory)

# Getting threads list
print("********** PHASE 2 : RÉCUPÉRATION DE LA LISTE DES CONVERSATIONS\n")

threads = []
loop = True
i = 0
if not file_exists(saving_directory+"/threads_list.json"):
    while loop:
        url = BASE_URL+"/restapi/personal/instantmessages/messagethreads/v2?threadPage="+str(i)+"&maxThreadCount=15"
        response = get_request_with_cookie(url, request_headers)
        if response.status_code == 200:
            print("Requête "+str(i)+" (Statut : "+str(response.status_code)+" OK)")
        else:
            show_error("Erreur lors de la requête (Statut : "+str(response.status_code)+" KO) : "+response.text)
        response_formatted = json.loads(response.text)
        threads.append(response_formatted)

        i += 1

        if response_formatted["EntityArray"]:
            time.sleep(1)
        else:
            loop = False
    save_dict_to_json(concatenate_json_threads(threads), saving_directory+"/threads_list.json")
    print("")

# Checking threads integrity in file
print("Liste des conversations détectée dans le dossier courant. Vérification de son intégrité...")
with open(saving_directory+"/threads_list.json", "r") as threads_list_raw:
    threads_list = threads_list_raw.read()
    threads_number = json.loads(threads_list)["Total"]
    threads_ids = get_threads_ids(json.loads(threads_list))
    if len(threads_ids) != threads_number:
        show_error("Conversations manquantes détectées ! Supprimez le fichier de conversations et relancez le script.")
    else:
        print("Aucune erreur détectée. \n")

print("********** PHASE 2 : SUCCÈS\n")

# Getting messages
print("********** PHASE 3 : RÉCUPÉRATION DES MESSAGES DE CHAQUE CONVERSATION\n")

for element in threads_ids:
    loop = True
    msgs = []
    last_msg_id = threads_ids[element]["lastMsgId"]
    thread_name = threads_ids[element]["name"]
    if len(thread_name) > 50:
        thread_name = thread_name[:50]+"..."
    print("Traitement de la conversation :", thread_name, "(id :", str(element)+")")
    i = 0
    while loop:
        i += 1
        url = BASE_URL+"/restapi/personal/instantmessages/messagethreads/"+str(element)+"/messages/v2?upperBoundInstantMessageId="+str(last_msg_id)+"&maxMessages=25"
        response = get_request_with_cookie(url, request_headers)
        if response.status_code == 200:
            print("Requête "+str(i)+" (Statut : "+str(response.status_code)+" OK)")
        else:
            show_error("Erreur lors de la requête (Statut : "+str(response.status_code)+" KO) : "+response.text)
        msgs.append(json.loads(response.text))
        content = json.loads(response.text)
        if content["EntityArray"]:
            time.sleep(1)
##            save_dict_to_json(content, saving_directory+"/thread"+str(element)+"-"+str(time.time())+".json") # One request per file
            last_msg_id = content["EntityArray"][len(content["EntityArray"])-1]["MessageId"]
        else:
            loop = False
    save_dict_to_json(concatenate_json_threads(msgs), saving_directory+"/thread"+str(element)+".json")
    show_loading_animation("Tous les messages de cette conversation ont été téléchargés. En attente")
    print("\n")

print("********** PHASE 3 : SUCCÈS\n")

print("********** PHASE 4 : RÉCUPÉRATION DES PIÈCES-JOINTES DE CHAQUE CONVERSATION\n")

attachments = {}
thread_files_names = list_thread_files()
for thread_name in thread_files_names:
    print("Traitement du fichier : ", thread_name)
    attachments[thread_name] = {}
    thread = load_content_from_json_file(thread_name)
    for element in thread["EntityArray"]:
        if element["AttachmentUrl"] != None:
            attachments[thread_name][element["AttachmentName"]] = element["AttachmentUrl"]

print("\n********** PHASE 4 : SUCCÈS\n")

print("********** PHASE 5 : TÉLÉCHARGEMENT DES PIÈCES-JOINTES DE CHAQUE CONVERSATION")

for thread in attachments:
    if attachments[thread]:
        print("\nTraitement des fichiers de la conversation :", thread)
        maximum = len(attachments[thread].keys())
        current = 0
        for attachment in attachments[thread]:
            download_file_with_cookie(attachments[thread][attachment], request_headers, thread.replace(".json", ""), attachment)
            current += 1
            display_progress_bar(round((100*current)/maximum, 0))
            time.sleep(1)
        show_loading_animation("Tous les fichiers ont été téléchargés avec succès. En attente")
        print("")

print("********** PHASE 4 : SUCCÈS\n")
