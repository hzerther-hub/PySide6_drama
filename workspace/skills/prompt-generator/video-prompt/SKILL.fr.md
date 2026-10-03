---
name: video-prompt
description: Norme du prompt vidéo — génère à partir du contenu d'un segment de storyboard un prompt de génération vidéo découpé en plages temporelles, avec coupes autorisées à l'intérieur d'un segment
---

# Prompt vidéo (segment de storyboard → video_prompt)

À partir du description d'un seul segment de storyboard (contenant la structure de sous-plans 【镜头N】 et les répliques / narrations), de atmosphere et de duration, générez le `video_prompt` qui pilotera la génération vidéo par IA. **Un segment de storyboard = une vidéo de 8-15 secondes, avec coupes autorisées à l'intérieur** : des segments consécutifs peuvent être des plans différents (changement d'échelle de plan / d'angle / de sujet), reliés par des coupes franches ; mais l'ensemble **ne change jamais de scène** et ne recourt pas aux flashbacks.

## Format

La **première ligne du `video_prompt` est l'en-tête d'information** : présentez d'abord quels personnages et quelle scène apparaissent dans cette vidéo, puis enchaînez avec les plages temporelles. Les personnages et les scènes sont toujours référencés avec @ (lors de la génération, ils sont remplacés par les marqueurs d'images de référence correspondants, afin que le modèle vidéo identifie d'abord « qui » et « où »).

```
Personnages présents : @Lucas, @Léa ; scène : @Café.
0-3 s : @Café, plan rapproché, la caméra ondule légèrement comme une respiration et avance lentement vers @Lucas ; tête baissée sur son téléphone, il tambourine nerveusement des doigts sur la table.
3-6 s : coupe au plan d'ensemble de l'entrée ; la sonnette retentit, @Léa pousse la porte et entre, emportant avec elle une bouffée d'air froid.
6-9 s : retour au plan moyen ; @Léa s'avance vers Lucas en souriant et vient s'asseoir, Lucas dit : « Tu es enfin là. »
```

Règles de l'en-tête :
- Ne listez que les personnages réellement présents dans ce segment de storyboard et la scène qui lui est liée ; n'inscrivez pas les absents
- Lorsqu'un accessoire apparaît de façon notable, vous pouvez l'ajouter à l'en-tête (par ex. ` ; accessoire : @Lettre`)
- L'en-tête occupe sa propre ligne, se termine par un point, suivi des plages temporelles

Découpez en segments de 3 secondes, chaque segment sur sa propre ligne séparée par des sauts de ligne, avec des plages temporelles continues et juxtaposées (ni chevauchement, ni trou).

## Correspondance avec la description du storyboard

