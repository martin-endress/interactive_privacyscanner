## Evaluation Konzept: Third Party Tracking auf .de domains

Analyse von `.de` domains auf Tracking Eigenschaften vor und nach Einwilligung des Consent Banners.

### Auswahl Seiten
Beispielsweise Top 100 `.de` domains der [tranco-list](https://tranco-list.eu/), oder random sample von top 1k.

### Vorgehen
Beim Besuch der Seite werden gesetzte Cookies und third party requests sowie JS Funktionsaufrufe aufgezeichnet.
Gespeichert werden Cookies, requests und Funktionsaufrufe jeweils vor und nach der Einwilligung des Banners, sofern dieser vorhanden ist.
Das eventuelle Fehlen des Banners wird als Notiz vermerkt.

### Datenerhebung Aktivitätsdiagramm

Die Datenerhebung wird in folgendem Aktivitätsdiagramm zusammengefasst:

![Activity Diagram](activity.png)

### Auswertung

Die Auswertung ist in Teilen eine Replikation des [ConsentGuard](https://gitlab.com/papamano/consent-guard/) Paper von Papadogiannakis und anderen (2021).

Sie soll folgende Fragen beantworten:
- Welche der third party requests sowie der gesetzten Cookies vor (bzw. nach) Nutzer Einwilligung sind tracker (tracking Kontext)?
  - Welche requests kamen erst nach der Einwilligung hinzu?
- Gibt es einen Cookie Banner?
- Gibt es vor Einwilligung tracking ID leaks? 
- Gibt es vor Einwilligung bereits Funktionsaufrufe die im Tracking Kontext stehen? (vielleicht out of scope?)

Weitere optionale Fragestellungen: (out of scope)
- Besteht korrekte Verwendung von anonymize IP?
- Ist die Seite während der Darstellung des consent Banners benutzbar?
- Kann der Consent (einfach!) wiederrufen werden?

Für die Klassifizierung der Requests und Cookies wird [adblockeval](https://github.com/hprid/adblockeval) mithilfe der Tracking Datenbanken EasyList und EasyPrivacy verwendet.
Die tracking ID leaks werden anhand des Request logs ausgewertet (vgl. [leaks.js](https://gitlab.com/papamano/consent-guard/-/blob/main/Source/Detector/detectors/leaks.js)).
Der log der Funktionsaufrufe wird mit bekannten tracking Funktionen verglichen (vgl. [fingerprinting.js](https://gitlab.com/papamano/consent-guard/-/blob/main/Source/Detector/detectors/fingerprinting.js)).


### Vorläufige Studie

Eine Teststudie wurde an 5 zufällig gewählten Seiten der Tranco Top 1k Liste durchgeführt:
Zum Zeitpunkt der vorläufigen Studie ist die Analyse teilweise automatisiert, teilweise manuell (vgl. [Analyse Python Skript](https://github.com/martin-endress/interactive_privacyscanner/blob/main/manager/test_main.py)).

Die Analyse enthält nicht die Fragestellung der Fingerprinting Funktionsaufrufe. Diese werden vom scanner noch nicht aufgezeichnet.

Ausgewählte Seiten (keine DE domains):
- https://mercadolibre.com.ar/
- https://crunchyroll.com/
- https://playstation.net/
- https://scribd.com/
- https://stumbleupon.com/


#### https://mercadolibre.com.ar/

Alle 6 Cookies, welche vor Einwilligung geladen werden, stehen im Tracking Kontext. 2 davon scheinen 'echte' third party tracker zu sein: `nr-data.net` und `doubleclick.net`.

Der First Party tracking Cookie (value="aa33158d-f6f3-4d57-a6d0-f33b4ff56fff") wird als post Request an `google-analytics.com` geleakt.

Nach consent werden keine weiteren Tracker und Cookies geladen bzw. gesetzt.

Es folgt die Ausgabe des [Analyse Skripts](https://github.com/martin-endress/interactive_privacyscanner/blob/main/manager/test_main.py):

```
Analysis of https://mercadolibre.com.ar/:
 Cookie Analysis:
   TP tracking cookie domains before (n=6): {'.mercadopago.com.ar', '.mercadolibre.com', '.nr-data.net', '.mercadoshops.com.ar', '.doubleclick.net', '.mercadopago.com'}
   TP tracking cookie domains after (n=6): {'.mercadopago.com.ar', '.mercadolibre.com', '.nr-data.net', '.mercadoshops.com.ar', '.doubleclick.net', '.mercadopago.com'}
 TP request Analysis:
   TP before:24 / 24 (trackers / total TPs)
   TP after: 2 / 2
   trackers before (n=24):
{'39b1b09e47ad07d22f61f98b0ff3f5bb.safeframe.googlesyndication.com', 'melidata.mercadopago.com', 'adservice.google.com', 'melidata.mercadolibre.com', 'www.google.com', 'script.hotjar.com', 'melidata.mercadopago.com.ar', 'adservice.google.de', 'www.google-analytics.com', 'js-agent.newrelic.com', 'www.google.de', 'melidata.mercadoshops.com.ar', 'bam.nr-data.net', 'pagead2.googlesyndication.com', 'static.hotjar.com', 'http2.mlstatic.com', 'vc.hotjar.io', 'analytics.mercadolibre.com', 'api.mercadolibre.com', 'tpc.googlesyndication.com', 'securepubads.g.doubleclick.net', 'vars.hotjar.com', 'www.googletagservices.com', 'stats.g.doubleclick.net'}
   trackers after (n=2):
{'api.mercadolibre.com', 'bam.nr-data.net'}
   additional trackers (n=0):
set()
```

#### https://crunchyroll.com/

Die Seite Crunchyroll verwendet ein Opt-Out Mechanismus und leitet nicht auf die deutsche Seite weiter. Die durchgeführte Interaktion ist kein consent, sondern Opt-Out. Neue third party domain im tracking Kontext: `csm.nl.eu.criteo.net`. Die Seite setzt 10 Cookies im tracking Kontext.


```
Analysis of https://crunchyroll.com/:
  Cookie Analysis:
   TP tracking cookie domains before (n=10): {'.t.co', '.casalemedia.com', '.analytics.yahoo.com', '.yahoo.com', '.twitter.com', '.krxd.net', '.criteo.com', '.fwmrm.net', '.doubleclick.net', 'ads.stickyadstv.com'}
   TP tracking cookie domains after (n=10): {'.t.co', '.casalemedia.com', '.analytics.yahoo.com', '.yahoo.com', '.twitter.com', '.krxd.net', '.criteo.com', '.fwmrm.net', '.doubleclick.net', 'ads.stickyadstv.com'}
 TP request Analysis:
   TP before:66 / 67 (trackers / total TPs)
   TP after: 15 / 15
   trackers before (n=66):
{'ib.adnxs.com', 'exchange.mediavine.com', 'analytics.twitter.com', 'dis.criteo.com', 'contextual.media.net', 'trends.revcontent.com', 'dgcollector.evidon.com', '1f2e7.v.fwmrm.net', 'partner.mediawallahscript.com', 'fonts.googleapis.com', 'connect.facebook.net', 'pixel.rubiconproject.com', 'fonts.gstatic.com', 'l.evidon.com', 'ssl.google-analytics.com', 's.ad.smaato.net', 'ads.stickyadstv.com', 'idsync.rlcdn.com', 'cdn.segment.io', 'match.sharethrough.com', 'dntcl.qualaroo.com', 'cm.g.doubleclick.net', 'ads.yahoo.com', 'rtb-csync.smartadserver.com', 'gum.criteo.com', 'widget.us.criteo.com', 'criteo-sync.teads.tv', 'static.ads-twitter.com', 'sslwidget.criteo.com', 'js.adsrvr.org', 'platform.twitter.com', 'jadserve.postrelease.com', 'www.googletagmanager.com', 'www.google-analytics.com', 'i.liadm.com', 'www.google.com', 'www.googleadservices.com', 'conduit.redfast.com', 'beacon.krxd.net', 'syndication.twitter.com', 'sp.analytics.yahoo.com', 'sync-t1.taboola.com', 'secure.adnxs.com', 'r.casalemedia.com', 'c.evidon.com', '8f2bfa24-f12a-458a-89ac-391b91f711e3.redfastlabs.com', 'cw.addthis.com', 'x.bidswitch.net', 'cdn.stickyadstv.com', 't.co', 'stats.g.doubleclick.net', 'www.facebook.com', 'static.xx.fbcdn.net', 'mssl.fwmrm.net', 'eb2.3lift.com', 'cl.qualaroo.com', 'simage2.pubmatic.com', 'sync.outbrain.com', '5fd74.v.fwmrm.net', 'ad.360yield.com', 'googleads.g.doubleclick.net', 'ups.analytics.yahoo.com', 'criteo-partners.tremorhub.com', 'static.criteo.net', 'www.google.de', 'insight.adsrvr.org'}
   trackers after (n=15):
{'conduit.redfast.com', 'csm.nl.eu.criteo.net', 'mssl.fwmrm.net', 'dgcollector.evidon.com', 'fonts.googleapis.com', 'fonts.gstatic.com', 'c.evidon.com', 'l.evidon.com', '8f2bfa24-f12a-458a-89ac-391b91f711e3.redfastlabs.com', 'www.googletagmanager.com', 'ssl.google-analytics.com', 'www.google-analytics.com', 'optoutapi.evidon.com', 'www.facebook.com', 'cdn.segment.io'}
   additional trackers (n=2):
{'optoutapi.evidon.com', 'csm.nl.eu.criteo.net'}
```

#### Manueller Follow up scan mit der deutschen Seite https://crunchyroll.com/de/

Die deutsche Seite verwendet Opt-in mechanismus. Kein TP cookie wird vor der Zustimmung gesetzt. Alle 12 TP requests vor Einwilligung sind laut easylist / easyprivacy im tracking kontext.

```
Analysis of https://crunchyroll.com/de/:
 Cookie Analysis:
   TP tracking cookie domains before (n=0): set()
   TP tracking cookie domains after (n=10): {'.t.co', '.casalemedia.com', '.analytics.yahoo.com', '.yahoo.com', '.twitter.com', '.krxd.net', '.criteo.com', '.fwmrm.net', '.doubleclick.net', 'ads.stickyadstv.com'}
 TP request Analysis:
   TP before:12 / 12 (trackers / total TPs)
   TP after: 66 / 67
   trackers before (n=12):
{'conduit.redfast.com', 'mssl.fwmrm.net', 'dgcollector.evidon.com', 'fonts.googleapis.com', 'fonts.gstatic.com', 'c.evidon.com', '8f2bfa24-f12a-458a-89ac-391b91f711e3.redfastlabs.com', 'l.evidon.com', 'www.googletagmanager.com', 'ssl.google-analytics.com', 'www.google-analytics.com', 'cdn.segment.io'}
   trackers after (n=66):
{'ib.adnxs.com', 'exchange.mediavine.com', 'analytics.twitter.com', 'dis.criteo.com', 'contextual.media.net', 'trends.revcontent.com', 'dgcollector.evidon.com', '1f2e7.v.fwmrm.net', 'partner.mediawallahscript.com', 'fonts.googleapis.com', 'connect.facebook.net', 'pixel.rubiconproject.com', 'fonts.gstatic.com', 'l.evidon.com', 'ssl.google-analytics.com', 'ads.stickyadstv.com', 'idsync.rlcdn.com', 'cdn.segment.io', 'match.sharethrough.com', 'dntcl.qualaroo.com', 'cm.g.doubleclick.net', 'ads.yahoo.com', 'rtb-csync.smartadserver.com', 'gum.criteo.com', 'widget.us.criteo.com', 'criteo-sync.teads.tv', 'static.ads-twitter.com', 'sslwidget.criteo.com', 'js.adsrvr.org', 'platform.twitter.com', 'jadserve.postrelease.com', 'www.googletagmanager.com', 'www.google-analytics.com', 'i.liadm.com', 'www.google.com', 'www.googleadservices.com', 'conduit.redfast.com', 'beacon.krxd.net', 'syndication.twitter.com', 'sp.analytics.yahoo.com', 'sync-t1.taboola.com', 'd.turn.com', 'secure.adnxs.com', 'r.casalemedia.com', 'c.evidon.com', '8f2bfa24-f12a-458a-89ac-391b91f711e3.redfastlabs.com', 'cw.addthis.com', 'x.bidswitch.net', 'cdn.stickyadstv.com', 't.co', 'stats.g.doubleclick.net', 'www.facebook.com', 'static.xx.fbcdn.net', 'mssl.fwmrm.net', 'eb2.3lift.com', 'cl.qualaroo.com', 'simage2.pubmatic.com', 'sync.outbrain.com', '5fd74.v.fwmrm.net', 'ad.360yield.com', 'googleads.g.doubleclick.net', 'ups.analytics.yahoo.com', 'criteo-partners.tremorhub.com', 'static.criteo.net', 'www.google.de', 'insight.adsrvr.org'}
   additional trackers (n=54):
{'ib.adnxs.com', 'dis.criteo.com', 'trends.revcontent.com', 'connect.facebook.net', 'pixel.rubiconproject.com', 'idsync.rlcdn.com', 'cm.g.doubleclick.net', 'rtb-csync.smartadserver.com', 'gum.criteo.com', 'criteo-sync.teads.tv', 'static.ads-twitter.com', 'sslwidget.criteo.com', 'jadserve.postrelease.com', 'i.liadm.com', 'www.google.com', 'beacon.krxd.net', 'sp.analytics.yahoo.com', 'secure.adnxs.com', 'r.casalemedia.com', 't.co', 'www.facebook.com', 'eb2.3lift.com', 'sync.outbrain.com', 'ad.360yield.com', 'googleads.g.doubleclick.net', 'static.criteo.net', 'www.google.de', 'insight.adsrvr.org', 'exchange.mediavine.com', 'analytics.twitter.com', 'contextual.media.net', '1f2e7.v.fwmrm.net', 'partner.mediawallahscript.com', 'ads.stickyadstv.com', 'match.sharethrough.com', 'dntcl.qualaroo.com', 'ads.yahoo.com', 'widget.us.criteo.com', 'js.adsrvr.org', 'platform.twitter.com', 'www.googleadservices.com', 'syndication.twitter.com', 'sync-t1.taboola.com', 'd.turn.com', 'cw.addthis.com', 'x.bidswitch.net', 'cdn.stickyadstv.com', 'stats.g.doubleclick.net', 'static.xx.fbcdn.net', 'cl.qualaroo.com', 'simage2.pubmatic.com', '5fd74.v.fwmrm.net', 'ups.analytics.yahoo.com', 'criteo-partners.tremorhub.com'}
```

#### https://playstation.net/

Seite nicht verfügbar. (Could not resolve name)

#### https://scribd.com/


Scribd setzt 1 cookie für tiktok vor Interaktion mit dem Cookie consent banner, wahrscheinlich ein tracking cookie (value="2AUnmAeHxwVFGTeCZp9ca4Tb03f").

Nach consent werden skripte von 28 weiteren domains geladen.

Einige requests 

```
Analysis of https://scribd.com/:
 Cookie Analysis:
   TP tracking cookie domains before (n=1): {'.tiktok.com'}
   TP tracking cookie domains after (n=14): {'.yahoo.com', 'www.clarity.ms', '.ads.linkedin.com', '.linkedin.com', '.liadm.com', '.bing.com', '.doubleclick.net', '.tiktok.com', '.twitter.com', '.c.bing.com', '.www.linkedin.com', '.clarity.ms', '.t.co', '.c.clarity.ms'}
 TP request Analysis:
   TP before:17 / 18 (trackers / total TPs)
   TP after: 31 / 31
   trackers before (n=17):
{'', 'd1lu3pmaz2ilpx.cloudfront.net', 'd2hrivdxn8ekm8.cloudfront.net', 'utt.impactcdn.com', 'dvqigh9b7wa32.cloudfront.net', 'browser.sentry-cdn.com', 'www.facebook.com', 'cmp.osano.com', 'connect.facebook.net', 'imgv2-2-f.scribdassets.com', 'imgv2-1-f.scribdassets.com', 'acdn.adnxs.com', 'ib.adnxs.com', 'www.googletagmanager.com', 's-f.scribdassets.com', 'apis.google.com', 'd330aiyvva2oww.cloudfront.net'}
   trackers after (n=31):
{'', 'hexagon-analytics.com', 'c.bing.com', 'www.googleadservices.com', 'cdn.siftscience.com', 'us-central1-adaptive-growth.cloudfunctions.net', 'www.clarity.ms', 'stats.g.doubleclick.net', 'snap.licdn.com', 'www.google.com', 's.yimg.com', 'static.ads-twitter.com', 'cdn.pdst.fm', 'alb.reddit.com', 'cmp.osano.com', 'www.redditstatic.com', 'px.ads.linkedin.com', 'rp.liadm.com', 'm.clarity.ms', 'googleads.g.doubleclick.net', 't.co', 'www.linkedin.com', 'bat.bing.com', 'analytics.twitter.com', 'www.google.de', 'c.clarity.ms', 'sp.analytics.yahoo.com', 'www.facebook.com', 'consent.api.osano.com', 'b-code.liadm.com', 'www.google-analytics.com'}
   additional trackers (n=28):
{'hexagon-analytics.com', 'c.bing.com', 'www.googleadservices.com', 'cdn.siftscience.com', 'us-central1-adaptive-growth.cloudfunctions.net', 'www.clarity.ms', 'stats.g.doubleclick.net', 'snap.licdn.com', 'www.google.com', 's.yimg.com', 'static.ads-twitter.com', 'cdn.pdst.fm', 'alb.reddit.com', 'www.redditstatic.com', 'px.ads.linkedin.com', 'rp.liadm.com', 'm.clarity.ms', 'googleads.g.doubleclick.net', 't.co', 'www.linkedin.com', 'bat.bing.com', 'analytics.twitter.com', 'www.google.de', 'c.clarity.ms', 'sp.analytics.yahoo.com', 'consent.api.osano.com', 'b-code.liadm.com', 'www.google-analytics.com'}

```

#### https://stumbleupon.com/

Seite setzt keine Cookies im tracking kontext.

Skripte sind wahrscheinlich keine tracker.

```
Analysis of https://stumbleupon.com/:
 Cookie Analysis:
   TP tracking cookie domains before (n=0): set()
   TP tracking cookie domains after (n=0): set()
 TP request Analysis:
   TP before:4 / 4 (trackers / total TPs)
   TP after: 0 / 0
   trackers before (n=4):
{'img.mix.com', 'into.mix.com', 'www.googletagmanager.com', 'region1.google-analytics.com'}
   trackers after (n=0):
set()
   additional trackers (n=0):
set()

```
