# Roadmap bis Version 1.0

## Produktziel für 1.0

Freak Media Player 1.0 ist ein stabiler, eigenständiger Windows-Musikplayer für
lokale Audiodateien. Die vorhandenen Stärken – modulare Oberfläche, Wiedergabeliste,
DAW-Equalizer, Visualizer und Skins – sollen zuverlässig zusammenspielen und als
sauber installierbares Release ausgeliefert werden.

Die Versionsnummern markieren Qualitäts- und Funktionsziele, keine festen Termine.
Ein Meilenstein ist erst abgeschlossen, wenn seine Abnahmekriterien erfüllt sind.

## Leitplanken

- Bis einschließlich 1.0 werden ausschließlich lokale Audiodateien als Quelle
  unterstützt.
- Externe Audioquellen wie Webradio, direkte Stream-URLs, YouTube Music oder andere
  Online-Dienste beginnen frühestens nach dem stabilen 1.0-Release.
- Stabilität, Datenintegrität und verständliche Fehlerbehandlung haben Vorrang vor
  neuen Modulen und zusätzlichen Effekten.
- Bereits vorhandene Funktionen werden zuerst vervollständigt und abgesichert.
- Crossfade, ReplayGain und echtes Gapless Playback sind keine Pflicht für 1.0. Sie
  bleiben mögliche Erweiterungen, sofern sie die Stabilisierung nicht verzögern.

## Ausgangspunkt: 0.8.0

Der aktuelle Stand besitzt bereits den vollständigen lokalen Wiedergabepfad:

- lokale Bibliothek und persistente, geordnete Wiedergabeliste
- Streaming-Decoding über PyAV/FFmpeg und native Ausgabe über Qt AudioSink
- Shuffle, Repeat, Seek, Lautstärke und Wiederherstellung der letzten Sitzung
- hörbarer parametrischer Equalizer und audio-reaktiver Visualizer
- modulares, abdockbares Desktop-Layout
- wechselbare und erweiterbare Skins
- SQLite-Migrationen, automatisierte Tests und Windows-Build

Die verbleibende Arbeit bis 1.0 konzentriert sich deshalb auf robuste
Alltagsabläufe und Release-Qualität statt auf einen weiteren Architekturumbau.

## Priorisierung der neuen Funktionsvorschläge

Damit der Umfang bis 1.0 beherrschbar bleibt, sind die folgenden Funktionen in
drei Stufen eingeordnet:

- **MUSS:** gehört zum verbindlichen 1.0-Umfang.
- **SOLL:** hoher Nutzen und vorhandene technische Grundlage; ein Weglassen muss
  vor dem Release bewusst entschieden und dokumentiert werden.
- **OPTIONAL:** wird nur umgesetzt, wenn die MUSS- und SOLL-Funktionen stabil sind.

Die wichtigsten zusätzlichen Vorschläge nutzen bereits vorhandene Vorarbeit: Das
Datenbankschema kennt Favoriten, Bewertungen, Wiedergabeverlauf und Queue-Einträge,
während Favoriten- und Einstellungsbuttons in der Oberfläche schon vorgesehen sind.

## 0.9.1 – Wiedergabe und Windows-Integration abrunden

Ziel: Die Kernwiedergabe verhält sich unter realen Windows-Bedingungen vorhersehbar.

### Featureliste

- **SOLL – Cover-Auswahl:** Ein abweichendes lokales Cover pro Album oder Titel
  auswählen und auf die automatische Erkennung zurücksetzen können.
- **OPTIONAL – Infobereich:** Konfigurierbares Minimieren in den Windows-Tray mit
  Wiedergabesteuerung; standardmäßig bleibt normales Taskleistenverhalten erhalten.
- **OPTIONAL – Schlaf-Timer:** Wiedergabe nach einer Zeitspanne oder am Ende des
  aktuellen Titels stoppen, ohne den Rechner automatisch herunterzufahren.

### Stabilität und Technik

- Wechsel, Verlust und Wiederkehr des Audio-Ausgabegeräts robust behandeln.
- Unterstützte Dateiformate sowie Sonderfälle bei Dauer, Seek und Metadaten mit
  echten Testdateien abdecken.
