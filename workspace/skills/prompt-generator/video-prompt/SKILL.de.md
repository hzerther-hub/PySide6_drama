---
name: video-prompt
description: Spezifikation für Video-Prompts — erzeugt aus dem Inhalt eines Storyboard-Segments einen zeitlich segmentierten Video-Generierungs-Prompt, mit Schnitten innerhalb des Segments
---

# Video-Prompt (Storyboard-Segment → video_prompt)

Aus der description eines einzelnen Storyboard-Segments (mit der 【镜头N】-Sub-Shot-Struktur sowie Dialog/Erzählung) / atmosphere / duration wird der `video_prompt` erzeugt, der die KI-Videogenerierung antreibt. **Ein Storyboard-Segment = ein Video von 8-15 Sekunden, innere Schnitte sind erlaubt**: Aufeinanderfolgende Abschnitte dürfen verschiedene Einstellungen sein (Wechsel von Einstellungsgröße/Winkel/Subjekt), verbunden mit harten Schnitten; aber **niemals wird die Szene gewechselt**, keine Rückblenden.

## Format

**Die erste Zeile des `video_prompt` ist der Informationskopf**: zuerst angeben, welche Figuren und Szene in diesem Video auftreten, danach die Zeitsegmente. Figuren und Szenen werden stets mit @ referenziert (bei der Generierung werden sie durch die jeweiligen Referenzbild-Marker ersetzt, damit das Videomodell zuerst „wer“ und „wo“ verankert).

```
Im Bild: @Lukas, @Mia; Szene: @Café.
0-3 Sekunden: @Café, Naheinstellung, die Kamera schwingt leicht wie im Atemtempo und fährt langsam auf @Lukas zu; er blickt auf sein Handy, die Finger trommeln immer wieder auf den Tisch, die Miene ist nervös.
3-6 Sekunden: Schnitt zur Weiteinstellung der Tür; die Klingel ertönt, @Mia stößt die Tür auf und tritt ein, ein Hauch kalter Luft zieht mit ihr herein.
6-9 Sekunden: Zurück auf halbtotal; @Mia geht lächelnd zu Lukas und setzt sich; Lukas sagt: „Endlich kommst du.“
```

Kopf-Regeln:
- Nur die Figuren listen, die in diesem Storyboard-Segment tatsächlich auftreten, und die gebundene Szene — nicht Auftretende nicht listen
- Tritt eine Requisite deutlich auf, darf sie im Kopf ergänzt werden (z. B. `; Requisite: @Brief`)
- Der Kopf steht in eigener Zeile und endet mit einem Punkt, danach folgen die Zeitsegmente

In 3-Sekunden-Abschnitte teilen, jeder Abschnitt in eigener Zeile, durch Zeilenumbrüche getrennt; die Zeitbereiche schließen lückenlos aneinander (keine Überlappung, keine Lücken).

## Zuordnung zur Storyboard-Beschreibung

Die `description` ist die alleinige Inhaltsquelle des video_prompt (Bild, Aktion, Repliken, Erzählung liegen alle in ihr). Umsetzungsregeln:

- Jedes `【镜头N】` der `description` wird auf **1-2 aufeinanderfolgende 3-Sekunden-Abschnitte** abgebildet — gleiche Reihenfolge, keine Auslassung, keine Verschmelzung, keine neuen Sub-Shots
- Dialog/Erzählung wird aus „Charaktername sagt: ‚…‘“ / „Erzähler: …“ innerhalb des jeweiligen `【镜头N】` extrahiert und den zugeordneten Abschnitten des Sub-Shots zugewiesen; **keine neuen Repliken außerhalb der description erfinden**
- Bild und Aktion richten sich nach der `description`; `atmosphere` dient nur dazu, Licht, Farbstich und Stimmungsbeschreibung der einzelnen Abschnitte zu ergänzen

## Abschnittsinterne Struktur

Jeden Abschnitt in dieser Reihenfolge aufbauen (Elemente ohne Inhalt dürfen entfallen, aber Aktion/Bild sind Pflicht):

**Zeitbereich + Szenen-@Referenz + Einstellungsgröße/Kamerabewegung + Figuren-@Referenz + Hauptaktion · Mimik + Dialog/Erzählung + Stimmung und Licht**