Le `description` est la source de contenu unique du video_prompt (images, actions, répliques et narrations s'y trouvent tous). Règles de conversion :

- Chaque `【镜头N】` du `description` correspond à **1-2 segments continus de 3 secondes**, dans le même ordre, sans omission, sans fusion, sans ajout de sous-plan
- Les répliques / narrations sont extraites des entrées « NomDuPersonnage dit : « … » » / « Narration : … » contenues dans le `【镜头N】` correspondant, puis affectées aux segments mappés sur ce sous-plan ; **n'inventez pas de nouvelles répliques au-delà du description**
- Les actions à l'image font foi d'après le `description` ; `atmosphere` sert uniquement à compléter la lumière, la tonalité et l'ambiance de chaque segment

## Structure interne d'un segment

Organisez le contenu de chaque segment dans cet ordre (les rubriques sans contenu peuvent être omises, mais l'action / l'image est obligatoire) :

**Plage de temps + @référence de scène + échelle de plan / mouvement de caméra + @référence de personnage + action principale · expression + dialogue / narration + ambiance et lumière**

- **Le premier segment doit établir l'espace** : scène + position de caméra + position et état des personnages, pour que le spectateur sache d'un coup d'œil où l'on est et qui regarder
- **Coupe** : le segment qui suit une coupe commence par un mot de liaison tel que « coupe vers / retour sur », et redonne l'échelle de plan et le sujet ; les points de coupe doivent s'aligner sur la structure `【镜头N】` du `description` du storyboard
- **Échelle de plan / mouvement de caméra (règle dure)** : chaque segment doit énoncer à la fois **l'échelle de plan** (plan rapproché / moyen / d'ensemble / gros plan) et **une instruction de mouvement de caméra** ; le mouvement est continu à l'intérieur d'un même sous-plan et peut changer après une coupe. Écriture = « échelle de départ + type de mouvement + vitesse / rythme », par ex. « avance lente et régulière du plan moyen jusqu'au gros plan du visage », « déplacement latéral synchronisé avec le personnage, parallaxe de fond en mouvement ». Interdiction de réduire tout un segment à un « plan fixe » sans information de mouvement — la caméra doit « bouger » (translation, zoom, suivi, ondulation respiratoire comptent tous), afin d'éviter les images figées façon diaporama. Le vocabulaire des mouvements figure plus bas dans « Normes de mouvement de caméra »
- **Action** : une action principale par segment, avec des verbes concrets et visibles (marcher, se retourner, lever la tête, serrer, marquer un arrêt)
- **Toute émotion devient description visible** : pas de termes abstraits comme « il est très triste / l'ambiance est tendue » ; écrivez « il baisse la tête, ses doigts serrent le rebord du gobelet, sa respiration s'alourdit »
- **Dialogue / narration** : écrivez « NomDuPersonnage dit : « réplique » », et la narration « Narration : contenu » ; une longue réplique impossible à dire en 3 secondes se répartit sur plusieurs segments ; un segment sans dialogue peut porter un son d'ambiance / d'action (par ex. « le rugissement des machines ne cesse pas »)

## Règles de référence

- `@NomDeScene` — référence de scène ; le nom doit correspondre exactement au lieu figurant dans la liste des scènes
- `@NomDePersonnage` — référence de personnage ; le nom doit correspondre exactement au nom figurant dans la liste des personnages
- `@NomDAccessoire` — référence d'accessoire ; le nom doit correspondre exactement au nom figurant dans la liste des accessoires ; référencez un accessoire lorsqu'il est nettement visible à l'image, utilisé ou montré en gros plan
- Lors de la génération, chaque `@nom` est automatiquement remplacé par le marqueur d'image de référence correspondant (par ex. `@Lucas` → `@Image1Lucas`), les noms doivent donc correspondre exactement — pas d'abréviation ni de symbole supplémentaire
- **Chaque segment doit compter au moins une référence @ pour ancrer l'image** ; tout segment où un personnage apparaît doit faire @ à ce personnage ; ne référencez que les scènes / personnages / accessoires déjà liés à ce segment de storyboard

## Règles de chronologie

- Nombre de segments = durée du segment de storyboard ÷ 3 secondes (arrondi au supérieur) ; la somme des plages temporelles des segments doit égaler exactement la durée totale du segment
- Rythme du contenu : le premier segment installe → les segments médians font progresser l'action / le conflit → le dernier segment se pose sur un résultat ou un point émotionnel

## Normes de mouvement de caméra

Chaque plage temporelle porte un mouvement de caméra, choisi dans le vocabulaire ci-dessous et cohérent avec l'intention de mouvement des champs `description` / `movement` du storyboard (ce que le description écrit comme mouvement de caméra, le video_prompt le déploie tel quel ; lorsque le description n'en écrit pas, choisissez librement le plus adapté au contenu visuel) :

