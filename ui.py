"""Shared look and feel: theme CSS, hero banner, badges, art cards, stat tiles."""
from __future__ import annotations

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@600;700&display=swap');

:root {
  --navy: #1a2340; --navy-2: #26304f; --plum: #4a2c3f;
  --red: #d0342c; --red-hover: #b52a23; --green: #16a34a; --green-hover: #12823b;
  --ink: #1e293b; --muted: #64748b; --line: #e3e7ef; --card: #ffffff;
  --mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  --page: 1180px;
}
[data-testid="stMain"] { overflow-x: hidden; }
[data-testid="stMainBlockContainer"] { max-width: var(--page); padding: 60px 24px 140px; }

/* ---- header / top nav ---------------------------------------------- */
header[data-testid="stHeader"] { background: var(--navy) !important; height: 76px;
  border-bottom: 1px solid rgba(255,255,255,.06); }
header[data-testid="stHeader"] [data-testid="stToolbar"] { height: 76px; padding: 0 28px; }
[data-testid="stHeaderLogo"], header img { height: 44px !important; max-height: 44px !important; }
a[data-testid="stTopNavLink"] { background: transparent !important; border-radius: 0 !important;
  padding: 10px 4px !important; margin: 0 14px; border-bottom: 2px solid transparent; }
a[data-testid="stTopNavLink"] p { color: rgba(255,255,255,.72) !important; font-weight: 600;
  font-size: 1.02rem; }
