"""K디자인 지역별 페이지 생성기.
사용법: python3 build.py <사이트폴더>
data.py 의 AREAS 를 고치고 다시 실행하면 지역 페이지, 메인 링크, sitemap, llms.txt 가 모두 다시 만들어진다.
"""
import json, os, re, shutil, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import *

ROOT = os.path.abspath(sys.argv[1])
E = html.escape


def write(rel, text):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


def loc_full(a):
    c = CITIES[a[0]]
    return " ".join(x for x in [c["name"], a[3], a[2]] if x)


def url_dong(a, cat):
    return f"area/{a[0]}/{a[1]}/{cat}/"


def url_city(city, cat=None):
    return f"area/{city}/{cat}/" if cat else f"area/{city}/"


def photo_set(cat, start, n):
    ph = CATS[cat]["photos"]
    return [ph[(start + i) % len(ph)] for i in range(min(n, len(ph)))]


# ---------- 공통 조각 ----------
def head(title, desc, rel_url, up, place=None, region="KR-44", jsonld=None, og_img="images/og-image.jpg"):
    canon = f"{SITE}/{rel_url}"
    geo = f'  <meta name="geo.region" content="{region}">\n'
    if place:
        geo += f'  <meta name="geo.placename" content="{E(place)}">\n'
    ld = f'  <script type="application/ld+json">\n{json.dumps(jsonld, ensure_ascii=False, indent=1)}\n  </script>\n' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{E(title)}</title>
  <meta name="description" content="{E(desc)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
  <meta name="theme-color" content="#f3eee6">
{geo}  <link rel="canonical" href="{canon}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{BRAND}">
  <meta property="og:title" content="{E(title)}">
  <meta property="og:description" content="{E(desc)}">
  <meta property="og:url" content="{canon}">
  <meta property="og:image" content="{SITE}/{og_img}">
  <meta property="og:locale" content="ko_KR">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="alternate" type="application/rss+xml" title="{BRAND}" href="{SITE}/rss.xml">
  <link rel="icon" href="{up}favicon.ico" sizes="any">
  <link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
  <link rel="preconnect" href="https://hangeul.pstatic.net" crossorigin>
  <link rel="stylesheet" href="https://hangeul.pstatic.net/hangeul_static/css/maru-buri.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{up}assets/site.css">
{ld}</head>
"""


def header(up):
    return f"""<body>
  <header class="top" id="top">
    <div class="wrap">
      <a href="{up}" class="brand" aria-label="{BRAND} 홈"><b>{BRAND}</b><span>Interior &amp; Remodeling</span></a>
      <nav class="nav" id="nav" aria-label="주요 메뉴">
        <a href="{up}#works">시공사례</a>
        <a href="{up}#services">시공분야</a>
        <a href="{up}area/">지역별 인테리어</a>
        <a href="{up}#faq">자주 묻는 질문</a>
      </nav>
      <a href="tel:{PHONE}" class="call">{PHONE}</a>
      <button class="nav-toggle" id="navToggle" aria-label="메뉴 열기" aria-expanded="false" aria-controls="nav">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M3 7h18M3 12h18M3 17h18"/></svg>
      </button>
    </div>
  </header>
"""


def footer(up):
    return f"""  <footer>
    <div class="wrap">
      <div>
        <b>{BRAND}</b>
        <address>대표 {CEO}, 전화 <a href="tel:{PHONE}">{PHONE}</a><br>충남 천안, 아산, 당진 / 경기 평택 주거공간·상업공간 인테리어</address>
      </div>
      <p style="align-self:end"><a href="{up}area/">지역별 인테리어</a> &nbsp; © 2026 {BRAND}</p>
    </div>
  </footer>
  <a href="tel:{PHONE}" class="callbar">전화 상담 {PHONE}</a>
  <dialog class="viewer" id="viewer" aria-label="사진 크게 보기">
    <img src="" alt="" id="viewerImg">
    <p><span id="viewerCap"></span><button type="button" id="viewerClose">닫기</button></p>
  </dialog>
  <script src="{up}assets/site.js"></script>
</body>
</html>
"""


def crumbs_html(items):
    out = []
    for i, (name, href) in enumerate(items):
        if href and i < len(items) - 1:
            out.append(f'<li><a href="{href}">{E(name)}</a></li>')
        else:
            out.append(f'<li aria-current="page">{E(name)}</li>')
    return '<nav class="crumbs" aria-label="현재 위치"><ol>' + "".join(out) + "</ol></nav>"


def crumbs_ld(items, page_url):
    return {
        "@type": "BreadcrumbList",
        "@id": page_url + "#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{SITE}/{u}" if u is not None else page_url}
            for i, (n, u) in enumerate(items)
        ],
    }


def business_ld():
    return {
        "@type": ["HomeAndConstructionBusiness", "LocalBusiness"],
        "@id": f"{SITE}/#business",
        "name": BRAND,
        "alternateName": ["K DESIGN", "K디자인"],
        "url": f"{SITE}/",
        "telephone": PHONE_INTL,
        "founder": {"@type": "Person", "name": CEO},
        "address": {"@type": "PostalAddress", "addressLocality": "천안시", "addressRegion": "충청남도", "addressCountry": "KR"},
    }


def gallery(photos, up, label_prefix=""):
    out = []
    for f, w, h, t, d, alt in photos:
        out.append(
            f'<figure class="work"><button type="button" data-full="{up}images/{f}" data-cap="{E(t)}, {E(d)}">'
            f'<div class="photo"><img src="{up}images/{f}" width="{w}" height="{h}" alt="{BRAND} {E(label_prefix)}{E(alt)}" loading="lazy" decoding="async"></div>'
            f'</button><figcaption><h3>{E(t)}</h3><span>{E(d)}</span></figcaption></figure>'
        )
    return '<div class="works works-even">' + "\n".join(out) + "</div>"


def faq_block(qas):
    items = "\n".join(
        f'<details{" open" if i == 0 else ""}><summary>{E(q)}</summary><p>{a}</p></details>' for i, (q, a) in enumerate(qas)
    )
    return f"""    <section class="sec" id="faq">
      <div class="wrap faq-grid">
        <h2>자주 묻는 질문</h2>
        <div class="faq-list">
{items}
        </div>
      </div>
    </section>
