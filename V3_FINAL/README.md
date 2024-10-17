## extract_align_pepper_carrot.py

Programme permettant d'extraire et d'aligner automatiquement depuis le site de *Pepper & Carrot* des corpus bilingues ou bivariétés ayant pour pivot l'occitan languedocien ou l'occitan gascon pour chaque épisode de la webcomic.  
Une participation de l'utilisateur est nécessaire pour saisir manuellement le titre et le numéro de l'épisode traité.

Retourne un ou trois dossiers zip comprenant : 
    - des corpus alignés bilingues *languedocien-autre langue* (priorité donnée)
    - des corpus alignés bilingues *gascon-autre langue* (s'il existe une traduction en gascon)
    - un corpus aligné *bivariété languedocien-gascon* (s'il existe une traduction en gascon)

Les dossiers zip retournés en sortie seront placés dans le même répertoire que celui où se situe le présent script.

Pour exécuter le script : 
    - se placer en ligne de commande à l'emplacement du répertoire parent du script (`cd [repertoire_parent]`...)
    - créer un environnement virtuel (recommandé) : 
        - sur Windows : 
                1. `python -m venv env`
                2. `env\Scripts\activate` 
                3. `pip install requests`
        - sur Linux : 
                1. `python3 -m venv env`
                2. `source env/bin/activate`
                3. `pip install requests` 
    - lancer le programme : `python3 extract_align_pepper_carrot.py`
    - Saisir le titre de l'épisode __en anglais__ et en respectant __scrupuleusement__ la présence éventuelle de majuscules
    - Saisir le numéro de l'épisode en chiffres arabes

Pour interrompre le script : 
    - en ligne de commande : `CTRL`+`Z`