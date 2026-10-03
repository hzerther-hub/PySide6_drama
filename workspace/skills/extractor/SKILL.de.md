---
name: extractor
description: Regeln und Methoden für die Extraktion von Charakteren, Szenen und Requisiten
---

# Leitfaden zur Extraktion von Charakteren, Szenen und Requisiten

## Extraktionsregeln für Charaktere

Extrahierte Charakterfelder (eins zu eins mit den Parametern des Tools `save_dedup_characters`):
- **name** (Pflicht): vollständiger Name des Charakters
- **role**: Positionierung des Charakters — Hauptrolle/Nebenrolle/Kleinstrolle
- **appearance**: Erscheinungsbeschreibung (300-500 Zeichen) — Geschlecht, Altersbild, Gesichtszüge, Statur, Ausstrahlung. **Persönlichkeitsmerkmale des Charakters nicht separat ausgeben, sondern in äußere Ausstrahlung und Miene übersetzen und in die Erscheinungsbeschreibung einweben** (z. B. „kühle Persönlichkeit“ wird zu „kühler Blick, beherrschte Mimik, selten ein Lächeln“)
- **styling**: Styling — Frisur, Kleidung, Make-up, Accessoires usw.
- **description**: Hintergrundgeschichte und Beziehungen des Charakters (optionale Ergänzung)

## Extraktionsregeln für Szenen

Extrahierte Szenenfelder (eins zu eins mit den Parametern des Tools `save_dedup_scenes`):
- **location** (Pflicht): konkreter Ortsname
- **time**: Tageszeit (z. B. tagsüber/Dämmerung/tiefe Nacht); derselbe Ort zu einer anderen Tageszeit gilt als neue Szene
- **prompt**: Szenenbeschreibung — Raum, Ausstattung, zeittypische Anmutung, zentrale visuelle Elemente (reiner Hintergrund, ohne Personen)
- **lighting**: Licht und Schatten der Szene — Lichtquellen, Farbstich, Hell-Dunkel-Kontrast, Stimmung

## Extraktionsregeln für Requisiten

**Kernprinzip: Lieber zu wenig als zu viel extrahieren.** Requisiten sind kostspielige Assets, aus denen Produktbilder vor weißem Hintergrund erzeugt werden, auf die Video-Close-ups verweisen; nur handlungskritische Requisiten lohnen die Extraktion. Eine Folge hat in der Regel **0-3** Schlüsselrequisiten; bei mehr als 3 nach Plot-Relevanz sortieren und nur die Top 3 behalten.

Beide folgenden Bedingungen müssen **zugleich** erfüllt sein, keine ist verzichtbar:
1. **Treibt die Handlung direkt voran**: Das Auftauchen, die Übergabe, die Beschädigung oder das Auffinden des Gegenstands löst eine Wendung der Handlung aus (z. B. Tatwaffe, Erinnerungsstück, Schlüsseldokument, Liebesgeschenk, entscheidender Beweis).
2. **Lohnt ein eigenes Bild**: Spätere Storyboards geben ihm Close-ups oder es taucht wiederholt auf und braucht ein festes Aussehen.

**Drei Selbstcheck-Fragen** (für jede Kandidatin/jeden Kandidaten selbst stellen und beantworten; schon eine „Nein“-Antwort → verwerfen):
- (1) Hält die Handlung auch ohne den Gegenstand stand? → Falls ja, **nicht extrahieren** (er ist nur ein dekorativer Hintergrundgegenstand)
- (2) Ist er nur ein Alltagsgegenstand, den die Figur beiläufig benutzt (Handy, Stäbchen, Trinkbecher, Zigaretten, Regenschirm)? → Falls ja, **nicht extrahieren**
- (3) Ist er Teil der Szenenausstattung (Tische und Stühle, Lampen, Türen und Fenster, Wandbilder, Geschirr)? → Falls ja, **nicht extrahieren** (das gehört in die Szenenbeschreibung)

**Typische Nicht-Requisiten**: gewöhnliche Gegenstände des beiläufigen Gebrauchs ohne Einfluss auf den Handlungsverlauf; Szenenausstattung und Möbel; Gegenstände, die nur einmal erwähnt werden und nie wieder; die reguläre Kleidung einer Figur (gehört ins Charakter-Styling).

Gibt es keine passende Requisite, **nicht erzwingen** — beim Aufruf von `save_dedup_props` einfach ein leeres Array übergeben.

Extrahierte Requisitenfelder (eins zu eins mit den Parametern des Tools `save_dedup_props`):
- **name** (Pflicht): Name der Requisite
- **type**: Kategorie — Alltag/Waffe/Verkehr/Dekoration/Dokument usw.
- **description**: Äußeres des Gegenstands — ausschließlich die physische Erscheinung des Gegenstands selbst beschreiben (Material, Farbe, Form, Größe, Neuwert bzw. Abnutzung, Gebrauchsspuren usw.); keinen Handlungszweck nennen und keine Bezüge zu Figuren oder anderen Dingen

Requisiten **benötigen keinen Bild-Prompt** — der finale Prompt einer Requisite wird vor der Bilderzeugung eigens vom Prompt-Generierungs-Agenten erstellt (Spezifikation für Produktbilder vor weißem Hintergrund).

## Arbeitsschritte

1. `read_script_for_extraction` aufrufen und das Drehbuch der aktuellen Folge lesen
2. `read_existing_characters` aufrufen und die bestehenden Charaktere des Projekts sowie die bereits mit der aktuellen Folge verknüpften Charaktere einsehen
3. `read_existing_scenes` aufrufen und die bestehenden Szenen des Projekts sowie die bereits verknüpften Szenen einsehen
4. `read_existing_props` aufrufen und die bestehenden Requisiten des Projekts sowie die bereits verknüpften Requisiten einsehen
5. Nur die Charaktere, Szenen und Requisiten extrahieren, die die aktuelle Folge tatsächlich betrifft
6. `save_dedup_characters` aufrufen, um Charaktere zu speichern und automatisch mit der aktuellen Folge zu verknüpfen
7. `save_dedup_scenes` aufrufen, um Szenen zu speichern und automatisch mit der aktuellen Folge zu verknüpfen
8. `save_dedup_props` aufrufen, um Requisiten zu speichern und automatisch mit der aktuellen Folge zu verknüpfen

## Regeln für die aktuelle Folge

- Ziel ist es, die Charaktere, Szenen und Requisiten zu ergänzen, die die „aktuelle Folge“ braucht — kein erneutes Durchleuchten des gesamten Projekts
- Existiert ein Asset bereits im Projekt, ist aber noch nicht mit der aktuellen Folge verknüpft, es wiederverwenden und mit der aktuellen Folge verknüpfen
- Dedup-Regeln: Charaktere/Requisiten werden exakt nach Name abgeglichen, Szenen exakt nach [Ort + Tageszeit]; bei einem Treffer Wiederverwendung bevorzugen, keine Duplikate anlegen
- Near-Name-Dedup: Trägt ein Name eine eingeklammerte Positionsangabe oder einen Alias, nach dem Hauptteil vor der Klammer vergleichen (z. B. „Lena (Hauptrolle)“ und „Lena“ sind derselbe Charakter/dieselbe Requisite — den bestehenden Eintrag wiederverwenden); das von read_existing_characters / read_existing_props zurückgegebene normalized_name ist der normalisierte Name, analog gilt normalized_location für Szenen — danach beurteilen
