# Très long code qui peut largement être optimisé

'''
Programme permettant d'extraire et d'aligner automatiquement depuis le site de Pepper & Carrot des corpus bilingues ou bivariétés ayant pour pivot l'occitan languedocien ou l'occitan gascon pour chaque épisode de la webcomic.
Une participation de l'utilisateur est nécessaire pour saisir manuellement le titre et le numéro de l'épisode traité.

Retourne un ou trois dossiers zip comprenant : 
    - des corpus alignés bilingues languedocien-autre langue (priorité donnée)
    - des corpus alignés bilingues gascon-autre langue (s'il existe une traduction en gascon)
    - un corpus aligné bivariété languedocien-gascon (s'il existe une traduction en gascon)

Les dossiers zip retournés en sortie seront placés dans le même répertoire que celui où se situe le présent script.

Pour exécuter le script : 
    - se placer en ligne de commande à l'emplacement du répertoire parent du script
    - créer un environnement virtuel (recommandé) : 
        - sur Windows : 
                1. python -m venv env
                2. env/Scripts/activate 
                3. pip install requests
        - sur Linux : 
                1. python3 -m venv env
                2. source env/bin/activate
                3. pip install requests 
    - lancer : "python3 [nom du script].py"
    - Saisir le titre de l'épisode en anglais et en respectant scrupuleusement la présence éventuelle de majuscules
    - Saisir le numéro de l'épisode en chiffres arabes

Pour interrompre le script : 
    - en ligne de commande, faire "CTRL+Z"

'''

import os
import requests
import zipfile
import csv
import shutil
from xml.etree import ElementTree as ET
from itertools import zip_longest
import sys

# Chargement de la table de correspondances entre les codes de langue utilisés par Pepper&Carrot (clés) et les codes de langue utilisés par Lo Congrès (valeurs)
# Pour les langues construites n'ayant pas de code normalisé officiel, les valeurs correspondent au nom de la langue
correspondances = {
    'ar': 'ar', 'at': 'ast', 'kt': 'avk', 'bn': 'bn', 'br': 'br', 'ca': 'ca', 'cs': 'cs', 'da': 'da', 'de': 'de', 'el': 'el', 'en': 'en', 'eo': 'eo', 'es': 'es', 'mx': 'es-MX', 'fa': 'fa', 'fi': 'fi', 'ph': 'fil', 'fr': 'fr', 'gb': 'globasa', 'go': 'fr-gallo', 'gd': 'gd', 'gl': 'gl', 'he': 'he', 'hi': 'hi', 'hu': 'hu', 'id': 'id', 'ie': 'ie', 'io': 'io', 'it': 'it', 'ja': 'ja', 'jb': 'jbo-Latn', 'jz': 'jbo', 'kr': 'ko-Hang', 'kh': 'ko', 'kw': 'kw', 'la': 'la', 'ld': 'ldn', 'lf': 'lfn', 'lt': 'lt', 'ls': 'espanol-latino', 'ml': 'ml', 'ms': 'ms', 'mw': 'mwl', 'no': 'nb', 'ns': 'nds', 'nl': 'nl', 'nn': 'nn', 'nm': 'nrf', 'ga': 'oc-gascon-grclass', 'oc': 'oc-lengadoc-grclass', 'pl': 'pl', 'pt': 'pt', 'rc': 'rcf', 'ro': 'ro', 'ru': 'ru', 'sb': 'sambahsa', 'si': 'si', 'sk': 'sk', 'sl': 'sl', 'sp': 'sitelen-pona', 'sr': 'sr', 'su': 'su', 'sv': 'sv', 'sz': 'szl', 'ta': 'ta', 'tp': 'tok', 'tr': 'tr', 'uk': 'uk', 'vi': 'vi', 'cn': 'zh'
}

def nettoyer_titre(titre: str):
    # nettoyage du titre saisi par l'utilisateur (suppression du potentiel espace final, transformation espaces en tirets)
    return titre.strip().replace(" ", "-")
    
