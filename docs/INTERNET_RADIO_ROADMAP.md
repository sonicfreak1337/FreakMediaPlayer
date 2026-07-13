# Roadmap: Internetradio-Plugin

## Produktziel

Das Internetradio-Plugin erweitert Freak Media Player nach Version 1.0 um direkt
integriertes Live-Radio. Sender werden innerhalb der bestehenden Anwendung gesucht,
gefiltert, gestartet und als Favoriten gespeichert. Wiedergabe, Lautstärke,
Audioausgabe, Equalizer und Visualizer bleiben Bestandteile des zentralen Players;
es wird weder ein Browser geöffnet noch ein externer Player benötigt.

Die Bedienidee orientiert sich an der einfachen weltweiten Senderentdeckung von
Radio Garden, verwendet aber bewusst keine Weltkarte. Im Mittelpunkt stehen eine
schnelle Senderliste und kombinierbare Filter.

## Verbindlicher Umfang

- direkte Wiedergabe von Internetradio im vorhandenen Player
- weltweiter Senderkatalog aus einer austauschbaren Verzeichnisquelle
- Suche nach Sender, Land, Region und Ort
- kombinierbare Filter nach Land, Region, Sprache, Genre/Tags, Codec und Bitrate
- Sortierung nach Name, Popularität, Bewertung, Bitrate und Aktualität
- Favoriten, Verlauf, zuletzt gehörte Sender und Zufallssender
- manuell hinzugefügte Stream-URLs
- Anzeige verfügbarer Live-Metadaten wie Sendungs-, Titel- und Interpretenname
- robuste Behandlung von Unterbrechungen, Weiterleitungen und defekten Streams
- vollständige Integration in Audioausgabe, Equalizer, Visualizer und Skins

## Nicht vorgesehen

- keine Weltkarte und kein 3D-Globus
- keine Einbettung oder automatisierte Abfrage der Radio-Garden-Weboberfläche
- keine Abhängigkeit von einer inoffiziellen oder nicht freigegebenen
  Radio-Garden-API
- keine Aufnahme oder dauerhafte Speicherung von Radioprogrammen in der ersten
  stabilen Plugin-Version
- keine Anmeldung und kein Cloud-Konto
- keine Podcasts, On-Demand-Sendungen oder Musikdienst-Integration

## Datenquelle und Unabhängigkeit

Das Plugin erhält eine eigene `StationDirectory`-Schnittstelle. Suche, Kategorien
und Senderdetails dürfen nicht direkt an einen einzelnen Anbieter gekoppelt sein.
Als erste Datenquelle ist die öffentliche Radio-Browser-API vorgesehen. Sie liefert
unter anderem Sendername, Stream-URL, Land, Region, Sprache, Tags, Codec, Bitrate,
Favicon, Erreichbarkeitsstatus und – soweit vorhanden – Ortsangaben.

Ein späterer Wechsel oder eine zusätzliche Verzeichnisquelle muss möglich bleiben,
ohne Player, Datenbank oder Oberfläche neu zu schreiben. Favoriten verwenden deshalb
eine interne stabile Sender-ID und speichern zusätzlich die zuletzt bekannte URL und
Metadaten als lokale Rückfallebene.

Radio Browser ist eine Senderverzeichnisquelle, nicht Radio Garden. Name, Gestaltung
und Inhalte von Radio Garden werden nicht übernommen.

## Prioritäten

- **MUSS:** erforderlich für die stabile Plugin-Version 1.0.
- **SOLL:** hoher Alltagsnutzen; Umsetzung vor 1.0, sofern keine Stabilitätsrisiken
  entstehen.
- **OPTIONAL:** erst nach vollständiger Erfüllung aller MUSS-Kriterien.

## Umsetzungsstand

**Internet Radio Plugin 1.0.0 ist implementiert.** Die ursprüngliche Dock-Vorgabe
wurde auf ausdrücklichen Produktwunsch durch ein vollständig separates, lazy
erzeugtes Fenster ersetzt, damit das Hauptlayout unverändert bleibt. Favoritengruppen,
lokale Empfehlungen und Stream-Gesundheitsstatistik bleiben optionale spätere
Erweiterungen. Die automatisierten Release-Gates verwenden ausschließlich lokale
Server; die öffentliche Format-/Standby-Langzeitprobe steht in `RELEASE_CHECKLIST.md`.

## Plugin 0.1 – Architektur und Netzwerk-Prototyp

Ziel: Ein realer Radiostream erreicht die vorhandene Audio-Pipeline, ohne lokale
Wiedergabe oder die Plugin-Grenzen zu beschädigen.

### Featureliste

- **MUSS – Plugin-Kontext erweitern:** Dem Plugin kontrollierten Zugriff auf
  Provider-Registrierung, Playback-Service, Plugin-Datenbank, Einstellungen und
  Dock-Modul-Registrierung geben.
