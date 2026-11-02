# EA Coach

Contrôleur de démarche d'architecture d'entreprise, compatible TOGAF®. Il lit un **modèle ArchiMate®** et les **livrables** d'un projet, puis indique ce qui manque au regard de l'ADM : livrables absents, objectifs sans partie prenante, exigences que rien ne réalise, lots qui ne comblent aucun écart…

Il fonctionne comme un linter de code : en local ou sur GitHub à chaque modification, avec un rapport lisible et un code de sortie pour bloquer une PR.

> EA Coach contrôle la **présence** et la **traçabilité** de ce que la méthode attend. Il ne juge pas la qualité du contenu et ne remplace pas une revue d'architecture.

## Exemple de rapport

```text
❌ A-04 — Chaque objectif est porté par une partie prenante ou un driver
- Moderniser la plateforme (Goal) : aucune relation vers Assessment, Driver, Stakeholder.
Que faire : relier l'objectif à un Stakeholder ou à un Driver (Influence ou Association).
```

Le rapport complet regroupe les contrôles par phase ADM (Preliminary, A à H, Requirements Management) : ✅ conforme, ❌ manque bloquant, ⚠️ alerte, ➖ non applicable par adaptation déclarée.

## Utilisation

Python 3.11 ou plus, sans dépendance.

```bash
python -m ea_coach check examples/demo-incomplet/tailoring.toml          # rapport Markdown à l'écran
python -m ea_coach check mon-projet/tailoring.toml --out rapport.md       # dans un fichier
python -m ea_coach check mon-projet/tailoring.toml --format json          # pour l'outillage
```

Code de sortie : `0` aucun manque bloquant, `1` au moins un manque bloquant, `2` erreur d'utilisation. Sur GitHub Actions, le rapport s'affiche aussi dans le résumé du job.

## Ce qu'il faut fournir

1. **Un modèle ArchiMate**, au choix :
   - le fichier natif d'**Archi** (`.archimate`) ;
   - ou l'**Open Exchange Format** (`.xml`) : dans Archi, *Fichier › Exporter › Modèle au format Open Exchange*.
2. **Un fichier d'adaptation** (`tailoring.toml`) : TOGAF n'impose pas tous ses livrables, on adapte la méthode au projet. EA Coach contrôle **ce que le projet a décidé d'appliquer**.

```toml
[project]
name = "Mon projet"
rules = "togaf-adm"            # jeu de règles intégré, ou chemin vers un fichier TOML
model = "model.archimate"      # relatif à ce fichier
root = "."                     # racine du projet pour les livrables

[deliverables]                 # où se trouvent les livrables (chemins ou motifs)
architecture_vision = "docs/vision.md"
architecture_decisions = "docs/adr/*.md"

[not_applicable."B-03"]        # écarter une règle : justification OBLIGATOIRE
reason = "Migration purement technique : aucun processus métier modifié."

[severity]                     # ajuster la sévérité pour ce projet
"Q-01" = "warning"
```

Une exemption sans justification est refusée et compte comme manque bloquant : une adaptation de la méthode doit être expliquée.

## Les règles

Le jeu `togaf-adm` contient 33 contrôles répartis sur les phases de l'ADM : voir [docs/regles-togaf-adm.md](docs/regles-togaf-adm.md). Ils sont décrits dans [`ea_coach/rules/togaf-adm.toml`](ea_coach/rules/togaf-adm.toml). Le moteur ne connaît pas TOGAF : il exécute six types de règles génériques.

| Type | Contrôle |
| --- | --- |
| `presence` | au moins N éléments d'un type (ex. des Principles) |
| `trace` | chaque élément d'un type est relié à un élément attendu (ex. chaque Requirement est réalisé) |
| `deliverable` | le livrable est déclaré dans l'adaptation et ses fichiers existent |
| `view` | une vue avec un viewpoint donné existe (ex. Implementation and Migration) |
| `plateaus` | base et cible modélisées, et un Gap entre les deux |
| `in_view` | chaque élément apparaît dans au moins une vue |

On peut écrire son propre jeu (standards internes, exigences réglementaires…) dans le même format.

## Exemples

| Dossier | Contenu |
| --- | --- |
| [`examples/cert-exam-trainer`](examples/cert-exam-trainer) | Modèle ArchiMate de l'appli [cert-exam-trainer](https://github.com/zdmooc/cert-exam-trainer) (93 éléments, 6 vues), dérivé de son dossier `docs/architecture`. À ouvrir dans Archi : *Fichier › Importer › Open Exchange XML*. |
| [`examples/demo-incomplet`](examples/demo-incomplet) | Projet fictif volontairement incomplet, au format natif Archi, pour voir ce qu'EA Coach signale. |

Le modèle d'exemple est vérifié en CI contre le **schéma XSD officiel** de l'Open Exchange Format et la **table des relations ArchiMate 3.2** d'Archi (`tools/validate_archimate.py`).

## Feuille de route

| Version | Contenu |
| --- | --- |
| v0.1 | Contrôles automatiques : complétude par phase, traçabilité, cohérence base/cible, adaptation justifiée ; rapports Markdown et JSON ; CI |
| v0.2 | Action GitHub réutilisable pour contrôler un autre dépôt ; règles de cohérence ADM supplémentaires |
| v0.3 | Coach IA : lit le rapport et les livrables, pose les questions d'un architecte expérimenté et propose les prochaines actions |

## Mentions

TOGAF® et ArchiMate® sont des marques déposées de The Open Group. Ce projet n'est ni affilié à The Open Group ni approuvé par elle ; le jeu de règles est une lecture outillée de la méthode, non une publication officielle.
