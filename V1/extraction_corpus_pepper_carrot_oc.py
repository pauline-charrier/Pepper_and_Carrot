# résolution du problème de la dernière page ignorée
# résolution du problème des double extensions
# résolution du problème du bon alignement : globalement
# résolution du problème du nombre de fichiers en sortie
# résolution du problème du séparateur
# résolution du problème de gestion de l'erreur Index (absence de fichier occitan)
# résolution du problème d'alignement : passage de flowPara à flowRoot et de tspan à text

'''
Programme permettant l'extraction et l'alignement automatique de corpus bilingues obtenus à partir du website de Pepper&Carrot (traduction occitane d'un épisode, alignée avec les traductions des autres langues disponibles).

Retourne un dossier zip comprenant des fichiers CSV alignant le texte occitan au texte en langue étrangère (séparateur '§'). 
Chaque fichier CSV correspond à un corpus bilingue.

Le dossier zip sera placé au niveau du répertoire d'où est exécuté le script.

Lancer le script depuis la ligne de commande : "python3 extraction_corpus_pepper_carrot.py".

L'utilisateur est invité à entrer manuellement le nom d'un épisode de Pepper&Carrot en anglais (en respectant strictement les majuscules) ainsi que le numéro d'épisode correspondant à ce titre.

'''

import os
import requests
import zipfile
import csv
import shutil
from xml.etree import ElementTree as ET
from itertools import zip_longest
import sys

def nettoyer_titre(titre: str):
    # Nettoyer le titre saisi par l'utilisateur (suppression du potentiel espace final, transformation des espaces en tirets)
    return titre.strip().replace(" ", "-")

def chercher_episode(titre: str, numero_episode: str):
    # Ajouter un zéro pour les numéros inférieurs à 10 si l'utilisateur ne l'a pas fait
    numero_episode = numero_episode.zfill(2)
    
    # Construction de l'URL
    base_url = "https://peppercarrot.com/0_sources"
    zip_url = f"{base_url}/ep{numero_episode}_{titre}/zip/ep{numero_episode}_{titre}_lang-pack.zip"
    
    # Téléchargement du dossier ZIP
    try:
        response = requests.get(zip_url)
        response.raise_for_status() 
        print("Fichier bien téléchargé")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'épisode : {e}.\nSolutions possibles :\n1) vérifiez que le titre en anglais existe bien et soit bien orthographié, \n2) vérifiez que vous ayez bien respecté les majuscules du titre original et bien remplacé les espaces par des tirets,\n3) vérifiez qu'il y ait une correspondance entre le titre et le numéro d'épisode saisi, \n4) pensez également à vérifier votre connexion internet, \n5) contactez un membre du pôle Informatique.")
        return None
    
    fichier_zip = f"ep{numero_episode}_{titre}_lang-pack.zip"
    
    with open(fichier_zip, 'wb') as f:
        f.write(response.content)
    
    # Décompression du dossier ZIP 
    try:
        with zipfile.ZipFile(fichier_zip, 'r') as zip_ref:
            zip_ref.extractall(f"ep{numero_episode}_{titre}_lang-pack")
    except zipfile.BadZipFile:
        print("Erreur : le fichier ZIP ne peut être lu.")
        return None
    
    os.remove(fichier_zip)  # Supprimer l'archive ZIP après extraction
    return f"ep{numero_episode}_{titre}_lang-pack"

def extraire_texte_du_svg(path_fichier_svg, numero_episode, code_langue):
    # pour contraindre le programme à ne traiter que des fichiers SVG (et pas les fichiers Markdown ou Json !)
    if not path_fichier_svg.lower().endswith('.svg'):
        print(f"Le fichier {path_fichier_svg} n'est pas un fichier SVG et sera ignoré.")
        return []
    
    # Ouvrir le fichier SVG et lire son contenu
    try:
        tree = ET.parse(path_fichier_svg)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Erreur lors du parsing du fichier SVG {path_fichier_svg} : {e}")
        return []    
    
    elements_texte = []
    
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    if int(numero_episode) <= 12:
        # Extraction du texte entre <flowPara> pour les épisodes 1 à 12
        paragraphes = root.findall('.//svg:flowRoot', namespaces) #essayer en remplaçant flowPara par flowRoot (balise parente)
        for para in paragraphes:
            texte = " ".join(para.itertext()).strip()  # Ajouter un espace pour éviter les mots collés
            if texte:
                elements_texte.append(f"{texte}§{code_langue}\n")
    else:
        # Extraction du texte entre <tspan> pour les épisodes 13 et plus
        tspans = root.findall('.//svg:text', namespaces) #essayer en remplaçant tspan par text (balise parente)
        for tspan in tspans:
            texte = " ".join(tspan.itertext()).strip()  # Ajouter un espace pour éviter les mots collés
            if texte:
                elements_texte.append(f"{texte}§{code_langue}\n")  
    
    return elements_texte

