---
name: video-prompt
description: Regole del prompt video — genera un prompt per la generazione video segmentato nel tempo a partire dal contenuto del segmento storyboard, con cambi di inquadratura ammessi all'interno del segmento
---

# Prompt video (segmento storyboard → video_prompt)

A partire da description (con la struttura di sotto-inquadrature 【镜头N】 e battute/narrazione) / atmosphere / duration di un singolo segmento storyboard, genera il `video_prompt` che guida la generazione video dell'IA. **Un segmento storyboard = un video di 8-15 secondi, con cambi di inquadratura ammessi al suo interno**: tra segmenti consecutivi ci possono essere inquadrature diverse (cambio di ampiezza/angolazione/soggetto), raccordati con hard cut; ma per l'intero segmento **non si cambia mai scena** e non si usano flashback.

## Formato

La **prima riga del `video_prompt` è l'intestazione informativa**: prima presenta quali personaggi e quale scena compaiono nel video, poi seguono i segmenti temporali. Personaggi e scene sono sempre richiamati con @ (al momento della generazione vengono sostituiti dai corrispondenti marker di immagine di riferimento, così il modello video allinea subito «chi» e «dove»).

```
Personaggi presenti: @Marco, @Anna; Scena: @Caffè.
0-3s: @Caffè, primo piano, la macchina oscilla lievemente come un respiro e si avvicina lentamente a @Marco con un carrello in avanti; lui guarda il telefono a testa bassa, le dita tamburellano ripetutamente sul tavolo, espressione ansiosa.
3-6s: si passa al piano generale dell'ingresso; il campanello suona, @Anna spinge la porta ed entra portando una raffica di aria fredda.
6-9s: si torna al piano medio; @Anna si avvicina sorridendo e va a sedersi, Marco dice: "Finalmente sei arrivato."
```

Regole dell'intestazione:
- Elenca solo i personaggi che compaiono davvero in questo segmento storyboard e la scena collegata, non elencare chi non compare
- Quando un prop ha una presenza evidente, può essere aggiunto all'intestazione (es. `; Props: @Lettera`)
- L'intestazione sta su una riga a sé, termina con un punto, quindi seguono i segmenti temporali

Un segmento ogni 3 secondi, ogni segmento su una riga a sé separato dai ritorni a capo, con intervalli di tempo continui e consecutivi (nessuna sovrapposizione, nessun vuoto).

## Corrispondenza con la descrizione dello storyboard

`description` è l'unica fonte di contenuto del video_prompt (visuali, azioni, battute e narrazione sono tutte lì dentro); regole di conversione:

- Ogni `【镜头N】` della `description` corrisponde a **1-2 segmenti consecutivi da 3 secondi**, nello stesso ordine, senza omissioni, senza fusioni, senza aggiungere sotto-inquadrature
- Le battute/la narrazione si estraggono dai blocchi «NomePersonaggio dice: "…"» / «Narratore: …» contenuti nella corrispondente `【镜头N】` e si assegnano ai segmenti mappati su quella sotto-inquadratura; **non inventare battute nuove al di fuori della description**
- Le azioni in campo seguono la `description`; `atmosphere` serve solo ad arricchire la descrizione di luce, tonalità e atmosfera di ogni segmento

## Struttura interna al segmento

Organizza il contenuto di ogni segmento in quest'ordine (le voci senza contenuto possono essere omesse, ma azione/visuale sono obbligatorie):

**Intervallo di tempo ＋ riferimento @ della scena ＋ ampiezza/movimento di macchina ＋ riferimento @ del personaggio + azione principale·espressione ＋ battuta/narrazione ＋ atmosfera e luce**