################# TELECHARGEMENT DU ZIP ############################


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
        print(f"\nErreur lors du téléchargement de l'épisode : {e}.\nSolutions possibles :\n1) vérifiez que le titre en anglais existe bien et soit bien orthographié, \n2) vérifiez que vous ayez bien respecté les majuscules du titre original, \n3) vérifiez qu'il y ait une correspondance entre le titre et le numéro d'épisode saisi, \n4) pensez également à vérifier votre connexion internet, \n5) enfin, contactez un membre du pôle Informatique.")
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


################# TRAITEMENT DU SVG ############################

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

################# ECRITURE DE NOUVEAUX CSV AVEC LE TEXTE SVG ##############

def creer_csv_avec_svg_data(langue_code, numero_episode, numero_page, texte_svg):    
    nv_fichier_csv = f"{langue_code}_E{numero_episode.zfill(2)}P{numero_page.zfill(2)}.csv"
    with open(nv_fichier_csv, 'w', newline='', encoding='utf-8') as fichier_csv:
        writer = csv.writer(fichier_csv)
        for row in texte_svg:
            writer.writerow([row])
    
    return nv_fichier_csv

################# FUSION DES CSV DE PAGES EN UN SEUL CSV PAR LANGUE ########

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

################## ALIGNEMENT GASCON / AUTRES LANGUES ##################

# Produire un corpus aligné avec le gascon
def aligner_corpus_avec_gascon(csv_gascon, csv_langue_tierce, gascon_code='ga'):
    numero_episode = csv_gascon.split('_')[1][1:].zfill(2)
    fichier_aligne_ga = f"{gascon_code}-{csv_langue_tierce.split('_')[0]}_E{numero_episode}.csv"

    with open(csv_gascon, 'r', encoding='utf-8') as fichier_ga, \
         open(csv_langue_tierce, 'r', encoding='utf-8') as fichier_autre, \
         open(fichier_aligne_ga, 'w', newline='', encoding='utf-8') as fichier_aligne_2:
        
        ga_reader = csv.reader(fichier_ga)
        other_reader = csv.reader(fichier_autre)
        writer = csv.writer(fichier_aligne_2, delimiter='§', escapechar=' ', quoting=csv.QUOTE_NONE)        
        
        for ligne_oc, ligne_autre in zip_longest(ga_reader, other_reader, fillvalue=[""]):            
            if ligne_oc and ligne_oc[0].strip():  
                # supprimer les retours à la ligne                
                texte_oc = ligne_oc[0].replace('\n', ' ').strip()
                # Eviter les doublons de '§oc'
                if f"§{gascon_code}" not in texte_oc:
                    ligne_oc_avec_lang = f"{texte_oc}§{gascon_code}"
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
    
    return fichier_aligne_ga

################## ALIGNEMENT LANGUEDOCIEN / AUTRES LANGUES ##############

# Produire un corpus aligné avec le languedocien
def aligner_corpus_avec_languedocien(csv_occitan, csv_langue_tierce, occitan_code='oc'):
    # Aligner le CSV occitan avec un autre fichier CSV de langue
    numero_episode = csv_occitan.split('_')[1][1:].zfill(2)  
    fichier_aligne = f"{occitan_code}-{csv_langue_tierce.split('_')[0]}_E{numero_episode}.csv"
        
    with open(csv_occitan, 'r', encoding='utf-8') as fichier_oc, \
         open(csv_langue_tierce, 'r', encoding='utf-8') as fichier_autre, \
         open(fichier_aligne, 'w', newline='', encoding='utf-8') as fichier_aligne_2:
        
        oc_reader = csv.reader(fichier_oc)
        other_reader = csv.reader(fichier_autre)
        writer = csv.writer(fichier_aligne_2, delimiter='§', escapechar=' ', quoting=csv.QUOTE_NONE) #le quote_none est nécessaire ici pour éviter les guillemets autour des chaînes de caractères       
        
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

