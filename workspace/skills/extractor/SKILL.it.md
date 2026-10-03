---
name: extractor
description: Regole e metodi per l'estrazione di personaggi, scene e props
---

# Guida all'estrazione di personaggi, scene e props

## Regole di estrazione dei personaggi

Campi del personaggio estratto (in corrispondenza biunivoca con i parametri dello strumento `save_dedup_characters`):
- **name** (obbligatorio): nome completo del personaggio
- **role**: ruolo del personaggio — protagonista / secondario / comparsa
- **appearance**: descrizione dell'aspetto (300-500 caratteri) — sesso, età percepita, tratti del viso, corporatura, presenza. **I tratti caratteriali del personaggio non vanno emessi a parte: vanno trasformati in portamento esteriore ed espressione, integrati nella descrizione dell'aspetto** (es. «carattere freddo e severo» va scritto come «sguardo glaciale, espressione controllata, raramente un sorriso»)
- **styling**: look — acconciatura, abbigliamento, trucco, accessori ecc.
- **description**: passato del personaggio e relazioni con gli altri (integrazione facoltativa)

## Regole di estrazione delle scene

Campi della scena estratta (in corrispondenza biunivoca con i parametri dello strumento `save_dedup_scenes`):
- **location** (obbligatorio): nome specifico del luogo
- **time**: fascia oraria (es. giorno/tramonto/notte fonda); lo stesso luogo in una fascia oraria diversa conta come nuova scena
- **prompt**: descrizione della scena — spazio, arredi, texture d'epoca, elementi visivi chiave (solo ambientazione, senza persone)
- **lighting**: luce della scena — sorgenti luminose, tonalità, contrasto chiaro/scuro, atmosfera

## Regole di estrazione dei props

**Principio cardine: meglio estrarne pochi che troppi.** I props sono risorse ad alto costo, usate per generare immagini prodotto su fondo bianco e richiamate nei primissimi piani video; solo i props decisivi per la trama meritano l'estrazione. Un episodio di norma ha **0-3** props chiave; se ce ne sono più di 3, ordinarli per importanza narrativa e conservarne solo i primi 3.

Devono essere soddisfatte **entrambe** le condizioni seguenti, senza eccezioni:
1. **Spinge direttamente la trama**: la comparsa, la consegna, il danneggiamento o il ritrovamento dell'oggetto innesca una svolta narrativa (es. l'arma del delitto, un pegno, un documento chiave, un regalo d'amore, una prova decisiva).
2. **Merita un'immagine dedicata**: gli storyboard successivi gli riserveranno primissimi piani o lo faranno ricomparire, quindi serve un aspetto fisso.

**Tre domande di verifica** (fai le domande e risponditi per ogni prop candidato; se anche una sola risposta è «no», scartalo):
- ① La trama regge comunque senza di lui? → Se regge, **non estrarlo** (è solo un oggetto di scena decorativo)
- ② È soltanto un oggetto quotidiano che il personaggio usa di fretta (telefono, bacchette, bicchiere, sigarette, ombrello)? → Se sì, **non estrarlo**
- ③ Fa parte degli arredi della scena (tavoli e sedie, lampade, porte e finestre, quadri appesi, stoviglie)? → Se sì, **non estrarlo** (questi elementi appartengono alla descrizione della scena)

**Casi tipici che NON sono props**: oggetti comuni usati di fretta senza alcun effetto sull'andamento della trama; arredi e mobilio della scena; oggetti menzionati una volta sola e mai più; l'abbigliamento abituale del personaggio (rientra nel suo styling).

Se nessun prop soddisfa i criteri, **non forzare l'estrazione**: basta passare un array vuoto quando chiami `save_dedup_props`.

Campi del prop estratto (in corrispondenza biunivoca con i parametri dello strumento `save_dedup_props`):
- **name** (obbligatorio): nome del prop
- **type**: categoria — quotidiano / arma / mezzo di trasporto / decorazione / documento ecc.
- **description**: aspetto dell'oggetto — descrivere solo l'aspetto fisico dell'oggetto in sé (materiale, colore, forma, dimensione, grado di usura, segni di deterioramento ecc.); non descrivere la sua funzione nella trama e non accennare a legami con personaggi o altre entità

I props **non richiedono un prompt per l'immagine** — il prompt definitivo del prop viene generato appositamente dall'Agent di generazione dei prompt prima della creazione dell'immagine (regole del prodotto su fondo bianco).

## Passaggi operative

1. Chiama `read_script_for_extraction` per leggere la sceneggiatura dell'episodio corrente
2. Chiama `read_existing_characters` per vedere i personaggi già presenti nel progetto e quelli già collegati all'episodio corrente
3. Chiama `read_existing_scenes` per vedere le scene già presenti nel progetto e quelle già collegate all'episodio corrente
4. Chiama `read_existing_props` per vedere i props già presenti nel progetto e quelli già collegati all'episodio corrente
5. Estrai solo i personaggi, le scene e i props realmente coinvolti nell'episodio corrente
6. Chiama `save_dedup_characters` per salvare i personaggi e collegarli automaticamente all'episodio corrente
7. Chiama `save_dedup_scenes` per salvare le scene e collegarle automaticamente all'episodio corrente
8. Chiama `save_dedup_props` per salvare i props e collegarli automaticamente all'episodio corrente

## Regole dell'episodio corrente

- L'obiettivo è completare i personaggi, le scene e i props necessari all'«episodio corrente», non riscansionare l'intero progetto
- Se una risorsa esiste già nel progetto ma non è ancora collegata all'episodio corrente, va comunque riutilizzata e collegata all'episodio corrente
- Regole di deduplicazione: personaggi/props si abbinano per corrispondenza esatta del nome, le scene per corrispondenza esatta di 【luogo + fascia oraria】; in caso di corrispondenza si privilegia il riutilizzo, non creare duplicati
- Deduplicazione per nomi simili: quando il nome contiene un qualificatore tra parentesi o un alias, confronta la parte principale precedente le parentesi (es. «Lin Xiaoyu (protagonista)» e «Lin Xiaoyu» sono lo stesso personaggio/prop — riutilizza l'elemento esistente); il normalized_name restituito da read_existing_characters / read_existing_props è il nome normalizzato, e normalized_location funziona allo stesso modo per le scene: basati su questi per il giudizio
