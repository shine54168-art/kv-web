#!/usr/bin/env python3
"""
HRK365 static site builder.

Content lives in _src/config.json and _src/pages/*.json as paired
zh/en strings. This script renders it into a plain static tree:

    /            /about/  /services/permanent/  ...   (Traditional Chinese)
    /en/         /en/about/                     ...   (English)

Output is committed HTML — GitHub Pages needs no build step. Run this
whenever content changes:

    python3 tools/build.py
"""

import json
import os
import re
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_src")
LANGS = ("zh", "en")
HTML_LANG = {"zh": "zh-Hant", "en": "en"}


# ---------------------------------------------------------------- helpers
def t(val, lang):
    """Pick a language out of a {"zh": ..., "en": ...} pair, or pass through."""
    if isinstance(val, dict) and ("zh" in val or "en" in val):
        return val.get(lang, val.get("zh", ""))
    return val if val is not None else ""


def url(href, lang):
    if not href.startswith("/"):
        return href
    return href if lang == "zh" else ("/en" + href)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


ICONS = {
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    "users": '<path d="M16 19v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 19v-2a4 4 0 0 0-3-3.87"/>',
    "layers": '<path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 0 20a15 15 0 0 1 0-20Z"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-5 3 3 5-7"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "chip": '<rect x="7" y="7" width="10" height="10" rx="2"/><path d="M4 10h3M4 14h3M17 10h3M17 14h3M10 4v3M14 4v3M10 17v3M14 17v3"/>',
    "bank": '<path d="M3 10h18"/><path d="M5 10v9M19 10v9M9 10v9M15 10v9"/><path d="m12 3 9 5H3l9-5Z"/><path d="M3 21h18"/>',
    "doc": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/>',
    "handshake": '<path d="m11 17 2 2 4-4"/><path d="M3 10l4-4 5 2 5-2 4 4-4 5-3-2-2 2-3-2-2 2-4-5Z"/>',
    "compass": '<circle cx="12" cy="12" r="9"/><path d="m15 9-2 5-5 2 2-5 5-2Z"/>',
}


def icon(name):
    return ('<span class="card__icon"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></span>'
            % ICONS.get(name, ICONS["layers"]))


TICK = ('<span class="tick"><svg viewBox="0 0 24 24" aria-hidden="true">'
        '<path d="m5 13 4 4L19 7"/></svg></span>')
ARROW = '<span class="arrow" aria-hidden="true">&rarr;</span>'


def btn(cta, lang, default="btn--primary"):
    style = cta.get("style", default)
    href = url(cta["href"], lang)
    return '<a class="btn %s" href="%s">%s %s</a>' % (
        style, esc(href), esc(t(cta["label"], lang)),
        ARROW if cta.get("arrow", True) else "")


def btn_row(ctas, lang, default="btn--primary"):
    if not ctas:
        return ""
    out = []
    for i, c in enumerate(ctas):
        out.append(btn(c, lang, default if i == 0 else "btn--ghost"))
    return '<div class="btn-row">%s</div>' % "".join(out)


def bullets(items, lang):
    if not items:
        return ""
    return '<ul class="bullets">%s</ul>' % "".join(
        "<li>%s</li>" % t(i, lang) for i in items)


def head(block, lang, center=False):
    if not block.get("title") and not block.get("eyebrow"):
        return ""
    cls = "section-head section-head--center" if center or block.get("center") else "section-head"
    h = '<div class="%s" data-reveal>' % cls
    if block.get("eyebrow"):
        h += '<span class="eyebrow">%s</span>' % esc(t(block["eyebrow"], lang))
    if block.get("title"):
        h += "<h2>%s</h2>" % t(block["title"], lang)
    if block.get("body"):
        h += "<p>%s</p>" % t(block["body"], lang)
    return h + "</div>"


def section_open(block, extra=""):
    cls = "section"
    if block.get("soft"):
        cls += " section--soft"
    if block.get("tight"):
        cls += " section--tight"
    sid = ' id="%s"' % esc(block["id"]) if block.get("id") else ""
    return '<section class="%s%s"%s><div class="wrap">' % (cls, extra, sid)


SECTION_CLOSE = "</div></section>"


