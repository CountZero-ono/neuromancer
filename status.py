#!/usr/bin/env python3
"""
Neuromancer — Cyberpunk Telemetry Deck & Statusline for Antigravity CLI
Onyx & Cyberpunk Amber Telemetry HUD with Fail-Safe Execution, Dual Quota Timers, and Power Diagnostics
"""

import sys
import json
import os
import time
import re
import subprocess

# ─── Gibson / Neuromancer Cyberpunk Palette ────────────────────────────────────
FRAME_COLOR = "\033[38;5;240m"     # Dark Slate Gray for brackets/lines
BRACKET_COLOR = "\033[38;5;244m"   # Crisp Dim Slate for [ ]
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Cyberpunk Accent Colors
CYAN = "\033[38;5;39m"             # Matrix Cyan (Model, Git Branch)
AMBER_BRIGHT = "\033[38;5;214m"     # Bright Cyber Amber (State, Quota > 50%)
AMBER_WARM = "\033[38;5;208m"       # Warm Amber-Orange (Quota 20-50%)
RED_ALERT = "\033[38;5;196m"        # Crimson Red (Dirty Git, High Ctx, Low Quota)
GREEN_PHOSPHOR = "\033[38;5;48m"   # Phosphor Green (Ready, Clean Git)
MAGENTA_NEON = "\033[38;5;135m"     # Neon Purple (Tool Use)
WHITE_BRIGHT = "\033[38;5;255m\033[1m"
SHADOW_GRAY = "\033[38;5;238m"     # Dark Shadow for empty gauge blocks

# ─── Icon Presets & Configuration ──────────────────────────────────────────────
# Themes: 'unicode' (Default, zero font dependencies), 'nerd', 'ascii'
ICON_THEMES = {
    "unicode": {
        "READY": "●",
        "THINKING": "◆",
        "WORKING": "⚙",
        "TOOL": "🔧",
        "UNKNOWN": "⏳",
        "VCS": "⎇",
        "MODEL": "⚡",
        "CONV": "💬",
        "DIR": "📁",
        "RESET": "⌛",
        "PROJ": "📦",
        "HOST": "💻",
    },
    "nerd": {
        "READY": "●",
        "THINKING": "◆",
        "WORKING": "⚙",
        "TOOL": "🔧",
        "UNKNOWN": "⏳",
        "VCS": "",
        "MODEL": "⚡",
        "CONV": "󰍪",
        "DIR": "",
        "RESET": "⌛",
        "PROJ": "📦",
        "HOST": "󰒋",
    },
    "ascii": {
        "READY": "*",
        "THINKING": "~",
        "WORKING": "#",
        "TOOL": "+",
        "UNKNOWN": "?",
        "VCS": "git:",
        "MODEL": "@",
        "CONV": "id:",
        "DIR": "»",
        "RESET": "reset:",
        "PROJ": "pkg:",
        "HOST": "host:",
    },
}