"""


def faq_ld(qas, page_url):
    return {
        "@type": "FAQPage",
        "@id": page_url + "#faq",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}}
            for q, a in qas
        ],
    }


def contact_block(where):
    return f"""    <section class="sec contact" id="contact">
      <div class="wrap contact-grid">
        <div>
          <h2>{E(where)} 인테리어 상담</h2>
          <p>평수, 원하는 공사 범위, 희망 일정을 알려주시면 대표가 직접 상담하고 현장을 방문합니다.</p>
          <a href="tel:{PHONE}" class="phone-big">{PHONE}</a>
        </div>
        <dl class="nap">
          <dt>상호</dt><dd>{BRAND}</dd>
          <dt>대표</dt><dd>{CEO}</dd>
          <dt>시공 분야</dt><dd>주거공간, 상업공간 인테리어</dd>
          <dt>시공 지역</dt><dd>충남 천안, 아산, 당진 / 경기 평택</dd>
        </dl>
      </div>
    </section>
"""


STEPS = """        <ol class="steps">
          <li><h3>전화 상담</h3><p>원하는 공간, 예산, 일정을 들려주세요.</p></li>
          <li><h3>현장 실측</h3><p>{dong} 현장에 직접 방문해 구조와 상태를 확인합니다.</p></li>
          <li><h3>디자인과 견적</h3><p>디자인과 항목별 견적을 함께 드립니다.</p></li>
          <li><h3>시공</h3><p>공정마다 진행 상황을 공유합니다.</p></li>
          <li><h3>완공과 점검</h3><p>마감을 함께 확인한 뒤 인도합니다.</p></li>
        </ol>"""

INTRO = {
    "commercial": [
        "{loc}에서 상가, 카페, 음식점, 사무실 인테리어를 준비하고 계신가요? {b}은 업종과 손님 동선, 운영 방식을 먼저 확인한 뒤 매장을 설계하고 시공합니다.",
        "{dong} 상업공간 인테리어는 오픈 일정과 예산이 가장 중요합니다. {b}은 현장 실측 후 공정별 일정과 항목별 견적을 먼저 정리해 드리고, 그 일정에 맞춰 시공합니다.",
        "{dong}에서 매장을 새로 열거나 기존 매장을 리모델링할 때, {b} 대표가 직접 현장을 보고 상담합니다. 카페, 헤어샵, 필라테스 스튜디오, 음식점까지 업종에 맞는 공간을 만듭니다.",
        "{loc} 상가 인테리어, 철거부터 전기·설비, 조명, 마감, 외관까지 한 번에 맡길 수 있습니다. 업종에 필요한 설비와 손님이 머무는 공간을 함께 설계합니다.",
    ],
    "residential": [
        "{loc}에서 아파트 리모델링이나 주택 인테리어를 계획하고 계신가요? {b}은 가족의 생활 방식에 맞춰 구조, 수납, 조명을 함께 설계하고 시공합니다.",
        "{dong} 주거공간 인테리어는 전체 리모델링부터 욕실, 주방 부분 시공까지 가능합니다. 현장 실측 후 디자인과 항목별 견적을 먼저 안내해 드립니다.",
        "{dong} 아파트·주택 인테리어, 대표가 직접 상담하고 현장을 챙깁니다. 우물천장 간접조명, 아트월, 욕실 리모델링처럼 매일 쓰는 공간의 만족도를 높이는 시공을 합니다.",
        "{loc} 집 인테리어, 입주 전 리모델링이나 살면서 하는 부분 공사 모두 상담할 수 있습니다. 공정마다 진행 상황을 공유하며 시공합니다.",
    ],
}

FAQ = {
    "commercial": [
        ("{dong} 상가 인테리어도 시공하나요?", "네. {loc} 상가, 카페, 음식점, 사무실 등 상업공간 인테리어를 설계부터 시공까지 진행합니다."),
        ("{dong} 매장 인테리어 견적은 어떻게 받나요?", '전화(<a href="tel:{p}">{p}</a>)로 업종, 평수, 희망 일정을 알려주시면 {dong} 현장을 방문해 실측한 뒤 디자인과 항목별 견적을 안내합니다.'),
        ("영업 중인 매장도 부분 리모델링이 되나요?", "네. 카운터, 조명, 벽체, 외관 등 필요한 부분만 시공하는 것도 상담 가능합니다. 영업 일정에 맞춰 공정을 조율합니다."),
        ("어떤 업종의 매장을 시공했나요?", "카페, 음식점, 주점, 헤어·뷰티샵, 필라테스 스튜디오, 공방, 상담 라운지, 매장 외관 리모델링 등을 시공했습니다."),
        ("{city} 다른 동네도 시공하나요?", "네. {city} 전 지역과 천안, 아산, 당진, 평택의 상업공간 인테리어를 시공합니다."),
    ],
    "residential": [
        ("{dong} 아파트 인테리어도 시공하나요?", "네. {loc} 아파트, 빌라, 단독주택 인테리어와 리모델링을 시공합니다."),
        ("{dong} 인테리어 견적은 어떻게 받나요?", '전화(<a href="tel:{p}">{p}</a>)로 평수, 공사 범위, 희망 일정을 알려주시면 {dong} 현장을 방문해 실측한 뒤 디자인과 항목별 견적을 안내합니다.'),
        ("욕실이나 주방만 부분 시공할 수 있나요?", "네. 전체 리모델링뿐 아니라 욕실, 주방, 도배, 바닥 등 부분 시공도 상담 가능합니다."),
        ("입주 날짜에 맞춰 공사할 수 있나요?", "입주 일정을 알려주시면 실측 후 공정별 일정을 먼저 안내해 드리고, 그 일정에 맞춰 진행합니다."),
        ("{city} 다른 동네도 시공하나요?", "네. {city} 전 지역과 천안, 아산, 당진, 평택의 주거공간 인테리어를 시공합니다."),
    ],
}


TITLES = {
    "commercial": [
        "{dong} 상업공간 인테리어 | {city} {dong} 상가·카페 인테리어 {b}",
        "{dong} 상업공간 인테리어 전문 {b} | {city} {gu}매장·음식점 시공",
        "{city} {dong} 상업공간 인테리어, 카페·음식점·사무실 시공 | {b}",
        "{dong} 상업공간 인테리어 · 상가 리모델링 | {city} {b}",
        "{dong} 상업공간 인테리어 업체 {b} | 헤어샵·필라테스·카페 시공",
    ],
    "residential": [
        "{dong} 주거공간 인테리어 | {city} {dong} 아파트 리모델링 {b}",
        "{dong} 주거공간 인테리어 전문 {b} | {city} {gu}아파트·욕실 시공",
        "{city} {dong} 주거공간 인테리어, 아파트·주택 리모델링 | {b}",
        "{dong} 주거공간 인테리어 · 욕실·주방 리모델링 | {city} {b}",
        "{dong} 주거공간 인테리어 업체 {b} | 아파트 리모델링·부분 시공",
    ],
}

GUIDE = {
    "commercial": [
        ("업종에 맞는 설비부터 확인", "{dong}에서 카페나 음식점을 준비한다면 전기 용량, 급수·배수 위치, 주방 환기 덕트 경로를 먼저 확인해야 합니다. {b}은 실측 단계에서 이 부분을 함께 점검합니다."),
        ("손님 동선과 좌석 배치", "입구에서 카운터, 좌석, 화장실까지 손님이 움직이는 길을 먼저 그리고 좌석 수를 정합니다. 동선이 정리되면 직원이 일하는 동선도 함께 편해집니다."),
        ("조명으로 분위기 만들기", "라인 조명, 간접조명, 펜던트 조명을 공간 성격에 맞게 섞으면 같은 마감재도 전혀 다른 분위기가 됩니다. 아래 시공 사례의 카페와 한식당이 그 예입니다."),
        ("외관과 간판까지 한 톤으로", "매장 앞을 지나는 사람에게 처음 보이는 것은 외관입니다. 외벽 마감, 출입구, 간판 위치까지 실내와 같은 톤으로 맞추면 {dong} 거리에서도 매장 인상이 또렷해집니다."),
        ("오픈 날짜에서 거꾸로 일정 잡기", "오픈 날짜가 정해져 있다면 그 날짜에서 거꾸로 공정 일정을 짭니다. 집기 반입, 간판 설치, 준공 청소까지 포함해 일정을 안내합니다."),
        ("관리하기 쉬운 마감재", "바닥과 벽 마감재는 청소와 보수가 쉬운 소재를 고르는 것이 길게 보면 유리합니다. 업종별로 많이 쓰는 마감재를 비교해 안내합니다."),
        ("건물 공사 규정 확인", "상가 건물마다 공사 가능 시간, 소음 규정, 외부 간판 규정이 다릅니다. {dong} 현장도 착공 전 관리단 규정을 확인하고 일정에 반영합니다."),
        ("소방·안전 기준 검토", "업종과 면적에 따라 필요한 소방·안전 설비가 달라질 수 있어 설계 단계에서 함께 검토합니다."),
    ],
    "residential": [
        ("관리사무소 신고와 이웃 안내", "{dong} 아파트 인테리어는 착공 전 관리사무소 공사 신고와 이웃 안내가 필요한 경우가 많습니다. 공사 일정에 맞춰 함께 준비합니다."),
        ("공정 순서 미리 알기", "보통 철거, 설비, 전기, 목공, 타일, 도장·도배, 바닥, 가구·조명 순서로 진행됩니다. 공정이 바뀔 때마다 진행 상황을 공유합니다."),
        ("생활 짐에 맞춘 수납", "붙박이장, 팬트리, 현관 수납처럼 가족의 짐에 맞춘 수납을 먼저 계획하면 집이 오래 정돈됩니다."),
        ("조명으로 넓어 보이는 거실", "우물천장 간접조명, 매립등, 라인 조명을 함께 쓰면 거실이 넓고 아늑해 보입니다. 아래 시공 사례의 거실들이 그렇게 만들어졌습니다."),
        ("욕실은 방수가 먼저", "욕실 리모델링은 마감보다 방수가 먼저입니다. 철거 후 바닥과 벽 상태를 확인하고 필요한 경우 방수 공사를 함께 진행합니다."),
        ("주방 동선과 아일랜드", "싱크대, 가스레인지, 냉장고 위치와 아일랜드 유무에 따라 주방 동선이 달라집니다. 가족 구성과 요리 습관을 듣고 배치를 제안합니다."),
        ("바닥재 고르기", "포세린 타일, 강마루, 원목 마루는 느낌과 관리 방법이 다릅니다. 생활 방식에 맞는 바닥재를 비교해서 고를 수 있게 안내합니다."),
        ("예산은 우선순위부터", "전체 예산 중 어디에 비중을 둘지 먼저 정하면 만족도가 높아집니다. 항목별 견적을 보면서 조정할 부분을 함께 찾습니다."),
    ],
}

WHY = [
    ("대표 직접 상담", "{dong} 첫 상담부터 현장 실측, 완공 점검까지 대표 {ceo}가 직접 챙깁니다."),
    ("항목별 견적", "철거, 설비, 목공, 마감까지 항목별로 나눈 견적으로 어디에 비용이 드는지 한눈에 보여드립니다."),
    ("공정 공유", "공정이 바뀔 때마다 진행 상황을 공유해, 현장에 자주 오지 못해도 상황을 알 수 있습니다."),
    ("한 팀이 끝까지", "디자인한 사람이 시공까지 맡아, 처음 이야기한 내용이 마감까지 그대로 이어집니다."),
    ("가까운 시공 지역", "천안, 아산, 당진, 평택을 중심으로 시공해 {dong} 현장도 일정 조율이 수월합니다."),
]

FAQ_MORE = {
    "commercial": [
        ("상가 인테리어 상담 때 무엇을 준비하면 좋나요?", "업종, 대략적인 평수, 오픈 희망일, 참고하고 싶은 매장 사진이 있으면 상담이 빨라집니다. 도면이 없어도 현장 실측으로 진행할 수 있습니다."),
        ("{dong} 카페 인테리어도 가능한가요?", "네. 카페 카운터, 좌석 배치, 조명, 외관까지 설계하고 시공합니다. 시공 사례의 카페 사진을 참고해 보세요."),
        ("헤어샵이나 필라테스 스튜디오도 시공하나요?", "네. 헤어·뷰티샵, 필라테스 스튜디오, 공방처럼 업종에 맞는 설비와 동선이 필요한 공간도 시공했습니다."),
    ],
    "residential": [
        ("아파트 인테리어 상담 때 무엇을 준비하면 좋나요?", "평수, 원하는 공사 범위, 입주 또는 공사 희망 시기, 마음에 드는 인테리어 사진이 있으면 상담이 빨라집니다."),
        ("{dong} 오래된 아파트도 전체 리모델링이 되나요?", "네. 철거부터 설비, 전기, 마감까지 전체 리모델링을 진행합니다. 실측 때 배관과 설비 상태도 함께 확인합니다."),
        ("우물천장 간접조명 시공도 하나요?", "네. 거실 우물천장 간접조명, 아트월, 매립등 등 조명 공사를 함께 진행합니다. 시공 사례의 거실 사진을 참고해 보세요."),
    ],
}


def fill(t, a, cat):
    c = CITIES[a[0]]
    return t.format(loc=loc_full(a), dong=a[2], city=c["name"], b=BRAND, p=PHONE, ceo=CEO, gu=(a[3] + " ") if a[3] else "")


# ---------- 동 페이지 (페이지마다 다른 구성: 유사 문서 방지) ----------
import hashlib, random as _random


def _rng(*key):
    return _random.Random(int(hashlib.md5("|".join(key).encode()).hexdigest()[:12], 16))


H1_FMT = {
    "residential": ["{dong}<br>주거공간 인테리어", "{dong} 아파트<br>인테리어·리모델링", "{dong}<br>집 인테리어", "{dong}<br>아파트·주택 인테리어"],
    "commercial": ["{dong}<br>상업공간 인테리어", "{dong} 상가<br>인테리어", "{dong}<br>매장·카페 인테리어", "{dong}<br>상가·매장 인테리어"],
}
DESC_FMT = {
    "residential": [
        "{loc} 아파트·주택 인테리어 {b}. 전체 리모델링부터 욕실·주방 부분 시공까지 대표가 직접 실측하고 설계·시공합니다. 상담 {p}",
        "{dong} 주거공간 인테리어는 {b}. 우물천장 간접조명, 욕실 리모델링, 수납 설계까지 항목별 견적으로 안내합니다. {p}",
        "{loc} 집 인테리어 상담. 입주 전 리모델링, 살면서 하는 부분 공사 모두 {b} 대표가 직접 현장을 봅니다. 전화 {p}",
        "{dong} 아파트 리모델링·주택 인테리어 업체 {b}. 실측 후 디자인과 공정 일정을 먼저 정리해 드립니다. 상담 {p}",
    ],
    "commercial": [
        "{loc} 상가·카페·음식점 인테리어 {b}. 업종과 손님 동선을 먼저 보고 설계부터 시공까지 진행합니다. 상담 {p}",
        "{dong} 상업공간 인테리어는 {b}. 오픈 일정에 맞춘 공정표와 항목별 견적으로 매장을 준비합니다. {p}",
        "{loc} 매장 인테리어 상담. 헤어샵, 필라테스, 사무실, 외관 리모델링까지 {b} 대표가 직접 실측합니다. 전화 {p}",
        "{dong} 상가 리모델링·카페 인테리어 업체 {b}. 설비, 조명, 외관까지 한 번에 맡길 수 있습니다. 상담 {p}",
    ],
}
SEC_TITLES = {
    "scope": ["{dong} {s} 시공 분야", "{dong}에서 맡길 수 있는 공사", "{s} 인테리어, 이런 공사를 합니다", "{dong} 현장 시공 범위"],
    "guide": ["{dong} {s} 인테리어, 이렇게 준비하세요", "{dong} 인테리어 전에 알아 두면 좋은 것", "상담 전에 함께 확인하는 내용", "{dong} {s} 인테리어 체크포인트"],
    "works": ["{s} 시공 사례", "{b}이 시공한 {s} 현장", "직접 설계·시공한 {s}", "사진으로 보는 {s} 인테리어"],
    "process": ["{dong} 인테리어 진행 과정", "상담부터 완공까지", "{dong} 현장은 이렇게 진행됩니다", "공사 순서 한눈에 보기"],
}
SEC_SUB = {
    "guide": ["{loc} 현장을 상담할 때 함께 확인하는 내용입니다.", "실측 전에 알아 두시면 상담이 빨라집니다.", "{dong} 현장에서 자주 받는 질문을 정리했습니다."],
    "works": ["사진을 누르면 크게 볼 수 있습니다.", "{b}이 설계하고 시공한 현장입니다. 사진을 누르면 크게 볼 수 있습니다.", "같은 팀이 디자인하고 마감까지 시공했습니다."],
    "process": ["첫 통화부터 완공 후 점검까지 같은 사람이 끝까지 챙깁니다.", "공정이 바뀔 때마다 진행 상황을 공유합니다.", "각 단계마다 확인할 내용을 먼저 안내합니다."],
    "scope": ["{loc} 현장도 대표가 직접 방문해 실측하고, 디자인부터 마감까지 한 팀이 진행합니다.", "필요한 공정만 골라 부분 시공으로 맡겨도 됩니다.", "{dong} 현장 상황을 보고 꼭 필요한 공사부터 제안합니다."],
}
STEP_V = [
    ("전화 상담", ["원하는 공간, 예산, 일정을 들려주세요.", "평수와 공사 범위, 희망 일정을 알려주세요.", "참고 사진이 있으면 함께 보내 주세요."]),
    ("현장 실측", ["{dong} 현장에 직접 방문해 구조와 상태를 확인합니다.", "대표가 {dong} 현장을 직접 재고 설비 상태를 봅니다.", "현장 치수와 배관·전기 위치를 확인합니다."]),
    ("디자인과 견적", ["디자인과 항목별 견적을 함께 드립니다.", "공정별로 나눈 견적과 디자인 시안을 안내합니다.", "예산에 맞춰 조정할 항목을 함께 정합니다."]),
    ("시공", ["공정마다 진행 상황을 공유합니다.", "철거부터 마감까지 공정표대로 진행합니다.", "공정이 바뀔 때마다 사진으로 알려드립니다."]),
    ("완공과 점검", ["마감을 함께 확인한 뒤 인도합니다.", "마감 상태를 같이 둘러보고 인도합니다.", "완공 후 사용하며 불편한 점도 다시 살핍니다."]),
]
EXTRA_V = ["{dong}은 {f}입니다.", "{f}인 {dong}도 자주 상담합니다.", "{dong}({f}) 현장도 같은 방식으로 진행합니다."]
NEIGH_V = ["{dong}과 같은 {g}의 {n}도 같은 조건으로 상담하고 시공합니다.", "가까운 {n}에서도 시공 상담을 받고 있습니다.", "{g} 안에서는 {n} 현장도 함께 다닙니다."]


def dong_page(idx, a, cat):
    city = CITIES[a[0]]
    C = CATS[cat]
    other = "residential" if cat == "commercial" else "commercial"
    rel = url_dong(a, cat)
    up = "../../../../"
    page_url = f"{SITE}/{rel}"
    loc = loc_full(a)
    R = _rng(a[1], cat)
    place = f"{city['prov_full']} {city['full']} {a[3] + ' ' if a[3] else ''}{a[2]}"
    f = lambda t: fill(t, a, cat).replace("{s}", C["short"])
    fs = lambda t: f(t.replace("{s}", C["short"]))

    title = fill(TITLES[cat][(idx + R.randrange(5)) % len(TITLES[cat])], a, cat)
    desc = fill(R.choice(DESC_FMT[cat]), a, cat)
    h1 = R.choice(H1_FMT[cat]).format(dong=E(a[2]))
    intros = INTRO[cat][:]
    R.shuffle(intros)
    intro = fill(intros[0], a, cat)
    extra = ""
    if a[4]:
        extra += " " + R.choice(EXTRA_V).format(dong=a[2], f=a[4])
    memo = a[5] if cat == "residential" else a[6]
    if memo:
        extra += f" {BRAND}은 {a[2]}에서 {memo}"

    ph = C["photos"][:]
    R.shuffle(ph)
    photos = ph[:R.choice([3, 4, 6])]
    hero = photos[0]

    qpool = FAQ[cat][1:] + FAQ_MORE[cat]
    R.shuffle(qpool)
    qas = [(fill(q, a, cat), fill(x, a, cat)) for q, x in [FAQ[cat][0]] + qpool[:R.choice([3, 4])]]

    g = GUIDE[cat][:]
    R.shuffle(g)
    guide_html = "".join(f'<li><h3>{E(fill(t, a, cat))}</h3><p>{E(fill(x, a, cat))}</p></li>' for t, x in g[:R.choice([3, 4])])
    w = WHY[:]
    R.shuffle(w)
    why_html = "".join(f'<li><b>{E(t)}</b><span>{E(fill(x, a, cat))}</span></li>' for t, x in w[:3])
    items = C["items"][:]
    R.shuffle(items)
    items_html = "".join(f"<li>{E(i)}</li>" for i in items)
    steps_html = "".join(f'<li><h3>{t}</h3><p>{E(R.choice(v).format(dong=a[2]))}</p></li>' for t, v in STEP_V)

    same_gu = [x for x in AREAS if x[0] == a[0] and x[3] == a[3] and x[1] != a[1]]
    pos = [x[1] for x in AREAS].index(a[1])
    neigh = sorted(same_gu, key=lambda x: abs([y[1] for y in AREAS].index(x[1]) - pos))[:R.choice([2, 3])]
    neigh_txt = ", ".join(f'<a class="text-link" href="{up}{url_dong(x, cat)}">{x[2]}</a>' for x in neigh)
    gu_label = f"{city['name']} {a[3]}" if a[3] else city['name']
    near_links = sorted([x for x in AREAS if x[0] == a[0] and x[1] != a[1]], key=lambda x: abs([y[1] for y in AREAS].index(x[1]) - pos))[:6]
    crumbs = [("홈", ""), ("지역별 인테리어", "area/"), (f"{city['name']} {C['short']}", url_city(a[0], cat)), (f"{a[2]} {C['short']} 인테리어", None)]
    crumbs_view = [(n, up + u if u is not None else None) for n, u in crumbs]

    ld = {"@context": "https://schema.org", "@graph": [
        business_ld(),
        {"@type": "WebPage", "@id": page_url + "#webpage", "url": page_url, "name": title, "description": desc,
         "inLanguage": "ko-KR", "isPartOf": {"@id": f"{SITE}/#website"}, "breadcrumb": {"@id": page_url + "#breadcrumb"},
         "primaryImageOfPage": f"{SITE}/images/{hero[0]}", "dateModified": TODAY},
        {"@type": "Service", "@id": page_url + "#service", "name": f"{a[2]} {C['name']}", "serviceType": C["name"],
         "description": desc, "provider": {"@id": f"{SITE}/#business"},
         "areaServed": {"@type": "Place", "name": place,
                        "address": {"@type": "PostalAddress", "addressLocality": f"{city['full']} {a[3] + ' ' if a[3] else ''}{a[2]}".strip(),
                                    "addressRegion": city["prov_full"], "addressCountry": "KR"}},
         "image": [f"{SITE}/images/{p[0]}" for p in photos[:3]]},
        crumbs_ld(crumbs, page_url),
        faq_ld(qas, page_url),
    ]}

    T = lambda k: E(fs(R.choice(SEC_TITLES[k])))
    S = lambda k: E(fs(R.choice(SEC_SUB[k])))
    blocks = {
        "scope": f"""    <section class="sec" id="scope">
      <div class="wrap scope-grid">
        <div><h2>{T('scope')}</h2><p class="muted">{S('scope')}</p></div>
        <ul class="svc-list big">{items_html}</ul>
      </div>
      <div class="wrap"><ul class="why-list">{why_html}</ul></div>
    </section>
