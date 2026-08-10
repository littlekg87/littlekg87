# -*- coding: utf-8 -*-
"""kunslab.com 사이트 생성기 — 한 페이지 구조.

_data 의 YAML 을 읽어 _site 에 완성된 HTML 을 만든다.
쓰는 법:  python build.py
"""
import os, re, io, shutil
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "_site")
LANGS = ["ko", "en"]
TOP_N = 3  # 상단에 노출할 대표 항목 수

LABELS = {
    "ko": dict(
        career="경력", publications="연구성과", talks="학술대회 발표 및 특강",
        projects="프로젝트 참여 이력", two_axes="연구의 두 축",
        students="학생 성과 소개", data="자료 공개",
        nav_career="경력", nav_publications="연구성과", nav_talks="발표 · 특강",
        nav_projects="프로젝트", nav_research="연구", nav_students="학생 성과",
        nav_data="자료 공개",
        show_all="전체 보기", hide="접기", open="열기", courses="담당 과목",
        empty="아직 등록된 항목이 없습니다.",
        d1="조선왕조실록", d2="색인 · 임베딩", d3="검색", d4="답변 생성",
        d_evidence="원문 근거 제시",
        d_caption="검색되는 자료에서 물을 수 있는 연구 환경으로",
        diagram_alt="Ask Sillok 구조 개념도",
    ),
    "en": dict(
        career="Career", publications="Publications", talks="Talks & Lectures",
        projects="Research Projects", two_axes="Two Lines of Inquiry",
        students="Student Work", data="Data & Code",
        nav_career="Career", nav_publications="Publications", nav_talks="Talks",
        nav_projects="Projects", nav_research="Research", nav_students="Students",
        nav_data="Data",
        show_all="Show all", hide="Collapse", open="Open", courses="Courses",
        empty="No entries yet.",
        d1="Annals", d2="Index", d3="Retrieve", d4="Generate",
        d_evidence="cite the source text",
        d_caption="from searchable records to an askable research environment",
        diagram_alt="Ask Sillok architecture",
    ),
}

NAV = [("career", "nav_career"), ("publications", "nav_publications"),
       ("talks", "nav_talks"), ("projects", "nav_projects"),
       ("research", "nav_research"), ("students", "nav_students"),
       ("data", "nav_data")]


def load(lang, name, default=None):
    path = os.path.join(ROOT, "_data", lang, name + ".yml")
    if not os.path.exists(path):
        return default
    with io.open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or default


def year_of(s):
    m = re.search(r"(\d{4})", str(s or ""))
    return m.group(1) if m else "—"


def build_section(items, make):
    """대표 항목(top)과 나머지(rest, 연도별 묶음)로 나눈다."""
    norm = [make(x) for x in (items or [])]
    norm.sort(key=lambda r: r["_sort"], reverse=True)
    top = [r for r in norm if r.get("_featured")][:TOP_N]
    if not top:
        top = norm[:TOP_N]
    keys = {id(r) for r in top}
    rest = [r for r in norm if id(r) not in keys]
    groups, cur = [], None
    for r in rest:
        y = year_of(r["date"])
        if cur is None or cur["year"] != y:
            cur = dict(year=y, rows=[])
            groups.append(cur)
        cur["rows"].append(r)
    return dict(top=top, rest=rest, groups=groups)


def main():
    site = yaml.safe_load(io.open(os.path.join(ROOT, "_data", "site.yml"), encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, "_templates")),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    for extra in ("CNAME", ".nojekyll", "robots.txt"):
        if os.path.exists(os.path.join(ROOT, extra)):
            shutil.copy(os.path.join(ROOT, extra), os.path.join(OUT, extra))

    have = [l for l in LANGS
            if os.path.exists(os.path.join(ROOT, "_data", l, "profile.yml"))]

    made = []
    for lang in LANGS:
        p = load(lang, "profile")
        if p is None:
            print("  (건너뜀) _data/%s 없음" % lang)
            continue
        t = LABELS[lang]

        def mk_career(c):
            line = "%s, %s" % (c.get("title", ""), c.get("org", ""))
            if c.get("detail"):
                line += " · " + c["detail"]
            return dict(date=c.get("period", ""), line=line,
                        tags=([dict(text=c["kind"], cls="k")] if c.get("kind") else []),
                        _sort=year_of(c.get("period")), _featured=c.get("featured"))

        def authors_html(x):
            """공저자가 있을 때만 저자 목록을 앞에 붙이고 본인 이름을 굵게 표시한다."""
            a = x.get("authors")
            if not a:
                return None
            out = escape(a)
            me = escape(p["name"])
            return Markup(str(out).replace(str(me), "<b>%s</b>" % me))

        def compose(x):
            parts = []
            au = authors_html(x)
            if au:
                parts.append(au)
            parts.append(escape(x.get("title", "")))
            if x.get("venue"):
                parts.append(escape(x["venue"]))
            if x.get("note"):
                parts.append(escape(x["note"]))
            return Markup(", ".join(str(s) for s in parts))

        def tags_of(x):
            out = []
            if x.get("kind"):
                out.append(dict(text=x["kind"], cls="k"))
            idx = x.get("index")
            for i in ([idx] if isinstance(idx, str) else (idx or [])):
                out.append(dict(text=i, cls="i"))
            return out

        def mk_pub(x):
            return dict(date=x.get("date", ""), line=compose(x), tags=tags_of(x),
                        doi=x.get("doi"), _sort=str(x.get("date", "")),
                        _featured=x.get("featured"))

        def mk_talk(x):
            return dict(date=x.get("date", ""), line=compose(x), tags=tags_of(x),
                        _sort=str(x.get("date", "")), _featured=x.get("featured"))

        def mk_proj(x):
            line = "%s, %s" % (x.get("title", ""), x.get("org", ""))
            if x.get("role"):
                line += " · " + x["role"]
            return dict(date=x.get("period", ""), line=line, tags=[],
                        _sort=year_of(x.get("period")), _featured=x.get("featured"))

        ctx = dict(
            lang=lang, t=t, site=site, p=p,
            sec_career=build_section(load(lang, "career", []), mk_career),
            sec_pubs=build_section(load(lang, "publications", []), mk_pub),
            sec_talks=build_section(load(lang, "talks", []), mk_talk),
            sec_projects=build_section(load(lang, "projects", []), mk_proj),
            research=load(lang, "research", {}),
            teaching=load(lang, "teaching", {}),
            datasets=load(lang, "datasets", {"items": []}),
        )

        depth = 1 if lang == "en" else 0
        site_root = "../" * depth if depth else "./"
        base = site_root + ("en/" if lang == "en" else "")
        ctx.update(
            root=site_root, base=base,
            nav=[dict(key=k, label=t[lab], href="#" + k) for k, lab in NAV],
            active=None, is_home=True, page_title=p["name"],
            meta_desc=re.sub(r"<[^>]+>", "", p.get("tagline", "")).replace("\n", " ").strip(),
            canonical=("/" if lang == "ko" else "/en/"),
            address=site["address_ko"] if lang == "ko" else site["address_en"],
            ko_href=site_root, en_href=site_root + "en/",
            show_lang=(len(have) > 1),
        )

        outdir = os.path.join(OUT, "" if lang == "ko" else "en")
        os.makedirs(outdir, exist_ok=True)
        html = env.get_template("index.html").render(**ctx)
        with io.open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        made.append(os.path.relpath(os.path.join(outdir, "index.html"), OUT))

    print("생성 완료 — %d개 파일" % len(made))
    for m in made:
        print("   ", m.replace("\\", "/"))


if __name__ == "__main__":
    main()
