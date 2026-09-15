# 🐺 Witcher Book Assistant
A lightweight desktop overlay tool designed for readers of *The Witcher* book series. It captures a screen excerpt via a shortcut, sends it to Google's Gemini AI, and instantly provides deep lore, definitions.

---

## ✨ Features
- **Instant Screenshot Lookup**: Trigger a capture with a side mouse button and optionally specify a target word.
- **AI-Powered Analysis**: Powered by `google-genai` (Gemini Flash model) structured strictly into:
  - Precise Definition & Context
  - Three Interesting Facts (Lore / Real-world history)
  - Witcher Lore (Bestiary, alchemy, heraldry, etc.)
  - Elder Speech breakdown (when applicable)
  - Spoiler-Free: System instructions are tuned to prevent any spoilers for future events in the books.

---

## 🛠️ Requirements

- Python 3.8+
- Required Python libraries:
  ```bash
  python install google-genai pillow pynput