""",
        "guide": f"""    <section class="sec sec-tint" id="guide">
      <div class="wrap">
        <div class="sec-head"><h2>{T('guide')}</h2><p>{S('guide')}</p></div>
        <ul class="guide-list">{guide_html}</ul>
      </div>
    </section>
""",
        "works": f"""    <section class="sec" id="works">
      <div class="wrap">
        <div class="sec-head"><h2>{T('works')}</h2><p>{S('works')}</p></div>
        {gallery(photos, up, a[2] + ' ')}
      </div>
    </section>
""",
        "process": f"""    <section class="sec" id="process">
      <div class="wrap">
        <div class="sec-head"><h2>{T('process')}</h2><p>{S('process')}</p></div>
        <ol class="steps">{steps_html}</ol>
      </div>
    </section>
""",
    }
    order = ["scope", "guide", "works", "process"]
    R.shuffle(order)

    body = f"""  <main>
    <section class="hero area-hero">
      <div class="wrap">
        {crumbs_html(crumbs_view)}
        <div class="hero-grid">
          <div class="hero-copy">
            <div>
              <p class="hero-area">{E(city['prov'])} {E(loc)}</p>
              <h1>{h1}</h1>
              <p class="hero-lede">{E(intro)}{E(extra)}</p>
              <div class="hero-actions">
                <a href="tel:{PHONE}" class="btn btn-main">전화 상담 {PHONE}</a>
                <a href="#works" class="btn btn-sub">시공 사진 보기</a>
              </div>
            </div>
          </div>
          <div class="area-hero-photo photo"><img src="{up}images/{hero[0]}" width="{hero[1]}" height="{hero[2]}" alt="{BRAND} {E(a[2])} {E(C['name'])} 사례, {E(hero[5])}" fetchpriority="high"></div>
        </div>
      </div>
    </section>

