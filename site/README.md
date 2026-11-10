# StudIPSync Website

Diese Dateien bilden eine statische Cloudflare-Pages-Website.

## Vor der Veröffentlichung ersetzen

- `[Name / Organisation]`
- `[Postanschrift]`
- `[Straße und Hausnummer]`
- `[PLZ Ort]`
- `[E-Mail-Adresse]`
- `[Name der verantwortlichen Person]`
- die Download-URL in `index.html`

Der Text in `datenschutz.html` ist ein technischer Entwurf und ersetzt keine
rechtliche Prüfung.

## Cloudflare Pages

Beim Verbinden des Repositorys als Root-Verzeichnis `site` verwenden. Es ist
kein Build-Befehl erforderlich; als Ausgabeverzeichnis genügt `.`.

Alternativ kann der Inhalt dieses Ordners als fertige statische Website direkt
hochgeladen werden. PHP wird nicht benötigt. JavaScript wird derzeit ebenfalls
nicht benötigt.

## Logo-Dateien

- `assets/logo.svg`: skalierbares Logo für die Website
- `assets/google-oauth-logo-120.png`: 120 × 120 px für den Google-OAuth-Zustimmungsbildschirm
- `assets/icon-192.png` und `assets/icon-512.png`: Web-App-Icons
- `assets/apple-touch-icon.png`: Icon für iOS-Favoriten
- `favicon.ico`: Browser- und Google-Suchergebnis-Icon

Das Windows-App-Icon liegt zusätzlich unter `../assets/studipsync.ico` und wird
vom PyInstaller-Build automatisch in die EXE übernommen.
