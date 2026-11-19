# Lab 2 — Méthode AST : intégration et explications

État : seconde méthode intégrée, pas encore une remise finale du lab 2.
Archive de départ : school-lab2-review-20261118-225347.zip.
Vérification locale : Python 3.12.14, Linux ; installation normale du paquet puis 78 tests réussis (64 existants + 14 nouveaux). L'exécution Windows Python 3.14.7 reste à vérifier chez Emmanuel. Aucun fichier existant du projet n'a été modifié par cet ajout.

## Les cinq fichiers ajoutés

- `src/school_lab/ast_features.py` : préparation et normalisation des structures.
- `src/school_lab/ast_comparison.py` : comparaison de deux soumissions préparées.
- `src/school_lab/ast_cli.py` : lecture progressive, sélection des paires et export JSONL.
- `test_ast_method.py` : 14 tests automatisés supplémentaires.
- `AST_METHOD_FR.md` : ce guide.

`ast_scopes.py`, déjà dans ton projet, reste utilisé : chaque portée contient son propre objet NameScope. Aucun besoin de remplacer ton projet entier ou de toucher au tag lab-1.

## 1. La représentation et le score

`ast.parse(code)` construit un arbre sans exécuter le code. Une instruction comme `answer = value * 2` contient une affectation, un nom cible, une multiplication, un nom utilisé et une constante.

Un token décrit un élément lexical. Un sous-arbre d'instruction décrit une construction structurée. Cette méthode utilise les représentations des sous-arbres de toutes les instructions retenues, après normalisation des noms. Les opérateurs, constantes, ordre des listes AST et contextes Load/Store sont conservés. Les positions ne font pas partie des clés de comparaison.

Une fonction entière et son instruction return peuvent ainsi produire deux caractéristiques. Ces caractéristiques ne sont pas statistiquement indépendantes : leur pondération implicite est une limite du baseline. Il ne s'agit ni d'une distance d'édition d'arbres, ni d'une preuve d'équivalence des programmes.

`keys` est un frozenset : un ensemble immuable de caractéristiques uniques. `occurrences` conserve chaque apparition avec ses lignes, y compris les répétitions. L'ensemble sert au score, les occurrences servent à expliquer les correspondances.

Score = nombre de caractéristiques communes / nombre de caractéristiques dans l'union.

- Deux ensembles non vides identiques : 1.0.
- Un seul ensemble vide : 0.0.
- Deux ensembles vides : None, écrit null dans le JSON.

Les fréquences sont perdues par le passage en ensemble. Deux algorithmes équivalents mais écrits avec une boucle et un générateur peuvent avoir un faible score AST.

## 2. Pourquoi deux passes pour les noms ?

Une seule lecture qui remplace immédiatement les noms serait trompeuse. En Python, une affectation située plus loin dans une fonction peut déterminer que le nom est local dans tout son corps. Le normaliseur collecte donc d'abord les déclarations et les utilisations, puis les renomme.

`_Scope` possède :

- `number` : identifiant interne de la portée ;
- `parent` : référence vers la portée englobante, ou None pour le module ;
- `names` : objet NameScope déjà étudié ;
- `bindings` : ensemble des noms déclarés dans cette portée.

`field(default_factory=...)` construit une nouvelle collection pour chaque instance. Cela évite de partager accidentellement les dictionnaires entre deux fonctions.

Un événement contient `(node, attribute, original_name, scope)`. Par exemple, le nom d'une utilisation est dans `node.id`, mais celui d'un paramètre est dans `node.arg`.

Le premier parcours enregistre les événements et les déclarations. Le second trie les événements par `(lineno, col_offset)`, donc par position dans le texte. Il résout ensuite chaque nom dans sa portée, puis remonte les parents si nécessaire.

```python
while owner is not None and original not in owner.bindings:
    owner = owner.parent
```

`owner` désigne la portée où chercher. Tant qu'elle existe et ne déclare pas le nom, nous passons à sa parente. Cette boucle ne parcourt pas le code soumis : elle parcourt nos objets de description des portées.

Si le nom est déclaré, nous appelons `owner.names.normalize(original)`. Le résultat inclut aussi l'identifiant de portée, par exemple `scope1:name_0`. Cela distingue une variable locale d'une référence à une variable extérieure.

Si aucune déclaration n'est trouvée, nous conservons le nom avec le marqueur `external:`, par exemple `external:sum`. Ainsi sum et max restent différents. Les marqueurs empêchent les noms originaux d'entrer accidentellement en collision avec notre représentation interne.