# ---------------------------------------------------------------- blocks
def b_hero(b, lang, cfg):
    h = '<header class="hero"><div class="wrap"><div class="hero__grid"><div>'
    if b.get("eyebrow"):
        h += '<span class="eyebrow">%s</span>' % esc(t(b["eyebrow"], lang))
    h += "<h1>%s</h1>" % t(b["title"], lang)
    if b.get("sub"):
        h += '<p class="hero__sub">%s</p>' % t(b["sub"], lang)
    h += btn_row(b.get("ctas"), lang)
    if b.get("markets"):
        chips = "".join('<span class="chip">%s</span>' % esc(m)
                        for m in cfg["markets"][lang])
        h += '<div class="marketstrip">%s</div>' % chips
    h += "</div>"
    card = b.get("card")
    if card:
        h += '<aside class="hero__card"><h3>%s</h3><ul>' % esc(t(card["title"], lang))
        for it in card["items"]:
            h += "<li>%s<span>%s</span></li>" % (TICK, t(it, lang))
        h += "</ul></aside>"
    return h + "</div></div></header>"


def b_pagehero(b, lang, cfg):
    h = '<header class="hero hero--page"><div class="wrap">'
    crumbs = b.get("crumbs") or []
    if crumbs:
        parts = ['<a href="%s">%s</a>' % (url("/", lang), "首頁" if lang == "zh" else "Home")]
        for c in crumbs:
            if c.get("href"):
                parts.append('<a href="%s">%s</a>' % (esc(url(c["href"], lang)), esc(t(c["label"], lang))))
            else:
                parts.append(esc(t(c["label"], lang)))
        h += '<nav class="breadcrumb" aria-label="breadcrumb">%s</nav>' % "<span>/</span>".join(parts)
    if b.get("eyebrow"):
        h += '<span class="eyebrow">%s</span>' % esc(t(b["eyebrow"], lang))
    h += "<h1>%s</h1>" % t(b["title"], lang)
    if b.get("sub"):
        h += '<p class="hero__sub">%s</p>' % t(b["sub"], lang)
    h += btn_row(b.get("ctas"), lang)
    return h + "</div></header>"


def b_cards(b, lang, cfg):
    cols = b.get("cols", 3)
    h = section_open(b) + head(b, lang, b.get("center", True))
    h += '<div class="grid grid-%d">' % cols
    for it in b["items"]:
        link = it.get("link")
        tag = "a" if link else "div"
        attrs = ' href="%s"' % esc(url(link["href"], lang)) if link else ""
        h += '<%s class="card card--link"%s data-reveal>' % (tag, attrs)
        if it.get("icon"):
            h += icon(it["icon"])
        if it.get("num"):
            h += '<span class="card__num">%s</span>' % esc(t(it["num"], lang))
        h += "<h3>%s</h3>" % t(it["title"], lang)
        if it.get("body"):
            h += "<p>%s</p>" % t(it["body"], lang)
        h += bullets(it.get("bullets"), lang)
        if link:
            h += '<span class="cardlink">%s %s</span>' % (esc(t(link["label"], lang)), ARROW)
        h += "</%s>" % tag
    return h + "</div>" + SECTION_CLOSE


def b_split(b, lang, cfg):
    h = section_open(b)
    cls = "split split--wide"
    left = '<div data-reveal>%s' % head({"eyebrow": b.get("eyebrow"), "title": b.get("title"),
                                         "body": b.get("body")}, lang)
    left += bullets(b.get("bullets"), lang)
    left += btn_row(b.get("ctas"), lang)
    left += "</div>"
    panel = b.get("panel")
    right = ""
    if panel:
        pcls = "split__panel" if panel.get("dark", True) else "panel-soft"
        right = '<div class="%s" data-reveal><h3>%s</h3>' % (pcls, t(panel["title"], lang))
        if panel.get("body"):
            h_body = t(panel["body"], lang)
            right += '<p style="margin-top:12px">%s</p>' % h_body
        right += bullets(panel.get("items"), lang)
        right += "</div>"
    if b.get("reverse"):
        h += '<div class="%s">%s%s</div>' % (cls, right, left)
    else:
        h += '<div class="%s">%s%s</div>' % (cls, left, right)
    return h + SECTION_CLOSE


def b_steps(b, lang, cfg):
    h = section_open(b) + head(b, lang)
    h += '<div class="steps">'
    for i, it in enumerate(b["items"], 1):
        h += ('<div class="step" data-reveal><div class="step__n">%02d</div>'
              '<div><h3>%s</h3><p>%s</p></div></div>'
              % (i, t(it["title"], lang), t(it["body"], lang)))
    return h + "</div>" + SECTION_CLOSE


