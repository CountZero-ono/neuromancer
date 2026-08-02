#!/usr/bin/env python3
"""
Neuromancer — Cyberpunk Telemetry Deck & Statusline for Antigravity CLI
Onyx & Cyberpunk Amber Telemetry HUD with Fail-Safe Execution and Dual Quota Timers
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

# ─── Icons ─────────────────────────────────────────────────────────────────────
ICON_READY = "●"
ICON_THINKING = "◆"
ICON_WORKING = "⚙"
ICON_TOOL = "🔧"
ICON_UNKNOWN = "⏳"
ICON_VCS = ""
ICON_MODEL = "⚡"
ICON_CONV = "󰍪"
ICON_DIR = ""
ICON_RESET = "⌛"
ICON_HOST = "󰒋"

# ─── Helper Functions ──────────────────────────────────────────────────────────
def format_tokens(n: int) -> str:
    try:
        n = int(n)
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.0f}k"
        return str(n)
    except Exception:
        return "0"


def format_reset_time(sec: float) -> str:
    try:
        sec = int(sec)
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
        pct = max(0.0, min(100.0, float(pct)))
        filled_count = int(round(pct * length / 100.0))

        # Color based on remaining %
        if pct > 50:
            fill_color = AMBER_BRIGHT
        elif pct >= 20:
            fill_color = AMBER_WARM
        else:
            fill_color = RED_ALERT

        filled_str = f"{fill_color}{'▰' * filled_count}{RESET}"
        empty_str = f"{SHADOW_GRAY}{'▱' * (length - filled_count)}{RESET}"

        reset_str = ""
        if reset_sec > 0:
            r_fmt = format_reset_time(reset_sec)
            if r_fmt:
                reset_str = f" {AMBER_BRIGHT}{ICON_RESET}{r_fmt}{RESET}"

        lbl_colored = f"{WHITE_BRIGHT}{label}{RESET}"
        pct_colored = f"{fill_color}{pct:.0f}%{RESET}"

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


# ─── Render Neuromancer Deck Telemetry ─────────────────────────────────────────
def render_deck(data: dict) -> str:
    try:
        cols = int(data.get("terminal_width") or 80)
        
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
        model_obj = data.get("model", {})
        if isinstance(model_obj, dict):
            model_name = model_obj.get("display_name") or model_obj.get("id") or "AGY"
        else:
            model_name = str(model_obj or "AGY")
        model_str = f"{CYAN}{BOLD}{ICON_MODEL} {model_name}{RESET}"

        # 3. Git Branch
        cwd = str(data.get("cwd") or "")
        vcs_branch = str(data.get("vcs", {}).get("branch") or "")
        vcs_dirty = bool(data.get("vcs", {}).get("dirty", False))
        if not vcs_branch and cwd:
            vcs_branch, vcs_dirty = get_git_info(cwd)

        git_str = ""
        if vcs_branch:
            dirty_mark = f"{RED_ALERT}*{RESET}" if vcs_dirty else ""
            branch_color = RED_ALERT if vcs_dirty else CYAN
            git_str = f"{branch_color}{ICON_VCS} {vcs_branch}{dirty_mark}{RESET}"

        # 4. Working Directory
        cwd_short = shorten_path(cwd)
        cwd_str = f"{BRACKET_COLOR}{ICON_DIR} {cwd_short}{RESET}" if cwd_short else ""

        # 5. Conversation ID
        conv_id = str(data.get("conversation_id") or "")
        conv_str = f"{FRAME_COLOR}{ICON_CONV} {conv_id[:8]}{RESET}" if conv_id else ""

        # Assemble ROW 1 (Deck Status Header)
        row1_parts = [f"{BRACKET_COLOR}[{RESET}DECK:{state_str}{BRACKET_COLOR}]{RESET}", model_str]
        if git_str:
            row1_parts.append(git_str)
        if cwd_str:
            row1_parts.append(cwd_str)
        if conv_str and cols >= 110:
            row1_parts.append(conv_str)

        sep = f" {FRAME_COLOR}·{RESET} "
        row1 = f"{FRAME_COLOR}┌─{RESET} " + sep.join(row1_parts)

        # ─── ROW 2: Gauges & Diagnostics ────────────────────────────────────────

        # 6. Context Window Gauge
        cw = data.get("context_window", {})
        ctx_rem = float(cw.get("remaining_percentage", 100.0))
        ctx_used_pct = 100.0 - ctx_rem
        in_t = int(cw.get("total_input_tokens") or 0)
        out_t = int(cw.get("total_output_tokens") or 0)
        ctx_size = int(cw.get("context_window_size") or 0)
        ctx_used = in_t + out_t

        ctx_gauge = make_amber_gauge("CTX", ctx_used_pct, length=8 if cols >= 120 else 6)
        tok_info = ""
        if ctx_used > 0 and cols >= 140:
            tok_info = f" {DIM}(↑{format_tokens(in_t)} ↓{format_tokens(out_t)}){RESET}"

        # 7. Quota Gauges (5H & 7D)
        quota_data = data.get("quota", {})
        g_5h = quota_data.get("gemini-5h", {})
        g_wk = quota_data.get("gemini-weekly", {})
        tp_5h = quota_data.get("3p-5h", {})
        tp_wk = quota_data.get("3p-weekly", {})

        is_3p = "gemini" not in model_name.lower()
        if is_3p and (tp_5h.get("remaining_fraction") is not None or tp_wk.get("remaining_fraction") is not None):
            q_5h_frac = tp_5h.get("remaining_fraction")
            q_5h_sec = float(tp_5h.get("reset_in_seconds") or -1)
            q_wk_frac = tp_wk.get("remaining_fraction")
            q_wk_sec = float(tp_wk.get("reset_in_seconds") or -1)
        else:
            q_5h_frac = g_5h.get("remaining_fraction")
            q_5h_sec = float(g_5h.get("reset_in_seconds") or -1)
            q_wk_frac = g_wk.get("remaining_fraction")
            q_wk_sec = float(g_wk.get("reset_in_seconds") or -1)

        quota_parts = []
        if q_5h_frac is not None:
            pct_5h = float(q_5h_frac) * 100.0
            quota_parts.append(make_amber_gauge("5H", pct_5h, reset_sec=q_5h_sec, length=6))

        if q_wk_frac is not None:
            pct_wk = float(q_wk_frac) * 100.0
            quota_parts.append(make_amber_gauge("7D", pct_wk, reset_sec=q_wk_sec, length=6))

        quota_str = f" {FRAME_COLOR}──{RESET} ".join(quota_parts)

        # 8. System Resources Badge
        ram_str, load_str = get_system_telemetry()
        sys_badge = ""
        if ram_str and load_str and cols >= 130:
            sys_badge = f"{BRACKET_COLOR}[{RESET}{WHITE_BRIGHT}SYS{RESET} ram:{ram_str} ld:{load_str}{BRACKET_COLOR}]{RESET}"

        # 9. Tasks / Subagents / Sandbox
        task_cnt = int(data.get("task_count") or 0)
        sub_cnt = len(data.get("subagents") or []) if isinstance(data.get("subagents"), list) else 0
        art_cnt = int(data.get("artifact_count") or 0)
        sb_enabled = bool(data.get("sandbox", {}).get("enabled", False))

        deck_status = []
        if task_cnt > 0 or sub_cnt > 0 or art_cnt > 0:
            deck_status.append(f"tsk:{task_cnt} sub:{sub_cnt} art:{art_cnt}")
        if sb_enabled:
            deck_status.append("sandbox:ON")

        deck_badge = ""
        if deck_status and cols >= 150:
            deck_badge = f"{BRACKET_COLOR}[{RESET}{WHITE_BRIGHT}DECK{RESET} {' '.join(deck_status)}{BRACKET_COLOR}]{RESET}"

        # Assemble ROW 2
        row2_parts = [f"{ctx_gauge}{tok_info}"]
        if quota_str:
            row2_parts.append(quota_str)
        if sys_badge:
            row2_parts.append(sys_badge)
        if deck_badge:
            row2_parts.append(deck_badge)

        row2 = f"{FRAME_COLOR}└─{RESET} " + f" {FRAME_COLOR}──{RESET} ".join(row2_parts)

        return f"{row1}\n{row2}"
    except Exception:
        # Ultimate fail-safe fallback
        return f"\033[90m┌─ [DECK:READY] AGY Neuromancer Statusline\n└─ [NEURAL.HUD Online]\033[0m"


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