- **MUSS – Internetradio-Provider:** Radiosender als eigene Medienquelle modellieren
  und über die bestehende `ProviderRegistry` auflösen.
- **MUSS – Netzwerkfähiger Decoder:** HTTP- und HTTPS-Streams unterstützen, statt
  `AudioSource` ausschließlich in lokale Dateipfade umzuwandeln.
- **MUSS – Live-Status:** Live-Streams ohne feste Dauer abbilden; Seek und
  Restzeitanzeige werden während Live-Radio korrekt deaktiviert.
- **MUSS – Direkte Testverbindung:** Eine fest konfigurierte Teststation über den
  normalen Play/Pause-/Stop-Pfad wiedergeben.
- **MUSS – Abbruch:** Senderwechsel und Stop müssen Netzwerkzugriff, Decoder und
  Puffer sofort kontrolliert beenden.

### Technik und Sicherheit

- Netzwerkzugriffe laufen außerhalb des Qt-UI-Threads.
- Verbindungsaufbau besitzt getrennte DNS-, Verbindungs- und Lesetimeouts.
- HTTPS-Zertifikate werden standardmäßig geprüft; unsichere Ausnahmen werden nicht
  stillschweigend akzeptiert.
- HTTP-Weiterleitungen sind begrenzt und Schleifen werden erkannt.
- Pluginfehler dürfen lokale Wiedergabe und Anwendungsstart nicht verhindern.

### Abnahme

- MP3- und AAC-Teststreams starten, pausieren beziehungsweise stoppen zuverlässig.
- Ein nicht erreichbarer Stream blockiert die Oberfläche nicht.
- Nach Stop oder Senderwechsel bleiben keine Decoder- oder Netzwerk-Threads zurück.

## Plugin 0.2 – Integrierter Radioplayer

Ziel: Internetradio ist ohne Browser oder externes Programm vollständig im Player
bedienbar.

### Featureliste

- **MUSS – Radio-Modul:** Eigenes separates, über das Modulsystem öffnbares Fenster
  mit Senderliste, aktuellem Sender und Verbindungsstatus. Es verändert das
  Dock-Layout des Hauptplayers nicht.
- **MUSS – Zentrale Wiedergabesteuerung:** Play/Pause, Stop, Lautstärke, Stumm und
  Audioausgabegerät des Hauptplayers steuern den Radiostream.
- **MUSS – DSP-Integration:** Equalizer, Mono/Stereo/5.1/7.1-Ausgabemodus und
  Visualizer verarbeiten das dekodierte Radiosignal wie lokale Musik.
- **MUSS – Senderwechsel:** Ein Klick auf einen Sender ersetzt kontrolliert die
  aktuelle Quelle. Die lokale Playlist bleibt unverändert und kann danach
  fortgesetzt werden.
- **MUSS – Pufferanzeige:** Zustände „Verbinden“, „Puffern“, „Live“, „Erneut
  verbinden“ und „Nicht erreichbar“ sichtbar anzeigen.
- **MUSS – Live-Metadaten:** ICY-/StreamTitle-Metadaten für Titel, Interpret oder
  Sendungsname anzeigen, sofern der Sender sie liefert.
- **SOLL – Senderlogo:** Favicon oder Stationslogo mit sicherem lokalem Cache und
  neutralem Fallback anzeigen.
- **SOLL – Senderdetails:** Land, Region, Ort, Sprache, Genre/Tags, Codec, Bitrate
  und offizielle Homepage darstellen.
- **SOLL – Zwischenablage:** Sendername, Homepage und Stream-URL gezielt kopieren
  können.

### Unterstützte Streamarten

- **MUSS:** direkte MP3-, AAC- und AAC+-Streams
- **MUSS:** PLS- und M3U-Weiterleitungen zu einem tatsächlichen Audiostream
- **SOLL:** Ogg Vorbis und Opus
- **SOLL:** HLS-Audiostreams
- **OPTIONAL:** FLAC-Livestreams

### Abnahme

- Radio läuft hörbar durch den gewählten Ausgabemodus, Equalizer und Visualizer.
- Der Wechsel zwischen lokalem Titel und Radio hinterlässt keinen falschen
  Playlist-, Zeit- oder Metadatenzustand.
- Nicht vorhandene Metadaten führen zu einer sauberen Senderanzeige statt zu leeren
  oder flackernden Feldern.

## Plugin 0.3 – Senderkatalog, Suche und Filter

Ziel: Sender aus vielen Ländern lassen sich ohne Karte schnell finden und sinnvoll
eingrenzen.

### Featureliste

- **MUSS – Verzeichnissuche:** Sendernamen, Länder, Regionen/Bundesländer und Orte
  durchsuchen.
