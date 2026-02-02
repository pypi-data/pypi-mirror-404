# Biblioteka Urzędu Regulacji Energetyki

[![Licencja: GPL-3.0](https://img.shields.io/badge/Licencja-GPL--3.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI](https://img.shields.io/pypi/v/urzad-regulacji-energetyki.svg)](https://pypi.org/project/urzad-regulacji-energetyki/)
[![Python](https://img.shields.io/pypi/pyversions/urzad-regulacji-energetyki.svg)](https://pypi.org/project/urzad-regulacji-energetyki/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://wiktorhawrylik.github.io/urzad-regulacji-energetyki/)

Kompleksowa biblioteka Pythona do analizy danych z publicznie dostępnych źródeł Urzędu Regulacji Energetyki (URE):

- **Biuletyn Informacji Publicznej** - Śledzenie i analiza zmian w BIP
- **Taryfy Energia Elektryczna** - Analiza taryf i decyzji regulacyjnych
- **Rejestr MIOZE** - Monitoring małych instalacji odnawialnych (≤50kW)

## 📦 Instalacja

```bash
# Używając uv (zalecane)
uv pip install urzad-regulacji-energetyki

# Lub używając pip
pip install urzad-regulacji-energetyki
```

## 🚀 Szybki Start

### Analiza Biuletynu Informacji Publicznej

```python
from urzad_regulacji_energetyki.biuletyn_informacji_publicznej_changelog import BulletinChangelogAnalyzer
from datetime import date

analyzer = BulletinChangelogAnalyzer()
changes = analyzer.analyze_changes(
    start_date=date(2023, 1, 1),
    end_date=date(2023, 12, 31)
)

print(f"Liczba zmian: {len(changes)}")
```

### Analiza Taryf na Energię Elektryczną

```python
from urzad_regulacji_energetyki.taryfy_i_inne_decyzje_energia_elektryczna import TariffAnalyzer

analyzer = TariffAnalyzer()
tariffs = analyzer.get_current_tariffs()

for tariff in tariffs:
    print(f"{tariff.operator}: {tariff.rate} PLN/MWh")
```

### Analiza Rejestru MIOZE

```python
from urzad_regulacji_energetyki.rejestr_mioze import MIOZERegistry

registry = MIOZERegistry()
mioze_data = registry.get_mioze_by_region("mazowieckie")

print(f"Liczba instalacji: {len(mioze_data)}")
```

## 📚 Dokumentacja

Pełna dokumentacja dostępna pod adresem: **[https://wiktorhawrylik.github.io/urzad-regulacji-energetyki/](https://wiktorhawrylik.github.io/urzad-regulacji-energetyki/)**

- [Przewodnik instalacji](https://wiktorhawrylik.github.io/urzad-regulacji-energetyki/guide/installation/)
- [Szczegółowe przykłady](https://wiktorhawrylik.github.io/urzad-regulacji-energetyki/guide/quickstart/)
- [API Reference](https://wiktorhawrylik.github.io/urzad-regulacji-energetyki/api/biuletyn/)
- [Wkład w projekt](https://wiktorhawrylik.github.io/urzad-regulacji-energetyki/contributing/)

## 🛠️ Wymagania

- Python 3.9+
- requests, beautifulsoup4, pandas, numpy, lxml, pydantic

## 📄 Licencja

GPL-3.0 - zobacz plik [LICENSE](LICENSE)

## 🤝 Wkład

Zapraszamy do współpracy! Zobacz [przewodnik dla deweloperów](https://wiktorhawrylik.github.io/urzad-regulacji-energetyki/contributing/).

## 📬 Kontakt

- **GitHub Issues**: [Zgłoś problem](https://github.com/WiktorHawrylik/urzad-regulacji-energetyki/issues)
- **Discussions**: [Zadaj pytanie](https://github.com/WiktorHawrylik/urzad-regulacji-energetyki/discussions)
- **Email**: <wiktor.hawrylik@gmail.com>

---

Wykonane z ❤️ dla społeczności analityki rynku energii
