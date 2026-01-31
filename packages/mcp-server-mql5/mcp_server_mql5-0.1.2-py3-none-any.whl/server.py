from mcp.server.fastmcp import FastMCP
import subprocess
import os
import tempfile
import sys
import requests
from bs4 import BeautifulSoup
import urllib.parse
import glob

# --- AUTO-DETECTION FUNKTION ---
def find_metaeditor():
    """
    Sucht automatisch nach metaeditor64.exe in gängigen MT5-Installationspfaden.
    """
    search_patterns = [
        r"C:\Program Files\MetaTrader 5*\metaeditor64.exe",
        r"C:\Program Files (x86)\MetaTrader 5*\metaeditor64.exe",
        os.path.expanduser(r"~\AppData\Roaming\MetaQuotes\Terminal\*\metaeditor64.exe")
    ]
    
    for pattern in search_patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]  # Nimmt die erste gefundene Installation
    
    return None

# --- KONFIGURATION ---
# Liest den Pfad aus der Config oder nutzt Auto-Detection
METAEDITOR_PATH = os.getenv("MQL5_EDITOR_PATH") or find_metaeditor()
# ---------------------

mcp = FastMCP("MQL5 Developer Suite")

@mcp.tool()
def compile_mql5(code: str, filename: str = "ExpertAdvisor") -> str:
    """
    Kompiliert MQL5 Code über den MetaEditor und gibt die GENAUEN Fehlermeldungen 
    und Warnungen aus dem Log zurück.
    """
    if not METAEDITOR_PATH:
        return """KONFIGURATIONS-FEHLER: MetaEditor wurde nicht gefunden.

Bitte setzen Sie 'MQL5_EDITOR_PATH' in Ihrer MCP-Config:

Häufige Pfade:
- C:\\Program Files\\MetaTrader 5 [IHR_BROKER]\\metaeditor64.exe
- C:\\Program Files (x86)\\MetaTrader 5 [IHR_BROKER]\\metaeditor64.exe

So finden Sie Ihren Pfad:
1. Rechtsklick auf MetaEditor → Eigenschaften → "Ziel" kopieren
2. In claude_desktop_config.json unter "MQL5_EDITOR_PATH" eintragen
"""
    
    if not os.path.exists(METAEDITOR_PATH):
        return f"PFAD-FEHLER: MetaEditor nicht gefunden unter:\n{METAEDITOR_PATH}\nBitte Pfad prüfen."

    with tempfile.TemporaryDirectory() as temp_dir:
        mq5_file = os.path.join(temp_dir, f"{filename}.mq5")
        log_file = os.path.join(temp_dir, f"{filename}.log")
        
        try:
            with open(mq5_file, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            return f"SCHREIB-FEHLER: {str(e)}"
            
        try:
            # Headless Kompilierung
            subprocess.run([METAEDITOR_PATH, f"/compile:{mq5_file}", f"/log:{log_file}"], check=False)
        except Exception as e:
            return f"AUSFÜHRUNGS-FEHLER: {str(e)}"

        if os.path.exists(log_file):
            try:
                # Versuch UTF-16 (Standard bei MT5)
                with open(log_file, "r", encoding="utf-16") as f:
                    return f.read()
            except UnicodeError:
                # Fallback auf UTF-8
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    return f"LOG-ENCODING WARNUNG:\n{f.read()}"
        else:
            return "FEHLER: Keine Log-Datei erstellt."

@mcp.tool()
def search_mql5_docs(search_term: str) -> str:
    """
    Sucht via DuckDuckGo präzise in der offiziellen MQL5-Dokumentation (Reference)
    und gibt den Inhalt der passenden Seite zurück.
    """
    # Wir nutzen DuckDuckGo HTML für eine robuste Suche ohne API-Keys
    # Der Filter "site:mql5.com/en/docs" erzwingt Ergebnisse nur aus der Doku
    query = f"site:mql5.com/en/docs {search_term}"
    ddg_url = "https://html.duckduckgo.com/html/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://html.duckduckgo.com/"
    }

    try:
        # 1. Suche ausführen
        response = requests.post(ddg_url, data={'q': query}, headers=headers)
        if response.status_code != 200:
            return f"Such-Fehler: Status Code {response.status_code}"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Den ersten passenden Link extrahieren
        # DuckDuckGo HTML Results sind meist in 'a.result__a'
        target_link = None
        for link in soup.select("a.result__a"):
            href = link.get('href')
            if href and "mql5.com/en/docs" in href:
                # DDG Links müssen oft dekodiert werden (aus dem 'uddg' Parameter)
                if "uddg=" in href:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    target_link = parsed.get('uddg', [None])[0]
                else:
                    target_link = href
                break
        
        if not target_link:
            return f"Keine Dokumentation für '{search_term}' gefunden. (Query: {query})"

        # 3. Die gefundene Dokumentationsseite laden
        doc_response = requests.get(target_link, headers=headers)
        doc_soup = BeautifulSoup(doc_response.text, 'html.parser')
        
        # 4. Inhalt extrahieren
        # MQL5 Docs haben den Inhalt oft in div class="doc-content" oder id="content"
        content_div = doc_soup.find("div", class_="doc-content") or \
                      doc_soup.find("div", id="content") or \
                      doc_soup.find("body")

        if not content_div:
            return f"Seite gefunden ({target_link}), aber Inhalt konnte nicht extrahiert werden."

        # Unnötige Elemente entfernen (Navigation, Footer, Skripte)
        for junk in content_div(["script", "style", "nav", "footer", "header", "form"]):
            junk.decompose()

        text_content = content_div.get_text(separator="\n", strip=True)
        
        # Kürzen um Token zu sparen, falls der Artikel extrem lang ist
        if len(text_content) > 12000:
             text_content = text_content[:12000] + "\n... [Text gekürzt für bessere Lesbarkeit]"

        return f"QUELLE: {target_link}\n\n{text_content}"

    except Exception as e:
        return f"Fehler beim Abruf der Dokumentation: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()