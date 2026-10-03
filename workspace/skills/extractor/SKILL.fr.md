---
name: extractor
description: Normes et méthodes d'extraction des personnages, scènes et accessoires
---

# Guide d'extraction des personnages, scènes et accessoires

## Normes d'extraction des personnages

Champs des personnages extraits (correspondance un à un avec les paramètres de l'outil `save_dedup_characters`) :
- **name** (obligatoire) : nom complet du personnage
- **role** : positionnement du personnage — protagoniste / second rôle / figurant
- **appearance** : description physique (300-500 caractères) — sexe, âge apparent, traits du visage, corpulence, prestance. **N'exportez pas séparément les traits de caractère du personnage ; convertissez-les en prestance et expressions extérieures fondues dans la description physique** (par ex. « tempérament glacial » s'écrira « regard glacial, expressions contenues, sourire rare »)
- **styling** : coiffure et costume — coiffure, vêtements, maquillage, accessoires, etc.
- **description** : histoire personnelle et relations entre personnages (complément facultatif)

## Normes d'extraction des scènes

Champs des scènes extraites (correspondance un à un avec les paramètres de l'outil `save_dedup_scenes`) :
- **location** (obligatoire) : nom précis du lieu
- **time** : plage horaire (par ex. journée / crépuscule / pleine nuit) ; un même lieu à une autre plage horaire compte comme une nouvelle scène
- **prompt** : description de la scène — espace, aménagement, texture d'époque, éléments visuels clés (décor pur, sans personnage)
- **lighting** : lumière de la scène — sources, tonalité, contrastes clair-obscur, atmosphère

## Normes d'extraction des accessoires

**Principe fondamental : mieux vaut extraire trop peu que trop.** Les accessoires sont des actifs coûteux servant à générer des visuels produit sur fond blanc, référencés par les gros plans vidéo ; seuls les accessoires déterminants pour l'intrigue méritent d'être extraits. Un épisode compte généralement **0-3** accessoires clés ; au-delà de 3, classez-les par importance dramatique et ne conservez que les 3 premiers.

Les deux conditions suivantes doivent être **réunies** — aucune n'est facultative :
1. **Piloter directement l'intrigue** : l'apparition, la remise, la dégradation ou la découverte de l'objet déclenche un tournant de l'histoire (par ex. une arme du crime, un gage, un document clé, un cadeau de fiançailles, une preuve décisive).
2. **Mériter une image dédiée** : les storyboards ultérieurs lui consacreront des gros plans ou le feront réapparaître, ce qui exige une apparence fixe.

**Les trois questions de contrôle** (posez-les-vous et répondez pour chaque accessoire candidat ; un seul « non » suffit à l'écarter) :
- ① L'intrigue tient-elle toujours sans lui ? → Si oui, **ne l'extrayez pas** (ce n'est qu'un élément de décor déguisé en accessoire)
- ② N'est-ce qu'un objet du quotidien utilisé incidemment par le personnage (téléphone, baguettes, gobelet, cigarettes, parapluie) ? → Si oui, **ne l'extrayez pas**
- ③ Fait-il partie de l'aménagement de la scène (tables et chaises, lampes, portes et fenêtres, tableaux, vaisselle) ? → Si oui, **ne l'extrayez pas** (cela relève de la description de scène)

**Ce qui ne compte typiquement pas comme accessoire** : les objets ordinaires utilisés incidemment sans effet sur le cours de l'intrigue ; l'aménagement et le mobilier de la scène ; les objets mentionnés une seule fois puis jamais plus ; l'habituel vestimentaire d'un personnage (à classer dans son styling).

Si aucun accessoire ne remplit les conditions, **n'en extrayez pas de force** — passez simplement un tableau vide lors de l'appel de `save_dedup_props`.

Champs des accessoires extraits (correspondance un à un avec les paramètres de l'outil `save_dedup_props`) :
- **name** (obligatoire) : nom de l'accessoire
- **type** : catégorie — quotidien / arme / transport / décoration / document, etc.
- **description** : apparence de l'objet — décrivez uniquement son aspect physique propre (matière, couleur, forme, taille, degré de vétusté, traces d'usure, etc.) ; n'évoquez ni son rôle dans l'intrigue, ni son lien avec des personnages ou d'autres éléments

Les accessoires **n'exigent pas de prompt d'image** — le prompt final d'un accessoire est généré spécifiquement par l'Agent de génération de prompts avant la génération d'image (norme du visuel produit sur fond blanc).

## Étapes d'utilisation

1. Appelez `read_script_for_extraction` pour lire le scénario de l'épisode en cours
2. Appelez `read_existing_characters` pour consulter les personnages existants du projet et ceux déjà associés à l'épisode en cours
3. Appelez `read_existing_scenes` pour consulter les scènes existantes du projet et celles déjà associées à l'épisode en cours
4. Appelez `read_existing_props` pour consulter les accessoires existants du projet et ceux déjà associés à l'épisode en cours
5. N'extrayez que les personnages, scènes et accessoires réellement concernés par l'épisode en cours
6. Appelez `save_dedup_characters` pour enregistrer les personnages et les associer automatiquement à l'épisode en cours
7. Appelez `save_dedup_scenes` pour enregistrer les scènes et les associer automatiquement à l'épisode en cours
8. Appelez `save_dedup_props` pour enregistrer les accessoires et les associer automatiquement à l'épisode en cours

## Règles de l'épisode en cours

- L'objectif est de compléter les personnages, scènes et accessoires nécessaires à « l'épisode en cours », pas de rescanner tout le projet
- Si un élément existe déjà dans le projet sans être associé à l'épisode en cours, réutilisez-le et associez-le à cet épisode
- Règles de déduplication : les personnages / accessoires sont appariés exactement par nom, les scènes par correspondance exacte sur 【lieu + plage horaire】 ; en cas de correspondance, privilégiez la réutilisation, ne créez pas de doublons
- Déduplication par noms proches : lorsqu'un nom porte un qualificatif entre parenthèses ou un alias, comparez la partie principale située avant les parenthèses (par ex. « Camille (protagoniste) » et « Camille » désignent le même personnage / accessoire — réutilisez l'entrée existante) ; le normalized_name renvoyé par read_existing_characters / read_existing_props est le nom normalisé, et normalized_location fonctionne de même pour les scènes — basez-vous sur ces valeurs pour statuer
