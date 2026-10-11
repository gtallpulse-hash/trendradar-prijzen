# Prijsmotor voor de Trendradar

Elke werkdagochtend haalt GitHub automatisch koersen op voor de tickers in `tickers.csv`
en zet ze in `data/prijzen.json` en `data/slotkoersen.csv`. De Trendradar (Claude) leest die bestanden.

- Ticker toevoegen of schrappen: vraag het aan Claude (of pas `tickers.csv` aan).
- Met de hand starten: tabblad **Actions** → **Prijzen ophalen** → **Run workflow**.
- Bron: Yahoo Finance via yfinance (onofficieel). Belangrijke cijfers altijd nakijken.