def b_stats(b, lang, cfg):
    h = section_open(b) + head(b, lang, True)
    h += '<div class="stats">'
    for it in b["items"]:
        cls = "stat stat--tbc" if it.get("tbc") else "stat"
        h += ('<div class="%s" data-reveal><div class="stat__n">%s</div>'
              '<div class="stat__l">%s</div></div>'
              % (cls, esc(t(it["n"], lang)), t(it["l"], lang)))
    return h + "</div>" + SECTION_CLOSE


def b_table(b, lang, cfg):
    h = section_open(b) + head(b, lang)
    h += '<div class="tablewrap" data-reveal><table><thead><tr>'
    for c in b["columns"]:
        h += "<th>%s</th>" % esc(t(c, lang))
    h += "</tr></thead><tbody>"
    for row in b["rows"]:
        h += "<tr>%s</tr>" % "".join("<td>%s</td>" % t(c, lang) for c in row)
    return h + "</tbody></table></div>" + SECTION_CLOSE


def b_faq(b, lang, cfg):
    h = section_open(b) + head(b, lang)
    h += '<div class="acc" data-reveal>'
    for it in b["items"]:
        h += ('<div class="acc__item"><button class="acc__q" type="button" aria-expanded="false">%s</button>'
              '<div class="acc__a"><div>%s</div></div></div>'
              % (t(it["q"], lang), t(it["a"], lang)))
    return h + "</div>" + SECTION_CLOSE


def b_quotes(b, lang, cfg):
    h = section_open(b) + head(b, lang, True)
    h += '<div class="grid grid-%d">' % b.get("cols", 2)
    for it in b["items"]:
        h += ('<blockquote class="quote" data-reveal><p>%s</p><footer>%s</footer></blockquote>'
              % (t(it["text"], lang), t(it["author"], lang)))
    return h + "</div>" + SECTION_CLOSE


def b_logos(b, lang, cfg):
    h = section_open(b) + head(b, lang, True)
    slot = "客戶標誌待補" if lang == "zh" else "Client logo TBC"
    slots = ('<div class="logo-slot">%s</div>' % slot) * b.get("count", 6)
    h += '<div class="logo-row" data-reveal>%s</div>' % slots
    return h + SECTION_CLOSE


def b_posts(b, lang, cfg):
    h = section_open(b) + head(b, lang)
    h += '<div class="grid grid-3">'
    for it in b["items"]:
        h += '<article class="card card--link" data-reveal><div class="postcard">'
        h += '<time>%s</time>' % esc(t(it.get("date", ""), lang))
        h += "<h3>%s</h3><p>%s</p></div>" % (t(it["title"], lang), t(it["body"], lang))
        h += '<span class="cardlink">%s %s</span>' % (
            "即將上線" if lang == "zh" else "Coming soon", ARROW)
        h += "</article>"
    return h + "</div>" + SECTION_CLOSE


def b_rich(b, lang, cfg):
    h = section_open(b) + head(b, lang)
    h += '<div class="lede" data-reveal style="max-width:74ch">%s</div>' % t(b["html"], lang)
    return h + SECTION_CLOSE


