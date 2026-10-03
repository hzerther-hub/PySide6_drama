---
name: fight-cinematography
description: Manuel des mouvements de caméra de combat à grande vitesse — formules de position de caméra, annotations de vitesse et écriture des prompts pour les segments de combat / poursuite / temps fort
---

# Manuel des mouvements de caméra de combat à grande vitesse (réservé aux segments de combat / d'action à grande vitesse)

## Quand l'activer (détection automatique)

Lorsqu'un segment ou un sous-plan à l'intérieur d'un segment comporte des actions à grande vitesse telles que **combat, charge, poursuite, esquive-contre, coup de pied sauté, explosion de coup puissant, projection au sol par l'impact**, choisissez les mouvements de caméra dans les « formules de position de caméra » et les « annotations de vitesse » du présent manuel, en priorité sur le vocabulaire de mouvements de base ; les segments de dialogue, de préparation et de transition n'utilisent pas ce manuel.

La logique centrale tient en deux mots : **rapidité** et **anticipation** — fabriquer la vitesse, l'amplifier. Le mouvement de caméra sert trois objectifs :
1. Permettre au spectateur de lire la trajectoire de l'action
2. Renforcer la force d'impact dans la direction de l'attaque
3. Fabriquer la sensation de pression par la vitesse de la caméra

## Formules de position de caméra (10)

Chaque formule = combinaison position / mouvement + techniques applicables + écriture du prompt (l'écriture peut s'insérer directement au début du 【镜头N】 du `description`) :

| # | Formule | Techniques applicables | Écriture du prompt |
|---|---|---|---|
| 1 | Choc au point de départ : position basse + avance de caméra rapide | Coup de poing puissant, charge, premier échange | Position basse à 0.5 mètre, la caméra monte en avance rapide du bas vers le haut, capturant la poussière soulevée par la collision à grande vitesse des deux adversaires et le volume de l'onde de choc, l'angle LOW renforce la sensation de pression |
| 2 | Suivi latéral : caméra orbitale + changement de netteté | Combos, transitions attaque-défense, échanges dynamiques | ORBIT en demi-encerclement depuis l'arrière de l'attaquant, netteté verrouillée sur les mèches et le bas du vêtement du frappé, changement de netteté à l'instant de l'impact |
| 3 | Suivi au ras du sol : vue au ras du sol + suivi en position basse | Coup de pied balayé, roulade au sol, actions au niveau bas | La caméra, au ras du sol et en angle bas, suit le mouvement des jambes en balayage, les débris du sol fusillent face à l'objectif |
| 4 | Poursuite aérienne : position basse en contre-plongée + panoramique vertical rapide | Coup de pied sauté, coup circulaire, série de coups en l'air | Position basse en contre-plongée, TILT UP panoramique vertical rapide suivant le personnage dans son envol, en insistant sur la sensation de suspension |
| 5 | Instant de l'impact : arrêt brutal + légère vibration | Coup porté, temps fort | Gros plan sur l'instant de l'impact, image floutée à grande vitesse pendant 0.15 seconde, rémanence sur la partie touchée, léger rebond-vibration de la caméra |
| 6 | Projection par l'impact : recul rapide + poursuite | Projection au sol par coup puissant, refoulement | La caméra recule rapidement, en poursuite le long de la traînée de projection du personnage, l'arrière-plan se déchire en profondeur |
| 7 | Au plus près : vue de suivi + avancée DOLLY | Rafales de coups, séquences combinées | DOLLY en avancée horizontale, caméra au plus près des deux combattants enlacés, pour faire ressentir au spectateur la pression du vent des poings |
| 8 | Esquive-contre : avance inversée + changement de netteté | Esquive, défense-contre | La caméra part derrière l'attaquant en avance rapide, PAN fouetté latéral vers la direction du contre, PUSH avance rapide sur le geste du contre, netteté transférée en un instant de l'attaquant au contre-attaquant |
| 9 | Contre en contre-plongée : contre-plongée + recul rapide | Contre montant d'en bas, frappe aérienne | Départ en angle bas en contre-plongée, recul rapide accompagnant l'envol du personnage, le gros plan en contre-plongée s'ouvre en un instant sur un plan d'ensemble aérien |
| 10 | Fixation de fin de technique : avance lente en plan rapproché + recul lent | Fin de technique, pose, préparation du coup suivant | MCU plan moyen-rapproché en avance lente figeant la posture du personnage, puis PULL recul lent floutant l'arrière-plan, en conservant la tension de l'instant qui précède l'explosion du coup suivant |