a[data-testid="stTopNavLink"]:hover p { color: #fff !important; }
a[data-testid="stTopNavLink"][aria-current="page"] { border-bottom-color: #fff; }
a[data-testid="stTopNavLink"][aria-current="page"] p { color: #fff !important; }
header [data-testid="stMainMenuButton"], header [data-testid="stExpandSidebarButton"],
header [data-testid="stExpandSidebarButton"] span { color: #fff !important; }
header [data-testid="stMainMenuButton"] svg { fill: #fff !important; }

/* ---- full-bleed dark bands (hero, game desk) ------------------------ */
.st-key-hero, [class*="st-key-desk"] {
  margin-left: calc(50% - 50vw) !important; margin-right: calc(50% - 50vw) !important;
  width: 100vw !important; max-width: none !important;
  padding: 36px max(24px, calc(50vw - var(--page) / 2 + 24px)) 56px !important;
  color: #fff;
  background:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px) 0 0 / 56px 56px,
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px) 0 0 / 56px 56px,
    radial-gradient(ellipse at 85% 10%, rgba(208,52,44,.28), transparent 55%),
    linear-gradient(120deg, var(--navy-2) 0%, #2b3452 55%, var(--plum) 100%);
}
.st-key-hero { margin-bottom: 28px !important; }
[class*="st-key-desk"] { padding-top: 26px !important; padding-bottom: 34px !important;
  margin-bottom: 22px !important; }
.st-key-hero p, .st-key-hero span, [class*="st-key-desk"] p { color: inherit; }

.back { display: inline-flex; align-items: center; gap: 10px; color: rgba(255,255,255,.85) !important;
  text-decoration: none !important; font-weight: 600; font-size: 1.02rem; margin: 4px 0 18px; }
.back:hover { color: #fff !important; }

.hero-title { font-size: clamp(2rem, 3.8vw, 3.2rem); font-weight: 800; letter-spacing: -.02em;
  line-height: 1.08; color: #fff; display: flex; flex-wrap: wrap; align-items: center; gap: 14px; }
.hero-desc { font-size: 1.22rem; line-height: 1.6; color: rgba(255,255,255,.86); margin: 16px 0 0 !important;
  max-width: 62ch; }
.meta { display: flex; flex-wrap: wrap; gap: 28px; margin-top: 22px; color: rgba(255,255,255,.75);
  font-size: 1.05rem; }
.meta span { display: inline-flex; align-items: center; gap: 9px; }
.meta.light { color: var(--muted); margin: 12px 0 14px; font-size: .95rem; gap: 18px; }

.badge { display: inline-flex; align-items: center; height: 30px; padding: 0 13px; border-radius: 7px;
  font-size: .92rem; font-weight: 700; letter-spacing: 0; vertical-align: middle; }
.badge.green { background: rgba(34,197,94,.14); color: #4ade80; border: 1px solid rgba(74,222,128,.45); }
.badge.slate { background: #64748b; color: #fff; }
.badge.amber { background: rgba(245,158,11,.16); color: #fbbf24; border: 1px solid rgba(251,191,36,.45); }
.on-light .badge.green { color: #15803d; background: #dcfce7; border-color: #86efac; }
.on-light .badge.amber { color: #b45309; background: #fef3c7; border-color: #fcd34d; }

/* ---- art card (game thumbnail) -------------------------------------- */
.art { border-radius: 18px; padding: 34px 14px 28px; display: flex; justify-content: center;
  gap: clamp(12px, 1.8vw, 28px); background:
    radial-gradient(rgba(255,255,255,.07) 1px, transparent 1px) 0 0 / 14px 14px,
    linear-gradient(135deg, rgba(255,255,255,.07), rgba(255,255,255,.03));
  border: 1px solid rgba(255,255,255,.12); box-shadow: 0 18px 40px rgba(0,0,0,.25); }
.art.small { padding: 26px 16px 22px; gap: 26px; border-radius: 12px; box-shadow: none;
  background:
    radial-gradient(rgba(255,255,255,.07) 1px, transparent 1px) 0 0 / 14px 14px,
    linear-gradient(120deg, var(--navy-2), var(--plum)); }
.art .item { display: flex; flex-direction: column; align-items: center; gap: 12px; min-width: 0; }
.art .face { height: 76px; display: flex; align-items: center; justify-content: center; }
.art .emoji { font-size: 2.8rem; line-height: 1; filter: drop-shadow(0 6px 8px rgba(0,0,0,.3)); }
.chip { font-family: var(--mono); font-size: .86rem; font-weight: 700; color: #fff;
  background: rgba(15,23,42,.45); border: 1px solid rgba(255,255,255,.22); border-radius: 7px;
  padding: 4px 11px; white-space: nowrap; }
.pcard { width: 52px; height: 72px; border-radius: 8px; background: #fff; color: #111;
  display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.4rem;
  box-shadow: 0 6px 14px rgba(0,0,0,.3); }
.pcard.red { color: #c62828; }
.pcard.back { background: repeating-linear-gradient(45deg,#2b4c7e,#2b4c7e 6px,#3a62a0 6px,#3a62a0 12px);
  color: #fff; }

/* ---- buttons -------------------------------------------------------- */
.stButton button, .stPageLink a, .stFormSubmitButton button { border-radius: 10px; font-weight: 700; }
.stButton button[kind="primary"] { background: var(--red); border-color: var(--red); }
.stButton button[kind="primary"]:hover { background: var(--red-hover); border-color: var(--red-hover); }
[class*="st-key-big"] button { min-height: 58px; padding: 0 30px !important; }
[class*="st-key-big"] button p { font-size: 1.15rem !important; font-weight: 700; }
[class*="st-key-big_link"] a { background: var(--red); border-radius: 10px; min-height: 52px;
  justify-content: center; text-decoration: none; }
[class*="st-key-big_link"] a:hover { background: var(--red-hover); }
[class*="st-key-big_link"] a p, [class*="st-key-big_link"] a span { color: #fff !important;
  font-weight: 700; font-size: 1.08rem; }
.st-key-big_link_home a { min-height: 58px; }
.st-key-hero .stButton button[kind="secondary"] { background: transparent; color: #fff;
  border-color: rgba(255,255,255,.35); }

/* ---- sticky play bar ------------------------------------------------- */
.st-key-playbar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 99; background: #fff;
  border-top: 1px solid var(--line); box-shadow: 0 -6px 18px rgba(15,23,42,.06);
  padding: 14px max(24px, calc(50vw - var(--page) / 2 + 24px)); }
.st-key-playbar [data-testid="stHorizontalBlock"] { align-items: center; }
.bar-title { font-weight: 700; font-size: 1.15rem; color: var(--ink); }
.bar-meta { color: var(--muted); font-size: .98rem; margin-top: 2px; }

/* ---- tabs as a segmented control + content card ----------------------- */
[data-testid="stTabs"] [role="tablist"] { background: #e9edf4; padding: 6px; border-radius: 12px;
  gap: 4px; border: none !important; box-shadow: none !important; }
[data-testid="stTab"] { flex: 1; justify-content: center; height: 50px; border-radius: 9px !important;
  padding: 0 14px !important; border: none !important; background: transparent; }
[data-testid="stTab"] p { font-size: 1.02rem; font-weight: 600; color: var(--muted); }
[data-testid="stTab"][aria-selected="true"] { background: #fff;
  box-shadow: 0 1px 3px rgba(15,23,42,.12); }
[data-testid="stTab"][aria-selected="true"] p { color: var(--ink); }
[data-testid="stTab"] > div:not([data-testid]) { display: none; }
[data-testid="stTabPanel"] { background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 28px 34px 30px !important; margin-top: 18px; }
.sec-h { display: flex; align-items: center; gap: 12px; font-size: 1.45rem; font-weight: 800;
  color: var(--ink); margin: 0 0 10px; }
.sec-h svg { color: var(--red); flex: none; }
.formula { font-family: var(--mono); font-size: 1.05rem; background: #f3f5f9; border: 1px solid var(--line);
  border-left: 4px solid var(--red); border-radius: 8px; padding: 14px 18px; margin: 8px 0 14px; }

.section-title { font-size: 1.5rem; font-weight: 800; color: var(--ink); margin: 0 0 4px; }
.section-sub { color: var(--muted); margin-bottom: 14px; }
[class*="st-key-gc_"] { background: var(--card); border-radius: 16px !important; }
.gc-title { font-size: 1.35rem; font-weight: 800; color: var(--ink); display: flex; flex-wrap: wrap;
  align-items: center; gap: 10px; margin-top: 6px; }
.gc-desc { color: #475569; line-height: 1.55; margin-top: 8px; }

/* ---- live game desk --------------------------------------------------- */
.desk-top { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: 14px; margin-bottom: 6px; }
.desk-title { font-size: 1.6rem; font-weight: 800; color: #fff; }
.stats { display: flex; flex-wrap: wrap; gap: 10px; }
.stat { background: rgba(15,23,42,.35); border: 1px solid rgba(255,255,255,.14); border-radius: 10px;
  padding: 7px 14px; min-width: 92px; }
.stat .k { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; color: rgba(255,255,255,.6); }
.stat .v { font-family: var(--mono); font-size: 1.15rem; font-weight: 700; color: #fff; }
.bag { border-radius: 14px; padding: 14px 18px; min-height: 128px;
  background: linear-gradient(135deg, rgba(255,255,255,.08), rgba(255,255,255,.03));
  border: 1px solid rgba(255,255,255,.14); }
.bag .h { display: flex; justify-content: space-between; font-size: .8rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .08em; color: rgba(255,255,255,.6); margin-bottom: 6px; }
.bag .h .reset { color: #fbbf24; }
.bag .row { display: flex; align-items: center; gap: 12px; min-height: 44px; }
.bag .n { font-family: var(--mono); font-size: 1.9rem; font-weight: 700; color: #fff; min-width: 2.1ch; }
.bag .fr { font-size: 1.05rem; line-height: 1.35; word-break: break-all; }
.event { display: flex; align-items: center; gap: 10px; border-radius: 10px; padding: 10px 14px;
  background: rgba(245,158,11,.14); border: 1px solid rgba(251,191,36,.45); color: #fde68a;
  font-weight: 600; }
.quote { text-align: center; border-radius: 16px; padding: 12px 10px 8px; margin: 8px 0 2px;
  background: rgba(15,23,42,.4); border: 1px solid rgba(255,255,255,.14); }
.quote .px { display: flex; justify-content: center; align-items: flex-end; gap: clamp(14px, 3vw, 30px);
  font-family: var(--mono); font-size: clamp(2.6rem, 7vw, 4.2rem); font-weight: 700; line-height: 1.1; }
.quote .side { display: flex; flex-direction: column; align-items: center; }
.quote .side small { font-family: 'Inter', sans-serif; font-size: .78rem; font-weight: 700;
  letter-spacing: .14em; color: rgba(255,255,255,.55); line-height: 1.6; }
.quote .bid { color: #f87171; } .quote .ask { color: #4ade80; } .quote .at { color: rgba(255,255,255,.35); }
.lock { text-align: center; font-weight: 600; font-size: .98rem; min-height: 1.6em; margin: 4px 0 6px; }
.lock.on { color: #fbbf24; } .lock.off { color: #4ade80; }
[class*="st-key-sell_btn"] button, [class*="st-key-buy_btn"] button,
[class*="st-key-hi_btn"] button, [class*="st-key-lo_btn"] button, [class*="st-key-skip_btn"] button {
  min-height: 64px; border: none; color: #fff; }
[class*="st-key-sell_btn"] button p, [class*="st-key-buy_btn"] button p,
[class*="st-key-hi_btn"] button p, [class*="st-key-lo_btn"] button p, [class*="st-key-skip_btn"] button p {
  font-size: 1.25rem; font-weight: 800; letter-spacing: .02em; }
[class*="st-key-sell_btn"] button, [class*="st-key-lo_btn"] button { background: #dc2626; }
[class*="st-key-sell_btn"] button:hover, [class*="st-key-lo_btn"] button:hover { background: #b91c1c; color: #fff; }
[class*="st-key-buy_btn"] button, [class*="st-key-hi_btn"] button { background: var(--green); }
[class*="st-key-buy_btn"] button:hover, [class*="st-key-hi_btn"] button:hover { background: var(--green-hover); color: #fff; }
[class*="st-key-skip_btn"] button { background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.3); }
[class*="st-key-skip_btn"] button:hover { background: rgba(255,255,255,.2); color: #fff; }
[class*="st-key-desk"] button:disabled { opacity: .38; }
.msg { border-radius: 10px; padding: 10px 14px; background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.12); color: rgba(255,255,255,.9); font-family: var(--mono);
  font-size: .92rem; min-height: 44px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.tile { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
.tile .k { font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.tile .v { font-family: var(--mono); font-size: 1.6rem; font-weight: 700; color: var(--ink); }
.tile .v.pos { color: var(--green); } .tile .v.neg { color: #dc2626; }
.big-card { display: flex; justify-content: center; gap: 22px; padding: 10px 0; }
.big-card .pcard { width: 120px; height: 168px; font-size: 2.8rem; border-radius: 14px; }
.odds { text-align: center; color: rgba(255,255,255,.85); font-family: var(--mono); }
[class*="st-key-desk"] [data-testid="stWidgetLabel"] p { color: rgba(255,255,255,.8); }
[class*="st-key-desk"] .stButton button[kind="secondary"]:not([class*="key"]) { }
[class*="st-key-quit"] button { background: transparent; color: rgba(255,255,255,.8);
  border-color: rgba(255,255,255,.3); min-height: 44px; padding: 0 10px; white-space: nowrap; }
[class*="st-key-quit"] button p { white-space: nowrap; }
[class*="st-key-desk"] [data-testid="stColumn"]:has([class*="st-key-quit"]) { flex: 0 0 auto !important;
  width: auto !important; min-width: 72px !important; }

[class*="st-key-desk"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 10px; }
[class*="st-key-desk"] [data-testid="stColumn"] { min-width: 0 !important; }

/* ---- Make a Market ---------------------------------------------------- */
.die { width: 56px; height: 56px; border-radius: 12px; background: #fff; color: #111;
  display: flex; align-items: center; justify-content: center; font-family: var(--mono);
  font-weight: 700; font-size: 1.7rem; box-shadow: 0 6px 14px rgba(0,0,0,.3); }
.die.hidden { background: repeating-linear-gradient(45deg,#7a2e3a,#7a2e3a 6px,#8f3846 6px,#8f3846 12px);
  color: #fff; }
.dice-row { display: flex; justify-content: center; gap: 22px; padding: 6px 0 2px; }
.dice-row .die { width: 92px; height: 92px; font-size: 2.8rem; border-radius: 18px; }
.settle { border-radius: 12px; padding: 12px 16px; text-align: center; color: #fff;
  background: rgba(22,163,74,.16); border: 1px solid rgba(74,222,128,.45); }
.flow { display: flex; flex-direction: column; gap: 8px; }
.fl { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px; border-radius: 10px;
  padding: 9px 14px; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.12);
  color: rgba(255,255,255,.88); font-size: .95rem; }
.fl b { font-family: var(--mono); color: #fff; }
.fl em { margin-left: auto; font-style: normal; color: rgba(255,255,255,.6); font-size: .88rem; }
.fl .lift { color: #4ade80; } .fl .hit { color: #f87171; } .fl .pass { color: rgba(255,255,255,.5); }
[class*="st-key-send_btn"] button { min-height: 44px; background: var(--red); color: #fff; border: none; }
[class*="st-key-send_btn"] button:hover { background: var(--red-hover); color: #fff; }
[class*="st-key-send_btn"] button p { font-weight: 700; }
[class*="st-key-shift"] button { background: transparent; color: rgba(255,255,255,.85);
  border-color: rgba(255,255,255,.3); }
[class*="st-key-shift"] button:hover { color: #fff; border-color: #fff; }

@media (max-width: 640px) {
  .dice-row .die { width: 70px; height: 70px; font-size: 2.1rem; }
  .fl em { margin-left: 0; }
  .bag { padding: 10px 12px; min-height: 0; }
  .bag .n { font-size: 1.4rem; }
  .bag .fr { font-size: .8rem; }
  [class*="st-key-sell_btn"] button p, [class*="st-key-buy_btn"] button p,
  [class*="st-key-hi_btn"] button p, [class*="st-key-lo_btn"] button p,
  [class*="st-key-skip_btn"] button p { font-size: 1rem; }
  .big-card .pcard { width: 92px; height: 128px; font-size: 2.2rem; }
  header[data-testid="stHeader"] [data-testid="stToolbar"] { padding: 0 12px; }
  .st-key-playbar { padding: 10px 16px; }
  .st-key-playbar [data-testid="stColumn"]:first-child { display: none; }
  .st-key-playbar [class*="st-key-big"] button { min-height: 50px; }
  .art { gap: 20px; padding: 26px 12px; }
  [data-testid="stTabPanel"] { padding: 20px 18px !important; }
  [data-testid="stTab"] p { font-size: .85rem; }
}
</style>
"""

ICON = {
    "users": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "clock": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
    "arrow": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>',
    "info": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    "calc": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8"/><path d="M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/></svg>',
    "play": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m10 8 6 4-6 4z"/></svg>',
    "bulb": '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>',
}


def html(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


def inject_css() -> None:
    html(CSS)


def badges(items: list[tuple[str, str]]) -> str:
    return "".join(f"<span class='badge {cls}'>{text}</span>" for text, cls in items)


def meta(players: str, minutes: str, light: bool = False) -> str:
    return (f"<div class='meta{' light' if light else ''}'>"
            f"<span>{ICON['users']}{players}</span><span>{ICON['clock']}{minutes}</span></div>")


def section(icon: str, title: str) -> None:
    html(f"<div class='sec-h'>{ICON[icon]}{title}</div>")


def hero(art: str, title: str, badge_items, desc: str, players: str, minutes: str,
         back: bool = True):
    """Dark full-width banner. Returns the right-hand column for the call-to-action."""
    with st.container(key="hero"):
        if back:
            html(f"<a class='back' href='./' target='_self'>{ICON['arrow']}Back to Games</a>")
        if art:
            a, b, c = st.columns([3.6, 6, 2.4], gap="large", vertical_alignment="top")
            a.markdown(art, unsafe_allow_html=True)
        else:
            b, c = st.columns([8.6, 2.4], gap="large", vertical_alignment="top")
        b.markdown(f"<div class='hero-title'>{title}{badges(badge_items)}</div>"
                   f"<p class='hero-desc'>{desc}</p>{meta(players, minutes)}",
                   unsafe_allow_html=True)
        return c


def play_bar(title: str, players: str, minutes: str, on_click, key: str) -> None:
    with st.container(key="playbar"):
        a, b = st.columns([7, 2], vertical_alignment="center")
        a.markdown(f"<div class='bar-title'>{title}</div>"
                   f"<div class='bar-meta'>{players} | {minutes}</div>", unsafe_allow_html=True)
        with b.container(key=f"big_{key}"):
            st.button("Play Now", key=key, type="primary", icon=":material/play_arrow:",
                      on_click=on_click, width="stretch")


def fruit_art(small: bool = False) -> str:
    return (f"<div class='art{' small' if small else ''}'>"
            "<div class='item'><div class='face emoji'>🍎</div><span class='chip'>× 11</span></div>"
            "<div class='item'><div class='face emoji'>🍊</div><span class='chip'>× 13</span></div>"
            "<div class='item'><div class='face emoji'>📈</div><span class='chip'>141 @ 142</span></div>"
            "</div>")


def cards_art(small: bool = False) -> str:
    return (f"<div class='art{' small' if small else ''}'>"
            "<div class='item'><div class='face'><div class='pcard'>7♠</div></div>"
            "<span class='chip'>now</span></div>"
            "<div class='item'><div class='face'><div class='pcard back'>?</div></div>"
            "<span class='chip'>next</span></div>"
            "<div class='item'><div class='face emoji'>⚖️</div><span class='chip'>f* 17%</span></div>"
            "</div>")


def mm_art(small: bool = False) -> str:
    return (f"<div class='art{' small' if small else ''}'>"
            "<div class='item'><div class='face'><div class='die'>6</div></div>"
            "<span class='chip'>shown</span></div>"
            "<div class='item'><div class='face'><div class='die hidden'>?</div></div>"
            "<span class='chip'>hidden</span></div>"
            "<div class='item'><div class='face emoji'>🏦</div><span class='chip'>11.5 @ 14.5</span></div>"
            "</div>")


def stat(k: str, v) -> str:
    return f"<div class='stat'><div class='k'>{k}</div><div class='v'>{v}</div></div>"


def tile(k: str, v: str, tone: str = "") -> str:
    return f"<div class='tile'><div class='k'>{k}</div><div class='v {tone}'>{v}</div></div>"


def tone(x: float) -> str:
    return "pos" if x > 0 else ("neg" if x < 0 else "")
