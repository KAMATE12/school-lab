# Changements de la vérification finale

La structure que tu as construite est conservée.

1. validation.py : ajout des annotations manquantes. object accepte une entrée inconnue que le corps contrôle ; Never décrit une fonction qui lève toujours une exception. Aucune annotation ne remplace un contrôle.
2. assignments.py : nouvelle fonction parse_assignments. Elle vérifie un tableau de devoirs, leurs champs, les exigences et les identifiants uniques ; elle construit des Assignment. Aucun accès disque dans cette fonction.
3. analyze_cli.py : option --assignments, lecture du catalogue, sélection du devoir et erreur structurée si le devoir manque. Les anciennes commandes restent utilisables.
4. report_validation.py : contrôles des types des observations/preuves, date avec fuseau, empreintes, explications et score fini. Les contrôles de positions sont conservés.
5. AIDeclarationAnalyzer : vérifie aussi tool/purpose lorsqu’un objet est construit directement. Les entrées JSON étaient déjà contrôlées par parse_submission.
6. test_final_contracts.py : mêmes attentes pour les trois analyseurs ; résultat déterministe hors date/identifiant ; entrée préservée ; analyseur volontairement mutateur ; métadonnées incorrectes ; catalogue et CLI.
7. pyproject.toml : ajout du README et de la commande school-lab-analyze.

Nouveaux termes : каталог заданий = catalogue de devoirs = assignment catalog ; контрактный тест = test de contrat = contract test ; воспроизводимость = reproductibilité = reproducibility.

La version 0.1.0 est conservée. Le zip contient aussi le rapport russe, les exemples et les journaux réels de vérification. Les anciennes expériences sont conservées ; ne les exécute pas pour préparer les données finales : exploration.py réécrit son fichier de démonstration.

## Vérification Windows avant remise

Décompresse dans un nouveau dossier. Crée .venv avec python -m venv .venv, puis exécute .\.venv\Scripts\python.exe -m pip install . et .\.venv\Scripts\python.exe -m unittest discover -v. Utilise ensuite les commandes du README. Le mode normal installe une copie : après une modification, réinstalle, ou utilise -e pour développer.

## Préparer la défense

- Protocol : décrit les opérations attendues ; une implémentation n’a pas besoin d’en hériter. Hériter d’Exception fournit un comportement et une famille d’exceptions.
- Composition : le contexte contient un Assignment, la soumission contient une AIDeclaration, le service reçoit un dépôt.
- SHA-256 : empreinte stable des octets UTF-8 du JSON canonique ; hash() de Python n’est pas ce contrat de persistance.
- with : l’appelant contrôle la durée de vie du fichier. break seul ne ferme pas nécessairement un itérateur ; la sortie du bloc with ferme la ressource.
- Duplication : même identifiant et même empreinte retourne l’objet enregistré ; conflit : même identifiant et contenu différent ne le remplace pas.
- Extension : enregistrer une fabrique supplémentaire suffit ; le service central appelle toujours analyze.
- Evidence : références aux lignes originales, début et fin inclus, sans renumérotation après filtrage.
- Limites : compter des lignes ne mesure pas la qualité ; une déclaration d’IA n’est pas une preuve ; un modèle autorisé n’est pas du plagiat.

L’exercice similaire personnel sera proposé après la remise, comme convenu.