- Decoder, DSP, Visualizer-Sample-Tap und AudioSink von der bisher festen
  Stereoannahme lösen. Kanalzahl und Kanallayout müssen durch die gesamte Pipeline
  erhalten oder an genau einer definierten Stelle konvertiert werden.
- Mono, Stereo, 5.1 und 7.1 mit Kanal-Identifikationstönen und echten
  Mehrkanal-Testdateien prüfen. Equalizer, Lautstärke, Seek, Pause und Titelwechsel
  müssen in jedem unterstützten Modus hörbar und ohne Kanalfehler funktionieren.
- Fokusführung, Tooltips, Skalierung und Kontrast für 100 %, 125 %, 150 % und 200 %
  DPI prüfen.
- Leerlauf-, Wiedergabe- und Visualizer-Last auf typischer Hardware messen und
  dokumentierte Zielwerte festhalten.

Abnahme:

- Audio-Gerätewechsel und Decoderfehler führen nicht zum Anwendungsabsturz.
- Mono und Stereo funktionieren auf jedem unterstützten Ausgabegerät; 5.1 und 7.1
  werden auf geeigneter Hardware mit korrekter Windows-Kanalkonfiguration und
  eindeutigem Lautsprechertest nachgewiesen.
- Ein Wechsel des Ausgabemodus startet den Audiopfad kontrolliert neu, behält den
  aktuellen Titel und setzt die Wiedergabe nahe der vorherigen Position fort.
- Die wichtigsten Bedienabläufe funktionieren vollständig mit Maus und Tastatur.
- Ein definierter Format- und Windows-Smoke-Test ist reproduzierbar bestanden.

## 0.9.2 – Release Candidate vorbereiten

Ziel: Aus dem Entwicklungsstand wird ein wartbares Produkt, das auf einem sauberen
Windows-System zuverlässig installiert und diagnostiziert werden kann.

### Featureliste

- **MUSS – Sicherung und Wiederherstellung:** Bibliothek, Wiedergabelisten,
  Favoriten, Bewertungen, Einstellungen und benutzerdefinierte Equalizer-Daten in
  ein lokales Sicherungspaket exportieren und wieder einlesen.
- **MUSS – Diagnoseansicht:** App-Version, Datenbankversion, Datenpfade,
  Audioausgabe und letzte Fehler anzeigen sowie Protokollordner öffnen können.
- **MUSS – Über/About-Dialog:** Version, Projektinformationen, Lizenzen und
  mitgelieferte Drittanbieterkomponenten auffindbar machen.
- **SOLL – Erster-Start-Assistent:** Kurz Musikordner, Audioausgabe und
  Sitzungsverhalten abfragen; jeder Schritt bleibt überspringbar.
- **SOLL – Dateizuordnung:** Während der Installation optional unterstützte
  Audiodateien mit Freak Media Player öffnen beziehungsweise an die aktive
  Wiedergabeliste übergeben.
- **SOLL – Wartungsfunktionen:** Standardlayout wiederherstellen, Bibliotheksindex
  neu aufbauen und Einstellungen mit klarer Bestätigung zurücksetzen.
- **OPTIONAL – Portable Ausgabe:** Zusätzlich zur Installation ein klar
  gekennzeichnetes portables Paket bereitstellen, dessen Datenablage nicht mit der
  installierten Variante kollidiert.

### Release-Qualität und Technik

- Einstellungen und Bibliotheksdaten vor riskanten Migrationen sichern und bei
  Fehlern verständlich reagieren.
- Rotierende Logdateien, aussagekräftige Fehlermeldungen und eine leicht auffindbare
  Diagnoseinformation bereitstellen; keine persönlichen Dateipfade ungefragt in
  Berichte übernehmen.
- Reproduzierbaren Release-Build auf einem sauberen System prüfen.
- Installations- oder portable Release-Verteilung festlegen, inklusive sauberer
  Deinstallation beziehungsweise klar dokumentierter Datenablage.
- Lizenzhinweise für Python-, Qt-, FFmpeg/PyAV-, NumPy- und SciPy-Bestandteile
  vollständig mitliefern.