def _resolve_icon_theme() -> dict:
    theme_name = os.environ.get("NEUROMANCER_ICONS", "").strip().lower()
    if theme_name not in ICON_THEMES:
        config_path = os.path.expanduser("~/.config/neuromancer/config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    cfg_theme = str(cfg.get("icons") or "").strip().lower()
                    if cfg_theme in ICON_THEMES:
                        theme_name = cfg_theme
            except Exception:
                pass
    if theme_name not in ICON_THEMES:
        theme_name = "unicode"
    return ICON_THEMES[theme_name]


_ICONS = _resolve_icon_theme()

ICON_READY = _ICONS["READY"]
ICON_THINKING = _ICONS["THINKING"]
ICON_WORKING = _ICONS["WORKING"]
ICON_TOOL = _ICONS["TOOL"]
ICON_UNKNOWN = _ICONS["UNKNOWN"]
ICON_VCS = _ICONS["VCS"]
ICON_MODEL = _ICONS["MODEL"]
ICON_CONV = _ICONS["CONV"]
ICON_DIR = _ICONS["DIR"]
ICON_RESET = _ICONS["RESET"]
ICON_PROJ = _ICONS["PROJ"]
ICON_HOST = _ICONS["HOST"]

def safe_int(val, default: int = 0) -> int:
    try:
        if val is None:
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def format_tokens(n: int) -> str:
    try:
        n = safe_int(n, 0)
        if n >= 1_000_000:
            val = n / 1_000_000
            return f"{val:.1f}".rstrip('0').rstrip('.') + "M"
        if n >= 1_000:
            val = n / 1_000
            return f"{val:.1f}".rstrip('0').rstrip('.') + "k"
        return str(n)
    except Exception:
        return "0"


def format_reset_time(sec: float) -> str:
    try:
        sec = safe_int(sec, 0)
        if sec <= 0:
            return ""
        days = sec // 86400
        rem = sec % 86400
        hours = rem // 3600
        rem %= 3600
        mins = rem // 60

        if days > 0:
            return f"{days}d {hours}h" if hours > 0 else f"{days}d"
        if hours > 0:
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
        if mins > 0:
            return f"{mins}m"
        return "<1m"
    except Exception:
        return ""


def make_amber_gauge(label: str, pct: float, reset_sec: float = -1, length: int = 8) -> str:
    """Renders a Neuromancer Amber Segmented Gauge: [LABEL ▰▰▰▰▰▱▱▱▱▱ 65% ⌛1h]"""
    try:
        pct_val = safe_float(pct, 0.0)
        pct_val = max(0.0, min(100.0, pct_val))
        filled_count = safe_int(round(pct_val * length / 100.0), 0)

        # Color based on remaining %
        if pct_val > 50:
            fill_color = AMBER_BRIGHT
        elif pct_val >= 20:
            fill_color = AMBER_WARM
        else:
            fill_color = RED_ALERT

        filled_str = f"{fill_color}{'▰' * filled_count}{RESET}"
        empty_str = f"{SHADOW_GRAY}{'▱' * (length - filled_count)}{RESET}"

        reset_str = ""
        r_sec = safe_float(reset_sec, -1.0)
        if r_sec > 0:
            r_fmt = format_reset_time(r_sec)
            if r_fmt:
                reset_str = f" {AMBER_BRIGHT}{ICON_RESET}{r_fmt}{RESET}"

        lbl_colored = f"{WHITE_BRIGHT}{label}{RESET}"
        pct_colored = f"{fill_color}{pct_val:.0f}%{RESET}"

        return f"{BRACKET_COLOR}[{RESET}{lbl_colored} {filled_str}{empty_str} {pct_colored}{reset_str}{BRACKET_COLOR}]{RESET}"
    except Exception:
        return f"[{label} N/A]"


def shorten_path(path: str, max_len: int = 25) -> str:
    if not path:
        return ""
    try:
        home = os.path.expanduser("~")
        if path.startswith(home):
            path = "~" + path[len(home):]
        if len(path) > max_len:
            return "..." + os.path.basename(path)
        return path
    except Exception:
        return path


def get_system_telemetry() -> tuple[str, str]:
    """Reads system RAM utilization and CPU load 1m without external dependencies."""
    ram_str = ""
    load_str = ""
    try:
        if os.path.exists("/proc/meminfo"):
            mem_total = 0
            mem_avail = 0
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        if parts[0] == "MemTotal:":
                            mem_total = int(parts[1])
                        elif parts[0] == "MemAvailable:":
                            mem_avail = int(parts[1])
            if mem_total > 0:
                ram_pct = int((mem_total - mem_avail) * 100 / mem_total)
                ram_str = f"{ram_pct}%"

        if os.path.exists("/proc/loadavg"):
            with open("/proc/loadavg", "r") as f:
                parts = f.read().split()
                if parts:
                    load_str = parts[0]
    except Exception:
        pass
    return ram_str, load_str


def get_power_telemetry() -> str:
    """Reads AC mains and Battery level safely from /sys/class/power_supply or pmset."""
    try:
        sys_power = "/sys/class/power_supply"
        if os.path.exists(sys_power):
            ac_online = False
            bat_cap = -1

            for dev in os.listdir(sys_power):
                dev_path = os.path.join(sys_power, dev)
                if not os.path.isdir(dev_path):
                    continue

                online_file = os.path.join(dev_path, "online")
                if os.path.exists(online_file):
                    try:
                        with open(online_file, "r") as f:
                            if f.read().strip() == "1":
                                ac_online = True
                    except Exception:
                        pass

                cap_file = os.path.join(dev_path, "capacity")
                if os.path.exists(cap_file):
                    try:
                        with open(cap_file, "r") as f:
                            bat_cap = int(f.read().strip())
                    except Exception:
                        pass

            if bat_cap >= 0:
                if ac_online:
                    cap_str = f" ({bat_cap}%)" if bat_cap < 100 else ""
                    return f"{GREEN_PHOSPHOR}⚡ AC{cap_str}{RESET}"
                else:
                    if bat_cap >= 50:
                        c = GREEN_PHOSPHOR
                        icon = "🔋"
                    elif bat_cap >= 20:
                        c = AMBER_WARM
                        icon = "🔋"
                    else:
                        c = RED_ALERT
                        icon = "🪫"
                    return f"{icon} {c}{bat_cap}%{RESET}"

        if sys.platform == "darwin":
            res = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True, timeout=0.5)
            if res.returncode == 0:
                match = re.search(r"(\d+)%", res.stdout)
                if match:
                    cap = int(match.group(1))
                    is_ac = "AC Power" in res.stdout
                    if is_ac:
                        cap_str = f" ({cap}%)" if cap < 100 else ""
                        return f"{GREEN_PHOSPHOR}⚡ AC{cap_str}{RESET}"
                    c = GREEN_PHOSPHOR if cap >= 50 else (AMBER_WARM if cap >= 20 else RED_ALERT)
                    return f"🔋 {c}{cap}%{RESET}"
    except Exception:
        pass
    return ""


