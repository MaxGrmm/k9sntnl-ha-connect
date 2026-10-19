# Hinweise für Claude

- Kommunikation auf Deutsch. Der Projektinhaber ist Einsteiger in der Softwareentwicklung:
  in kleinen Schritten arbeiten und jeden Schritt verständlich erklären (was, warum, wo).
- Dieses Repo ist die Home-Assistant-Integration für K9SNTNL. Server, App und Fahrplan liegen in
  `MaxGrmm/k9sntnl-backend` (siehe dort `docs/ARCHITEKTUR.md`, Punkt 11, und Issue #21).
  Die Schnittstellen, die die Integration nutzt, stehen in `custom_components/k9sntnl/api.py`.
- Tests: `.venv/bin/pytest`. Vorher: `python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt`.
- Code-Namen englisch, Kommentare/Doku deutsch. Texte in Home Assistant: `translations/de.json` und `en.json`
  (beide pflegen). Immer „Box“, nie „Hundebox“.
- Keine Passwörter, Tokens oder Schlüssel als Text im Code – auch nicht in Tests (`secrets.token_urlsafe`).
- Offene Punkte als GitHub Issue anlegen. Nach jeder Änderung zu einem Issue einen vollständigen Kommentar
  darunter setzen: aktueller Gesamtstand, was geändert wurde, Link zum PR, was noch offen ist.
- Fertige Änderungen direkt als Pull Request einreichen (nicht erst nachfragen) – außer der Projektinhaber
  sagt ausdrücklich, dass kein PR erstellt werden soll. Bei jeder Änderung die Version in `manifest.json` erhöhen.