def b_contact(b, lang, cfg):
    c = cfg["contact"]
    L = {
        "zh": {"name": "姓名", "company": "公司", "email": "公司 Email", "phone": "聯絡電話",
               "topic": "需求類型", "msg": "需求說明", "send": "送出需求",
               "note": "我們會在一個工作日內回覆。表單內容僅用於本次聯繫。",
               "topics": ["正職人才推薦（獵才）", "人力派遣／約聘", "大量招募／RPO",
                          "薪資外包／勞健保實務", "HR 顧問專案", "其他"],
               "dt": ["Email", "電話", "LINE", "地址", "服務時間"]},
        "en": {"name": "Name", "company": "Company", "email": "Work email", "phone": "Phone",
               "topic": "What do you need?", "msg": "Tell us about the role or project",
               "send": "Send enquiry",
               "note": "We reply within one business day. Your details are used for this enquiry only.",
               "topics": ["Permanent placement", "Contract staffing", "Volume hiring / RPO",
                          "Payroll outsourcing", "HR consulting", "Something else"],
               "dt": ["Email", "Phone", "LINE", "Address", "Hours"]},
    }[lang]
    opts = "".join("<option>%s</option>" % esc(o) for o in L["topics"])
    endpoint = c.get("form_endpoint") or ""
    if endpoint:
        form_attrs = 'method="POST" action="%s"' % esc(endpoint)
        note = L["note"]
    else:
        # No form backend configured yet: the form composes an email instead,
        # so enquiries still reach us on a purely static host.
        form_attrs = 'data-mailto="%s"' % esc(c["email"])
        note = {"zh": "送出後會開啟你的郵件軟體並帶入內容，寄到 %s。也可以直接來信。" % c["email"],
                "en": "Submitting opens your email client with the details filled in, addressed to %s. You are welcome to write to us directly."  % c["email"]}[lang]
    h = section_open(b) + head(b, lang)
    h += '<div class="split" style="align-items:start"><div data-reveal>'
    h += ('<form class="form" %s>'
          '<div class="form__row">'
          '<div class="field"><label for="f-name">%s</label><input id="f-name" name="name" required></div>'
          '<div class="field"><label for="f-co">%s</label><input id="f-co" name="company"></div></div>'
          '<div class="form__row">'
          '<div class="field"><label for="f-mail">%s</label><input id="f-mail" type="email" name="email" required></div>'
          '<div class="field"><label for="f-tel">%s</label><input id="f-tel" name="phone"></div></div>'
          '<div class="field"><label for="f-topic">%s</label><select id="f-topic" name="topic">%s</select></div>'
          '<div class="field"><label for="f-msg">%s</label><textarea id="f-msg" name="message"></textarea></div>'
          '<button class="btn btn--primary" type="submit">%s</button>'
          '<p class="form__note">%s</p></form>'
          % (form_attrs, L["name"], L["company"], L["email"], L["phone"],
             L["topic"], opts, L["msg"], L["send"], note))
    h += "</div>"
    h += ('<div class="panel-soft" data-reveal><dl class="contactlist">'
          '<div><dt>%s</dt><dd><a href="mailto:%s">%s</a></dd></div>'
          '<div><dt>%s</dt><dd><a href="tel:%s">%s</a></dd></div>'
          '<div><dt>%s</dt><dd>%s</dd></div>'
          '<div><dt>%s</dt><dd>%s</dd></div>'
          '<div><dt>%s</dt><dd>%s</dd></div></dl></div>'
          % (L["dt"][0], esc(c["email"]), esc(c["email"]),
             L["dt"][1], esc(c["phone_href"]), esc(c["phone_display"]),
             L["dt"][2], esc(c["line_id"]),
             L["dt"][3], esc(t(c["address"], lang)),
             L["dt"][4], esc(t(c["hours"], lang))))
    return h + "</div>" + SECTION_CLOSE


def b_cta(b, lang, cfg):
    h = '<section class="section"><div class="wrap"><div class="ctaband" data-reveal>'
    h += "<h2>%s</h2>" % t(b["title"], lang)
    if b.get("body"):
        h += "<p>%s</p>" % t(b["body"], lang)
    ctas = b.get("ctas") or [
        {"label": {"zh": "預約諮詢", "en": "Book a consultation"}, "href": "/contact/"}]
    row = "".join(btn(c, lang, "btn--primary" if i == 0 else "btn--onDark")
                  for i, c in enumerate(ctas))
    return h + '<div class="btn-row">%s</div></div></div></section>' % row


BLOCKS = {
    "hero": b_hero, "pagehero": b_pagehero, "cards": b_cards, "split": b_split,
    "steps": b_steps, "stats": b_stats, "table": b_table, "faq": b_faq,
    "quotes": b_quotes, "logos": b_logos, "posts": b_posts, "rich": b_rich,
    "contact": b_contact, "cta": b_cta,
}


