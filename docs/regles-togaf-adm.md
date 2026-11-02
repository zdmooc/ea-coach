# Règles « TOGAF ADM — contrôles de démarche »

Référence : TOGAF® Standard, 10e édition — ADM et Architecture Content Framework, modélisés en ArchiMate® 3.x.

Fichier source : `ea_coach/rules/togaf-adm.toml` (ce tableau est généré par `tools/rules_table.py`).

## Preliminary

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| PRE-01 | Des principes d'architecture sont modélisés | Présence | Bloquant | La phase préliminaire établit les Architecture Principles qui guident toutes les décisions suivantes. |
| PRE-02 | Le document des principes d'architecture existe | Livrable | Bloquant | Les principes s'énoncent avec nom, énoncé, justification et implications ; ce texte ne tient pas dans un diagramme. |
| PRE-03 | Chaque principe a une conséquence visible | Traçabilité | Alerte | Un principe sans implication tracée ne guide aucune décision vérifiable. |
| PRE-04 | L'adaptation de la méthode (tailoring) est documentée | Livrable | Alerte | Le Tailored Architecture Framework explique ce qui est fait, allégé ou écarté pour ce projet. |

## Phase A — Architecture Vision

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| A-01 | Les parties prenantes sont identifiées | Présence | Bloquant | La phase A commence par identifier les stakeholders et leurs concerns. |
| A-02 | Des objectifs métier sont formulés | Présence | Bloquant | L'Architecture Vision relie la transformation à des business goals mesurables. |
| A-03 | Les moteurs du changement (drivers) sont explicites | Présence | Alerte | Les business drivers expliquent pourquoi l'architecture est nécessaire maintenant. |
| A-04 | Chaque objectif est porté par une partie prenante ou un driver | Traçabilité | Bloquant | Un objectif sans origine identifiée n'a pas de légitimité ni de responsable. |
| A-05 | Chaque partie prenante a une préoccupation modélisée | Traçabilité | Alerte | La gestion des parties prenantes part de leurs concerns ; une partie prenante sans concern est un nom sur une liste. |
| A-06 | L'Architecture Vision existe | Livrable | Bloquant | C'est le livrable central de la phase A : périmètre, valeur, parties prenantes, indicateurs. |
| A-07 | Une vue présente les parties prenantes et leurs objectifs | Vue | Alerte | Les décisions de phase A se prennent sur des vues adaptées aux concerns des parties prenantes. |

## Phase B — Business Architecture

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| B-01 | L'architecture métier est décrite | Présence | Bloquant | La phase B décrit ce que l'entreprise doit savoir faire, indépendamment des applications. |
| B-02 | Chaque capacité est réalisée par quelque chose | Traçabilité | Alerte | Une capacité qu'aucun processus, service ou ressource ne réalise reste un souhait. |
| B-03 | Une vue métier (carte des capacités) existe | Vue | Alerte | La carte des capacités est l'artefact le plus utilisé pour arbitrer la transformation. |

## Phase C — Information Systems (Data, Application)

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| C-01 | Les données sont décrites | Présence | Bloquant | La Data Architecture identifie les entités de données et leur propriétaire. |
| C-02 | Les composants applicatifs sont décrits | Présence | Bloquant | L'Application Architecture identifie les applications et leurs interactions. |
| C-03 | Chaque donnée est utilisée par une application | Traçabilité | Alerte | Une donnée qu'aucun composant n'utilise est soit oubliée dans les flux, soit inutile. |
| C-04 | Chaque composant applicatif a un rôle tracé | Traçabilité | Alerte | Un composant isolé ne montre ni ce qu'il rend comme service ni à quoi il sert. |

## Phase D — Technology Architecture

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| D-01 | La plateforme technique est décrite | Présence | Bloquant | La Technology Architecture décrit l'infrastructure qui porte les applications. |
| D-02 | Chaque composant applicatif repose sur une technologie identifiée | Traçabilité | Alerte | Sans lien vers la technologie, impossible d'évaluer l'impact d'un changement d'infrastructure. |

## Phases E et F — Opportunities, Migration Planning

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| EF-01 | Les états de base et cible, et l'écart entre eux, sont modélisés | Base / cible / écart | Bloquant | L'analyse d'écarts (gap analysis) compare une Baseline et une Target ; sans les deux, elle est impossible. |
| EF-02 | Le travail de transformation est découpé en lots | Présence | Bloquant | Les phases E et F regroupent les changements en work packages ordonnés. |
| EF-03 | Chaque lot produit un livrable ou comble un écart | Traçabilité | Bloquant | Un work package qui ne réalise aucun livrable et ne comble aucun gap n'a pas de justification d'architecture. |
| EF-04 | Chaque écart est pris en charge par un lot | Traçabilité | Alerte | Un gap sans work package est un écart identifié mais jamais planifié. |
| EF-05 | Une vue de migration existe | Vue | Alerte | La feuille de route se lit sur une vue Implementation and Migration ou Migration. |
| EF-06 | L'Architecture Roadmap existe | Livrable | Bloquant | La roadmap ordonne les lots et les transitions ; c'est un livrable des phases E et F. |

## Phase G — Implementation Governance

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| G-01 | Le contrat d'architecture (ou son équivalent) est documenté | Livrable | Alerte | La phase G gouverne la mise en œuvre au travers d'un Architecture Contract et de revues de conformité. |

## Phase H — Architecture Change Management

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| H-01 | Le traitement des changements est documenté | Livrable | Alerte | La phase H dit comment un changement est évalué : simple mise à jour, ou nouveau cycle ADM. |
| H-02 | Les décisions d'architecture sont tracées | Livrable | Info | Garder la trace des décisions (ADR, Governance Log) permet d'évaluer un changement sans tout redécouvrir. |

## Requirements Management

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| RM-01 | Les exigences sont modélisées | Présence | Bloquant | La gestion des exigences est au centre de l'ADM : chaque phase en consomme et en produit. |
| RM-02 | Chaque exigence est réalisée par un élément de l'architecture | Traçabilité | Bloquant | Une exigence que rien ne réalise ne peut pas être vérifiée en phase G. |
| RM-03 | Chaque exigence a une origine (objectif, principe ou partie prenante) | Traçabilité | Alerte | Sans origine, on ne sait pas qui peut arbitrer ou abandonner l'exigence. |

## Qualité du modèle

| Règle | Contrôle | Type | Sévérité | Pourquoi |
| --- | --- | --- | --- | --- |
| Q-01 | Chaque élément apparaît dans au moins une vue | Qualité | Info | Un élément présent dans aucune vue n'est vu par aucune partie prenante ; c'est souvent un oubli ou un doublon. |
