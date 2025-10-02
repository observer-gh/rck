# AI Club Matching Demo (Streamlit)

Minimal rule-based grouping demo.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Core Logic

Score = 10 _ common_interests + 5 _ same_region + 3 _ same_rank + 2 _ same_atmosphere.

Greedy grouping to target size (default 5). Tiny final group (<3) redistributed.

## Files

- `data/*.json` persistence
- `services/matching.py` algorithm
- `services/persistence.py` atomic JSON I/O
- `services/sample_data.py` synthetic users
- `domain/models.py` dataclasses
- `app.py` Streamlit UI

## Next Ideas

- Activity reports + verification simulation
- Optional Ollama explanations
- Swap JSON -> SQLite

## License

Demo purpose.
