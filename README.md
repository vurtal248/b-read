# ◈ Bionic Reader

A minimal Windows desktop app that applies **Bionic Reading** to any PDF — bold anchors on the first syllable of every word to accelerate fixation and reading speed.

---

## Features

| | |
|---|---|
| 📂 | Drag-and-drop **or** file picker to load any PDF |
| ⚡ | Bionic transform applied instantly in a background thread |
| 📜 | Scrollable reading canvas with warm paper aesthetic |
| 💾 | Export transformed document as standalone HTML |
| 🪟 | Single `.exe` — no Python/Node install required |

---

## Bionic Transform Rules

| Word length | Characters bolded |
|---|---|
| 1–3 | Full word |
| 4–5 | First 2 |
| 6–9 | First 3 |
| 10+ | First 4 |

Punctuation, whitespace, and paragraph structure are fully preserved.

---

## Quick Start (dev)

```powershell
# 1. Create/activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python src/main.py
```

---

## Build `.exe`

```powershell
# From the repo root (venv active)
.\build.ps1
```

Output: `dist\BionicReader.exe` — single portable executable (~80–120 MB).

> **First launch** extracts its payload to `%TEMP%` (PyInstaller --onefile), which takes ~3 seconds. Subsequent launches from the same installation are instant.

---

## Project Structure

```
b-read/
├── src/
│   ├── main.py        # Entry point, HighDPI, CLI arg support
│   ├── window.py      # QMainWindow — toolbar, drop zone, text browser
│   ├── bionic.py      # Bionic Reading transform engine
│   ├── extractor.py   # PDF text extraction (PyMuPDF)
│   └── renderer.py    # HTML generator with styled output
├── requirements.txt
├── build.ps1          # PyInstaller build script
└── README.md
```

---

## Stack

- **Python 3.11+**
- **PyQt6** — UI framework (QTextBrowser, no WebEngine → smaller bundle)
- **PyMuPDF (fitz)** — Fast PDF text extraction with font-size metadata
- **PyInstaller 6+** — Single-file Windows executable packaging

---

## Design

Dark Atelier Typographer aesthetic:
- Chrome: `#0a0806` near-black · `#d4942a` amber accent  
- Reading canvas: `#f6f0e6` warm paper · `#1a0e00` deep bold anchors  
- Typography: Lora serif (reading) · Courier New (UI chrome)
