# Lab 2 — terminer l’étape B

Emmanuel Kamate — M80-103CB-26. Trajectoire Python Core, niveau principal.

Ce paquet ajoute l’évaluation et les mesures au projet existant. Il ne remplace pas le corpus
`data/lab2_quality_v1`, enregistré dans le commit `dee17ba`. Les exercices pédagogiques
sont reportés à la discussion de compréhension demandée par Emmanuel.

## 1. Installer la mise à jour

Télécharger `school-lab2-stage-b-update.zip`, extraire son contenu et copier les dossiers/fichiers
**à la racine** de `school-lab-final` en fusionnant `src` avec le dossier existant.
Ne pas créer un projet imbriqué. La commande `Test-Path .\run_lab2_stage_b.ps1` doit afficher True.
Les seuls fichiers existants remplacés par ce paquet sont README.md, AI_USAGE.md et .gitignore.
Les autres fichiers ajoutent les fonctions de l’étape B. Les scripts Python ont des commentaires RU/EN.

Depuis PowerShell :

```powershell
# RU: Переходим в существующий проект.
# EN: Open the existing project.
Set-Location "$HOME\Projects\school-lab\school-lab-final"

# RU: Проверяем наличие сценария запуска.
# EN: Check that the runner was copied to the project root.
Test-Path .\run_lab2_stage_b.ps1

# RU: Запускаем все проверки и эксперименты этапа Б.
# EN: Run all stage B checks and experiments.
powershell -ExecutionPolicy Bypass -File .\run_lab2_stage_b.ps1
```

Le paramètre ExecutionPolicy ne modifie pas durablement la politique PowerShell : il s’applique
au processus lancé. Le script utilise le Python de `.venv`, réinstalle le projet, puis exécute
les tests, le réglage, l’évaluation, les profils, les mesures et la génération du rapport russe.
Il ne crée aucun commit et ne publie rien sur GitHub. Les commandes s’arrêtent à la première erreur.

Ne pas relancer un test après chaque ligne de mesure : laisser le script terminer.
Le calcul peut prendre plusieurs minutes, davantage sur une machine moins rapide.
Il affiche une ligne après chaque mesure. Une ligne `cached=False` n’est pas une erreur :
c’est la mesure du programme sans cache, nécessaire à la comparaison.
Éviter d’utiliser des applications lourdes pendant les mesures.

## 2. Ce que le script produit

Un nouveau dossier `results/lab2_windows_DATE-HEURE/` contient :

| Fichier | Utilité |
|---|---|
| tests_stderr.txt | Journal unittest (unittest écrit normalement sur stderr) |
| tests.txt | Sortie stdout des tests, éventuellement vide |
| frozen_policy.json | Seuils choisis exclusivement sur tuning, paramètres et empreintes |
| evaluation.json | Scores, décisions, preuves et métriques sur evaluation |
| performance/performance.json | Tous les temps/mémoires, médianes et paramètres |
| performance/profile_*.txt et .prof | Profils avant/après optimisation |
| REPORT_LAB2_RU.md | Rapport russe construit à partir de **ce** lancement |
| base_commit.txt, working_tree.txt | Contexte Git avant la publication de cette mise à jour |

Le rapport est un document Markdown lisible dans VS Code ou GitHub. Les fichiers de charge
`load_*.jsonl` se régénèrent exactement avec le seed indiqué et sont ignorés par Git.
Les sorties de mesures, rapports, profils et seuils doivent être conservés dans la livraison.
Les résultats Linux fournis dans `results/lab2_reference_linux/` servent de référence distincte ;
ne pas les présenter comme des mesures effectuées sur Windows.

## 3. Résultats de référence réellement mesurés

Python 3.12.14 / Linux : **114 tests réussis** après installation normale du paquet.
Les tests Windows restent à exécuter avec ce paquet. Le corpus est le même que celui publié.

| Méthode | Seuil tuning | TP | FP | TN | FN | Precision | Recall | F1 | Indéterminés |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tokens | 0,20 | 16 | 2 | 4 | 2 | 88,89 % | 88,89 % | 88,89 % | 6/30 |
| AST | 0,25 | 16 | 0 | 6 | 2 | 100 % | 88,89 % | 94,12 % | 6/30 |