`setattr(node, attribute, replacement)` écrit dans l'attribut dont le nom est contenu dans `attribute`. Si attribute vaut "id", cela revient à `node.id = replacement`.

Le nouvel arbre est seulement une représentation de comparaison. Les marqueurs contiennent des caractères qui ne forment pas des identifiants Python exécutables. Nous ne compilons ni n'exécutons cet arbre transformé.

## 3. Les portées effectivement prises en charge

Le module, les fonctions ordinaires ou async, les fonctions lambda, les compréhensions et les expressions génératrices ont leurs propres correspondances.

Les fonctions imbriquées peuvent lire les noms de leurs portées parentes. Les noms de fonctions sont déclarés dans la portée englobante. Leurs paramètres sont déclarés dans leur portée propre.

Les valeurs par défaut des paramètres sont analysées dans la portée englobante. Le premier itérable d'une compréhension est aussi analysé dans la portée englobante ; les cibles, filtres et résultats sont analysés dans sa portée propre.

Pour `items = [1, 2]; result = [item * 2 for item in items]`, items appartient au module, item à la compréhension. Les règles de résolution préservent cette différence.

Le code n'est jamais exécuté. L'absence de SyntaxError dans ast.parse ne prouve pas qu'un programme pourrait s'exécuter correctement : certaines erreurs apparaissent à la compilation complète ou à l'exécution.

## 4. Le modèle autorisé et les preuves

Nous réutilisons `find_template_lines` du projet. La détection est celle du baseline existant : un bloc contigu de lignes identiques, avec indentation et espaces significatifs.

Un NodeTransformer retire les instructions entièrement contenues dans les lignes du modèle avant la normalisation. Retirer le modèle avant la numérotation évite qu'un nom provenant uniquement du modèle décale les noms utiles.

Une instruction dont le sous-arbre couvre des lignes exclues ne devient pas une caractéristique. Les instructions enfants admissibles peuvent toutefois rester des caractéristiques. Nous ne supprimons pas les lignes du texte original : les numéros de ligne restent valides.

Cette exclusion est conservatrice. Un modèle partiel qui coupe une instruction sur plusieurs lignes peut supprimer toute cette caractéristique. Un bloc identique placé dans une chaîne multiligne peut aussi être détecté comme modèle par la règle de lignes existante. Ce sont des limites à mesurer et à expliquer, pas des garanties sémantiques.

## 5. Comparer et enregistrer

`PreparedAstSubmission` réunit la soumission validée et ses caractéristiques préparées.

`compare_ast_submissions` refuse : auto-comparaison, devoirs différents, même étudiant, configurations ou versions incompatibles. Elle utilise les caractéristiques déjà préparées ; elle ne rappelle pas ast.parse.

Le résultat contient les deux identifiants, les empreintes des soumissions, le score, les occurrences communes de chaque côté, les lignes du modèle, le nom de la méthode, sa version et l'empreinte de configuration.

La configuration comprend le modèle autorisé, la version de méthode et la version majeure/mineure de Python. La grammaire AST peut changer entre versions de Python : nous évitons de mélanger silencieusement leurs résultats.

Le CLI réutilise la validation et la réception du lab 1. Les doublons sont ignorés, les conflits sont signalés, les erreurs d'une ligne n'empêchent pas les suivantes. Les travaux sont indexés par devoir et les paires du même étudiant sont ignorées. Chaque paire admissible est produite une seule fois.

La lecture et l'écriture sont progressives. L'index conserve toutefois les soumissions et leurs caractéristiques : mémoire non constante. Le nombre de comparaisons peut être quadratique. Les longues clés de sous-arbres sont aussi un coût à examiner au profilage.

`open('x')` refuse d'écraser un fichier existant. Les diagnostics vont sur stderr, le bilan JSON sur stdout. Codes de sortie : 0 sans erreur de ligne, 1 avec erreurs de ligne, 2 pour problème de fichier ou configuration. Une erreur fatale pendant l'écriture peut laisser un fichier partiel : ne pas le présenter comme une exécution complète.

## 6. Limites explicites de la version 1.0