{''.join(blocks[k] for k in order)}
{faq_block(qas)}
    <section class="sec sec-tint" id="nearby">
      <div class="wrap">
        <p class="neigh">{(R.choice(NEIGH_V).format(dong=E(a[2]), g=E(gu_label), n=neigh_txt)) if neigh else ''}</p>
        <div class="sec-head"><h2>{E(city['name'])} 가까운 지역 {E(C['short'])} 인테리어</h2>
          <p><a class="text-link" href="{up}{url_dong(a, other)}">{E(a[2])} {E(CATS[other]['name'])}</a> · <a class="text-link" href="{up}{url_city(a[0], cat)}">{E(city['name'])} {E(C['name'])} 전체</a></p></div>
        <ul class="chip-links">{''.join(f'<li><a href="{up}{url_dong(x, cat)}">{x[2]}</a></li>' for x in near_links)}</ul>
      </div>
    </section>

{contact_block(a[2])}  </main>
"""
    return head(title, desc, rel, up, place=place, region=city["region"], jsonld=ld) + header(up) + body + footer(up)


# ---------- 도시 + 분야 페이지 ----------
def city_cat_page(ck, cat):
    city = CITIES[ck]
    C = CATS[cat]
    other = "residential" if cat == "commercial" else "commercial"
    rel = url_city(ck, cat)
    up = "../../../"
    page_url = f"{SITE}/{rel}"
    dongs = [x for x in AREAS if x[0] == ck]
    title = f"{city['name']} {C['name']} | {city['name']} {'상가·카페·매장' if cat == 'commercial' else '아파트·주택'} 인테리어 업체 {BRAND}"
    desc = f"{city['prov']} {city['name']} {C['name']} 업체 {BRAND}. {', '.join(x[2] for x in dongs[:6])} 등 {city['name']} 전 지역 {'상가, 카페, 음식점, 사무실' if cat == 'commercial' else '아파트, 주택 리모델링, 욕실, 주방'} 인테리어를 시공합니다. 상담 {PHONE}"
    photos = CATS[cat]["photos"][:9]
    hero = photos[0]
    groups = {}
    for x in dongs:
        groups.setdefault(x[3] or city["name"], []).append(x)
    lists = ""
    for g, xs in groups.items():
        li = "".join(f'<li><a href="{up}{url_dong(x, cat)}">{x[2]} {C["short"]} 인테리어</a></li>' for x in xs)
        lists += f'<div class="area-group"><h3>{E(city["name"] + " " + g if g != city["name"] else city["name"])}</h3><ul class="chip-links">{li}</ul></div>'
    pseudo = (ck, "", city["name"], "", "", "", "")
    qas = [(fill(q, pseudo, cat).replace(f"{city['name']} {city['name']}", city["name"]), fill(an, pseudo, cat).replace(f"{city['name']} {city['name']}", city["name"])) for q, an in FAQ[cat][:4]]
    crumbs = [("홈", ""), ("지역별 인테리어", "area/"), (f"{city['name']} {C['name']}", None)]
    crumbs_view = [(n, up + u if u is not None else None) for n, u in crumbs]
    ld = {"@context": "https://schema.org", "@graph": [
        business_ld(),
        {"@type": "WebPage", "@id": page_url + "#webpage", "url": page_url, "name": title, "description": desc, "inLanguage": "ko-KR",
         "breadcrumb": {"@id": page_url + "#breadcrumb"}, "dateModified": TODAY},
        {"@type": "Service", "name": f"{city['name']} {C['name']}", "serviceType": C["name"], "provider": {"@id": f"{SITE}/#business"},
         "areaServed": {"@type": "City", "name": city["full"], "containedInPlace": {"@type": "AdministrativeArea", "name": city["prov_full"]}}},
        crumbs_ld(crumbs, page_url), faq_ld(qas, page_url)]}
    body = f"""  <main>
    <section class="hero area-hero">
      <div class="wrap">
        {crumbs_html(crumbs_view)}
        <div class="hero-grid">
          <div class="hero-copy"><div>
            <p class="hero-area">{E(city['prov_full'])} {E(city['full'])}</p>
            <h1>{E(city['name'])}<br>{E(C['name'])}</h1>
            <p class="hero-lede">{E(city['name'])} 전 지역 {E('상가, 카페, 음식점, 사무실, 헤어샵' if cat == 'commercial' else '아파트, 빌라, 단독주택')} 인테리어를 {BRAND} 대표가 직접 상담하고 시공합니다. 아래에서 동네를 고르면 해당 지역 안내를 볼 수 있습니다.</p>
            <div class="hero-actions"><a href="tel:{PHONE}" class="btn btn-main">전화 상담 {PHONE}</a><a href="#dongs" class="btn btn-sub">동네별 보기</a></div>
          </div></div>
          <div class="area-hero-photo photo"><img src="{up}images/{hero[0]}" width="{hero[1]}" height="{hero[2]}" alt="{BRAND} {E(city['name'])} {E(C['name'])} {E(hero[5])}" fetchpriority="high"></div>
        </div>
      </div>
    </section>
    <section class="sec" id="dongs">
      <div class="wrap">
        <div class="sec-head"><h2>{E(city['name'])} 동네별 {E(C['short'])} 인테리어</h2><p><a class="text-link" href="{up}{url_city(ck, other)}">{E(city['name'])} {E(CATS[other]['name'])} 보기</a></p></div>
        {lists}
      </div>
    </section>
    <section class="sec sec-tint" id="works">
      <div class="wrap">
        <div class="sec-head"><h2>{E(C['short'])} 시공 사례</h2><p>사진을 누르면 크게 볼 수 있습니다.</p></div>
        {gallery(photos, up)}
      </div>
    </section>
{faq_block(qas)}
{contact_block(city['name'])}  </main>
"""
    return head(title, desc, rel, up, place=f"{city['full']}, {city['prov_full']}", region=city["region"], jsonld=ld) + header(up) + body + footer(up)


# ---------- 도시 허브 ----------
def city_hub(ck):
    city = CITIES[ck]
    rel = url_city(ck)
    up = "../../"
    page_url = f"{SITE}/{rel}"
    dongs = [x for x in AREAS if x[0] == ck]
    title = f"{city['name']} 인테리어 | {city['name']} 주거공간·상업공간 인테리어 업체 {BRAND}"
    desc = f"{city['prov']} {city['name']} 인테리어 업체 {BRAND}. {city['name']} 아파트·주택 리모델링과 상가·카페·음식점 인테리어를 동네별로 안내합니다. 상담 {PHONE}"
    rows = "".join(
        f'<li><b>{x[2]}</b><span><a href="{up}{url_dong(x, "residential")}">주거공간</a><a href="{up}{url_dong(x, "commercial")}">상업공간</a></span></li>'
        for x in dongs)
    crumbs = [("홈", ""), ("지역별 인테리어", "area/"), (f"{city['name']} 인테리어", None)]
    crumbs_view = [(n, up + u if u is not None else None) for n, u in crumbs]
    ld = {"@context": "https://schema.org", "@graph": [business_ld(),
          {"@type": "CollectionPage", "@id": page_url + "#webpage", "url": page_url, "name": title, "description": desc, "inLanguage": "ko-KR"},
          crumbs_ld(crumbs, page_url)]}
    body = f"""  <main>
    <section class="sec area-index">
      <div class="wrap">
        {crumbs_html(crumbs_view)}
        <h1 class="page-title">{E(city['name'])} 인테리어</h1>
        <p class="muted page-lede">{E(city['prov_full'])} {E(city['full'])} 주거공간과 상업공간 인테리어를 동네별로 안내합니다.</p>
        <div class="split-links">
          <a href="{up}{url_city(ck, 'residential')}"><b>{E(city['name'])} 주거공간 인테리어</b><span>아파트, 주택 리모델링, 욕실, 주방</span></a>
          <a href="{up}{url_city(ck, 'commercial')}"><b>{E(city['name'])} 상업공간 인테리어</b><span>상가, 카페, 음식점, 사무실, 헤어샵</span></a>
        </div>
        <h2 class="list-title">동네별 인테리어</h2>
        <ul class="dong-table">{rows}</ul>
      </div>
    </section>
{contact_block(city['name'])}  </main>
"""
    return head(title, desc, rel, up, place=f"{city['full']}, {city['prov_full']}", region=city["region"], jsonld=ld) + header(up) + body + footer(up)


# ---------- 지역 전체 목록 ----------
def area_index():
    rel = "area/"
    up = "../"
    page_url = f"{SITE}/{rel}"
    title = f"지역별 인테리어 | 천안·아산·당진·평택 동네별 주거·상가 인테리어 {BRAND}"
    desc = f"천안, 아산, 당진, 평택 동네별 주거공간·상업공간 인테리어 안내. {BRAND} 상담 {PHONE}"
    blocks = ""
    for ck, city in CITIES.items():
        dongs = [x for x in AREAS if x[0] == ck]
        rows = "".join(
            f'<li><b>{x[2]}</b><span><a href="{up}{url_dong(x, "residential")}">주거공간</a><a href="{up}{url_dong(x, "commercial")}">상업공간</a></span></li>'
            for x in dongs)
        blocks += f"""<div class="city-block">
          <h2><a href="{up}{url_city(ck)}">{E(city['name'])} 인테리어</a></h2>
          <p class="muted"><a class="text-link" href="{up}{url_city(ck, 'residential')}">{E(city['name'])} 주거공간</a> · <a class="text-link" href="{up}{url_city(ck, 'commercial')}">{E(city['name'])} 상업공간</a></p>
          <ul class="dong-table">{rows}</ul>
        </div>"""
    crumbs = [("홈", ""), ("지역별 인테리어", None)]
    crumbs_view = [(n, up + u if u is not None else None) for n, u in crumbs]
    ld = {"@context": "https://schema.org", "@graph": [business_ld(),
          {"@type": "CollectionPage", "@id": page_url + "#webpage", "url": page_url, "name": title, "description": desc, "inLanguage": "ko-KR"},
          crumbs_ld(crumbs, page_url)]}
    body = f"""  <main>
    <section class="sec area-index">
      <div class="wrap">
        {crumbs_html(crumbs_view)}
        <h1 class="page-title">지역별 인테리어</h1>
        <p class="muted page-lede">시공하실 동네를 고르면 그 지역 주거공간·상업공간 인테리어 안내를 볼 수 있습니다.</p>
        {blocks}
      </div>
    </section>
{contact_block('천안·아산·당진·평택')}  </main>
"""
    return head(title, desc, rel, up, jsonld=ld) + header(up) + body + footer(up)


# ---------- 메인 페이지 블록 ----------
def main_works():
    tabs = ('<div class="tabs" role="tablist" aria-label="시공 분야 선택">'
            '<button type="button" role="tab" aria-selected="true" data-f="all">전체</button>'
            '<button type="button" role="tab" aria-selected="false" data-f="residential">주거공간</button>'
            '<button type="button" role="tab" aria-selected="false" data-f="commercial">상업공간</button></div>')
    mix = []
    r, c = RES[1:], COM
    for i in range(max(len(r), len(c))):
        if i < len(c): mix.append(("commercial", c[i]))
        if i < len(r): mix.append(("residential", r[i]))
    out = []
    for k, (cat, (f, w, h, t, d, alt)) in enumerate(mix):
        out.append(
            f'<figure class="work" data-c="{cat}"><button type="button" data-full="images/{f}" data-cap="{E(t)}, {E(d)}">'
            f'<div class="photo"><img src="images/{f}" width="{w}" height="{h}" alt="{BRAND} {E(alt)}" loading="lazy" decoding="async"></div>'
            f'</button><figcaption><h3>{E(t)}</h3><span>{"상업공간" if cat == "commercial" else "주거공간"} · {E(d)}</span></figcaption></figure>')
    return (tabs + '\n        <div class="works works-even" id="worksGrid">\n' + "\n".join(out) +
            '\n        </div>\n        <div class="more-wrap"><button type="button" class="btn btn-sub" id="moreBtn">시공 사진 더 보기</button></div>')


def main_areas(up=""):
    blocks = ""
    for ck, city in CITIES.items():
        dongs = [x for x in AREAS if x[0] == ck]
        links = "".join(f'<li><a href="{up}{url_dong(x, "residential")}">{x[2]} 주거</a></li><li><a href="{up}{url_dong(x, "commercial")}">{x[2]} 상가</a></li>' for x in dongs)
        blocks += (f'<details class="city-links"><summary><a href="{up}{url_city(ck)}">{E(city["name"])}</a> 동네별 인테리어 <small>{len(dongs)}개 동네</small></summary>'
                   f'<ul class="chip-links small">{links}</ul></details>')
    return blocks


def replace_block(s, name, content):
    a, b = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    i, j = s.index(a) + len(a), s.index(b)
    return s[:i] + "\n" + content + "\n        " + s[j:]


def main():
    # 동 페이지
    urls = ["", "area/"]
    for ck in CITIES:
        write(url_city(ck) + "index.html", city_hub(ck)); urls.append(url_city(ck))
        for cat in CATS:
            write(url_city(ck, cat) + "index.html", city_cat_page(ck, cat)); urls.append(url_city(ck, cat))
    for i, a in enumerate(AREAS):
        for cat in CATS:
            write(url_dong(a, cat) + "index.html", dong_page(i, a, cat)); urls.append(url_dong(a, cat))
    write("area/index.html", area_index())

    # 메인 페이지 블록 갱신
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf-8").read()
    s = replace_block(s, "WORKS", main_works())
    s = replace_block(s, "AREALINKS", main_areas())
    open(p, "w", encoding="utf-8").write(s)

    # sitemap
    imgs = [x[0] for x in RES] + [x[0] for x in COM]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for u in urls:
        pr = "1.0" if u == "" else ("0.9" if u.count("/") <= 2 else ("0.8" if u.count("/") == 3 else "0.7"))
        sm.append(f"  <url>\n    <loc>{SITE}/{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>{pr}</priority>")
        if u == "":
            for im in imgs:
                sm.append(f"    <image:image><image:loc>{SITE}/images/{im}</image:loc></image:image>")
        sm.append("  </url>")
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")

    # rss.xml (네이버 서치어드바이저 RSS 제출용)
    def _t(u):
        h = open(os.path.join(ROOT, u, "index.html"), encoding="utf-8").read()
        t = re.search(r"<title>(.*?)</title>", h, re.S).group(1)
        d = re.search(r'<meta name="description" content="(.*?)"', h).group(1)
        return t, d
    items = []
    for u in urls:
        t, d = _t(u)
        items.append(f"  <item><title>{t}</title><link>{SITE}/{u}</link><guid>{SITE}/{u}</guid><description>{d}</description><pubDate>Tue, 24 Nov 2026 00:00:00 +0900</pubDate></item>")
    write("rss.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>\n'
          f"  <title>{BRAND}</title><link>{SITE}/</link><description>천안·아산·당진·평택 주거공간·상업공간 인테리어</description><language>ko</language>\n"
          + "\n".join(items) + "\n</channel></rss>\n")

    # llms.txt
    lines = [f"# {BRAND} (K DESIGN, K디자인)", "",
             "> 충남 천안·아산·당진, 경기 평택 지역의 주거공간·상업공간 인테리어 설계·시공 업체입니다.", "",
             "## 업체 정보", f"- 상호: {BRAND}", f"- 대표: {CEO}", f"- 전화: {PHONE}",
             "- 시공 지역: 천안시, 아산시, 당진시(충청남도), 평택시(경기도)", f"- 홈페이지: {SITE}/", "",
             "## 시공 분야",
             "- 주거공간 인테리어: 아파트 리모델링, 빌라·단독주택, 주방·욕실, 도배·바닥, 부분 시공",
             "- 상업공간 인테리어: 상가·매장, 카페·음식점·주점, 사무실, 헤어·뷰티샵, 필라테스·스튜디오, 학원·병원, 외관 리모델링", "",
             "## 진행 과정", "상담 → 현장 실측 → 디자인·견적 → 시공 → 완공·점검", "",
             "## 지역별 안내 페이지"]
    for ck, city in CITIES.items():
        lines.append(f"- [{city['name']} 주거공간 인테리어]({SITE}/{url_city(ck, 'residential')})")
        lines.append(f"- [{city['name']} 상업공간 인테리어]({SITE}/{url_city(ck, 'commercial')})")
    lines.append(f"- [동네별 전체 목록]({SITE}/area/)")
    lines += ["", "## 시공 동네", ", ".join(f"{loc_full(a)}" for a in AREAS)]
    write("llms.txt", "\n".join(lines) + "\n")
    print(f"pages: {len(urls)}")


if __name__ == "__main__":
    main()
