# Lab 2 — Construire le corpus annoté avant l'évaluation

## Avancement

La partie A est publiée au commit 910c837, tag lab-2-stage-a. Cet ajout commence la partie B. Il construit des données et vérifie leur cohérence. Il ne choisit aucun seuil et ne mesure pas encore la qualité des méthodes.

Vérification de cette livraison : installation normale, Python 3.12.14/Linux, 98 tests réussis (86 existants et 12 nouveaux). La vérification Windows reste à effectuer par l'étudiant.

## Ce que contient le corpus

Deux devoirs synthétiques : sum_squares (somme des carrés des entiers non négatifs) et count_even (nombre d'entiers pairs). Chaque devoir a six racines, avec des stratégies différentes. Les trois premières familles de chaque devoir sont destinées au réglage, les trois suivantes à l'évaluation.

Chaque racine a trois soumissions : original, renommage des identifiants, modification des commentaires/formatage. Cela fait 12 × 3 = 36 soumissions. Huit contrôles supplémentaires contiennent uniquement le modèle autorisé et un commentaire, sans solution. Total : 44 soumissions, 20 familles et 22 soumissions par ensemble.

| Ensemble | Paires positives | Paires négatives | Dont modèle uniquement | Total |
|---|---:|---:|---:|---:|
| Réglage (tuning) | 18 | 12 | 6 | 30 |
| Évaluation (evaluation) | 18 | 12 | 6 | 30 |
| Total | 36 | 24 | 12 | 60 |

Les paires modèle uniquement sont incluses dans les négatives : elles ne s'ajoutent pas au total. Les 60 paires sont une sélection fixée, pas toutes les combinaisons possibles des 44 soumissions.

Positif signifie « relation de dérivation présente dans la construction du corpus ». Négatif signifie « relation absente selon la provenance déclarée ». Ces mots ne jugent ni la qualité de la solution ni le comportement d'un étudiant.

## Provenance honnête et portée des conclusions

Les premières racines sum_squares reprennent/adaptent les exemples publics sub-001, sub-004 et sub-006 du corpus de démonstration. Cette origine est indiquée dans source. Les autres racines sont des exemples synthétiques rédigés avec ChatGPT. Les variantes sont produites par des transformations déterministes, enregistrées dans parent_id et renaming.

Les racines déclarées distinctes correspondent à des constructions distinctes de ce corpus, pas à une preuve d'indépendance historique entre travaux réels. Des solutions au même problème partagent naturellement des éléments de syntaxe et d'algorithme. Le corpus reste petit, artificiel et rédigé avec l'aide du même outil que le programme : les métriques seront descriptives de ces exemples et ne justifieront pas une généralisation aux étudiants réels.

Les contrôles modèle uniquement sont volontairement simples et sans solution. Ils vérifient l'abstention après exclusion du modèle, mais ne couvrent pas toutes les difficultés d'un modèle mêlé à une solution substantielle. Les douze paires de ce type ne représentent pas douze phénomènes indépendants.

Le champ annotation_status vaut construction_based_not_independently_reviewed. Les labels n'ont pas été attribués par un évaluateur indépendant. La déclaration d'IA des soumissions synthétiques contient used=true et verified_by_student=false. La date de soumission est une valeur de fixture fixe, pas une date de remise réelle.

## Les fichiers générés

Le générateur crée un nouveau dossier data/lab2_quality_v1, séparé des fichiers de démonstration existants.

| Fichier | Rôle |
|---|---|
| submissions.jsonl | Soumissions respectant exactement le schéma du lab 1 |
| provenance.jsonl | Origine, famille, ensemble, parent, transformation et justification de provenance |
| pairs.jsonl | Liste fixe des paires et de leurs annotations |
| assignments.json | Les deux devoirs et leur modèle autorisé |
| manifest.json | Version, politique de séparation, comptages et empreintes SHA-256 |
| .gitattributes | Maintien des fins de ligne LF pour les fichiers du corpus dans Git |

Pourquoi un fichier de provenance séparé ? La validation du lab 1 refuse les champs inconnus. Ajouter family_id directement dans une soumission casserait ce contrat. Le submission_id permet de relier la soumission à sa fiche de provenance.

Les empreintes permettent de détecter un changement de données. Elles ne prouvent pas la vérité des annotations. La séparation est explicitement fixée ; aucune sélection aléatoire n'est utilisée, donc seed vaut null.

## Comprendre les principales fonctions

### build_quality_data

Cette fonction fabrique quatre collections Python : submissions, provenance, pairs et assignments. Elle ne lit pas de résultats de comparaison et ne fait appel ni au score AST ni au score token.

La boucle principale parcourt les deux devoirs puis leurs racines. enumerate(..., start=1) fournit un numéro commençant à 1. La règle `split = "tuning" if index <= 3 else "evaluation"` place une famille entière d'un côté. Le même split est utilisé pour l'original et ses deux variantes.

Le code `for first, second in itertools.combinations(ids, 2)` sélectionne chaque paire distincte une seule fois. Pour [original, renamed, formatted], les trois paires sont original/renamed, original/formatted et renamed/formatted. Aucune paire original/original ni répétition inversée n'est créée.

Pour les paires négatives ordinaires, nous combinons des racines différentes du même devoir et du même ensemble. Pour les contrôles modèle uniquement, nous combinons leurs identifiants au sein de chaque ensemble. Les labels sont donc déterminés par la construction, avant les scores.

### rename_identifiers

Un remplacement naïf avec str.replace pourrait changer aussi une chaîne, un commentaire ou une partie d'un nom plus long. Nous utilisons tokenize et ne remplaçons que les tokens NAME présents dans le dictionnaire de renommage.

Exemple : si value devient number, la chaîne "value" et le nom value2 restent intacts. Les coordonnées de tokenize sont transformées en positions dans la chaîne complète.

Les modifications sont appliquées de droite à gauche avec reversed(edits). Pourquoi ? Si un nom plus long est inséré au début, les positions des noms suivants se décalent. Commencer par la fin préserve toutes les positions encore à modifier.

### format_variant

Cette fonction ajoute un commentaire bilingue, des lignes vides et des espaces en fin de ligne. Elle conserve l'indentation utile. Les chaînes du code sont des données : aucune soumission n'est exécutée.

### validate_quality_data

Cette fonction appelle la validation du lab 1 et vérifie les liens entre les collections : identifiants uniques, provenance complète, familles disjointes entre ensembles, un seul original par famille, parents cohérents, transformations reproductibles, paires du même devoir et d'étudiants distincts, absence de doublons inversés, labels booléens et compatibles avec la provenance déclarée.

La règle de cohérence des labels est spécifique à ce corpus : même famille implique relation de dérivation. Elle ne doit pas être réutilisée sans adaptation pour des données réelles, où la provenance peut être inconnue ou multiple.

`family_split.setdefault(family, split)` mémorise le premier ensemble rencontré pour une famille. Lorsqu'on rencontre une autre variante, la valeur mémorisée doit rester égale à son split. Sinon le validateur signale une fuite de famille.

ast.parse vérifie la construction de l'arbre sans exécuter le code. Cela ne prouve pas qu'une solution est correcte sur toutes les entrées. Les tests de cet ajout vérifient le corpus et les transformations, pas l'exécution des solutions.

### corpus_files et write_quality_corpus

corpus_files sérialise les données dans un ordre déterministe et calcule les SHA-256 des fichiers. Aucune heure courante n'est introduite. Deux générations donnent les mêmes octets.

write_quality_corpus crée le dossier s'il est absent. S'il existe, elle compare les fichiers avec les octets attendus. Si tout est identique, elle ne réécrit rien ; si un fichier diffère, elle s'arrête pour protéger les changements manuels. Il faut alors examiner la différence ou choisir un nouveau dossier/version, pas écraser silencieusement les annotations.

Les sorties de ce générateur sont les données de l'expérience : contrairement aux exports locaux de comparaison, elles devront être suivies dans Git après revue. Le tag lab-2-stage-a reste attaché à sa version antérieure.

## Installation et génération sous Windows

Après extraction de l'archive à la racine du projet :

```powershell
# RU: Устанавливаем генератор учебного корпуса.
# EN: Install the learning-corpus generator.
.\.venv\Scripts\python.exe -m pip install .

# RU: Проверяем весь проект.
# EN: Test the entire project.
.\.venv\Scripts\python.exe -m unittest discover -v

# RU: Создаём и проверяем фиксированный корпус.
# EN: Create and validate the fixed corpus.
.\.venv\Scripts\python.exe build_lab2_corpus.py --output .\data\lab2_quality_v1
```

Attendu : 98 tests OK ; submissions=44, families=20, pairs=60, family_overlap=0. Pour chaque ensemble : pairs=30, positive=18, negative=12, template_only=6.

Lecture de quelques annotations :

```powershell
# RU: Показываем три первые размеченные пары.
# EN: Display the first three annotated pairs.
Get-Content .\data\lab2_quality_v1\pairs.jsonl -Encoding UTF8 |
    Select-Object -First 3 |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Select-Object first_id, second_id, split, derivation_relation, template_only
```

## Vérifications et suite

Les douze nouveaux tests couvrent les comptages, les familles disjointes, les paires traversant les ensembles, les labels incorrects, les paires inversées répétées, les transformations non conformes, les contrôles modèle contenant du code supplémentaire, le renommage sélectif, la provenance absente, la génération reproductible sans appel aux scores et la protection des fichiers modifiés.

La suite sera la revue de quelques annotations, l'enregistrement du corpus fixé, puis le calcul des deux méthodes sur les mêmes paires. Le seuil sera choisi uniquement sur tuning. Les résultats indisponibles, notamment les contrôles sans caractéristiques après exclusion du modèle, devront être comptabilisés séparément et non transformés silencieusement en score 0.

Les contrôles de syntaxe invalide et de constructions AST non prises en charge restent dans les tests de contrat du projet ; ce corpus de qualité ne contient pas de syntaxe invalide. Les mesures de qualité et de performances ne sont pas encore réalisées.

## Vocabulaire et exercice

| Russe | Français | Anglais |
|---|---|---|
| происхождение | provenance | provenance |
| размеченная пара | paire annotée | labelled pair |
| семейство | famille | family |
| преобразование | transformation | transformation |
| утечка данных | fuite de données | data leakage |
| воспроизводимость | reproductibilité | reproducibility |

Exercice : une paire de variantes du même original obtient un score token de 0.2. Faut-il modifier derivation_relation=True en False pour être d'accord avec le score, ou conserver son annotation ? Explique pourquoi.