Les matrices et les trois métriques portent sur les **24 scores définis** de chaque méthode.
Les six abstentions sont toutes des contrôles négatifs contenant uniquement le modèle autorisé.
Elles ne sont pas transformées en vrais négatifs. La couverture vaut 80 %.
Un résultat `review_required=True` demande une revue humaine ; il ne prouve pas un plagiat.

Le seuil maximise F1 sur une grille prédéfinie. En cas d’égalité : meilleure précision,
puis seuil le plus élevé. La règle s’applique avant de regarder evaluation.
L’expérience conserve les erreurs constatées : pas de changement de seuil, d’annotation ou
de normalisation après lecture des résultats d’évaluation.

## 4. Performance : ce qui est mesuré et ce qui ne l’est pas

Pour chacun de 100, 1 000 et 5 000 enregistrements : lecture JSONL, validation, index de caractéristiques,
puis cinq requêtes comparées à toutes les autres copies. Cela représente **5 × (N − 1)** comparaisons
orientées. Ce n’est pas le benchmark de toutes les N(N−1)/2 paires ; le rapport distingue les deux.
Chaque variante des deux méthodes est mesurée trois fois. Les médianes et toutes les valeurs
brutes sont conservées. Tout est séquentiel, sans threads ni processus parallèles.

Optimisation : cache LRU borné à 128 textes exacts avec leur modèle autorisé. Les caractéristiques
sont immuables et réutilisables, les positions originales restent identiques. Le profil montre
le coût de leur préparation répétée. Le scénario principal contient 32 textes différents répétés
avec des identifiants distincts. Un contrôle de 1 000 textes tous différents expose les limites du cache.

Sur la référence Linux à N=5000, médianes :

- Tokens : 19,583 s → 17,366 s ; pic Python 48,307 → 5,153 MiB.
- AST : 6,303 s → 3,044 s ; pic Python 16,299 → 4,804 MiB.

Ces gains dépendent fortement des répétitions. Sur les sources uniques à N=1000, les temps sont
très proches : aucune accélération générale n’est revendiquée. La mémoire est mesurée avec tracemalloc
(allocations Python, pas RSS global), et le chronométrage inclut son surcoût. Le calcul de la somme de
contrôle des preuves fait aussi partie du temps mesuré. Le stockage de l’index n’est pas constant en N.

## 5. Erreurs expliquées dans le rapport russe

1. Tokens : certains renommages massifs entraînent des faux négatifs.
2. Tokens : des fragments syntaxiques communs entre racines distinctes entraînent des faux positifs.
3. AST : un modèle dont la ligne a reçu des espaces finaux n’est plus reconnu par l’exclusion exacte.
   Le changement des liaisons de noms peut alors provoquer un faux négatif. Cette limite reste visible.
4. Les contrôles uniquement constitués du modèle donnent None : il s’agit d’un résultat indéterminé attendu.

Les six erreurs observées sont listées avec les identifiants et scores dans le rapport.
L’analyse détaillée de leur logique sera reprise dans la discussion pédagogique séparée.

## 6. Nouveau modèle lors de la soutenance

Créer deux fichiers UTF-8 : `defense_code.py` (code de démonstration) et `defense_template.txt`
(modèle exact donné par le professeur). Puis :

```powershell
# RU: Показываем новые признаки и изменённую конфигурацию шаблона.
# EN: Display the features and changed template configuration.
.\.venv\Scripts\python.exe defense_lab2_template.py --code-file defense_code.py --template-file defense_template.txt
```

La sortie montre les lignes exclues, le nombre de caractéristiques et le nouvel ast_config_hash.
Le corpus déjà figé ne doit pas être modifié : toute nouvelle évaluation nécessite une nouvelle
version de données et de politique. La démo n’exécute pas le code fourni.

## 7. Avant la livraison

Après le message final `Etape B executee. Resultats: ...`, transmettre :

- la fin des tests (`Ran ... tests`, `OK`) ;
- les résumés token et ast de `evaluation.json` ;
- le fichier `performance/performance.json` et le rapport russe généré.

Nous pourrons vérifier le lancement Windows, puis sélectionner les fichiers du commit et créer le tag
final `lab-2`. Ne pas déplacer ni recréer `lab-1` ou `lab-2-stage-a`. Ne pas changer les dates Git.
L’archive `school-lab2-stage-a-docs.zip` est désormais ignorée par .gitignore ; elle peut rester locale.

Le code, le rapport de référence et le protocole de l’étape B sont préparés. La reproduction Windows
et la publication du résultat final ne sont pas encore confirmées.