## Annotations de vitesse (4, à superposer aux formules de position)

| Annotation | Utilisée pour | Effet | Écriture |
|---|---|---|---|
| Swift suivi rapide | Charge, irruption, poursuite, déplacement au corps à corps | Tension, sensation de vitesse, rythme soutenu | Avance-recul rapide en plan moyen ; les éléments de premier plan défilent rapidement, l'arrière-plan gagne un flou de mouvement horizontal |
| Whip panoramique fouetté | Demi-tour, esquive, instant de l'impact, changement brusque de direction | Soudaineté, sensation d'explosion | WHIP balaie à l'instant du contact avec la cible, netteté basculant immédiatement sur le frappé |
| Gentle recul lent | Fin de domination, retombée de la poussière, présentation du champ de bataille | Tension de la clôture | La caméra part du point le plus intense du conflit et recule lentement, netteté verrouillée sur le personnage, le champ de bataille en arrière-plan se déploie progressivement |
| Shock secousse | Coups puissants, explosions, fracas, effondrements | Choc en profondeur | À l'instant de l'impact, shake de la caméra pendant 0.3 seconde, image vibrant légèrement, les graviers du sol éclatent dans la direction de l'onde de choc |

## Règles d'écriture (raccord avec les champs du storyboard)

- `movement` : choisissez dans les tableaux ci-dessus un nom de formule ou une combinaison (par ex. « poursuite aérienne (position basse en contre-plongée + panoramique vertical rapide) »), un mouvement principal par sous-plan
- Dans le 【镜头N】 du `description` : écrivez en tête de sous-plan l'instruction de plan complète = **position / angle + type de mouvement + adverbe de vitesse + échelle de plan** ; les valeurs numériques (0.5 mètre, 0.15 seconde, 0.3 seconde) se conservent telles quelles — le video-prompt déploie le description segment par segment, et une valeur perdue est une sensation de vitesse perdue
- Les adverbes de vitesse doivent être précis : rapide / vitesse constante / lent / d'abord rapide puis lent ; interdiction de n'écrire que « travelling avant » ou « suivi »
- Un mouvement de caméra par segment, continu à l'intérieur du segment ; les segments de combat autorisent des changements de formule en coupe franche entre sous-plans, les points de coupe s'alignant sur les 【镜头N】
- **Alterner rapide et lent** : après 2-3 sous-plans rapides consécutifs, insérez un Gentle recul lent ou une fixation d'impact comme respiration, avant de repartir vers l'explosion suivante ; tout le segment en rapide se noierait dans un flou uniforme, tout en lent perdrait la pression
- Le bullet time / le ralenti restent des figures d'accent, dans la limite de 1-2 occurrences par épisode imposée par les normes de base, réservés à l'instant de l'impact ou à la fixation de fin de technique

## Modèles universels (à appliquer directement)

- **Départ à grande vitesse** : formule 1 (avance rapide en position basse) + Swift
- **Segment de combos** : formule 7 (au plus près en DOLLY) ↔ formule 2 (ORBIT avec changement de netteté), coupes franches entre sous-plans
- **Esquive-contre** : formule 8 (avance inversée avec changement de netteté) + Whip
- **Explosion de coup puissant** : formule 5 (flou de 0.15 seconde à l'impact) + Shock (shake de 0.3 seconde) → formule 6 (recul rapide sur la traînée)
- **Fixation de fin de technique** : formule 10 (MCU avance lente → Gentle recul lent), pour préparer la vague suivante

## Résumé en une phrase

L'essence du mouvement de caméra de combat est « **toujours en mouvement** » — transmettre au spectateur la sensation de vitesse et de pression par le mouvement de la caméra, en alternant vitesse extrême et arrêts brefs, de sorte que les intervalles entre techniques portent la préparation et le raccord.