def get_git_info(cwd: str) -> tuple[str, bool]:
    """Fast timeout-guarded git branch & dirty checker."""
    if not cwd or not os.path.exists(cwd):
        return "", False
    try:
        res = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=0.6,
        )
        if res.returncode != 0:
            return "", False
        branch = res.stdout.strip()
        if not branch:
            return "", False

        status_res = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=0.6,
        )
        dirty = bool(status_res.stdout.strip())
        return branch, dirty
    except Exception:
        return "", False


def get_project_name(data: dict, cwd: str) -> str:
    """Determines the project name from telemetry JSON, git root, or cwd folder name."""
    try:
        if isinstance(data, dict):
            p_name = str(data.get("project_name") or data.get("project") or data.get("workspace_name") or "").strip()
            if p_name:
                return p_name

        if cwd and os.path.exists(cwd):
            res = subprocess.run(
                ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=0.6,
            )
            if res.returncode == 0:
                top_dir = res.stdout.strip()
                if top_dir:
                    return os.path.basename(top_dir)

            return os.path.basename(os.path.abspath(cwd))
    except Exception:
        pass
    return ""


# ─── Render Neuromancer Deck Telemetry ─────────────────────────────────────────
def render_deck(data: dict) -> str:
    try:
        if not isinstance(data, dict):
            data = {}

        cols = safe_int(data.get("terminal_width"), 80)
        
        # 1. State
        state = str(data.get("agent_state") or "idle").lower()
        if state == "idle":
            state_str = f"{GREEN_PHOSPHOR}{ICON_READY} READY{RESET}"
        elif state == "thinking":
            state_str = f"{AMBER_BRIGHT}{ICON_THINKING} THINKING{RESET}"
        elif state == "working":
            state_str = f"{CYAN}{ICON_WORKING} WORKING{RESET}"
        elif state == "tool_use":
            state_str = f"{MAGENTA_NEON}{ICON_TOOL} TOOL{RESET}"
        else:
            state_str = f"{WHITE_BRIGHT}{ICON_UNKNOWN} {state.upper()}{RESET}"

        # 2. Model
        model_obj = data.get("model") or {}
        if isinstance(model_obj, dict):
            model_name = model_obj.get("display_name") or model_obj.get("id") or "AGY"
        else:
            model_name = str(model_obj or "AGY")
        model_str = f"{CYAN}{BOLD}{ICON_MODEL} {model_name}{RESET}"

        # 3. Project Name
        cwd = str(data.get("cwd") or "")
        proj_name = get_project_name(data, cwd)
        proj_str = f"{MAGENTA_NEON}{ICON_PROJ} {proj_name}{RESET}" if proj_name else ""

        # 4. Git Branch
        vcs_obj = data.get("vcs") or {}
        vcs_branch = str(vcs_obj.get("branch") or "") if isinstance(vcs_obj, dict) else ""
        vcs_dirty = bool(vcs_obj.get("dirty", False)) if isinstance(vcs_obj, dict) else False
        if not vcs_branch and cwd:
            vcs_branch, vcs_dirty = get_git_info(cwd)

        git_str = ""
        if vcs_branch:
            dirty_mark = f"{RED_ALERT}*{RESET}" if vcs_dirty else ""
            branch_color = RED_ALERT if vcs_dirty else CYAN
            git_str = f"{branch_color}{ICON_VCS} {vcs_branch}{dirty_mark}{RESET}"

        # 5. Working Directory
        cwd_len = 15 if cols < 90 else 25
        cwd_short = shorten_path(cwd, max_len=cwd_len)
        cwd_str = f"{BRACKET_COLOR}{ICON_DIR} {cwd_short}{RESET}" if cwd_short else ""

        # 6. Conversation ID
        conv_id = str(data.get("conversation_id") or "")
        conv_str = f"{FRAME_COLOR}{ICON_CONV} {conv_id[:8]}{RESET}" if conv_id else ""

        # Assemble Header Parts
        row1_parts = [f"{BRACKET_COLOR}[{RESET}DECK:{state_str}{BRACKET_COLOR}]{RESET}", model_str]
        if proj_str:
            row1_parts.append(proj_str)
        if git_str:
            row1_parts.append(git_str)
        if cwd_str:
            row1_parts.append(cwd_str)
        if conv_str and cols >= 110:
            row1_parts.append(conv_str)

        # 6. Context Window Gauge & Token Ratio
        cw = data.get("context_window") or {}
        if not isinstance(cw, dict):
            cw = {}
        ctx_rem = safe_float(cw.get("remaining_percentage"), 100.0)
        ctx_used_pct = 100.0 - ctx_rem
        in_t = safe_int(cw.get("total_input_tokens") or cw.get("input_tokens"), 0)
        out_t = safe_int(cw.get("total_output_tokens") or cw.get("output_tokens"), 0)
        ctx_size = safe_int(cw.get("context_window_size") or cw.get("max_tokens") or cw.get("token_limit"), 0)
        ctx_used = safe_int(cw.get("used_tokens") or cw.get("current_usage"), in_t + out_t)

        gauge_len = 8 if cols >= 120 else 6
        ctx_gauge = make_amber_gauge("CTX", ctx_used_pct, length=gauge_len)

        tok_info = ""
        if ctx_used > 0 or ctx_size > 0:
            if ctx_size > 0:
                tok_usage_str = f"{format_tokens(ctx_used)} / {format_tokens(ctx_size)}"
            else:
                tok_usage_str = f"{format_tokens(ctx_used)}"

            io_str = f" (↑{format_tokens(in_t)} ↓{format_tokens(out_t)})" if (in_t > 0 or out_t > 0) else ""
            tok_info = f" {CYAN}{tok_usage_str}{RESET}{DIM}{io_str}{RESET}"

        ctx_section = f"{ctx_gauge}{tok_info}"

        # 7. Quota Gauges (Adaptive Dynamic Resolution: Argon, Gemini, 3P, Custom)
        quota_data = data.get("quota") or {}
        if not isinstance(quota_data, dict):
            quota_data = {}

        quota_parts = []
        model_lower = model_name.lower()
        is_argon = "argon" in model_lower
        is_3p = "gemini" not in model_lower

        found_5h = None
        found_wk = None

        if is_argon:
            # Check Argon-specific buckets first
            for k, b in quota_data.items():
                if not isinstance(b, dict):
                    continue
                k_lower = k.lower()
                if "argon" in k_lower:
                    if "5h" in k_lower or "rolling" in k_lower or "short" in k_lower:
                        found_5h = ("ARGON 5H" if cols >= 120 else "5H", b)
                    elif "week" in k_lower or "7d" in k_lower or "wk" in k_lower:
                        found_wk = ("ARGON 7D" if cols >= 120 else "7D", b)
                    elif found_wk is None:
                        found_wk = ("ARGON" if cols >= 120 else "7D", b)

        elif is_3p:
            # Third-party model check
            for k, b in quota_data.items():
                if not isinstance(b, dict):
                    continue
                k_lower = k.lower()
                if "3p" in k_lower or "third_party" in k_lower:
                    if "5h" in k_lower:
                        found_5h = ("3P 5H" if cols >= 120 else "5H", b)
                    elif "week" in k_lower or "7d" in k_lower:
                        found_wk = ("3P 7D" if cols >= 120 else "7D", b)

        # Fallback to standard Gemini buckets if not found
        if not found_5h:
            g_5h = quota_data.get("gemini-5h")
            if isinstance(g_5h, dict):
                found_5h = ("5H", g_5h)

        if not found_wk:
            g_wk = quota_data.get("gemini-weekly")
            if isinstance(g_wk, dict):
                found_wk = ("7D", g_wk)

        # Dynamic heuristic match for remaining unmatched buckets
        if not found_5h or not found_wk:
            for k, b in quota_data.items():
                if not isinstance(b, dict):
                    continue
                if b.get("remaining_fraction") is None:
                    continue
                k_lower = k.lower()
                if not found_5h and ("5h" in k_lower or "short" in k_lower):
                    found_5h = ("5H", b)
                elif not found_wk and ("week" in k_lower or "7d" in k_lower):
                    found_wk = ("7D", b)

        # Render resolved primary gauges
        for item in [found_5h, found_wk]:
            if not item:
                continue
            lbl, b_data = item
            frac = b_data.get("remaining_fraction")
            if frac is not None:
                val = safe_float(frac, -1.0)
                if val >= 0:
                    pct = val * 100.0
                    r_sec = safe_float(b_data.get("reset_in_seconds"), -1.0)
                    quota_parts.append(make_amber_gauge(lbl, pct, reset_sec=r_sec, length=6))

        # Dynamic fallback: if no standard buckets matched, render up to 2 arbitrary buckets
        if not quota_parts and quota_data:
            for k, b_data in quota_data.items():
                if not isinstance(b_data, dict):
                    continue
                frac = b_data.get("remaining_fraction")
                if frac is not None:
                    val = safe_float(frac, -1.0)
                    if val >= 0:
                        pct = val * 100.0
                        r_sec = safe_float(b_data.get("reset_in_seconds"), -1.0)
                        raw_lbl = k.upper().replace("_", " ").replace("-", " ")
                        lbl = raw_lbl[:8].strip()
                        quota_parts.append(make_amber_gauge(lbl, pct, reset_sec=r_sec, length=6))
                        if len(quota_parts) >= 2:
                            break

        # 8. System Resources Badge
        ram_str, load_str = get_system_telemetry()
        sys_badge = ""
        if ram_str and load_str and cols >= 120:
            sys_badge = f"{BRACKET_COLOR}[{RESET}{WHITE_BRIGHT}SYS{RESET} ram:{ram_str} ld:{load_str}{BRACKET_COLOR}]{RESET}"

        # 9. Tasks / Subagents / Sandbox
        task_cnt = safe_int(data.get("task_count"), 0)
        sub_cnt = len(data.get("subagents") or []) if isinstance(data.get("subagents"), list) else 0
        art_cnt = safe_int(data.get("artifact_count"), 0)
        sb_obj = data.get("sandbox") or {}
        sb_enabled = bool(sb_obj.get("enabled", False)) if isinstance(sb_obj, dict) else False

        deck_status = []
        if task_cnt > 0 or sub_cnt > 0 or art_cnt > 0:
            deck_status.append(f"tsk:{task_cnt} sub:{sub_cnt} art:{art_cnt}")
        if sb_enabled:
            deck_status.append("sandbox:ON")

        deck_badge = ""
        if deck_status and cols >= 140:
            deck_badge = f"{BRACKET_COLOR}[{RESET}{WHITE_BRIGHT}DECK{RESET} {' '.join(deck_status)}{BRACKET_COLOR}]{RESET}"

        # 10. Power / Battery Badge
        pwr_str = get_power_telemetry()
        pwr_badge = ""
        if pwr_str and cols >= 150:
            pwr_badge = f"{BRACKET_COLOR}[{RESET}{WHITE_BRIGHT}PWR{RESET} {pwr_str}{BRACKET_COLOR}]{RESET}"

        sep = f" {FRAME_COLOR}·{RESET} "
        dash_sep = f" {FRAME_COLOR}──{RESET} "

        # Layout Selection (2-line default, 3-line when cols < 100)
        if cols >= 100:
            # 2-Line Standard Layout
            row1 = f"{FRAME_COLOR}┌─{RESET} " + sep.join(row1_parts)
            
            row2_parts = [ctx_section]
            if quota_parts:
                row2_parts.append(dash_sep.join(quota_parts))
            if sys_badge:
                row2_parts.append(sys_badge)
            if deck_badge:
                row2_parts.append(deck_badge)
            if pwr_badge:
                row2_parts.append(pwr_badge)
                
            row2 = f"{FRAME_COLOR}└─{RESET} " + dash_sep.join(row2_parts)
            return f"{row1}\n{row2}"

        else:
            # < 100 cols: 3-Line Responsive Wrapped Layout
            line1 = f"{FRAME_COLOR}┌─{RESET} " + sep.join(row1_parts)
            line2 = f"{FRAME_COLOR}├─{RESET} {ctx_section}"

            line3_parts = []
            if quota_parts:
                line3_parts.append(dash_sep.join(quota_parts))
            if sys_badge:
                line3_parts.append(sys_badge)

            if line3_parts:
                line3 = f"{FRAME_COLOR}└─{RESET} " + dash_sep.join(line3_parts)
                return f"{line1}\n{line2}\n{line3}"
            else:
                line2_alt = f"{FRAME_COLOR}└─{RESET} {ctx_section}"
                return f"{line1}\n{line2_alt}"

    except Exception:
        # Ultimate fail-safe fallback with vibrant colors
        return f"{BRACKET_COLOR}┌─[{RESET}DECK:{GREEN_PHOSPHOR}● READY{RESET}{BRACKET_COLOR}]{RESET} {CYAN}{BOLD}⚡ AGY Neuromancer Statusline{RESET}\n{FRAME_COLOR}└─{RESET} {BRACKET_COLOR}[{RESET}{WHITE_BRIGHT}NEURAL.HUD Online{RESET}{BRACKET_COLOR}]{RESET}"


# ─── Main Streaming Input Receiver ─────────────────────────────────────────────
def main():
    try:
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
            if input_text.strip():
                decoder = json.JSONDecoder()
                idx = 0
                last_data = None
                while idx < len(input_text):
                    try:
                        input_text_slice = input_text[idx:].lstrip()
                        if not input_text_slice:
                            break
                        data, end_idx = decoder.raw_decode(input_text_slice)
                        if isinstance(data, dict):
                            last_data = data
                        idx += len(input_text[idx:]) - len(input_text_slice) + end_idx
                    except json.JSONDecodeError:
                        break
                
                if last_data:
                    print(render_deck(last_data))
                    return

        print("\033[90m┌─ [DECK:READY] Neuromancer Telemetry HUD\n└─ [NEURAL.HUD Standby]\033[0m")
    except Exception:
        print("\033[90m┌─ [DECK:READY] Neuromancer Telemetry HUD\n└─ [NEURAL.HUD Online]\033[0m")


if __name__ == "__main__":
    main()
