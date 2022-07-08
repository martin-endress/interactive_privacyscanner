## Evaluation: Third Party Tracking auf .de domains

Analyse von `.de` domains auf Tracking Eigenschaften vor und nach Einwilligung des Consent Banners.

### Auswahl Seiten
Zufällige Auswahl von 200 domains der [tranco-list](https://tranco-list.eu/) innerhalb der Top 1000 `.de` domains.

### Datenerhebung

Das Tool untersucht Webseiten nach Trackingeigenschaften (Cookie Sync + Fingerprint). In der Datenerhebung werden 200 zufällig gewählte .de Seiten untersucht.

Stand Untersuchung: https://psi.secpad.de/p/endress-klickstudie

Vorgehen:
1. URL aus Liste auswählen
2. Starte Scan (Websocket muss verbunden sein)
3. Warte, bis Interaktion mit Seite möglich
4. Suche nach Cookie Notice
    1. sofern vorhanden: untersuche ob Modal (Interaktion möglich) -> Screenshot falls Interaktion nicht möglich; -> Einwilligung aller Cookies
    2. wenn nicht vorhanden -> Screenshot.
5. Scan beenden

Notizen:  
`x` kein Banner  
`m` Modal, keine Interaktion möglich  
oder Freitext

Hinweise:
- Falls kritische Fehler auftreten: Seite neu Laden und Scan einmal erneut probieren. Falls es dann immernoch nicht klappt, Seite als fehlerhaft vermerken und weiter mit nächster Seite.
- Das Tool hat noch ein Paar bugs, z.B. dauert das Verbinden mit dem Websocket manchmal etwas (bis zu 10s). Es liegt an Caching, nicht an eurem Browser.
- Der Fehler `Guacamole msg:guac error (status=519) - Aborted. See logs.` kann ignoriert werden. Es wird automatisch neu verbunden. Falls länger nicht klappt, siehe oben.

Die Datenerhebung wird in folgendem Aktivitätsdiagramm zusammengefasst:

![Activity Diagram](activity.png)
