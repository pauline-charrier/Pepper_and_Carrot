import os
import zipfile
import shutil 
#import csv
from collections import defaultdict

'''
Note : pour décommenter des blocs de code sur VSCode : CTRL+K puis CTRL+U, pour commenter des blocs de code : CTRL+K puis CTRL+C. 

Script pour transformer les répertoires zippés retournés par le script 'extract_align_pepper_carrot.py' et classés par épisodes, en deux répertoires bilingues (un rép. languedocien + un rép. gascon) comprenant eux-mêmes chacun un répertoire pour chaque langue faisant l'objet d'un alignement avec le languedocien ou le gascon.

Deux approches possibles : 
    1) soit le programme prend en entrée directement les répertoires zippés retournés par le script d'extraction/alignement.
    Choisir dans ce cas la fonction extraire_fichiers_csv() prenant en paramètre un "dossier_zip"
    Et décommenter les lignes de code correspondantes dans la fonction main()

    2) soit le programme prend en entrée un répertoire non zippé contenant lui-même les répertoires zippés (un choix plus intéressant dans le cas d'une grande volumétrie de répertoires zippés).
    Choisir dans ce cas la fonction extraire_fichiers_csv() prenant en paramètre un "repertoire_zip"
    Et commenter/décommenter les lignes de code correspondantes dans la fonction main()

'''
### FONCTION POUR EXTRAIRE LES CSV A PARTIR D'UN RÉPERTOIRE NON ZIPPÉ, CONTENANT LES RÉPERTOIRES ZIPPÉS
### Approche 2
def extraire_fichiers_csv(repertoire_zip):
    fichiers_csv = defaultdict(list)

    for nom_fichier in os.listdir(repertoire_zip):
        if nom_fichier.endswith('.zip'):
            chemin_zip = os.path.join(repertoire_zip, nom_fichier)
            with zipfile.ZipFile(chemin_zip, 'r') as zipf:
                for fichier in zipf.namelist():
                    if fichier.endswith('.csv'):
                        zipf.extract(fichier)
                        try:
                            langue1, langue2, numero_episode = fichier.split('_')
                            fichiers_csv[langue1].append((langue2, fichier))
                        except ValueError:
                            print(f"Nom de fichier invalide : {fichier}")
    return fichiers_csv

### FONCTION POUR EXTRAIRE LES CSV DE RÉPERTOIRES ZIPPÉS
### Approche 1 : 
# def extraire_fichiers_csv(dossiers_zip):
#     fichiers_csv = defaultdict(list)

#     # Parcourir chaque dossier ZIP
#     for dossier_zip in dossiers_zip:
#         with zipfile.ZipFile(dossier_zip, 'r') as zipf:
#             # Extraire tous les fichiers du ZIP
#             for fichier in zipf.namelist():
#                 if fichier.endswith('.csv'):
#                     # Extraire le fichier CSV
#                     zipf.extract(fichier)
#                     # Récupérer la langue2 à partir du nom du fichier
#                     try:
#                         langue1, langue2, numero_episode = fichier.split('_')
#                         fichiers_csv[langue1].append((langue2, fichier))
#                     except ValueError:
#                         print(f"Nom de fichier non valide : {fichier}")

#     return fichiers_csv

### FONCTION POUR CLASSER LES CSV PAR LANGUE 2 
### Approches 1 et 2
def creer_repertoires_bilingues(fichiers_csv):
    for langue1, fichiers in fichiers_csv.items():
        # créer un dossier pour la langue 1 (soit gascon soit languedocien)
        dossier_bilingue = f"{langue1}_bilingue"
        os.makedirs(dossier_bilingue, exist_ok=True)

        # créer un dictionnaire pour les langues2 (langues autres que l'occitan, sauf pour le corpus bivar)
        fichiers_par_langue2 = defaultdict(list)
        for langue2, fichier in fichiers:
            fichiers_par_langue2[langue2].append(fichier)
        
        # créer les répertoires pour chaque langue2 et y déplacer les fichiers
        for langue2, fichiers_langue2 in fichiers_par_langue2.items():
            dossier_langue2 = os.path.join(dossier_bilingue, langue2)
            os.makedirs(dossier_langue2, exist_ok=True)

            for fichier in fichiers_langue2:
                os.rename(fichier, os.path.join(dossier_langue2, fichier))


def main():
    ## Approche 1 : Liste de dossiers ZIP (à compléter ou à commenter manuellement)
    # dossiers_zip = []
    # fichiers_csv = extraire_fichiers_csv(dossiers_zip)

    ## Approche 2 : Chemin vers le répertoire contenant les fichiers zip
    repertoire_zip = "corpus_corpus"   
    fichiers_csv = extraire_fichiers_csv(repertoire_zip)

    #creer_zips_par_langue(fichiers_csv)
    creer_repertoires_bilingues(fichiers_csv)

if __name__ == "__main__":
    main()