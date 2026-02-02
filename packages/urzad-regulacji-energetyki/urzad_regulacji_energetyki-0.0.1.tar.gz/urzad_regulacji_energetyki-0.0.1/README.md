# Biblioteka Urzędu Regulacji Energetyki

[![Licencja: GPL-3.0](https://img.shields.io/badge/Licencja-GPL--3.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Kompleksowa biblioteka Pythona do tworzenia analiz z publicznie dostępnych danych ze stron internetowych Urzędu Regulacji Energetyki (URE):
- [ure.gov.pl](https://ure.gov.pl)
- [bip.ure.gov.pl](https://bip.ure.gov.pl)

## 🚀 Funkcjonalności

To repozytorium zawiera 3 specjalistyczne moduły Pythona do analizy rynku energii:

### 📋 Biuletyn Informacji Publicznej - Rejestr Zmian
- Śledzenie i analiza zmian opublikowanych w BIP
- Wyszukiwanie dokumentów i decyzji
- Generowanie raportów zmian
- Analiza historyczna opublikowanych informacji

### ⚡ Taryfy i Inne Decyzje - Energia Elektryczna
- Analiza i śledzenie taryf na energię elektryczną
- Porównywanie struktur taryf
- Generowanie prognoz zmian
- Historyczna analiza decyzji regulacyjnych

### 🗂️ Rejestr MIOZE
- Monitorowanie małych instalacji wytwórczych (≤50kW)
- Śledzenie wdrażania systemu MIOZE
- Analiza rozpowszechnienia mikroinstalacji
- Ocena wpływu na sieci dystrybucyjne

## 📦 Instalacja

### Z PyPI (rekomendowane)
```bash
# Using uv (fastest)
uv pip install urzad-regulacji-energetyki

# Or using pip
pip install urzad-regulacji-energetyki
```

### Ze źródła
```bash
git clone https://github.com/WiktorHawrylik/urzad-regulacji-energetyki.git
cd urzad-regulacji-energetyki

# Using uv (recommended - creates symlinks to src directory)
uv pip install -e .
```

### Instalacja dla deweloperów

```bash
git clone https://github.com/WiktorHawrylik/urzad-regulacji-energetyki.git
cd urzad-regulacji-energetyki

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# Or on macOS with Homebrew: brew install uv

# Install project with all dev dependencies
uv sync --extra dev --extra test --extra docs

# Install pre-commit hooks
uv run pre-commit install
```

### Budowanie Dystrybucji

Projekt używa standardu **PEP 517** z setuptools jako backendem budowania.

```bash
# Install build tool (if not already installed)
uv pip install build

# Build both wheel and source distribution
uv run python -m build

# Or using uv's built-in build command
uv build
```

To utworzy dwa pliki w katalogu `dist/`:
- **Wheel** (`.whl`): `urzad_regulacji_energetyki-0.0.1-py3-none-any.whl` - Szybka instalacja, preferowana
- **Source Distribution** (`.tar.gz`): `urzad_regulacji_energetyki-0.0.1.tar.gz` - Tradycyjna dystrybucja źródłowa

**Instalacja z zbudowanej dystrybucji:**
```bash
# Install from wheel (faster)
uv pip install dist/urzad_regulacji_energetyki-0.0.1-py3-none-any.whl

# Or from source distribution
uv pip install dist/urzad_regulacji_energetyki-0.0.1.tar.gz
```

**Publikacja do PyPI:**
```bash
# Install twine (if not already installed)
uv pip install twine

# Upload to PyPI (requires credentials)
uv run twine upload dist/*

# Or to TestPyPI for testing
uv run twine upload --repository testpypi dist/*
```

**Co jest zawarte w dystrybucji:**
- ✅ Wszystkie pliki Pythona w `src/urzad_regulacji_energetyki/`
- ✅ `README.md` (jako długi opis pakietu)
- ✅ Metadane pakietu (wersja, zależności, autorzy)
- ❌ Testy, konfiguracja deweloperska, dokumentacja (nie są potrzebne użytkownikom)

## 🔧 Szybki Start

### Analiza Biuletynu Informacji Publicznej
```python
from urzad_regulacji_energetyki.biuletyn_informacji_publicznej_changelog import BulletinChangelogAnalyzer
from datetime import date

# Inicjalizacja analizatora
analyzer = BulletinChangelogAnalyzer()

# Analiza zmian w biuletynie
changes = analyzer.analyze_changes(
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31)
)

print(f"Liczba zmian: {len(changes)}")
print(f"Średnia zmian na miesiąc: {len(changes) / 12}")
```

### Analiza Taryf na Energię Elektryczną
```python
from urzad_regulacji_energetyki.taryfy_i_inne_decyzje_energia_elektryczna import TariffAnalyzer

# Inicjalizacja analizatora
analyzer = TariffAnalyzer()

# Pobierz obowiązujące taryfy
current_tariffs = analyzer.get_current_tariffs()

for tariff in current_tariffs:
    print(f"Taryfa: {tariff.name}")
    print(f"Stawka: {tariff.rate} PLN/MWh")
```

### Analiza Rejestru MIOZE
```python
from urzad_regulacji_energetyki.rejestr_mioze import MIOZERegistry

# Inicjalizacja rejestru
registry = MIOZERegistry()

# Pobierz dane o MIOZE w województwie
mioze_data = registry.get_mioze_by_region("mazowieckie")
print(f"Liczba MIOZE w Mazowieckimi: {len(mioze_data)}")

# Generuj statystyki regionalne
regional_stats = registry.generate_regional_statistics()
for region, stats in regional_stats.items():
    print(f"{region}: {stats.total_capacity_kw:.2f} kW całkowitej mocy")
```

## 📋 Struktura Modułów

```
src/urzad_regulacji_energetyki/
├── biuletyn_informacji_publicznej_changelog/
│   ├── analyzer.py         # Główny silnik analizy
│   ├── models.py           # Modele danych
│   ├── scrapers.py         # Narzędzia web scrapingu
│   └── utils.py            # Funkcje pomocnicze
├── taryfy_i_inne_decyzje_energia_elektryczna/
│   ├── analyzer.py         # Analiza taryf
│   ├── models.py           # Modele danych taryf
│   ├── scrapers.py         # Web scraper taryf
│   └── utils.py            # Narzędzia pomocnicze
└── rejestr_mioze/
    ├── registry.py         # Silnik rejestru MIOZE
    ├── models.py           # Modele danych MIOZE
    ├── scrapers.py         # Web scraper MIOZE
    └── utils.py            # Narzędzia analizy
```

## 🧪 Testowanie

Uruchom testy za pomocą pytest:
```bash
# Uruchom wszystkie testy
make test
# Or: uv run pytest

# Uruchom z pokryciem kodu
make test-cov
# Or: uv run pytest --cov=urzad_regulacji_energetyki --cov-report=html

# Uruchom konkretny plik testowy
uv run pytest tests/unit/test_tariff_analyzer.py
```

**Testowanie wielu wersji Pythona**: CI/CD automatycznie testuje na Python 3.9, 3.10, 3.11, 3.12 w GitHub Actions.

## 🔍 Jakość Kodu

Projekt używa **`pyproject.toml` jako pojedynczego źródła konfiguracji** dla wszystkich narzędzi:

```bash
# Formatowanie kodu
make format
# Or: uv run ruff check --fix src tests && uv run ruff format src tests

# Sprawdzanie jakości (ruff, mypy)
make lint

# Lub uruchom narzędzia bezpośrednio
uv run ruff check src tests
uv run ruff format src tests
uv run mypy src
```

**Konfiguracja**: Wszystkie narzędzia automatycznie czytają z `pyproject.toml` - nie potrzeba przekazywać argumentów `--config`.

**Pre-commit hooks**: Zainstaluj hooks aby automatycznie sprawdzać kod przed każdym commitem:
```bash
make pre-commit
# Or: uv run pre-commit install
```

## 📚 Dokumentacja

Zbuduj dokumentację lokalnie:
```bash
make docs
```

## 🛠️ Środowisko Deweloperskie

### Konfiguracja (Python 3.9+)

1. **Klonowanie repozytorium**:
   ```bash
   git clone https://github.com/WiktorHawrylik/urzad-regulacji-energetyki.git
   cd urzad-regulacji-energetyki
   ```

2. **Instalacja uv** (jeśli jeszcze nie zainstalowane):
   ```bash
   # macOS (Homebrew)
   brew install uv
   ```

3. **Instalacja projektu i zależności**:
   ```bash
   uv sync --extra dev --extra test --extra docs
   ```

4. **Instalacja pre-commit hooks**:
   ```bash
   uv run pre-commit install
   ```

### Dostępne Komendy Make

```bash
make help          # Pokaż wszystkie dostępne komendy
make install-dev   # Zainstaluj zależności deweloperskie
make format        # Sformatuj kod (ruff)
make lint          # Sprawdź jakość kodu
make test          # Uruchom testy
make test-cov      # Uruchom testy z raportem pokrycia
make clean         # Wyczyść artefakty
make docs          # Zbuduj dokumentację
```

### Narzędzia Deweloperskie

Wszystkie narzędzia używają **`pyproject.toml`** jako pojedynczego źródła konfiguracji:

- **uv**: Szybki menedżer pakietów i środowisk Python
- **ruff**: bardzo szybkie formatowanie i linting (zastępuje black, isort, flake8)
- **mypy**: sprawdzanie typów (strict mode)
- **pytest**: testy i pokrycie kodu

Szczegóły konfiguracji w [TOOL_CONFIGURATION.md](TOOL_CONFIGURATION.md).

### Wkład

Ten projekt podąża za strategią gałęziowania **Git Flow** dla zorganizowanego rozwoju i wydań. Zobacz [CONTRIBUTING.md](CONTRIBUTING.md) aby uzyskać szczegółowe instrukcje dotyczące przepływu pracy, konwencji nazewnictwa gałęzi i procesu przesyłania.

## 📄 Licencja

Ten projekt jest licencjonowany na warunkach licencji GPL-3.0 - zobacz plik [LICENSE](LICENSE) aby uzyskać szczegóły.

## 🤝 Pomoc

- **Problemy**: [GitHub Issues](https://github.com/WiktorHawrylik/urzad-regulacji-energetyki/issues)
- **Dyskusje**: [GitHub Discussions](https://github.com/WiktorHawrylik/urzad-regulacji-energetyki/discussions)
- **Autor**: Wiktor Hawrylik
- **Email**: <wiktor.hawrylik@gmail.com>

## 📈 Plan Rozwoju

- [ ] Dodanie wsparcia dla analiz danych historycznych
- [ ] Implementacja modeli uczenia maszynowego do predykcji zmian
- [ ] Dodanie możliwości transmisji danych w czasie rzeczywistym
- [ ] Stworzenie interaktywnego pulpitu nawigacyjnego
- [ ] Rozszerzenie wsparcia na dane europejskiego rynku energii
- [ ] Implementacja automatycznego generowania raportów

## 🙏 Podziękowania

- Urząd Regulacji Energetyki za zapewnienie dostępu do danych publicznych
- Wspólnota oprogramowania open-source
- Ekosystem nauki o danych Python (pandas, requests, BeautifulSoup, itp.)

---

Wykonane z ❤️ dla społeczności analityki rynku energii