- **Narration de base** : travelling avant lent (plan moyen → gros plan, vitesse constante, arrière-plan qui se floute progressivement), travelling arrière de révélation (gros plan → plan d'ensemble, d'abord rapide puis lent), travelling latéral de suivi (déplacement synchronisé avec le personnage, parallaxe de fond en mouvement), travelling vertical en plongée (montée / descente verticale révélant l'espace), orbite en arc (90-180 degrés autour du personnage), marche à la première personne (hauteur du regard, ondulation légère comme la respiration)
- **Émotion et atmosphère** : souffle caméra à l'épaule (tremblement léger, accentué après l'effort), angle voyeur (obstruction en premier plan par une entrefîte de porte ou de fenêtre), pouls cardiaque (avant-arrière synchronisé au rythme émotionnel, avance lente au calme / avance rapide en tension), épousement respiratoire (micro-avancée à l'inspiration, recul lent à l'expiration)
- **Détails psychologiques** : mise au point du regard (avancée lente vers l'objet regardé, transfert de netteté), terreur tremblante (vibration fine irrégulière), orbite tendre (orbite lente à petit angle, netteté verrouillée sur le visage), filature à grande vitesse (suivi serré avec flou de mouvement), tissage de combat (alternance rapide entre les deux adversaires), piqué plongeant (descente en piqué depuis les hauteurs, micro-secousse à l'atterrissage)
- **Combats à grande vitesse** : uniquement lorsque le `description` du storyboard écrit explicitement un mouvement de caméra de combat, déployez-le à l'identique (position de caméra, vitesse, valeurs — rien ne doit se perdre) : avance rapide en position basse, suivi au ras du sol, panoramique vertical rapide vers le haut, suivi au plus près, avance inversée avec changement de netteté, recul rapide sur la traînée, flou à grande vitesse de 0.15 seconde à l'instant de l'impact, secousse shake de 0.3 seconde
- **Angles spéciaux** : contre-plongée extrême, angle hollandais incliné, plan rapproché par-dessus l'épaule, plan subjectif
- **Transitions rythmiques** : panoramique fouetté (direction du fouetté alignée sur la direction du mouvement du segment suivant), transition par obstruction (objet de premier plan qui balaie le cadre au moment de la coupe), arrêt sur image après freinage (décélération jusqu'à l'arrêt figé, réservé aux segments de temps fort)

Exigences de rédaction :
- Le mouvement de caméra s'écrit lié à l'échelle de plan et à la vitesse : « du plan d'ensemble, avance lente jusqu'au plan moyen », jamais un simple « travelling avant »
- Adverbes de vitesse précis : vitesse constante / lent / rapide / d'abord rapide puis lent / du lent au rapide
- Un mouvement de caméra par segment ; continu à l'intérieur du segment, il ne change qu'aux points de coupe
- Bullet time / gros plan au ralenti / fisheye / miniature sont des figures d'accent : à n'employer que lorsque le `description` du storyboard les écrit explicitement, 1-2 occurrences au maximum par épisode
- Le tremblement à l'épaule et l'ondulation respiratoire sont des « micro-mouvements » : utilisables dans les segments que l'on aurait écrits en caméra fixe, en remplacement de l'immobilité totale

## Interdictions

- Changement de scène, flashbacks (un segment se déroule dans une seule scène)
- Références à des scènes / noms de personnages hors des listes
- Description psychologique abstraite, métaphore littéraire (le modèle ne reconnaît que des images visibles)
- Jeu surjoué : n'écrivez ni cris, ni hurlements, ni clameur, ni sanglots à voix haute ; la frayeur s'écrit en micro-réactions (se figer, pupilles qui se resserrent, inspiration brutale, demi-pas en arrière), les dialogues restent sur un ton et à un volume quotidiens (quand l'intrigue extrême exige réellement une explosion, écrivez explicitement « explosion émotionnelle » dans le segment concerné pour la couvrir)
- Ralenti et statisme traînant : par défaut, pas de ralenti ni de longues immobilités contemplatives ; exception : les sous-plans de temps fort où le `description` du storyboard écrit explicitement bullet time / gros plan au ralenti / arrêt sur image, à employer conformément au description. Chaque segment doit conserver un mouvement de caméra visible ou une progression d'action ; le « plan purement statique » n'est pas admis
- Langue non conforme à la consigne de langue de la session

## Enregistrement

Appelez `update_storyboard` pour ne mettre à jour que le champ `video_prompt` de ce segment de storyboard, sans modifier les autres champs, sans redécouper tout l'épisode. La plateforme ajoute automatiquement des garde-fous de jeu et de rythme lors des requêtes de génération réelles ; inutile de réécrire ces exigences dans le prompt.