- Classes, global, nonlocal, affectations :=, match, alias de type et paramètres de type génériques, imports étoile et template strings : erreur structurée `unsupported_ast`. Les fonctions imbriquées ordinaires sont prises en charge.
- Les annotations sont conservées littéralement et ne font pas l'objet d'une résolution sémantique. Les noms d'attributs et les noms des arguments nommés des appels sont conservés. Renommer un paramètre et ses appels par mots-clés n'est donc pas entièrement invariant.
- Les chemins d'import sont conservés ; les alias locaux sont normalisés. Le comportement dynamique des modules, de getattr, de globals, de exec et eval n'est pas interprété. Ces fonctions éventuellement présentes dans une soumission ne sont jamais exécutées par l'analyseur.
- Une numérotation locale de noms ou l'identifiant d'une portée peut changer si l'on insère du code avant. Le score est structurel et sensible à ces modifications.
- Les chaînes, docstrings et annotations sont significatives. Les commentaires ordinaires et le formatage ne le sont pas dans l'AST.
- Aucun seuil review_required n'est choisi à ce stade. Il devra être réglé uniquement sur le jeu de réglage, pas sur le jeu d'évaluation.
- Un score élevé demande une analyse humaine ; il ne prouve aucun plagiat. Une erreur unsupported_ast n'est pas un score 0. Elle devra compter comme résultat indisponible dans l'évaluation.

## 7. Résultats vérifiés sur le corpus de l'archive

Bilan : accepted=12, prepared=11, duplicate=0, errors=1, comparisons=54, insufficient=0.

L'erreur est le code Python invalide de la ligne 8. La ligne contenant seulement un commentaire produit un ensemble vide ; ses comparaisons avec un ensemble non vide donnent 0. Aucun couple ne réunit deux ensembles vides ici.

- sub-001 / sub-002 (copie) : 1.0.
- sub-001 / sub-003 (renommage) : 1.0.
- sub-001 / sub-007 (formatage/commentaire) : 1.0.
- sub-004 / sub-011 (renommage dans une boucle) : 1.0.

Ces observations portent sur le petit corpus de démonstration. Ce ne sont pas des mesures de qualité sur le futur corpus annoté.

## 8. Commandes Windows après copie des fichiers

```powershell
# RU: Устанавливаем пакет с методом AST.
# EN: Install the package with the AST method.
.\.venv\Scripts\python.exe -m pip install .

# RU: Проверяем весь проект.
# EN: Test the entire project.
.\.venv\Scripts\python.exe -m unittest discover -v

# RU: Выбираем новый файл результатов.
# EN: Choose a new results file.
$astOutput = ".\ast_comparisons_$(Get-Date -Format 'yyyyMMdd-HHmmss').jsonl"

# RU: Сравниваем учебный корпус методом AST.
# EN: Compare the learning corpus using the AST method.
.\.venv\Scripts\python.exe -m school_lab.ast_cli submissions.jsonl --assignments assignments.json --output $astOutput
$LASTEXITCODE
```

Attendu : 78 tests OK, bilan ci-dessus et code de sortie 1 à cause de l'exemple invalide connu. Refaire l'installation après une modification des fichiers du paquet avec l'installation normale utilisée dans ce projet.

## 9. Lire la documentation Python

https://docs.python.org/3.14/library/ast.html : rechercher `Name`, `arg`, `NodeTransformer`, `iter_fields` et `lineno`. Comparer les attributs décrits avec les nœuds observés dans explore_ast.py.

https://docs.python.org/3.14/reference/executionmodel.html : lire Naming and binding, puis Resolution of names. Cela explique pourquoi nous collectons d'abord les noms déclarés dans une portée.

## 10. Vocabulaire et exercice

| Russe | Français | Anglais |
|---|---|---|
| область видимости | portée | scope |
| родительская область | portée englobante | enclosing scope |
| связывание имени | liaison d'un nom | name binding |
| поддерево | sous-arbre | subtree |
| исходные строки | lignes sources | source lines |
| недостаточно данных | données insuffisantes | insufficient data |
| неподдерживаемая конструкция | construction non prise en charge | unsupported construct |

Exercice : pourquoi sum doit-il conserver une identité différente de max, alors que les paramètres values et items peuvent être normalisés de la même façon ?

## 11. Travail restant

Vérifier cet ajout sous Windows, compléter les critères communs de réception (dont la sélection top-k mentionnée dans la fiche), préparer le point stage-a. Ensuite : corpus d'au moins 30 soumissions et 40 paires annotées, séparation par familles, réglage et évaluation des deux méthodes, mesures 100/1000/5000 trois fois, profilage et optimisation mesurée, documentation et rapport final. Le lab 2 n'est pas terminé par ce seul ajout.
