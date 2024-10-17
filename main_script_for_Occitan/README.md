# extract_align_pepper_carrot.py

Programme permettant d'extraire et d'aligner automatiquement depuis le site de *Pepper & Carrot* des corpus bilingues ou bivariétés ayant pour pivot l'occitan languedocien ou l'occitan gascon pour chaque épisode de la webcomic.  
Une participation de l'utilisateur est nécessaire pour saisir manuellement le titre et le numéro de l'épisode traité.

Retourne un ou trois dossiers zip comprenant :  
- des corpus alignés bilingues languedocien-autre langue
- des corpus alignés bilingues gascon-autre langue (seulement s'il existe une traduction en gascon)  
- un corpus aligné bivariété languedocien-gascon (seulement s'il existe une traduction en gascon)  

Les dossiers zip retournés en sortie seront placés dans le même répertoire que celui où se situe le présent script.

Pour exécuter le script :   
1) se placer en ligne de commande à l'emplacement du répertoire parent du script (`cd [repertoire_parent]`...)
2) créer un environnement virtuel (optionnel) : 
- sur Windows :  
    - `python -m venv env`  
    - `env\Scripts\activate`   
    - `pip install requests`  
- sur Linux :
    - `python3 -m venv env`  
    - `source env/bin/activate`  
    - `pip install requests`
3) lancer le programme : `python3 extract_align_pepper_carrot.py`  
4) Saisir le titre de l'épisode __en anglais__ et en respectant __scrupuleusement__ la présence éventuelle de majuscules  
5) Saisir le numéro de l'épisode en chiffres arabes  

Pour interrompre le script :   
	- en ligne de commande : `CTRL`+`Z` 

Pour quitter l'environnement virtuel :   
	- en ligne de commande  `deactivate`