- **Der erste Abschnitt muss den Raum etablieren**: Szene + Kameraposition + Position und Zustand der Figuren, damit das Publikum auf einen Blick weiß, wo wir sind und wen wir beobachten
- **Schnitte**: Ein Abschnitt nach einem Schnitt beginnt mit einem Verbindungswort wie „Schnitt zu / zurück auf“ und nennt Einstellungsgröße und Subjekt erneut; die Schnittpunkte richten sich an der 【镜头N】-Struktur der Storyboard-`description` aus
- **Einstellungsgröße/Kamerabewegung (harte Regel)**: Jeder Abschnitt muss sowohl die **Einstellungsgröße** (nah/halbtotal/weit/Großaufnahme) als auch eine **Kamerabewegungs-Anweisung** nennen; innerhalb eines Sub-Shots läuft die Kamerabewegung kontinuierlich, nach einem Schnitt darf sie wechseln. Schreibweise = „Ausgangsgröße + Bewegungsart + Tempo/Rhythmus“, z. B. „gleichmäßige langsame Heranfahrt von halbtotal bis zur Gesichtsgroßaufnahme“, „seitliche Mitfahrt mit der Figur, fließende Parallaxe im Hintergrund“. Verboten, einen ganzen Abschnitt auf ein bloßes „statische Kamera“ zu setzen — die Kamera muss „fahren“ (Verfahren, Zoom, Verfolgen, atmendes Auf und Ab zählen alles), um PPT-artige Standbilder zu vermeiden. Das Vokabular findet sich unten unter „Kamerabewegungs-Regeln“
- **Aktion**: eine Hauptaktion pro Abschnitt, mit konkreten sichtbaren Verben (gehen, sich umdrehen, aufblicken, fest umklammern, innehalten)
- **Alle Emotion wird zu sichtbarer Beschreibung**: keine abstrakten Wörter wie „er ist sehr traurig / die Stimmung ist angespannt“, sondern „er senkt den Kopf, die Finger umklammern den Becherrand, der Atem wird schwerer“
- **Dialog/Erzählung**: als „Charaktername sagt: ‚Replik‘“ schreiben, Erzählung als „Erzähler: Inhalt“; lange Repliken, die in 3 Sekunden nicht ausgesprochen werden können, auf mehrere Abschnitte verteilen; Abschnitte ohne Dialog dürfen Ambiente-/Aktionsgeräusche nennen (z. B. „die Maschinen dröhnen ununterbrochen“)

## Referenzregeln

- `@Szenenname` — Szenenreferenz; der Name muss exakt dem Ort in der Szenenliste entsprechen
- `@Charaktername` — Figurenreferenz; der Name muss exakt dem Namen in der Charakterliste entsprechen
- `@Requisitenname` — Requisitenreferenz; der Name muss exakt dem Namen in der Requisitenliste entsprechen; eine Requisite referenzieren, wenn sie im Bild klar sichtbar, benutzt wird oder im Close-up erscheint
- Bei der Generierung wird jedes `@Name` automatisch durch den jeweiligen Referenzbild-Marker ersetzt (z. B. `@Lukas` → `@Bild1Lukas`); die Namen müssen daher exakt stimmen — nicht abkürzen und keine zusätzlichen Zeichen anhängen
- **Jeder Abschnitt braucht mindestens eine @-Referenz, die das Bild verankert**; in jedem Abschnitt, in dem eine Figur auftritt, muss diese Figur mit @ genannt werden; nur Szenen/Figuren/Requisiten referenzieren, die an dieses Storyboard-Segment gebunden sind

## Zeitlinien-Regeln

- Abschnittszahl = duration des Storyboard-Segments ÷ 3 Sekunden (aufrunden); die Zeitbereiche aller Abschnitte müssen in der Summe exakt der Gesamtdauer des Segments entsprechen
- Inhaltliches Tempo: der erste Abschnitt etabliert → die mittleren Abschnitte treiben Aktion/Konflikt voran → der letzte Abschnitt landet auf dem Ergebnis oder einem emotionalen Punkt

## Kamerabewegungs-Regeln

Jeder Zeitabschnitt bekommt eine Kamerabewegung, gewählt aus dem folgenden Vokabular und konsistent mit der Absicht in den Feldern `description`/`movement` des Storyboards (was die description an Kameraführung vorgibt, wird im video_prompt genauso ausgebaut; gibt sie nichts vor, das Passendste zum Bildinhalt wählen):

