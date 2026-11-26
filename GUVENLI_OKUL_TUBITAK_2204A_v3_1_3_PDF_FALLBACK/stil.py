"""Arayüz stili. Harici yazı tipi/CDN çağrısı YOK (öğrenci IP'si üçüncü taraflara gitmez,
çevrimdışı çalışır). Streamlit'in iç sınıf adlarına bağımlılık en aza indirilmiştir."""
import streamlit as st

CSS = """
<style>
:root { --ink:#1d2b3d; --muted:#5b6b7e; --line:#dfe5ec; --navy:#1b3554; --blue:#315f96; }
.stApp { background:#f4f6f8; color:var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
.block-container { padding-top:1rem; max-width:1250px; }
h1,h2,h3 { color:#17263c; letter-spacing:-.025em; }
:focus-visible { outline:3px solid #3d78b5 !important; outline-offset:2px; }

/* tüm düğmeler kapsayıcı genişliğinde (use_container_width kullanımdan kalktı) */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button { width:100%; border-radius:10px; font-weight:700; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { background:var(--blue); border:0; color:#fff; }

.top-brand { display:flex; align-items:center; gap:.8rem; padding:.35rem 0 .6rem; }
.brand-mark { width:40px; height:40px; border-radius:10px; background:#203c5c; color:#fff; font-weight:800;
  display:flex; align-items:center; justify-content:center; }
.top-brand-name { font-weight:800; font-size:1.2rem; color:#172b46; }
.top-brand-sub { color:var(--muted); font-size:.78rem; }

/* radyo seçenekleri: alt alta, dokunması kolay kartlar (telefonda kesilmez) */
div[data-testid="stRadio"] > div[role="radiogroup"] { display:flex; flex-direction:column; gap:.45rem; }
div[data-testid="stRadio"] > div[role="radiogroup"] label { width:100%; margin:0; background:#fff; border:1px solid var(--line);
  border-radius:10px; padding:.65rem .9rem; color:#31445c; font-weight:600; }
div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) { border-color:var(--blue); background:#eef4fc; color:#1f4a78; }

.notice-bar { display:flex; align-items:center; gap:.55rem; padding:.6rem .85rem; margin:.4rem 0 .8rem;
  border:1px solid #dbe5ef; border-radius:11px; background:#fff; color:#4d5f75; font-size:.82rem; }
.notice-dot { width:8px; height:8px; flex-shrink:0; border-radius:50%; background:#3d78b5; }

.hero { padding:2rem 2rem; border-radius:16px; background:var(--navy); color:#fff; margin:.3rem 0 1.2rem; }
.hero h1 { color:#fff !important; margin:0 0 .5rem; font-size:clamp(1.8rem,4vw,2.5rem); }
.hero p { color:#e4efff; margin:0; max-width:720px; font-size:1.02rem; }
.eyebrow { text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:700; color:#bde9f3; margin-bottom:.6rem; }
.eyebrow-dark { color:#2d5f9a; font-size:.72rem; font-weight:800; letter-spacing:.14em; }
.page-heading h1 { margin:.1rem 0 .3rem; font-size:clamp(1.7rem,3vw,2.2rem); }
.page-heading p { margin:0; color:var(--muted); max-width:760px; }
.soft-card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:1.1rem 1.2rem; height:100%; }
.soft-card h3 { margin:.1rem 0 .4rem; font-size:1.1rem; }
.soft-card p { color:var(--muted); margin:0; }
.emergency { border:1px solid #f0c9c4; background:#fff5f3; color:#7a2a20; border-radius:12px; padding:.7rem .9rem; font-size:.9rem; }
.emergency b { color:#a1281b; }

div[data-testid="stMetric"], div[data-testid="stForm"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; }
.record-banner { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.8rem 1rem;
  margin-bottom:1rem; border:1px solid #e4eaf2; border-radius:14px; background:#f8fbff; }
.record-kicker { color:var(--muted); font-size:.68rem; font-weight:800; letter-spacing:.12em; }
.record-id { color:#17263c; font-size:1.2rem; font-weight:800; }
.pills { display:flex; gap:.4rem; flex-wrap:wrap; justify-content:flex-end; }
.pill { display:inline-block; border-radius:999px; padding:.3rem .7rem; font-size:.76rem; font-weight:800; white-space:nowrap; }
.status-waiting { color:#8a5700; background:#fff3d6; }
.status-active { color:#1d4ed8; background:#e4edff; }
.status-followup { color:#9a3412; background:#ffeadf; }
.status-done { color:#166534; background:#dcfce7; }
.prio-none { color:#475569; background:#eef2f6; }
.prio-low { color:#1d4ed8; background:#e4edff; }
.prio-mid { color:#8a5700; background:#fff3d6; }
.prio-high { color:#9a3412; background:#ffeadf; }
.prio-urgent { color:#fff; background:#b42318; }
.access-panel { padding:1.1rem; border:1px solid #dbe5f1; border-radius:14px; background:#fff; }
@media (max-width:700px) { .hero { padding:1.4rem 1.1rem; } }
@media (prefers-reduced-motion:reduce) { * { transition:none !important; animation:none !important; } }

/* kurumsal yan panel */
[data-testid="stSidebar"] { background:#12263f; border-right:1px solid #0d1c30; }
[data-testid="stSidebar"] * { color:#dbe6f3; }
[data-testid="stSidebar"] .top-brand-name { color:#fff; font-size:1.05rem; line-height:1.35; }
[data-testid="stSidebar"] [data-testid="stImage"] { margin:.1rem auto .45rem; }
[data-testid="stSidebar"] [data-testid="stImage"] img { display:block; margin-left:auto; margin-right:auto; }
[data-testid="stSidebar"] .top-brand-sub { color:#8fa6c2; }
[data-testid="stSidebar"] .brand-mark { background:#315f96; border:1px solid #4a78ad; }
.nav-title { font-size:.66rem; font-weight:800; letter-spacing:.16em; color:#8fa6c2 !important; margin:1.1rem 0 .3rem; }
[data-testid="stSidebar"] .stButton > button { justify-content:flex-start; background:transparent; border:0; box-shadow:none;
  color:#dbe6f3; font-weight:600; padding:.45rem .7rem; border-radius:8px; margin-bottom:2px; }
[data-testid="stSidebar"] .stButton > button:hover { background:rgba(255,255,255,.09); }
[data-testid="stSidebar"] .stButton > button[kind="primary"] { background:#315f96; color:#fff; box-shadow:inset 3px 0 0 #8fc1ff; }
.topbar { display:flex; justify-content:space-between; align-items:center; padding:.2rem 0 .7rem;
  border-bottom:1px solid var(--line); margin-bottom:.8rem; }
.crumb { color:#5b6b7e; font-size:.88rem; } .crumb span { margin:0 .35rem; color:#a8b4c2; } .crumb b { color:#17263c; }
div[data-testid="stMetric"] { box-shadow:0 1px 2px rgba(23,44,71,.05); }
/* telefon ve dar ekranlar */
@media (max-width:640px) {
  .block-container { padding:.6rem .8rem 3rem; }
  h1 { font-size:1.55rem !important; }
  .hero { padding:1.2rem 1rem; }
  .page-heading p { font-size:.95rem; }
  .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button { min-height:48px; font-size:1rem; }
  input, textarea, [data-baseweb="select"] * { font-size:16px !important; }   /* iOS yakınlaştırmasını önler */
  div[data-testid="stForm"] { padding:.8rem; }
  div[data-testid="stMetric"] { padding:.7rem .9rem; }
  .record-banner { flex-direction:column; align-items:flex-start; }
  .pills { justify-content:flex-start; }
  .topbar { flex-direction:column; align-items:flex-start; gap:.4rem; }
  .notice-bar { align-items:flex-start; }
}
.durum-not { color:var(--muted); font-size:.92rem; margin:.2rem 0 1rem; }
/* ===== v2.3 modern tasarım (yukarıdaki kuralları geçersiz kılar) ===== */
.hero { display:grid; grid-template-columns:1.25fr .75fr; align-items:center; gap:1rem; padding:2rem 2.2rem;
  border-radius:24px; background:linear-gradient(135deg,#14305a 0%,#2b5d99 58%,#3f8fd0 100%);
  box-shadow:0 14px 34px rgba(27,53,84,.22); overflow:hidden; }
.hero h1 { font-size:clamp(1.7rem,3.6vw,2.4rem); line-height:1.15; margin:0 0 .6rem; }
.hero p { font-size:1.02rem; max-width:520px; }
.hero-pills { display:flex; gap:.45rem; flex-wrap:wrap; margin-top:1.1rem; }
.hero-pill { background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.3); color:#fff; border-radius:999px;
  padding:.3rem .8rem; font-size:.78rem; font-weight:700; }
.hero-art svg { width:100%; height:auto; max-height:250px; display:block; }
.soft-card { border-radius:18px; padding:1.2rem 1.25rem; box-shadow:0 6px 18px rgba(23,44,71,.07);
  transition:transform .18s ease, box-shadow .18s ease; margin-bottom:.6rem; }
.soft-card:hover { transform:translateY(-3px); box-shadow:0 12px 26px rgba(23,44,71,.12); }
.soft-card h3 { font-size:1.08rem; margin:.7rem 0 .3rem; }
.soft-card p { font-size:.93rem; line-height:1.5; }
.icon-badge { width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center; }
.icon-badge svg { width:24px; height:24px; }
.ib-blue { background:#e3eefc; color:#2b5d99; } .ib-green { background:#dff5ea; color:#1f7a52; }
.ib-violet { background:#ece8fb; color:#5b45b0; } .ib-amber { background:#fff0d4; color:#a8680a; }
.ib-rose { background:#fde6e8; color:#b23a48; }
.section-title { font-size:1.15rem; font-weight:800; color:#17263c; margin:1.6rem 0 .7rem; }
.emergency { border-radius:14px; }
.sb-logo { display:flex; justify-content:center; padding:.5rem 0 .7rem; }
.sb-logo img { width:108px; height:108px; border-radius:50%;
  box-shadow:0 0 0 4px rgba(255,255,255,.14), 0 10px 22px rgba(0,0,0,.35); }
[data-testid="stSidebar"] .top-brand { justify-content:center; text-align:center; padding-top:0; }
@media (max-width:700px) {
  .hero { grid-template-columns:1fr; padding:1.4rem 1.2rem; }
  .hero-art { order:-1; max-width:190px; margin:0 auto; }
}
@media (prefers-reduced-motion:reduce) { .soft-card:hover { transform:none; } }
</style>
"""


def uygula() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# Günlük özet / öncelik banner / küçük ekran uyarlamaları (mevcut tema korunur).
CSS += """
<style>
.emergency { border-left:5px solid #b42318; box-shadow:0 4px 16px rgba(140,35,25,.08); }
div[data-testid="stMetric"] { min-width:0; overflow-wrap:anywhere; }
@media (max-width: 900px) {
  .block-container { padding-left:1rem; padding-right:1rem; }
  .record-banner { align-items:flex-start; flex-direction:column; }
  .pills { justify-content:flex-start; }
}
@media (max-width: 600px) {
  .block-container { padding-left:.75rem; padding-right:.75rem; }
  div[data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.65rem; }
  div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { min-width:min(100%, 240px); }
  .soft-card { padding:.9rem; }
  .record-id { font-size:1rem; overflow-wrap:anywhere; }
}
</style>
"""
