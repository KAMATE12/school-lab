# Lab 2 — Classement top-k pour les deux méthodes

## Objectif et position dans le laboratoire

Les deux méthodes existent. Cet ajout traite la sélection de candidats top-k mentionnée dans les critères de réception de la partie A. Il ne termine pas la partie B : corpus annoté, réglage, évaluation, profilage et mesures restent à réaliser.

Un top-k renvoie au maximum k travaux admissibles, classés du score le plus élevé au plus faible. Le classement n'est pas un verdict et n'applique pas encore de seuil review_required.

## Fichiers ajoutés

- src/school_lab/ranking.py : logique commune et deux fonctions publiques.
- test_ranking.py : huit tests, chacun appliqué aux deux méthodes lorsque pertinent.
- explore_ranking.py : démonstration sur le corpus de douze soumissions.
- RANKING_FR.md : ce guide.

Les fichiers de l'ajout AST précédent doivent déjà être présents. Aucun fichier existant n'est remplacé.

## 1. Les objets retournés

RankedMatch contient candidate_id, score et comparison. Le dernier champ est l'objet de comparaison complet : il conserve les preuves et les informations sur le modèle. Nous ne perdons donc pas les explications en créant le classement.

RankingResult contient matches (tuple des candidats retenus), compared (nombre de comparaisons effectuées), excluded (paires exclues avant comparaison) et insufficient (comparaisons dont le score vaut None).

Une dataclass frozen rend les attributs non réaffectables par l'usage normal. Les objets de résultats et leurs collections tuple permettent de transmettre un résultat stable.

## 2. Pourquoi deux fonctions publiques et une fonction commune ?

rank_token_candidates et rank_ast_candidates choisissent la fonction de comparaison adaptée, puis appellent la même fonction interne _rank. Cela garantit les mêmes règles de sélection pour les deux méthodes.

Dans `return _rank(query, candidates, compare_ast_submissions, k)`, nous passons la fonction `compare_ast_submissions` sans parenthèses. Nous ne la lançons pas à cet endroit. _rank la reçoit sous le nom compare et l'appelle plus tard : `comparison = compare(query, candidate)`.

query désigne le travail étudié. candidates désigne l'itérable de travaux possibles. k désigne la taille maximale du résultat, pas le nombre de comparaisons à effectuer.

## 3. Valider k

`type(k) is not int` rejette notamment True et False, même si bool est une sous-classe d'int en Python. Le contrat choisit ici un entier strictement positif. Une chaîne "3", 1.5, 0 et -1 sont refusés.

Nous faisons cette vérification avant de lire candidates : une mauvaise option ne doit pas déclencher des lectures ou du calcul inutiles.

## 4. Filtrer avant de comparer

La boucle parcourt les candidats un à un. Le set seen_ids détecte les identifiants répétés ; ce niveau attend un corpus dont la réception a déjà résolu les doublons et les conflits. Il ne tente pas d'en choisir une version silencieusement.

Les trois exclusions sont reliées par `or` : une seule suffit à exclure la paire.

- Même submission_id : comparaison avec soi-même.
- assignment_id différent : autre devoir.
- Même student_id : autre version du même étudiant.

`continue` passe directement au candidat suivant. La fonction de comparaison n'est pas appelée pour le candidat exclu. Les incompatibilités de configuration entre candidats admissibles restent des erreurs explicites provenant du comparateur.

## 5. None et zéro ne sont pas interchangeables

Un score None signifie que les deux ensembles de caractéristiques sont vides. Nous augmentons insufficient et n'insérons pas ce candidat dans le classement.

Un score 0.0 est défini : l'union n'est pas vide, mais l'intersection est vide. Il peut figurer dans le top-k si peu de meilleurs candidats sont disponibles. L'utilisateur doit donc lire le score ; être dans un top-k ne signifie pas automatiquement être très similaire.

## 6. Pourquoi le signe moins dans le tri ?

`matches.sort(key=lambda match: (-match.score, match.candidate_id))`

