# ⚡ Neuromancer

> **High-Density Cyberpunk Onyx Telemetry Deck & Statusline for Antigravity CLI**

![Neuromancer Cyberpunk Telemetry HUD](assets/preview.png)

**Neuromancer** upgrades your `antigravity-cli` statusline into a high-density, crash-proof **Onyx Deck HUD** equipped with dynamic Cyberpunk Amber indicator gauges, fail-safe Python execution, dual-quota refresh timers, and automatic laptop battery/AC diagnostics.

---

## 🔥 Features

- **⚡ Fail-Safe Python Engine:** Pure Python 3 with type-safe numeric guards. Zero crashes from missing JSON attributes, `null` fields, `'N/A'` string values, or session resumptions.
- **📊 Context Window Ratio & Token Stats:** Displays exact context ceiling (`132k / 1M`) along with input/output token breakdowns (`(↑120k ↓12k)`).
- **📐 Responsive Adaptive HUD:** Maintains a 2-line deck (`┌─` / `└─`) on standard screens and automatically wraps into a 3-line tree (`┌─` / `├─` / `└─`) on narrow terminals (<100 cols) so stats are never clipped.
- **▰▰▰ Cyberpunk Amber Gauges:** Dynamic 3-tier Amber indicator bars for Context Window usage and Model Quotas (`5H` and `7D`).
- **⌛ Accurate Dual-Quota Timers & Gemini 4 Argon Support:** Correctly tracks both your short-term 5-hour rolling rate limit (**`5H`**) and weekly quota (**`7D`**), with dedicated dynamic bucket resolution for **Gemini 4 Argon** separate weekly allowances (`[ARGON 7D]`), third-party models (`3P`), and custom backend pools.
- **🔋 Laptop Power Diagnostics:** Auto-detects AC mains vs battery percentage (`[PWR ⚡ AC]` / `[PWR 🔋 75%]`), hiding automatically on desktop machines.
- **📦 Project Telemetry Badge:** Auto-detects project workspace from telemetry JSON, Git repository root, or directory fallback (`📦 neuromancer`).
- **🖥️ Onyx Deck Framework:** Matrix Cyan accents, dirty Git indicators, and real-time CPU load & RAM diagnostics.
- **🚀 1-Step Installation:** Auto-configures `~/.gemini/antigravity-cli/settings.json`.

---

## 💻 Installation

Run this single command in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/CountZero-ono/neuromancer/main/install.sh | bash
```

Or install manually:

```bash
git clone https://github.com/CountZero-ono/neuromancer.git
cd neuromancer
chmod +x install.sh && ./install.sh
```

---

## 🎨 Color Palette & Gauge Indicators

| Indicator | Remaining % | Color Theme |
| :--- | :--- | :--- |
| **High Quota / Low Ctx** | `> 50%` | **Bright Cyber Amber** (`#ffb000` / ANSI 214) |
| **Medium Quota / Ctx** | `20% – 50%` | **Warm Amber-Orange** (`#ff8700` / ANSI 208) |
| **Critical Quota / Ctx** | `< 20%` | **Crimson Alert** (`#ff0055` / ANSI 197) |
| **Empty Gauge Shadow** | `0%` | **Deep Slate Shadow** (`#3a3d4a` / ANSI 238) |

---

## 📄 License

MIT © Fuad Babaev
