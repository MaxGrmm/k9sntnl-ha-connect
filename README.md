# K9SNTNL für Home Assistant

*English:* Home Assistant integration for K9SNTNL dog trailers: trailers and boxes as devices, temperature/humidity/
voltage/power sensors, connectivity of sensors and trailer, and cameras (snapshots and live view). Install via HACS as a
custom repository, then pair with the code shown in the K9SNTNL app under *My account → Home Assistant*. Read-only.

Zeigt deine K9SNTNL-Anhänger in Home Assistant an: jeder Anhänger und jede Box als Gerät, die Fühler
(Temperatur, Luftfeuchte, Spannung, Leistung) als Sensoren, die Kameras mit Live-Bild und der Online-Status
von Sensoren und Anhänger.

Home Assistant kann dabei **nur lesen**, nichts ändern – mit denselben Rechten wie du in der K9SNTNL-App.

## Installation (HACS)

1. In HACS oben rechts **⋮ → Benutzerdefinierte Repositories**, Adresse
   `https://github.com/MaxGrmm/k9sntnl-ha-connect`, Typ **Integration**.
2. „K9SNTNL“ herunterladen und Home Assistant neu starten.

Updates zeigt HACS an, sobald es ein neues [Release](https://github.com/MaxGrmm/k9sntnl-ha-connect/releases) gibt.
Sofort prüfen: in HACS bei K9SNTNL **⋮ → Informationen aktualisieren**.

## Verbinden

1. In der K9SNTNL-App: **Mein Konto → Home Assistant → Home Assistant verbinden**. Die App zeigt einen
   Code wie `K7QP-4MZX` (10 Minuten gültig).
2. In Home Assistant: **Einstellungen → Geräte & Dienste → Integration hinzufügen → K9SNTNL** und den Code eingeben.

Die Verbindung siehst du danach in der App und kannst sie dort jederzeit trennen. Sie endet auch, wenn du
dich in der App auf allen Geräten abmeldest oder dein Passwort änderst – Home Assistant fragt dann nach einem neuen Code.

## Was du bekommst

| Entität | Gerät | Inhalt |
|---|---|---|
| Sensor je Fühler | Box bzw. Anhänger | Letzter Messwert; Attribute: Messzeit, `alert` (ok/high/low), Grenzwerte |
| „Sensoren“ (Verbindung) | Anhänger | Liefern die Sensoren am Anhänger Daten? |
| „Anhänger“ (Verbindung) | Anhänger | Ist der Anhänger (LTE-Router) online? Nur, wenn ein Tunnel eingerichtet ist |
| Kamera | Box bzw. Anhänger | Live-Bild (HLS), z. B. in der Karte „Bild-Entität“ mit Kameraansicht „live“ |

### Kameras und Datenvolumen

Das Bild kommt über das LTE-Netz des Anhängers. Deshalb holt Home Assistant das **Live-Bild nur, solange
jemand zuschaut**. Vorschaubilder (z. B. in einer Kachel) sind **Standbilder vom K9SNTNL-Server**: je Kamera
höchstens eins alle 30–90 Sekunden – wie oft, stellt der Eigentümer in der App unter „Einrichten → Kameras“ ein –
und nur, solange ein Dashboard mit der Kamera offen ist. Jedes Standbild kostet etwa 0,3–1 MB.
Ein Dashboard, das rund um die Uhr offen ist (z. B. ein Wand-Tablet), holt also ständig Standbilder.

Die Werte werden alle 30 Sekunden abgefragt.

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```
