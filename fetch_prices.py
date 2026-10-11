"""Prijsmotor voor de Trendradar.

Haalt elke werkdag de slotkoersen op van alle tickers in tickers.csv
(via yfinance / Yahoo Finance) en schrijft:
  data/prijzen.json    -> per ticker: laatste koers, 200-dagengemiddelde, rendement 1m/3m/1j, afstand tot top
  data/slotkoersen.csv -> slotkoersen van de laatste ~2 jaar (om rendement sinds een datum te meten)
Een ticker die mislukt, krijgt "fout" en laat de rest gewoon doorlopen.
"""
import csv
import json
import datetime as dt
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).parent
DATA = ROOT / "data"


def lees_tickers():
    with open(ROOT / "tickers.csv", newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("ticker", "").strip()]


def pct(nu, toen):
    if toen is None or pd.isna(toen) or toen == 0:
        return None
    return round((nu / toen - 1) * 100, 1)


def meet(reeks: pd.Series):
    reeks = reeks.dropna()
    if len(reeks) < 2:
        raise ValueError("te weinig koersen")
    laatste = float(reeks.iloc[-1])

    def terug(n):
        return float(reeks.iloc[-1 - n]) if len(reeks) > n else None

    sma200 = float(reeks.iloc[-200:].mean()) if len(reeks) >= 200 else None
    top52 = float(reeks.iloc[-252:].max())
    return {
        "datum": reeks.index[-1].strftime("%Y-%m-%d"),
        "koers": round(laatste, 4),
        "sma200": round(sma200, 4) if sma200 else None,
        "boven_sma200": (laatste > sma200) if sma200 else None,
        "afstand_sma200_pct": pct(laatste, sma200) if sma200 else None,
        "m1": pct(laatste, terug(21)),
        "m3": pct(laatste, terug(63)),
        "j1": pct(laatste, terug(252)),
        "top_52w": round(top52, 4),
        "onder_top_pct": pct(laatste, top52),
    }


def main():
    rijen = lees_tickers()
    tickers = [r["ticker"].strip() for r in rijen]
    ruw = yf.download(tickers, period="2y", interval="1d", auto_adjust=True,
                      group_by="ticker", progress=False, threads=True)
    resultaat, slot = {}, {}
    for r in rijen:
        t = r["ticker"].strip()
        basis = {"naam": r.get("naam", ""), "groep": r.get("groep", "")}
        try:
            reeks = ruw[t]["Close"] if isinstance(ruw.columns, pd.MultiIndex) else ruw["Close"]
            basis.update(meet(reeks))
            slot[t] = reeks.dropna()
            try:
                basis["munt"] = yf.Ticker(t).fast_info.get("currency")
            except Exception:
                basis["munt"] = None
        except Exception as e:  # één foute ticker mag de rest niet stoppen
            basis["fout"] = str(e)[:200]
        resultaat[t] = basis

    DATA.mkdir(exist_ok=True)
    uit = {
        "bijgewerkt_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "bron": "Yahoo Finance via yfinance (onofficieel; controleer belangrijke cijfers)",
        "uitleg": {
            "koers": "laatste slotkoers in de munt van de beurs",
            "sma200": "gemiddelde slotkoers van de laatste 200 beursdagen (regel R9)",
            "m1/m3/j1": "koersverandering in % over 1 maand, 3 maanden, 1 jaar",
            "onder_top_pct": "hoeveel % de koers onder de hoogste koers van het laatste jaar staat",
        },
        "tickers": resultaat,
    }
    (DATA / "prijzen.json").write_text(json.dumps(uit, ensure_ascii=False, indent=1), encoding="utf-8")
    if slot:
        pd.DataFrame(slot).sort_index().round(4).to_csv(DATA / "slotkoersen.csv", index_label="datum")
    fouten = [t for t, v in resultaat.items() if "fout" in v]
    print(f"{len(resultaat) - len(fouten)} gelukt, {len(fouten)} mislukt: {fouten}")


if __name__ == "__main__":
    main()