################# ALIGNEMENT LANGUEDOCIEN / GASCON ########################
def creer_repertoire_alignement_bivariete(numero_episode, fichiers_csv_alignes):
    # création répertoire temporaire pour les alignements languedocien-gascon
    rep_alignement_lg_ga = f"E{numero_episode.zfill(2)}_bivarietat_lg_ga"
    os.makedirs(rep_alignement_lg_ga, exist_ok=True)
    
    fichiers_a_deplacer = []

    # parcourir les fichiers alignés pour sélectionner les bons fichiers à déplacer et supprimer
    for fichier in fichiers_csv_alignes:
        if "oc-lengadoc-grclass_oc-gascon-grclass" in fichier:
            # déplacer les fichiers de ce type vers notre répertoire
            nouveau_chemin = os.path.join(rep_alignement_lg_ga, os.path.basename(fichier))
            shutil.move(fichier, nouveau_chemin)
            fichiers_a_deplacer.append(nouveau_chemin)

    if not fichiers_a_deplacer:
        #print("Aucun fichier correspondant n'a été trouvé. Arrêt de la fonction.")
        os.rmdir(rep_alignement_lg_ga) # supprimer le répertoire temporaire vide
        return # return vide pour sortir de la fonction       

    
    # création d'un fichier zip pour les alignements languedocien-gascon
    fichier_zip_alignement_lg_ga = f"E{numero_episode.zfill(2)}_bivarietat_lg_ga.zip"
    with zipfile.ZipFile(fichier_zip_alignement_lg_ga, 'w') as zipf:
        for fichier_csv in fichiers_a_deplacer:
            zipf.write(fichier_csv, arcname=os.path.basename(fichier_csv))
            os.remove(fichier_csv) # supprimer les fichiers "temporaires" pour éviter l'encombrement
            os.rmdir(rep_alignement_lg_ga) # supprimer le répertoire temporaire vide
    
    return fichier_zip_alignement_lg_ga

################# GESTION DES CODES DE LANGUE ###########################

# Modifier les fichiers csv et leurs noms pour correspondre aux codes de langues du Congrès selon la table de concordance fournie plus haut
def modifier_contenu_csv(fichier_csv, correspondances):
    lignes_modifiees = []
    
    with open(fichier_csv, 'r', encoding='utf-8') as fichier:
        reader = csv.reader(fichier, delimiter='§')
        for ligne in reader: 
            if len(ligne) > 1:
                if ligne[1] in correspondances:
                    ligne[1] = correspondances[ligne[1]]
                if len(ligne) > 3 and ligne[3] in correspondances:
                    ligne[3] = correspondances[ligne[3]]
            lignes_modifiees.append(ligne)
    
    with open(fichier_csv, 'w', newline='', encoding='utf-8') as fichier:
        writer = csv.writer(fichier, delimiter='§', escapechar=' ', quoting=csv.QUOTE_NONE)
        writer.writerows(lignes_modifiees)
    return fichier_csv

def renommer_fichiers_csv(fichier_csv, correspondances, numero_episode):
    # Extraire la valeur de la deuxième et de la quatrième colonne du premier élément pour créer le nouveau nom
    with open(fichier_csv, 'r', encoding='utf-8') as fichier:
        reader = csv.reader(fichier, delimiter='§')
        premiere_ligne = next(reader)
        
        if len(premiere_ligne) > 1:
            langue_2_col = premiere_ligne[1]
            langue_4_col = premiere_ligne[3] if len(premiere_ligne) > 3 else None
            
            if langue_2_col in correspondances:
                langue_2_col = correspondances[langue_2_col]
            if langue_4_col in correspondances:
                langue_4_col = correspondances[langue_4_col]
    
    nouveau_nom = f"{langue_2_col}_{langue_4_col}_E{numero_episode.zfill(2)}.csv"
    nouveau_chemin = os.path.join(os.path.dirname(fichier_csv), nouveau_nom)
    os.rename(fichier_csv, nouveau_chemin)    

    return nouveau_chemin

################ GENERATION DES ZIPS ##########################
# il serait possible d'optimiser les deux fonctions suivantes en les fusionnant et en allant chercher la valeur de la variable de langue