- **MUSS – Länderfilter:** Ein oder mehrere Länder wählen; die Trefferzahl pro Land
  anzeigen.
- **MUSS – Regions- und Ortsfilter:** Nach Auswahl eines Landes passende Regionen
  und Orte anbieten.
- **MUSS – Genre-/Tagfilter:** Mehrere Tags kombinieren, beispielsweise Metal,
  Rock, Jazz, Klassik, Nachrichten oder Talk.
- **MUSS – Sprachfilter:** Eine oder mehrere Sendesprachen wählen.
- **MUSS – Technikfilter:** Codec, Mindest-/Höchstbitrate und nur aktuell als
  erreichbar gemeldete Sender filtern.
- **MUSS – Kombinierte Filter:** Textsuche und alle Filter gemeinsam anwenden; ein
  gut sichtbarer Befehl setzt sämtliche Filter zurück.
- **MUSS – Sortierung:** Name, Land, Popularität, Bewertung, Bitrate, zuletzt
  geändert und zufällige Reihenfolge.
- **MUSS – Seitennavigation:** Ergebnisse stufenweise laden, damit niemals der
  gesamte weltweite Katalog die Oberfläche oder API belastet.
- **MUSS – Filterzustand:** Letzte Suche und Filter optional über Neustarts hinweg
  wiederherstellen.
- **SOLL – Schnellauswahl:** Häufig verwendete Länder, Sprachen und Genres oben
  anbieten.
- **SOLL – Ergebnisvorschau:** Codec, Bitrate, Sprache, Land und Tags bereits in der
  Trefferliste anzeigen.
- **SOLL – Tastaturbedienung:** Suche fokussieren, Treffer wechseln und ausgewählten
  Sender starten, ohne die Maus zu benötigen.

### Suchregeln

- Filter werden serverseitig angewendet, soweit die Verzeichnis-API dies unterstützt.
- Nur die verbleibende kleine Ergebnismenge darf lokal nachgefiltert werden.
- Tags werden normalisiert, ohne unterschiedliche Begriffe unbemerkt
  zusammenzuführen.
- Ein leeres Ergebnis erklärt, welche Filter aktiv sind, und bietet das Zurücksetzen
  direkt an.

### Abnahme

- Kombinationen wie „Deutschland + Metal + Deutsch + mindestens 128 kbit/s“ oder
  „Japan + Jazz + AAC“ liefern reproduzierbare Ergebnisse.
- Schnelles Ändern mehrerer Filter erzeugt keine veralteten Treffer durch verspätete
  Netzwerkanfragen.
- Suche, Scrollen und Wiedergabe bleiben während langsamer API-Antworten bedienbar.

## Plugin 0.4 – Favoriten und Senderentdeckung

Ziel: Gefundene Sender bleiben leicht erreichbar und neue Sender lassen sich ohne
Karte entdecken.

### Featureliste

- **MUSS – Radiofavoriten:** Sender mit dem Herz-Button speichern und entfernen;
  Favoriten sind klar von lokalen Titelfavoriten getrennt filterbar.
- **MUSS – Zuletzt gehört:** Lokalen Verlauf mit Sender und Zeitpunkt führen und
  einzeln oder vollständig löschen können.
- **MUSS – Zufallssender:** Einen erreichbaren zufälligen Sender aus den aktuell
  gesetzten Filtern starten.
- **MUSS – Beliebte Sender:** Weltweit oder innerhalb der aktuellen Länder-,
  Sprach- und Genrefilter anzeigen.
- **MUSS – Neu und aktualisiert:** Kürzlich hinzugefügte oder geänderte Sender
  anzeigen.
- **MUSS – Eigene Stream-URL:** Name und direkte URL manuell hinzufügen, testen,
  bearbeiten und löschen.
- **SOLL – Favoritengruppen:** Eigene Ordner oder Sammlungen wie „Metal“, „News“
  oder „International“ anlegen.
- **SOLL – Favoritenexport:** Favoriten und eigene Sender als JSON sowie als
  M3U-Liste sichern und wieder importieren.
- **OPTIONAL – Lokale Empfehlungen:** Ausschließlich aus Favoriten und Verlauf
  ähnliche Länder, Sprachen oder Tags vorschlagen; keine Cloudprofilierung.

### Abnahme

- Favoriten funktionieren auch dann als lokale Liste, wenn das Senderverzeichnis
  vorübergehend nicht erreichbar ist.
- Geänderte Stream-URLs können über die stabile Verzeichnis-ID aktualisiert werden,
  ohne Favoriten oder Gruppen zu verlieren.
- Verlauf und Empfehlungen lassen sich vollständig deaktivieren und löschen.

## Plugin 0.5 – Netzwerkstabilität und Datenschutz