def creer_csv_avec_svg_data(langue_code, numero_episode, numero_page, texte_svg):    
    nv_fichier_csv = f"{langue_code}_E{numero_episode.zfill(2)}P{numero_page.zfill(2)}.csv"
    with open(nv_fichier_csv, 'w', newline='', encoding='utf-8') as fichier_csv:
        writer = csv.writer(fichier_csv)
        for row in texte_svg:
            writer.writerow([row])
    
    return nv_fichier_csv

def fusionner_csv_par_langue(langue_code, numero_episode, fichiers_csv_temp):
    # Fusionner tous les fichiers CSV temporaires pour une langue donnée (fusionner les CSV traitant des pages)
    nom_fichier_fusionne = f"{langue_code}_E{numero_episode.zfill(2)}.csv"    
    with open(nom_fichier_fusionne, 'w', newline='', encoding='utf-8') as fichier_fusionne:
        writer = csv.writer(fichier_fusionne)
        for fichier_csv in sorted(fichiers_csv_temp): 
            with open(fichier_csv, 'r', encoding='utf-8') as fichier_temporaire:
                reader = csv.reader(fichier_temporaire)
                for row in reader:
                    writer.writerow(row)
            os.remove(fichier_csv)  # Supprimer le fichier CSV temporaire de traitement des pages pour éviter l'encombrement  
    
    return nom_fichier_fusionne

def aligner_corpus_avec_occitan(csv_occitan, csv_langue_tierce, occitan_code='oc'):
    # Aligner le CSV occitan avec un autre fichier CSV de langue
    numero_episode = csv_occitan.split('_')[1][1:].zfill(2)  
    fichier_aligne = f"{occitan_code}-{csv_langue_tierce.split('_')[0]}_E{numero_episode}.csv"
    
    with open(csv_occitan, 'r', encoding='utf-8') as fichier_oc, \
         open(csv_langue_tierce, 'r', encoding='utf-8') as fichier_autre, \
         open(fichier_aligne, 'w', newline='', encoding='utf-8') as fichier_aligne_2:
        
        oc_reader = csv.reader(fichier_oc)
        other_reader = csv.reader(fichier_autre)
        writer = csv.writer(fichier_aligne_2, delimiter='§', escapechar=' ', quoting=csv.QUOTE_NONE)        
        
        for ligne_oc, ligne_autre in zip_longest(oc_reader, other_reader, fillvalue=[""]):            
            if ligne_oc and ligne_oc[0].strip():  
                # supprimer les retours à la ligne                
                texte_oc = ligne_oc[0].replace('\n', ' ').strip()
                # Eviter les doublons de '§oc'
                if f"§{occitan_code}" not in texte_oc:
                    ligne_oc_avec_lang = f"{texte_oc}§{occitan_code}"
                else:
                    ligne_oc_avec_lang = texte_oc
            else:
                ligne_oc_avec_lang = ""

            if ligne_autre and ligne_autre[0].strip():                 
                texte_autre_langue = ligne_autre[0].replace('\n', ' ').strip()
                langue_code = csv_langue_tierce.split('_')[0]
                if f"§{langue_code}" not in texte_autre_langue:
                    autre_ligne_autre_texte = f"{texte_autre_langue}§{langue_code}"
                else:
                    autre_ligne_autre_texte = texte_autre_langue
            else:
                autre_ligne_autre_texte = ""
            
            if ligne_oc_avec_lang or autre_ligne_autre_texte:
                writer.writerow([ligne_oc_avec_lang, autre_ligne_autre_texte])
    
    return fichier_aligne

def creer_zip_fichiers_alignes(numero_episode, fichiers_csv_alignes):
    fichier_zip = f"E{numero_episode.zfill(2)}_oc_alignements.zip"
    with zipfile.ZipFile(fichier_zip, 'w') as zipf:
        for fichier_csv in fichiers_csv_alignes:
            nom_fichier_correct = fichier_csv.replace('.csv.csv', '.csv') # éviter la double extension '.csv.csv'
            zipf.write(fichier_csv, arcname=nom_fichier_correct)
            os.remove(fichier_csv)  # Supprimer le fichier CSV d'origine une fois placé dans le fichier compressé
    
    return fichier_zip


