# Executive Architectural Verdict: Neuromancer v1.3.0

**Audit Target:** `status.py`, `install.sh`  
**Reviewer:** Muse-Glimmer (30B) via Muse-Reviewer Protocol  
**Date:** 2026-10-22  
**Overall Grade:** **A- (Hardened with Minor Residual Hygiene Points)**

The core execution path of Neuromancer is robust: pure Python 3, zero external non-standard library dependencies, type-safe fallback handlers, and strict numeric casting across all telemetry keys. The transition from hardcoded Nerd Font Private Use Area (PUA) glyphs to a 3-tier theme engine successfully eliminates font dependency crashes on vanilla terminals.

However, Muse identified three sharp edge cases in the new theme implementation that must be remediated before cutting the public release.

---

## 1. P0 Critical Vulnerabilities & Race Conditions
*(None observed in this subsystem).*

---

## 2. P1 High / P2 Medium Deficiencies

### P1-1: Residual PUA Glyphs in the Default 'Unicode' Theme
* **File & Line:** `status.py:40` (`"VCS": ""`)
* **Failure Mode:** While `ICON_DIR` was fixed to `📁` and `ICON_CONV` to `💬`, the Git branch icon (`VCS`) in the default `unicode` preset still retains `` (`\ue0a0` - Powerline Private Use Area codepoint). On terminal emulators without Powerline or Nerd Font support (e.g., standard Windows Command Prompt/PowerShell with raster fonts, minimal Linux virtual TTYs), this still produces a missing glyph or replacement box.
* **Remediation:**
  In the `unicode` theme, use the universal standard Unicode branch symbol `⎇` (U+2387 Alternative Key Symbol) or `⌥`. Keep `` strictly in the `nerd` preset.

### P2-1: Duplicate Glyph Collision in ASCII Preset
* **File & Line:** `status.py:65`, `status.py:70` (`"WORKING": "#"`, `"CONV": "#"`)
* **Failure Mode:** In `ascii` mode, both `WORKING` state and `CONV` conversation ID prefix are assigned the identical character `#`. This causes visual ambiguity on narrow decks when a task is in flight.
* **Remediation:**
  Change `CONV` in the `ascii` theme to `id:` or `c:` to preserve distinct visual channels.

### P2-2: Silent Swallowing of Malformed Config Files
* **File & Line:** `status.py:84-91`
* **Failure Mode:** `_resolve_icon_theme()` wraps JSON parsing in a bare `except Exception: pass`. While crash-proofing is necessary for a statusline daemon, completely discarding parser errors means a user with an invalid comma or syntax typo in `~/.config/neuromancer/config.json` will silently see their config ignored without any diagnostic trail.
* **Remediation:**
  Safeguard with specific `(OSError, json.JSONDecodeError)` catches.

---

## 3. Remediation Diff

```diff
--- a/status.py
+++ b/status.py
@@ -37,7 +37,7 @@ ICON_THEMES = {
         "WORKING": "⚙",
         "TOOL": "🔧",
         "UNKNOWN": "⏳",
-        "VCS": "",
+        "VCS": "⎇",
         "MODEL": "⚡",
         "CONV": "💬",
         "DIR": "📁",
@@ -67,7 +67,7 @@ ICON_THEMES = {
         "UNKNOWN": "?",
         "VCS": "git:",
         "MODEL": "@",
-        "CONV": "#",
+        "CONV": "id:",
         "DIR": "»",
         "RESET": "reset:",
         "PROJ": "pkg:",
```