- **Basale Erzählung**: langsames Heranfahren (halbtotal → Großaufnahme, gleichmäßig, Hintergrund läuft langsam in Unschärfe), Zurückfahren zur Enthüllung (Großaufnahme → Totale, erst schnell dann langsam), seitliche Mitfahrt (mit der Figur mitziehend, Parallaxe im Hintergrund), Kranfahrt auf/ab (vertikales Steigen/Sinken, das den Raum zeigt), Bogen-Orbit (90-180 Grad um die Figur), Gang in der Ich-Perspektive (Augenhöhe, leichtes Auf und Ab wie beim Atmen)
- **Emotion und Atmosphäre**: Handkamera-Atem (leichtes Wackeln, nach Bewegungen verstärkt), Lauer-Perspektive (Schlitzblick durch Türspalt/Fensterritze mit Verdeckung im Vordergrund), Herzschlag-Puls (Vor- und Zurückfahrt synchron zum emotionalen Rhythmus, ruhig-langsam bzw. angespannt-schnell), Atem-Sync (beim Einatmen leicht heranfahren, beim Ausatmen langsam zurück)
- **Psychologie und Detail**: Blick-Fokus (langsam auf das angestaunte Objekt fahren, Fokuswechsel), zitternde Furcht (unregelmäßiges feines Beben), sanfter Orbit (langsame kleine Bogenfahrt, Fokus aufs Gesicht fixiert), Highspeed-Verfolgung (dicht am bewegten Ziel, Motion Blur), Kampf-Weave (schnelle Wechsel zwischen den Kontrahenten), Sprung-Sturzflug (Sturz aus der Höhe, leichtes Beben bei der Landung)
- **Highspeed-Kampf**: nur wenn die Storyboard-`description` ausdrücklich Kampf-Kameraführung vorschreibt, diese wortgetreu ausbauen (jede Position, jedes Tempo und jede Zahl bleibt erhalten): rasche Heranfahrt aus tiefer Position, bodennahe Verfolgung, rasches Aufschwenken, extreme Nahverfolgung, gegenläufige Heranfahrt mit Fokuswechsel, rasches Zurückfahren am Schweif, im Treffermoment 0.15 Sekunden Hochgeschwindigkeits-Unschärfe, Schock-shake 0.3 Sekunden
- **Besondere Perspektiven**: extreme Untersicht, holländischer Winkel, Over-the-Shoulder-Nahsicht, POV
- **Rhythmus und Übergänge**: Whip Pan (Schwungrichtung entspricht der Bewegungsrichtung des nächsten Abschnitts), Verdeckungswipe (Vordergrundobjekt fegt vorbei, Schnitt im Moment der Verdeckung), Bremsstopp-Freeze (abbremsen bis zum Standbild, nur für Highlight-Abschnitte)

Anforderungen an die Schreibweise:
- Die Kamerabewegung immer zusammen mit Einstellungsgröße und Tempo nennen: „aus der Totale langsam auf halbtotal heranfahren“, nie ein bloßes „heranfahren“
- Tempo-Adverbien konkret: gleichmäßig/langsam/rapid/erst schnell dann langsam/von langsam nach schnell
- Eine Kamerabewegung pro Abschnitt; innerhalb des Abschnitts kontinuierlich, Wechsel nur an Schnittpunkten
- Bullet-Time / Slow-Motion-Close-up / Fisheye / Miniatur-Diorama sind Akzent-Spezialeffekte — nur einsetzen, wenn die Storyboard-`description` sie ausdrücklich nennt, pro Folge höchstens 1-2 Mal
- Handkamera-Wackeln und atmendes Auf und Ab sind „Mikrobewegungen“ und dürfen in Abschnitten, die sonst als komplett statische Kamera geschrieben würden, den völligen Stillstand ersetzen

## Verbotsliste

- Szenenwechsel, Rückblenden (ein Abschnitt spielt in genau einer Szene)
- Szenen-/Figurennamen außerhalb der Listen referenzieren
- Abstrakte psychologische Beschreibung, literarische Metaphern (das Modell erkennt nur sichtbare Bilder)
- Überzeichnetes Schauspiel: kein Schreien, Kreischen, lautes Aufschreien, lautes Schluchzen; Erschrecken als Mikroreaktion schreiben (Erfrieren, zusammenziehende Pupille, scharfer Atemzug, ein halber Schritt zurück); Repliken in Alltagston und Alltagslautstärke (braucht eine extreme Handlung wirklich einen Ausbruch, im jeweiligen Abschnitt ausdrücklich „Emotionsausbruch“ vermerken)
- Slow Motion und Stillstand als Zeitstreckung: Standardmäßig keine Slow Motion und kein langes stilles Starren; Ausnahme: Highlight-Sub-Shots, in denen die Storyboard-`description` ausdrücklich Bullet-Time / Slow-Motion-Close-up / Bremsstopp-Freeze vorschreibt, dürfen der description entsprechend genutzt werden. Auch dann braucht jeder Abschnitt eine sichtbare Kamerabewegung oder einen Handlungsfortschritt — „rein statische Einstellungen“ sind nicht erlaubt
- Sprache widerspricht der Sprachanweisung der Sitzung

## Speichern

`update_storyboard` aufrufen und dabei nur das Feld `video_prompt` dieses Storyboard-Segments aktualisieren; keine anderen Felder anfassen und nicht die ganze Folge neu aufbrechen. Die Plattform fügt beim tatsächlichen Generierungs-Request automatisch Guards für Schauspiel und Tempo hinzu; diese Anforderungen müssen im Prompt nicht wiederholt werden.
