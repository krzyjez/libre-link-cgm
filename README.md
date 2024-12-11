# LibreLink CGM Analyzer

Program do analizy danych z systemu monitorowania glukozy LibreLink CGM.

## Funkcje
- Analiza danych z plików CSV z LibreLink
- Wykrywanie okresów wysokiego poziomu glukozy
- Interaktywne wykresy z biblioteką Plotly
- System notatek z możliwością edycji w przeglądarce

## Struktura projektu
- `data/source/` - katalog na pliki źródłowe CSV
- `data/processed/` - przetworzone dane w formacie JSON
- `data/user/` - dane użytkownika (np. notatki)

## Jak używać
1. Umieść pliki CSV z LibreLink w katalogu `data/source/`
2. Uruchom program:
   ```bash
   python main.py
   ```
3. Uruchom serwer do edycji notatek:
   ```bash
   python server.py
   ```
4. Otwórz `http://localhost:5000` w przeglądarce

## Wymagania
- Python 3.x
- Flask
- Plotly