Ziel: Unzuverlässige öffentliche Streams fühlen sich kontrolliert an und gefährden
weder Player noch Privatsphäre.

### Featureliste

- **MUSS – Wiederverbindung:** Begrenzte automatische Neuverbindung mit wachsender
  Wartezeit; sofortige manuelle Wiederholung bleibt möglich.
- **MUSS – Alternativ-URL:** Falls das Verzeichnis mehrere gültige Endpunkte liefert,
  nach einem Fehler kontrolliert zum nächsten wechseln.
- **MUSS – Pufferprofil:** Kleine, normale und stabile Pufferung anbieten; Wechsel
  wirkt ab der nächsten Verbindung.
- **MUSS – Verbindungsdiagnose:** Timeout, DNS-Fehler, TLS-Fehler, nicht unterstützter
  Codec und ungültige Playlist unterscheidbar melden.
- **MUSS – Offline-Verhalten:** Favoriten und Verlauf bleiben sichtbar; Aktionen mit
  Netzwerkbedarf werden eindeutig als offline gekennzeichnet.
- **MUSS – Datenschutz:** Keine Telemetrie, kein Standortzugriff und kein Konto.
  Netzwerkziele und lokal gespeicherte Radiodaten werden dokumentiert.
- **SOLL – Metadaten-/Logo-Cache:** Größen- und zeitbegrenzt, manuell löschbar und
  ohne dauerhaftes Speichern des Audiostreams.
- **SOLL – Proxy-Unterstützung:** Systemproxy verwenden und Proxyfehler verständlich
  anzeigen.
- **OPTIONAL – Stream-Gesundheit:** Lokal erfolgreiche und fehlgeschlagene
  Verbindungen anzeigen, ohne ungefragt Daten an Dritte zu melden.

### Abnahme

- Netzwerkverlust, Standby und Gerätewechsel führen nicht zum App-Absturz.
- Wiederverbindung kann jederzeit durch Stop oder Senderwechsel abgebrochen werden.
- Cache, Verlauf und Favoriten werden von Sicherung, Wiederherstellung und
  Deinstallation korrekt behandelt.

## Plugin 1.0 – Stabiles Internetradio

Ziel: Funktionsumfang einfrieren, alle Kernabläufe absichern und das Plugin als
stabile Erweiterung des Players ausliefern.

### Ausgelieferter Funktionsumfang

- integrierte Live-Wiedergabe ohne externen Browser oder Player
- Sendersuche mit kombinierbaren Länder-, Regions-, Orts-, Sprach-, Genre-, Codec-
  und Bitratenfiltern
- Favoriten, Verlauf, populäre, neue und zufällige Sender
- eigene Stream-URLs und Favoritenexport
- Live-Metadaten, Senderdetails und Logos, soweit verfügbar
- robuste Pufferung, Wiederverbindung und verständliche Fehlerdiagnose
- Nutzung der vorhandenen Audioausgabe, Mehrkanalkonfiguration, Equalizer,
  Lautstärke, Visualizer, Skins und Modulverwaltung

### Release-Gates

- keine bekannten reproduzierbaren Abstürze, Thread-Lecks oder dauerhaft blockierten
  Wiedergabezustände
- automatisierte Tests für Verzeichnissuche, Filter, Playlist-Auflösung,
  Metadatenparser, Timeouts, Wiederverbindung und Datenmigration
- Integrationstests mit lokalen Testservern; öffentliche Sender dienen nur dem
  manuellen Smoke-Test und nicht als dauerhaft fragile Testabhängigkeit
- manueller Langzeittest mit Senderwechseln, Netzwerkausfall, Standby,
  Audio-Gerätewechsel und verschiedenen Codecs
- Plugin kann deaktiviert werden, ohne lokale Playerfunktionen oder deren Daten zu
  verändern
- Datenquelle, Kartenfreiheit, Datenschutz, Lizenzen, Cache und bekannte
  Einschränkungen sind dokumentiert

## Empfohlene Umsetzungsreihenfolge

1. Plugin-Zugriffsgrenzen und netzwerkfähige Audioquelle
2. ein stabiler direkter Stream im Hauptplayer
3. Radio-Modul und Live-Metadaten
4. Verzeichnisadapter und paginierte Suche
5. kombinierbare Filter
6. Favoriten, Verlauf, Zufall und eigene URLs
7. Wiederverbindung, Cache, Diagnose und Datenschutz
8. Formatmatrix, Langzeittest und Plugin-1.0-Release

## Recherchegrundlage

- [Radio Garden](https://radio.garden/) als Referenz für einfache weltweite
  Senderentdeckung, Suche, Browse und Favoriten
- [Radio-Browser-API](https://docs.radio-browser.info/) als vorgeschlagene erste
  offene Verzeichnisquelle mit Such-, Filter- und Sender-Metadaten