- **Il primo segmento deve stabilire lo spazio**: scena + posizione macchina + posizione e stato dei personaggi, così che il pubblico capisca a colpo d'occhio dove siamo e chi guardare
- **Cambi di inquadratura**: apri i segmenti dopo il taglio con parole di raccordo tipo «si passa a/si torna a», e ridichiara ampiezza e soggetto; i punti di taglio devono allinearsi alla struttura `【镜头N】` della `description` dello storyboard
- **Ampiezza/movimento di macchina (regola rigida)**: ogni segmento deve indicare sia l'**ampiezza di inquadratura** (primo piano/piano medio/piano generale/primissimo piano) sia un'**istruzione di movimento di macchina**; il movimento di macchina è continuo all'interno di una singola sotto-inquadratura e può cambiare dopo un taglio. Si scrive come «ampiezza di partenza ＋ tipo di movimento ＋ velocità/ritmo», es. «lento carrello in avanti a velocità costante dal piano medio al primissimo piano del viso», «carrello laterale in sincrono con il personaggio, con parallasse scorrevole dello sfondo». Vietato lasciare un intero segmento su un nudo «macchina fissa» senza informazione di movimento — la macchina deve «muoversi» (traslazione, zoom, inseguimento, oscillazione da respiro vanno tutti bene), per evitare quadri fermi in stile PPT. Per il lessico dei movimenti vedi la sezione «Regole del movimento di macchina»
- **Azione**: un'azione principale per segmento, con verbi concreti e visibili (camminare, girarsi, alzare la testa, stringere, fermarsi)
- **Tutta l'emozione diventa descrizione visibile**: niente vocaboli astratti come «è molto triste/l'atmosfera è tesa», scrivi piuttosto «abbassa la testa, le dita stringono il bordo della tazza, il respiro si fa più pesante»
- **Battuta/narrazione**: le battute si scrivono «NomePersonaggio dice: "battuta"», la narrazione «Narratore: contenuto»; una battuta lunga che in 3 secondi non si riesce a pronunciare va spezzata su più segmenti; un segmento senza battute può riportare suoni d'ambiente/azioni (es. «le macchine ruggiscono senza sosta»)

## Regole dei riferimenti

- `@NomeScena` — riferimento alla scena; il nome deve coincidere esattamente con il luogo nell'elenco delle scene
- `@NomePersonaggio` — riferimento al personaggio; il nome deve coincidere esattamente con il nome nell'elenco dei personaggi
- `@NomeProp` — riferimento al prop; il nome deve coincidere esattamente con il nome nell'elenco dei props; richiama il prop quando è chiaramente visibile in campo, usato o mostrato in primissimo piano
- Al momento della generazione ogni `@nome` viene sostituito automaticamente dal corrispondente marker di immagine di riferimento (es. `@Marco` → `@Immagine1Marco`), quindi i nomi devono coincidere esattamente, senza abbreviazioni né simboli aggiuntivi
- **Ogni segmento deve avere almeno un riferimento @ che ancori l'inquadratura**; il segmento in cui compare un personaggio deve fare @ di quel personaggio; richiama solo scene/personaggi/props già collegati a questo segmento storyboard

## Regole della linea temporale

- Numero di segmenti = duration del segmento storyboard ÷ 3 secondi (arrotondato per eccesso); la somma degli intervalli di tempo dei segmenti deve essere pari alla durata totale del segmento
- Ritmo del contenuto: il primo segmento stabilisce → i segmenti intermedi fanno avanzare azione/conflitto → l'ultimo segmento approda al risultato o al punto emotivo

## Regole del movimento di macchina

Ogni intervallo di tempo deve avere un movimento di macchina, scelto dal lessico seguente e coerente con l'intento di movimento nei campi `description`/`movement` dello storyboard (ciò che la description indica viene sviluppato in quel senso; se non indica nulla, scegli liberamente ciò che calza meglio alle immagini):

