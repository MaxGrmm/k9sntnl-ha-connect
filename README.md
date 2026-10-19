# K9SNTNL für Home Assistant

Zeigt deine K9SNTNL-Anhänger in Home Assistant an: jeder Anhänger und jede Box als Gerät, die Fühler
(Temperatur, Luftfeuchte, Spannung, Leistung) als Sensoren und der Online-Status von Sensoren und Anhänger.
Kameras folgen.

Home Assistant kann dabei **nur lesen**, nichts ändern – mit denselben Rechten wie du in der K9SNTNL-App.

## Installation (HACS)

1. In HACS oben rechts **⋮ → Benutzerdefinierte Repositories**, Adresse
   `https://github.com/MaxGrmm/k9sntnl-ha-connect`, Typ **Integration**.
2. „K9SNTNL“ herunterladen und Home Assistant neu starten.

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

Die Werte werden alle 30 Sekunden abgefragt.

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```