def main():
    # Formulaire destiné à l'utilisateur
    titre = input("Entrez le titre de l'épisode en anglais en respectant strictement la casse : ")
    numero_episode = input("Entrez le numéro de l'épisode : ")

    # Nettoyer le titre saisi par l'utilisateur
    titre = nettoyer_titre(titre)
    print(f"Le titre de l'épisode téléchargé est : {titre}")
    
    # Téléchargement et extraction des fichiers
    dossier_extrait = chercher_episode(titre, numero_episode)
    # Gestion erreur
    if not dossier_extrait:
        print("Erreur : impossible de télécharger ou d'extraire les fichiers.")
        return
    
    # Variables pour suivre les fichiers temporaires et finaux
    fichiers_csv_temp = []
    fichiers_csv_finaux = []
    
    # Parcourir les fichiers SVG dans chaque dossier de langue
    for dossier_langues in os.listdir(f"{dossier_extrait}/lang/"):
        path_dossier_lang = os.path.join(dossier_extrait, "lang", dossier_langues)
        
        if os.path.isdir(path_dossier_lang):
            fichiers_csv_lang_temp = []
            svg_files = [f for f in os.listdir(path_dossier_lang) if f.endswith('.svg')]
            
            # Trouver le fichier avec le numéro de page le plus élevé et l'ignorer (la dernière page des épisodes ne comprenant pas le texte de l'épisode)
            max_page = max([int(f.split('P')[1].split('.')[0]) for f in svg_files])
            svg_files = [f for f in svg_files if int(f.split('P')[1].split('.')[0]) != max_page]
            
            for fichier_svg in svg_files:
                numero_page = fichier_svg.split('P')[1].split('.')[0]  
                path_fichier_svg = os.path.join(path_dossier_lang, fichier_svg)
                
                # Extraction du texte du fichier SVG
                texte_svg = extraire_texte_du_svg(path_fichier_svg, numero_episode, dossier_langues)
                
                # Création du fichier CSV temporaire pour la page
                if texte_svg:
                    fichier_csv = creer_csv_avec_svg_data(dossier_langues, numero_episode, numero_page, texte_svg)
                    fichiers_csv_lang_temp.append(fichier_csv)
            
            # Fusionner les fichiers CSV par langue
            if fichiers_csv_lang_temp:
                fichier_csv_lang_fusionne = fusionner_csv_par_langue(dossier_langues, numero_episode, fichiers_csv_lang_temp)
                fichiers_csv_finaux.append(fichier_csv_lang_fusionne)        
    
    fichiers_csv_alignes = []

    # Gestion de l'erreur liée à l'absence de fichier occitan pour un épisode donné
    erreur_survenue = False
    try:
        csv_occitan = [f for f in fichiers_csv_finaux if f.startswith("oc_")][0]
    except IndexError:
        print("Erreur : il n'y a pas encore de traduction en occitan disponible pour cet épisode.")
        erreur_survenue = True
        for fichier_csv in fichiers_csv_finaux:
            if os.path.exists(fichier_csv):
                os.remove(fichier_csv)
                #print(f"Fichier supprimé : {fichier_csv}") 
        sys.exit(1)     
    
    # Alignement du fichier occitan avec le fichier de langue tierce
    for fichier_csv in fichiers_csv_finaux:
        if not fichier_csv.startswith("oc_"):
            fichier_aligne = aligner_corpus_avec_occitan(csv_occitan, fichier_csv)
            fichiers_csv_alignes.append(fichier_aligne)
    
    # Créer un fichier ZIP avec tous les fichiers alignés
    fichier_zip_final = creer_zip_fichiers_alignes(numero_episode, fichiers_csv_alignes)
    
    # Suppression des fichiers temporaires
    for fichier_csv in fichiers_csv_finaux:
        os.remove(fichier_csv)
        #print(f"Fichier fusionné {fichier_csv} supprimé.")

    # Suppression du dossier extrait
    shutil.rmtree(dossier_extrait)
    
    print(f"Fichier ZIP final contenant les alignements : {fichier_zip_final}")

if __name__ == "__main__":
    main()