- Benutzerhandbuch für Import, Playlist, Equalizer, Visualizer, Skins,
  Tastenkürzel, Datenablage und Fehlerdiagnose fertigstellen.
- Versionsnummern, Dateieigenschaften, Programmtitel und Changelog automatisiert
  auf Konsistenz prüfen.

Abnahme:

- Release-Artefakt startet ohne installierte Python-Entwicklungsumgebung auf den
  unterstützten Windows-Versionen.
- Upgrade, Neuinstallation und Deinstallation wurden auf einer sauberen Umgebung
  getestet.
- Keine bekannten Fehler der Priorität Blocker oder Kritisch; alle übrigen
  bekannten Einschränkungen sind dokumentiert.

## 1.0.0 – Stabiler lokaler Player

Ziel: Funktionsumfang einfrieren, letzte Release-Blocker beheben und den lokalen
Player offiziell als stabil veröffentlichen.

### Ausgelieferter Funktionsumfang

- lokale Dateien und verwaltete Musikordner importieren und neu einlesen
- Bibliothek durchsuchen, filtern, sortieren und fehlende Dateien reparieren
- aktive Queue sowie mehrere persistente Wiedergabelisten verwalten
- Favoriten und – sofern das SOLL-Gate erfüllt ist – Bewertungen und Verlauf nutzen
- Wiedergabe mit Seek, Lautstärke, Shuffle, Repeat, wählbarem Ausgabegerät und
  funktionierenden Mono-, Stereo-, 5.1- und 7.1-Ausgabemodi
- parametrischen Equalizer, Visualizer, Skins und modulares Layout verwenden
- Sitzung, Layout und Einstellungen sicher wiederherstellen
- lokale Daten sichern, wiederherstellen und diagnostizieren
- als dokumentiertes Windows-Release installieren oder bewusst portabel starten

### Release-Freeze

- Ab 1.0-RC nur noch Fehlerkorrekturen, Dokumentation und notwendige
  Kompatibilitätsanpassungen aufnehmen.
- Vollständige Regression über Bibliothek, Wiedergabelisten, Decoder, Audioausgabe,
  Equalizer, Visualizer, Skins, Sitzungswiederherstellung und Migrationen ausführen.
- Release-Artefakt, Prüfsumme, Changelog, Lizenzhinweise und bekannte
  Einschränkungen veröffentlichen.
- Eine Rückkehr zur vorherigen Version darf Benutzerdaten nicht stillschweigend
  beschädigen; unvermeidbare Einschränkungen müssen vor dem Upgrade sichtbar sein.

1.0 gilt als fertig, wenn:

- lokale Musik ohne Netzwerkverbindung importiert, organisiert und zuverlässig
  wiedergegeben werden kann,
- Bibliothek, Wiedergabelisten und Einstellungen Neustarts und Upgrades ohne
  Datenverlust überstehen,
- keine bekannten reproduzierbaren Abstürze oder Wiedergabe-Blocker offen sind,
- automatisierte Tests sowie der definierte manuelle Release-Test bestanden sind,
- Build, Installation, Bedienung, Datenablage und Fehlerdiagnose dokumentiert sind.

## Nach 1.0

Erst nach dem stabilen 1.0-Release wird die vorhandene Provider-Architektur für
externe Audioquellen produktiv erweitert. Vor dem ersten Anbieter wird gemeinsam
geklärt, wie Authentifizierung, Netzwerkfehler, Caching, Quellenkennzeichnung,
Metadaten, Nutzungsbedingungen und optionale Abhängigkeiten behandelt werden.

Mögliche spätere Schritte, noch ohne feste Reihenfolge:

- direkte Stream-URLs und Webradio
- externe Musikkataloge und Musikdienste
- YouTube Music oder vergleichbare Anbieter, soweit technisch und rechtlich
  tragfähig
- quellenübergreifende Suche und gemischte Wiedergabelisten
- Offline-Cache nur dort, wo der jeweilige Dienst dies ausdrücklich erlaubt

Diese Punkte gehören ausdrücklich nicht zum Umfang von 0.8.x, 0.9.x oder 1.0.0.
