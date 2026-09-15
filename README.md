# 🐺 Witcher Book Assistant
A lightweight desktop overlay tool designed for readers of *The Witcher* book series. It captures a screen excerpt via a shortcut, sends it to Google's Gemini AI, and instantly provides deep lore, definitions, and context matching the book's language—all without spoilers!
## ✨ Features
- **Instant Screenshot Lookup**: Trigger a capture with a side mouse button (`X1`) and optionally specify a target word.
- **AI-Powered Analysis**: Powered by `google-genai` (Gemini Flash model) structured strictly into:
  - Precise Definition & Context
  - Three Interesting Facts (Lore / Real-world history)
  - Witcher Lore (Bestiary, alchemy, heraldry, etc.)
  - Elder Speech breakdown (when applicable)
- **Immersive Custom UI**: Dark-themed, borderless, resizable windows styled in an amber Witcher aesthetic.
- **Dynamic Controls**: 
  - Scale text size on the fly (`A-` / `A+`).
  - Native clipboard integration (`Ctrl+C` to copy text, `Ctrl+V` to paste in the search dialog).
  - Remembers window size and preferences via `config.json`.
- **Spoiler-Free**: System instructions are tuned to prevent any spoilers for future events in the books.

---

## 🛠️ Requirements

- Python 3.8+
- Required Python libraries:
  ```bash
  python install google-genai pillow pynput
