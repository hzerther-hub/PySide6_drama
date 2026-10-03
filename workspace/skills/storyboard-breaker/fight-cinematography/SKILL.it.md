---
name: fight-cinematography
description: Manuale dei movimenti di macchina ad alta velocità per i combattimenti — formule di posizione macchina, annotazioni di velocità e regole di scrittura del prompt per i segmenti di lotta/inseguimento/clou
---

# Manuale dei movimenti di macchina per combattimenti ad alta velocità (dedicato ai segmenti di lotta/azioni ad alta velocità)

## Quando attivarlo (giudizio automatico)

Quando il segmento o le sotto-inquadrature al suo interno presentano azioni ad alta velocità come **combattimenti, cariche, inseguimenti, schivate e contrattacchi, calci volanti, esplosioni di colpi potenti, scaraventate in volo**, i movimenti di macchina si scelgono tra le «formule di posizione» e le «annotazioni di velocità» di questo manuale, in precedenza rispetto al lessico di base dei movimenti di macchina; i segmenti di dialogo, di preparazione e di passaggio non usano questo manuale.

La logica di fondo è solo duplice: **velocità** e **anticipazione** — creare la velocità, amplificarla. I movimenti di macchina servono a tre scopi:
1. Far vedere allo spettatore la traiettoria dell'azione
2. Rafforzare la forza d'impatto della direzione dell'attacco
3. Creare una sensazione di oppressione con la velocità della macchina

## Formule di posizione (10)