# ---------------------------------------------------------------- chrome
def render_nav(cfg, lang, alt_href):
    b = cfg["brand"]
    h = '<a class="skip" href="#main">%s</a>' % ("跳到主要內容" if lang == "zh" else "Skip to content")
    h += '<nav class="nav"><div class="nav__inner">'
    h += ('<a class="logo" href="%s"><img class="logo__mark" src="%s" alt="" width="38" height="45">'
          '<span class="logo__text"><span class="logo__name">%s</span>'
          '<span class="logo__sub">%s</span></span></a>'
          % (url("/", lang), esc(b["logo"]), esc(b["name"]),
             "Talent &amp; HR" if lang == "en" else "獵才顧問"))
    h += '<ul class="nav__links">'
    for item in cfg["nav"]:
        sub = item.get("children")
        h += '<li class="%s">' % ("has-sub" if sub else "")
        h += '<a href="%s">%s</a>' % (esc(url(item["href"], lang)), esc(t(item["label"], lang)))
        if sub:
            h += '<div class="subnav">%s</div>' % "".join(
                '<a href="%s">%s</a>' % (esc(url(s["href"], lang)), esc(t(s["label"], lang)))
                for s in sub)
        h += "</li>"
    h += "</ul>"
    h += '<div class="nav__actions">'
    h += '<a class="langbtn" href="%s" hreflang="%s">%s</a>' % (
        esc(alt_href), "en" if lang == "zh" else "zh-Hant", "EN" if lang == "zh" else "中文")
    h += '<a class="btn btn--primary nav__cta" href="%s">%s</a>' % (
        esc(url("/contact/", lang)), "預約諮詢" if lang == "zh" else "Talk to us")
    h += ('<button class="burger" type="button" aria-label="Menu" aria-expanded="false">'
          "<span></span><span></span><span></span></button>")
    h += "</div></div>"
    # mobile drawer
    h += '<div class="mobile">'
    for item in cfg["nav"]:
        h += '<a href="%s">%s</a>' % (esc(url(item["href"], lang)), esc(t(item["label"], lang)))
        if item.get("children"):
            h += '<div class="sub">%s</div>' % "".join(
                '<a href="%s">%s</a>' % (esc(url(s["href"], lang)), esc(t(s["label"], lang)))
                for s in item["children"])
    h += '<a href="%s">%s</a>' % (esc(url("/contact/", lang)),
                                  "聯絡我們" if lang == "zh" else "Contact")
    h += '<a class="btn btn--primary" href="%s">%s</a>' % (
        esc(url("/contact/", lang)), "預約諮詢" if lang == "zh" else "Talk to us")
    h += "</div></nav>"
    return h


def render_footer(cfg, lang):
    b, c = cfg["brand"], cfg["contact"]
    about = {
        "zh": "HRK365 是跨境人才與 HR 顧問團隊，服務台灣與東南亞的企業客戶，"
              "從招募、派遣、薪資外包到組織與制度顧問，一條線串起來。",
        "en": "HRK365 is a cross-border talent and HR consulting team serving employers "
              "across Taiwan and Southeast Asia — from recruitment and contract staffing "
              "to payroll outsourcing and organisational consulting.",
    }[lang]
    h = '<footer class="footer"><div class="wrap"><div class="footer__grid"><div>'
    h += ('<a class="logo" href="%s"><img class="logo__mark" src="%s" alt="" width="38" height="45">'
          '<span class="logo__text"><span class="logo__name">%s</span>'
          '<span class="logo__sub">%s</span></span></a>'
          % (url("/", lang), esc(b["logo"]), esc(b["name"]), esc(t(b["tagline"], lang))))
    h += '<p class="footer__about">%s</p>' % about
    h += '<p class="footer__about"><a href="mailto:%s">%s</a><a href="tel:%s">%s</a></p>' % (
        esc(c["email"]), esc(c["email"]), esc(c["phone_href"]), esc(c["phone_display"]))
    h += "</div>"
    for col in cfg["footer"]["columns"]:
        h += "<div><h4>%s</h4>" % esc(t(col["title"], lang))
        for l in col["links"]:
            h += '<a href="%s">%s</a>' % (esc(url(l["href"], lang)), esc(t(l["label"], lang)))
        h += "</div>"
    h += "</div>"
    h += ('<div class="footer__meta"><span>&copy; <span class="js-year">%s</span> %s. %s</span>'
          "<span>%s</span></div>"
          % (date.today().year, esc(b["name"]),
             "All rights reserved." if lang == "en" else "版權所有。",
             esc(t(b["licence"], lang))))
    return h + "</div></footer>"