# Générer un fichier zip pour le languedocien
def creer_zip_fichiers_alignes_lg(numero_episode, fichiers_csv_alignes):
    fichier_zip_lg = f"E{numero_episode.zfill(2)}_oc-lengadoc-grclass_alignements.zip"    
    with zipfile.ZipFile(fichier_zip_lg, 'w') as zipf:
        for fichier_csv in fichiers_csv_alignes:
            nom_fichier_correct = fichier_csv.replace('.csv.csv', '.csv') # éviter la double extension '.csv.csv'
            zipf.write(fichier_csv, arcname=nom_fichier_correct)
            os.remove(fichier_csv)  # Supprimer le fichier CSV d'origine une fois placé dans le fichier compressé        
    return fichier_zip_lg

# Générer un fichier zip pour le gascon
def creer_zip_fichiers_alignes_ga(numero_episode, fichiers_csv_alignes_ga):    
    fichier_zip_ga = f"E{numero_episode.zfill(2)}_oc-gascon-grclass_alignements.zip"    
    with zipfile.ZipFile(fichier_zip_ga, 'w') as zipf:
        for fichier_csv in fichiers_csv_alignes_ga:
            nom_fichier_correct = fichier_csv.replace('.csv.csv', '.csv') # éviter la double extension '.csv.csv'
            zipf.write(fichier_csv, arcname=nom_fichier_correct)
            os.remove(fichier_csv)  # Supprimer le fichier CSV d'origine une fois placé dans le fichier compressé    
    return fichier_zip_ga

################### FONCTION MAIN() ###########################