Ogni formula ＝ combinazione posizione/movimento ＋ mosse a cui si applica ＋ scrittura del prompt (la scrittura può essere inserita direttamente all'inizio della `【镜头N】` della `description`):

| # | Formula | Mosse a cui si applica | Scrittura del prompt |
|---|---|---|---|
| 1 | Scontro di partenza: posizione bassa della macchina + carrello in avanti velocissimo | Pugni potentissimi, cariche, primo scontro | Posizione della macchina a bassa angolazione a 0.5 metri, la macchina esegue dal basso verso l'alto un carrello in avanti velocissimo, cogliendo la polvere sollevata dalla collisione ad alta velocità dei due e il volume dell'onda d'urto; l'angolazione LOW rafforza la sensazione di oppressione |
| 2 | Inseguimento laterale: ripresa orbitale + cambio di fuoco | Combo, inversioni di attacco/difesa, scambi dinamici | ORBIT: orbita che semi-accerchia l'attaccante da dietro, fuoco bloccato su ciocche di capelli e orli degli abiti del colpito, cambio di fuoco nell'istante dell'impatto |
| 3 | Inseguimento a ras di terra: vista a ras di terra + inseguimento con macchina in posizione bassa | Gamba a spazzata, rotolamenti a terra, azioni basse | La macchina, a ras di terra e in bassa angolazione, segue spazzando l'azione delle gambe; i detriti del suolo sfrecciano di fronte all'obiettivo |
| 4 | Inseguimento in volo: bassa angolazione dal basso + tilt-up velocissimo | Calci volanti, calci rotanti, sequenze di calci a mezz'aria | Bassa angolazione dal basso; TILT UP velocissimo che segue il personaggio in volo, enfatizzando la sensazione di sospensione |
| 5 | Istante dell'impatto: arresto su fermo + lieve tremolio | Il colpo che va a segno, momento clou | Primissimo piano nell'istante dell'impatto, immagine con blur ad alta velocità per 0.15 secondi, immagine residua sulla parte colpita, lieve rimbalzo e vibrazione della macchina |
| 6 | Scaraventato via: arretramento velocissimo + inseguimento | Colpo potente che manda in volo, respingimento | La macchina arretra velocissimo, inseguendo la direzione della scia lungo cui il personaggio è stato scaraventato; lo sfondo si strappa in profondità |
| 7 | Vicinanza estrema: vista di inseguimento + avanzamento DOLLY | Raffiche di pugni, colpi in combinazione | DOLLY in avanzamento orizzontale, macchina spinta a distanza estrema dai due che lottano, facendo sentire allo spettatore l'oppressione del vento dei pugni |
| 8 | Schivata e contrattacco: carrello inverso + cambio di fuoco | Schivate, contrattacchi dalla difesa | La macchina avanza velocissimo da dietro le spalle dell'attaccante, PAN sfilata laterale verso la direzione del contrattacco, PUSH carrello in avanti velocissimo sull'azione del contrattacco, il fuoco passa in un istante dall'attaccante a chi contrattacca |
| 9 | Contrattacco dal basso: angolazione dal basso + arretramento velocissimo | Contrattacco dal basso verso l'alto, colpo in volo | Si parte con bassa angolazione dal basso; mentre il personaggio si lancia in aria la macchina arretra velocissimo: dal primissimo piano dal basso si apre in un istante su un piano generale aereo |
| 10 | Chiusura della mossa su fermo: lento carrello in avanti sul primo piano + lento arretramento | Chiusura della mossa, posa di entrata in scena, caricamento del colpo successivo | MCU piano medio-corto con lento carrello in avanti che fissa la posa del personaggio; quindi PULL lento arretramento che sfoca lo sfondo, conservando la tensione dell'istante prima dell'esplosione della mossa successiva |

## Annotazioni di velocità (4, da sovrapporre alle formule di posizione)

| Annotazione | Si usa per | Effetto | Scrittura |
|---|---|---|---|
| Swift inseguimento rapido | Cariche, affondi, inseguimenti, movimento a contatto del corpo | Tensione, senso di velocità, ritmo marcato | Carrelli avanti/indietro velocissimi sul piano medio; gli elementi in primo piano sfrecciano via veloci, lo sfondo mostra motion blur orizzontale |
| Whip sfilata | Girarsi, schivate, istante dell'impatto, cambi improvvisi di direzione | Improvvisità, esplosività | WHIP sfreccia nell'istante del contatto con il bersaglio, fuoco commutato all'istante sul colpito |
| Gentle lento arretramento | Fine della dominazione, polvere che si assesta, presentazione dell'assetto del campo di battaglia | Tensione dopo la chiusura | La macchina arretra lentamente dal punto più violento del conflitto, fuoco bloccato sul personaggio, il campo di battaglia sullo sfondo si apre gradualmente |
| Shock scossa d'urto | Colpi potenti, esplosioni, frantumazioni, crolli | Impatto profondo | Nell'istante dell'impatto la macchina shake per 0.3 secondi, lieve tremolio dell'immagine, il pietrisco a terra si spalanca lungo la direzione dell'onda d'urto |

## Regole di scrittura (aggancio ai campi dello storyboard)

- `movement`: scegli dalla tabella il nome della formula o una combinazione (es. «Inseguimento in volo (bassa angolazione dal basso + tilt-up velocissimo)»), un movimento di macchina principale per sotto-inquadratura
- Nella `【镜头N】` della `description`: all'inizio della sotto-inquadratura si scrive l'istruzione completa dell'inquadratura ＝ **posizione/angolazione ＋ tipo di movimento ＋ avverbio di velocità ＋ ampiezza**; i valori numerici (0.5 metri, 0.15 secondi, 0.3 secondi) vanno conservati alla lettera — il video-prompt si sviluppa segmento per segmento sulla description, e perdere i valori significa perdere il senso di velocità
- Gli avverbi di velocità devono essere specifici: velocissimo/a velocità costante/lento/prima veloce poi lento; vietato scrivere solo «carrello in avanti» «inseguimento»
- Un movimento di macchina per segmento, continuo all'interno del segmento; nei segmenti di combattimento è ammesso passare con hard cut da una formula all'altra tra sotto-inquadrature, con i punti di taglio allineati alla `【镜头N】`
- **Combinare veloce e lento**: dopo 2-3 sotto-inquadrature velocissime di fila, inserisci un Gentle lento arretramento o un arresto su fermo all'impatto come respiro, prima di entrare nell'esplosione successiva; un segmento tutto velocissimo si riduce a una confusa macchia, uno tutto lento perde la sensazione di oppressione
- Bullet time/slow motion restano trucchi di rilievo: rispettano il tetto di 1-2 per episodio della regola di base e si usano solo nell'istante dell'impatto o nella chiusura della mossa su fermo

## Modello universale (da applicare direttamente)

- **Apertura ad alta velocità**: formula 1 (carrello basso e veloce) ＋ Swift
- **Segmento combo**: formula 7 (vicinanza estrema DOLLY) ↔ formula 2 (ORBIT cambio di fuoco), hard cut tra le sotto-inquadrature
- **Schivata e contrattacco**: formula 8 (carrello inverso con cambio di fuoco) ＋ Whip
- **Esplosione di colpo potente**: formula 5 (blur di 0.15 secondi all'impatto) ＋ Shock (shake di 0.3 secondi) → formula 6 (arretramento veloce sulla scia)
- **Chiusura della mossa su fermo**: formula 10 (lento carrello in avanti MCU → Gentle lento arretramento), per caricare la mossa successiva

## Riassunto in una frase

L'essenza dei movimenti di macchina da combattimento è «**muoversi sempre**» — trasmettere allo spettatore il senso di velocità e l'oppressione attraverso il movimento della macchina, alternando la corsa veloce ai brevi fermi d'immagine, e completando negli interstizi tra una mossa e l'altra la carica e il raccordo.