BASE = """<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="zh-Hant" href="{alt_zh}">
<link rel="alternate" hreflang="en" href="{alt_en}">
<link rel="alternate" hreflang="x-default" href="{alt_en}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="HRK365">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
{og_image}<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#232E39">
<link rel="icon" href="{favicon}">
<link rel="apple-touch-icon" href="{favicon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700;800&family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css">
<noscript><style>[data-reveal]{{opacity:1;transform:none}}</style></noscript>
{jsonld}
</head>
<body>
{nav}
<main id="main">
{body}
</main>
{footer}
<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


def org_jsonld(cfg):
    b, c = cfg["brand"], cfg["contact"]
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": b["name"],
        "url": b["base_url"],
        "email": c["email"],
        "telephone": c["phone_display"],
        "areaServed": cfg["markets"]["en"],
        "description": "Cross-border recruitment and HR consulting for employers in "
                       "Taiwan and Southeast Asia.",
    }
    return '<script type="application/ld+json">%s</script>' % json.dumps(
        data, ensure_ascii=False)


def faq_jsonld(page, lang):
    for b in page["blocks"]:
        if b["type"] == "faq":
            items = [{"@type": "Question", "name": re.sub(r"<[^>]+>", "", t(i["q"], lang)),
                      "acceptedAnswer": {"@type": "Answer",
                                         "text": re.sub(r"<[^>]+>", "", t(i["a"], lang))}}
                     for i in b["items"]]
            return '<script type="application/ld+json">%s</script>' % json.dumps(
                {"@context": "https://schema.org", "@type": "FAQPage",
                 "mainEntity": items}, ensure_ascii=False)
    return ""


# ---------------------------------------------------------------- build
NOT_FOUND = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>找不到這個頁面 | HRK365</title>
<meta name="robots" content="noindex">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<main id="main">
<header class="hero hero--page"><div class="wrap">
<span class="eyebrow">404</span>
<h1>這個頁面不存在</h1>
<p class="hero__sub">網址可能已經變更，或是連結有誤。<br><span lang="en">This page does not exist. The address may have changed, or the link is broken.</span></p>
<div class="btn-row">
<a class="btn btn--primary" href="/">回到首頁 <span class="arrow">&rarr;</span></a>
<a class="btn btn--onDark" href="/contact/">聯絡我們 <span class="arrow">&rarr;</span></a>
</div>
</div></header>
</main>
</body>
</html>
"""


def build():
    cfg = json.load(open(os.path.join(SRC, "config.json"), encoding="utf-8"))
    base_url = cfg["brand"]["base_url"]
    pages = []
    for fn in sorted(os.listdir(os.path.join(SRC, "pages"))):
        if fn.endswith(".json"):
            pages.append(json.load(open(os.path.join(SRC, "pages", fn), encoding="utf-8")))
    pages.sort(key=lambda p: (p["slug"].count("/"), p["slug"]))

    written = []
    for page in pages:
        slug = page["slug"].strip("/")
        for lang in LANGS:
            rel = ("" if lang == "zh" else "en/") + (slug + "/" if slug else "")
            out_dir = os.path.join(ROOT, rel)
            os.makedirs(out_dir, exist_ok=True)
            canonical = base_url + "/" + rel
            alt_zh = base_url + "/" + (slug + "/" if slug else "")
            alt_en = base_url + "/en/" + (slug + "/" if slug else "")
            alt_href = ("/en/" + (slug + "/" if slug else "")) if lang == "zh" \
                else ("/" + (slug + "/" if slug else ""))

            body = "".join(BLOCKS[b["type"]](b, lang, cfg) for b in page["blocks"])
            og = cfg["brand"].get("og_image", "")
            og_tag = ('<meta property="og:image" content="%s%s">\n' % (base_url, og)) \
                if og and os.path.exists(os.path.join(ROOT, og.lstrip("/"))) else ""
            jsonld = (org_jsonld(cfg) if not slug else "") + faq_jsonld(page, lang)
            html = BASE.format(
                html_lang=HTML_LANG[lang],
                title=esc(t(page["title"], lang)),
                desc=esc(t(page["desc"], lang)),
                canonical=canonical, alt_zh=alt_zh, alt_en=alt_en,
                jsonld=jsonld, favicon=cfg["brand"]["logo"], og_image=og_tag,
                nav=render_nav(cfg, lang, alt_href),
                body=body,
                footer=render_footer(cfg, lang),
            )
            with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
            written.append(canonical)

    # sitemap + robots
    urls = "".join(
        "<url><loc>%s</loc><changefreq>monthly</changefreq></url>" % u for u in written)
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % urls)
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % base_url)
    open(os.path.join(ROOT, ".nojekyll"), "w").close()
    with open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8") as f:
        f.write(NOT_FOUND)
    with open(os.path.join(ROOT, "CNAME"), "w", encoding="utf-8") as f:
        f.write(cfg["brand"]["domain"] + "\n")

    print("built %d pages (%d urls)" % (len(pages), len(written)))
    for u in written:
        print("  " + u)


if __name__ == "__main__":
    build()