- **Narrativa di base**: lento carrello in avanti (dal piano medio al primissimo piano, a velocità costante, sfondo che si sfoca progressivamente), arretramento di rivelazione (dal primissimo piano al piano generale, prima veloce poi lento), carrello laterale di inseguimento (in movimento con il personaggio, parallasse scorrevole dello sfondo), gru in salita/discesa (ascesa/discesa verticale che rivela lo spazio), orbita ad arco (90-180 gradi intorno al personaggio), camminata in soggettiva (altezza dello sguardo, lieve ondeggiamento come un respiro)
- **Emozione e atmosfera**: a mano ansimante (lieve tremolio che si accentua dopo il movimento), angolo voyeur (visione stretta con occlusione in primo piano), impulso cardiaco (carrelli avanti/indietro sincronizzati con il ritmo emotivo), sincronizzato col respiro (avanzamento all'inspirazione, arretramento all'espirazione)
- **Dettagli psicologici**: messa a fuoco sullo sguardo (lento avvicinamento all'oggetto osservato, spostamento del fuoco), tremore da paura (vibrazione fine irregolare), orbita delicata (orbita lenta a piccolo angolo con fuoco bloccato sul viso), inseguimento ad alta velocità (inseguimento stretto con motion blur), intreccio di combattimento (tagli rapidi che navigano tra i duellanti), picchiata in volo (picchiata dall'alto con scossa all'atterraggio)
- **Combattimenti ad alta velocità**: solo quando la `description` dello storyboard indica esplicitamente movimenti da combattimento, sviluppa fedelmente quanto scritto nella description (nessuna posizione, velocità o valore va perso): carrello in avanti basso velocissimo, inseguimento a ras di terra, tilt-up veloce, inseguimento a distanza estrema, carrello inverso con cambio di fuoco, arretramento veloce sulla scia, blur ad alta velocità di 0.15 secondi nell'istante dell'impatto, shake da shock di 0.3 secondi
- **Angolazioni speciali**: ripresa dal basso estrema, inclinazione olandese (Dutch angle), piano sopra la spalla, soggettiva
- **Ritmo e transizioni**: panoramica a frusta (la direzione della frusta coincide con la direzione del movimento del segmento successivo), transizione per occlusione (taglio nell'istante in cui un elemento in primo piano attraversa e copre l'inquadratura), arresto su fermo (rallentamento fino all'immagine congelata, solo per i segmenti clou)

Requisiti di scrittura:
- L'istruzione di movimento di macchina compare legata ad ampiezza e velocità: «dal piano generale lento avvicinamento al piano medio», non scrivere solo «carrello in avanti»
- Avverbi di velocità concreti: a velocità costante/lento/velocissimo/prima veloce poi lento/dal lento al veloce
- Un movimento di macchina per segmento; continuo all'interno del segmento, cambia solo nei punti di taglio
- Bullet time/primissimo piano in slow motion/fisheye/diorama in miniatura sono trucchi di rilievo: si usano solo quando la `description` dello storyboard li indica esplicitamente, al massimo 1-2 volte per episodio
- Il tremolio a mano e l'ondeggiamento da respiro sono «micro-movimenti»: possono sostituire la macchina completamente ferma nei segmenti che avresti scritto come fissi

## Divieti

- Cambi di scena, flashback (un segmento si svolge in una sola scena)
- Richiamare scene/nomi di personaggi al di fuori degli elenchi
- Descrizioni psicologiche astratte, metafore letterarie (il modello riconosce solo immagini visibili)
- Recitazione eccessiva: non scrivere urlo, strazio di urla, clamore, pianto a gran voce; la paura si scrive come micro-reazione (restare immobile, pupille che si stringono, respiro trattenuto, mezzo passo indietro), le battute con tono e volume quotidiani (quando la trama estrema lo richiede davvero, scrivi esplicitamente «esplosione emotiva» nel segmento, a copertura)
- Slow motion e rinvii con immagini ferme: per impostazione predefinita niente slow motion, niente sguardi immobili prolungati; eccezione: le sotto-inquadrature clou in cui la `description` dello storyboard indica esplicitamente bullet time/primissimo piano in slow motion/arresto su fermo possono usarli secondo la description. Ogni segmento deve comunque avere un movimento di macchina visibile o un'avanzazione d'azione; i «piani puramente fermi» non sono ammessi
- Lingua non conforme alla direttiva di lingua della sessione

## Salvataggio

Chiama `update_storyboard` per aggiornare solo il campo `video_prompt` di questo segmento storyboard, senza toccare alcun altro campo e senza ri-suddividere l'intero episodio. La piattaforma aggiungerà automaticamente le guardie di recitazione e ritmo alla richiesta di generazione effettiva; non serve riscrivere questi requisiti nel prompt.