Par défaut, sort classe du plus petit au plus grand. Transformer 1.0 en -1.0 et 0.7 en -0.7 fait passer le score 1.0 avant 0.7 : -1.0 est plus petit que -0.7.

La clé est un tuple. Python compare d'abord ses premiers éléments. S'ils sont égaux, il compare les identifiants. Deux candidats ayant le même score gardent donc un ordre reproductible fondé sur leur identifiant, même si l'ordre d'arrivée du corpus change.

Le tri des identifiants est lexicographique (texte), pas un tri numérique des suffixes.

`matches[:k]` sélectionne les k premiers éléments, ou tous les éléments s'il y en a moins. `tuple(...)` transforme cette sélection en collection immuable.

## 7. Coûts et limites

Cette première version compare la requête à tous les candidats admissibles puis trie les scores définis. Pour m candidats admissibles, il y a m comparaisons et un tri en O(m log m), en plus du coût propre aux ensembles et aux preuves. Le classement conserve tous les résultats avant d'en sélectionner k : sa mémoire n'est pas limitée à O(k).

seen_ids conserve les identifiants du corpus parcouru. L'index des caractéristiques conserve également des données. Le script de démonstration utilise list(...) pour conserver son petit corpus préparé ; cela ne doit pas être présenté comme une mémoire constante. Il lit néanmoins le JSONL ligne par ligne.

Il n'y a pas encore d'index accélérant la recherche, de cache persistant ou de seuil appris. L'optimisation éventuelle doit venir après un profilage et garder les mêmes résultats.

Le script est un exemple pour les fichiers fournis et l'identifiant sub-001. Si on change de corpus sans ce travail, next(...) lèvera StopIteration. Ce n'est pas encore une interface générale pour sélectionner arbitrairement une requête.

Les échecs de préparation AST sont affichés et leurs travaux ne sont pas classés. Pour l'évaluation de qualité, il faudra conserver le jeu de paires fixé et comptabiliser les résultats indisponibles, sans supprimer silencieusement ces paires.

## 8. Vérifications effectuées

Python 3.12.14 sous Linux : 86 tests réussis, dont les 78 existants avant cet ajout. Les huit nouveaux tests couvrent : exclusions avant calcul, classement reproductible et limite k, scores décroissants, différence None/0, k invalide, doublons et configuration, corpus vide, absence de nouveau parsing.

Sur le corpus de l'archive fournie :

```
Tokens top 3:
  sub-002: score=1.000000
  sub-007: score=1.000000
  sub-005: score=0.777778
Compared=9; excluded=2; insufficient=0

AST top 3:
  sub-002: score=1.000000
  sub-003: score=1.000000
  sub-007: score=1.000000
Compared=9; excluded=2; insufficient=0
```

L'erreur invalid_code de la ligne 8 est attendue et cette soumission ne rejoint pas le corpus préparé. Parmi les onze travaux préparés, sub-001 elle-même et sub-012 (même étudiant) sont exclues ; neuf comparaisons sont effectuées. Le score 0.777778 est arrondi seulement pour l'affichage : les calculs conservent le flottant original.

## 9. Commandes Windows

Après extraction à la racine du projet :

```powershell
# RU: Устанавливаем модуль ранжирования.
# EN: Install the ranking module.
.\.venv\Scripts\python.exe -m pip install .

# RU: Проверяем весь проект.
# EN: Test the entire project.
.\.venv\Scripts\python.exe -m unittest discover -v

# RU: Показываем три лучших кандидата для каждого метода.
# EN: Display the top three candidates for each method.
.\.venv\Scripts\python.exe explore_ranking.py
```

## Vocabulaire

| Russe | Français | Anglais |
|---|---|---|
| ранжирование | classement | ranking |
| кандидат | candidat | candidate |
| исключить | exclure | exclude |
| по убыванию | par ordre décroissant | descending |
| одинаковые оценки | scores égaux | tied scores |

Exercice : avec les candidats A=0.4, B=None, C=0.9 et k=2, lesquels sont retournés, et pourquoi B n'est-il pas traité comme un score zéro ?