def main():

    #################### APPEL AUX FONCTIONS COMMUNES ######################

    # Formulaire destiné à l'utilisateur
    titre = input("Entrez le titre de l'épisode en anglais en respectant strictement la casse : ")
    numero_episode = input("Entrez le numéro de l'épisode : ")

    # Nettoyer le titre si besoin
    titre = nettoyer_titre(titre)    
    
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
            
            # Appeler la fonction d'extraction du texte 
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
    
    ############ APPEL AUX FONCTIONS SPÉCIFIQUES POUR CHAQUE TYPE D'ALIGNEMENT ################
    
    # listes pour recueillir les fichiers alignés en languedocien et en gascon
    fichiers_csv_alignes = []
    fichiers_csv_alignes_ga = []

    # Gestion de l'erreur liée à l'absence de fichier occitan pour un épisode donné    
    try:
        csv_occitan = [f for f in fichiers_csv_finaux if f.startswith("oc_")][0]
    except IndexError:
        print("\nErreur : il n'y a pas encore de traduction en occitan disponible pour cet épisode. \nLe script va être interrompu et ne va pas retourner de résultats.")        
        for fichier_csv in fichiers_csv_finaux:
            if os.path.exists(fichier_csv):
                os.remove(fichier_csv) # supprimer les fichiers produits précédemment (éviter l'encombrement)                
        shutil.rmtree(dossier_extrait) # suppression du dossier lang-pack téléchargé au début du script
        sys.exit(1)   # arrêt du script si aucun fichier languedocien trouvé
     
    #### Appel aux fonctions de traitement des corpus languedociens :
    # Alignement du fichier occitan avec le fichier de langue tierce
    for fichier_csv in fichiers_csv_finaux:
        if not fichier_csv.startswith("oc_"):
            fichier_aligne_lg = aligner_corpus_avec_languedocien(csv_occitan, fichier_csv)
            fichiers_csv_alignes.append(fichier_aligne_lg)
    # Modification des fichiers et de leurs noms pour correspondre aux codes de langues du Congrès
    fichiers_csv_alignes_modifies_lg = []
    for fichier_csv in fichiers_csv_alignes:
        fichier_modifie_lg = modifier_contenu_csv(fichier_csv, correspondances)
        fichier_renomme_lg = renommer_fichiers_csv(fichier_modifie_lg, correspondances, numero_episode)
        fichiers_csv_alignes_modifies_lg.append(fichier_renomme_lg)
    
    fichier_zip_final_bivar = creer_repertoire_alignement_bivariete(numero_episode, fichiers_csv_alignes_modifies_lg)
    # éviter le FileNotFound pour le dossier languedocien (puisqu'il est amputé du fichier languedocien-gascon après l'appel à creer_repertoire() ci-dessus)
    fichiers_valides_lg = [f for f in fichiers_csv_alignes_modifies_lg if os.path.exists(f)]
    # Créer un fichier ZIP avec tous les fichiers alignés
    fichier_zip_final_lg = creer_zip_fichiers_alignes_lg(numero_episode, fichiers_valides_lg)   
   
    ### Appel conditionnel (plus de chances d'avoir des corpus languedociens sans gascon que l'inverse) aux fonctions de traitement des corpus gascons :     
    fichiers_gascon = [fichier for fichier in fichiers_csv_finaux if fichier.startswith("ga_")]
    if fichiers_gascon:
        csv_gascon = [f for f in fichiers_csv_finaux if f.startswith("ga_")][0]         
        # Alignement du fichier gascon avec le fichier de langue tierce
        for fichier_csv in fichiers_csv_finaux:
            if not fichier_csv.startswith("ga_"):
                fichier_aligne_ga = aligner_corpus_avec_gascon(csv_gascon, fichier_csv)
                fichiers_csv_alignes_ga.append(fichier_aligne_ga)
        # Modification des fichiers et de leurs noms pour correspondre aux codes de langues du Congrès
        fichiers_csv_alignes_modifies_ga = []
        for fichier_csv in fichiers_csv_alignes_ga:
            fichier_modifie_ga = modifier_contenu_csv(fichier_csv, correspondances)
            fichier_renomme_ga = renommer_fichiers_csv(fichier_modifie_ga, correspondances, numero_episode)
            fichiers_csv_alignes_modifies_ga.append(fichier_renomme_ga)
        # Suppression du fichier gascon-languedocien (car on a déjà un fichier languedocien-gascon !)
        for fichier in fichiers_csv_alignes_modifies_ga:
            if "oc-gascon-grclass_oc-lengadoc-grclass" in fichier:
                os.remove(fichier)
            break # arrêt de la boucle dès que le fichier est trouvé une fois
        # Pour résoudre le bug (fichier gascon supprimé auquel la fonction creer_zip() voulait accéder, et qui provoquait un File Not Found error):
        # il s'agit de vérifier que les fichiers à traiter par creer_zip() existent bien avant d'appeler la fonction
        fichiers_valides_ga = [f for f in fichiers_csv_alignes_modifies_ga if os.path.exists(f)]
        # Créer un fichier ZIP avec tous les fichiers alignés
        fichier_zip_final_ga = creer_zip_fichiers_alignes_ga(numero_episode, fichiers_valides_ga)
    else:
        print("\nErreur : il n'y a pas encore de traduction en gascon disponible pour cet épisode. \nLe script ne retournera pas de corpus alignés bilingue pour le gascon, ni de corpus bivariété pour le gascon et le languedocien.")    

    ############### PREPARATION SORTIE DE SCRIPT #################

    # Suppression des fichiers temporaires
    for fichier_csv in fichiers_csv_finaux:
        os.remove(fichier_csv)        

    # Suppression du dossier extrait
    shutil.rmtree(dossier_extrait)
    
    if fichiers_gascon:
        print(f"\nSUCCÈS DU PROGRAMME \nFichiers ZIP finaux: \n- Fichier contenant les alignements avec le languedocien : \n{fichier_zip_final_lg}\n- Fichier contenant les alignements avec le gascon : \n{fichier_zip_final_ga}\n- Fichier contenant les alignements languedocien/gascon : \n{fichier_zip_final_bivar}\n")
    else:
        print(f"\nSUCCÈS DU PROGRAMME \nFichier ZIP final : \n- Fichier contenant les alignements avec le languedocien : \n{fichier_zip_final_lg}\n")

if __name__ == "__main__":
    main()