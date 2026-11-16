#!/usr/bin/env python3
"""術語卡 Term Cards 規則檢查程式。

用法：
    python3 tools/check.py            # 檢查整個專案
    python3 tools/check.py --strict   # 警告也視為錯誤

檢查範圍（對應 CLAUDE.md）：
    第 2、10 節  網站結構：必要檔案、.nojekyll、不可有 package.json／其他 HTML／其他 CSS、JS、
                 外部資源只能是 Google Fonts、HTML／JS 不寫色碼、HTML／JS 不放術語內容
    第 4 節      slug 格式、slug 與檔名一致、主題有登記在 topics/index.json
    第 5 節      必填欄位、欄位型別、accent 允許清單、相鄰主題不同色、updated 日期格式、
                 full（縮寫才寫）、zh 最多兩個說法、字數上限、例句包含術語、related 指向存在的術語
    第 6 節      常見簡體字與大陸用語、敏感資訊（公開 IP、Email）、每個主題至少 8 張卡

「錯誤」代表違反規則，必須修正；「警告」代表程式無法確定，請人工（或 AI）判斷。
有任何錯誤時結束代碼為 1。
"""

import argparse
import datetime as dt
import ipaddress
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# 規則設定
# ---------------------------------------------------------------------------

ACCENTS = ["blue", "purple", "amber", "green", "rose", "teal"]
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MIN_TERMS = 8
MAX_EXPLAIN = 40      # 字（中文一字算 1，英文單字或數字串算 1，標點算 1）
MAX_NOTE = 60
MAX_EXAMPLE_WORDS = 25  # 英文字（以空白分隔）

TOPIC_FIELDS_REQUIRED = ["slug", "title_zh", "title_en", "description", "updated", "terms"]
TERM_FIELDS_REQUIRED = ["term", "zh", "explain", "example", "example_zh"]
TERM_FIELDS_OPTIONAL = ["full", "note", "related"]
TERM_FIELDS_ALL = ["term", "full", "zh", "explain", "example", "example_zh", "note", "related"]

REQUIRED_FILES = [
    "CLAUDE.md",
    "index.html",
    "topic.html",
    "assets/style.css",
    "assets/app.js",
    "topics/index.json",
    "templates/topic-template.json",
    "tools/check.py",
    ".nojekyll",
]
RECOMMENDED_FILES = ["README.md"]
FORBIDDEN_PATHS = ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "node_modules"]
ALLOWED_HTML = {"index.html", "topic.html"}
ALLOWED_CSS = {"assets/style.css"}
ALLOWED_JS = {"assets/app.js"}
ALLOWED_RESOURCE_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com"}
ALLOWED_FONT_FAMILIES = {"Noto Sans TC", "IBM Plex Mono"}
SKIP_DIRS = {".git", ".github", ".vscode", ".idea", "__pycache__"}

# 常見簡體字（已排除台灣也會正常使用的字，例如：台、里、干、准、表、范、床、舍、斗、胜、据）
SIMPLIFIED_CHARS = set(
    "们这个为发会对时说过还进实际现应该从开关门问间东车长马鸟鱼读写书学习见觉认识计电脑页线连务档"
    "术语设备变压导释图华级层显视频将节约强处无业专义乐买卖亲众传伤侧储兴养内册军农凤刘则刚创删别"
    "剧办动劳势区医单卫历县参双叶号叹吗员呜响团园围国场块坚坛执报声壳够头夹夺奋妈娱婴宝宠审宪宫寻"
    "尔尘尝属岁岛峡币师帐带帮库废广庆弃张弹归录彻径忆忧态总恋恶悬惧惯战户扩扫扬抚抛护担拟拥择挡挤"
    "挥损换掷捡揽搀摄摆摇撑数敌斋断旧旷昼晓晕暂杀杂权条来杨枪标栏树样桥梦检楼横欢欧歼殴毁毕汇汉汤"
    "沟没沪泪泼泽浅浆测济浑浓涛润涩渊渐渔湾湿满滚滞滤滥潜灭灯灵灾炉点炼烦烧热焕爱爷牵牺状犹独狭狮"
    "猎献环琐画畅疗盐监盖盘着矿码础碍礼积称穷窃竞笔笼筛签简类粮纠红纤纪纯纲纳纵纷纸纹组细终绍经结"
    "绕绘给络绝统继绩续维绵综绿缓编缘缩缴罗罚罢职联聪肃肠肤肾肿胀胁脏舰艺芦苏茎药莱获莲萝营萧萨蓝"
    "虑虽蚀蚁补规览誉订讨让训议讯记讲许论访证评诉词译试诗诚话询详误请诸课谁调谈谊谋谓谢谱贝负贡财"
    "责贤败货质贩购贯贵贷费贺资赋赌赏赔赖赚赛赞赠趋跃践踪轨转轮软轻载较辅辆辈辉输辞辩边达迁迈运远"
    "违迟选递逻遗邮邻郑针钟钢钥钱铁铃铜铭银链销锁锅错锤键镇镜闪闭闯闲闷闹闻阀阅队阳阴阵阶陆陈陕险"
    "随隐难雾静韩顶项顺须顾顿预领颗题额风飞饭饮饰饱饼馆驱验骑骗鸡麦黄齐齿龙辑宽脉烟"
    # 以下在 Big5 中有罕見異體，但在台灣文章裡幾乎一定是簡體字誤用
    "网机确种离极构气优体儿听与坏复宁怀惊扰柜洁痒筑荐触赶适圣异怜扑苹挂"
)

# 大陸用語 → 台灣用語。(正規表示式, 建議)；確定是錯誤的放 ERROR，需看上下文的放 WARNING
MAINLAND_ERROR_TERMS = [
    (r"網絡", "網路"),
    (r"軟件", "軟體"),
    (r"硬件", "硬體"),
    (r"服務器", "伺服器"),
    (r"萬用表", "三用電錶"),
    (r"視頻", "影片、視訊"),
    (r"信息", "資訊、訊息"),
    (r"默認", "預設"),
    (r"缺省", "預設"),
    (r"鼠標", "滑鼠"),
    (r"光標", "游標"),
    (r"內存", "記憶體"),
    (r"屏幕", "螢幕"),
    (r"打印", "列印"),
    (r"文件夾", "資料夾"),
    (r"博客", "部落格"),
    (r"寬帶", "寬頻"),
    (r"帶寬", "頻寬"),
    (r"芯片", "晶片"),
    (r"集成電路", "積體電路"),
    (r"數據庫", "資料庫"),
    (r"數據包", "封包"),
    (r"操作系統", "作業系統"),
    (r"字節", "位元組"),
    (r"比特(?!幣)", "位元"),
    (r"端口", "連接埠"),
    (r"互聯網", "網際網路"),
    (r"局域網", "區域網路"),
    (r"廣域網(?!路)", "廣域網路"),
    (r"以太網", "乙太網路"),
    (r"雲計算", "雲端運算"),
    (r"人工智能", "人工智慧"),
    (r"(?<!演)算法", "演算法"),
    (r"傳感器", "感測器"),
    (r"晶體管", "電晶體"),
    (r"二極管", "二極體"),
    (r"調制解調器", "數據機"),
    (r"程序員", "程式設計師"),
    (r"賬號", "帳號"),
    (r"源代碼", "原始碼"),
]
MAINLAND_WARNING_TERMS = [
    (r"數據(?!機|庫|包)", "指 data 時用「資料」"),
    (r"質量", "指 quality 時用「品質」（物理的 mass 才是質量）"),
    (r"程序(?!員)", "指 program 時用「程式」（procedure 可用程序）"),
    (r"計算機", "指 computer 時用「電腦」（台灣的計算機是 calculator）"),
    (r"項目", "指 project 時用「專案」"),
    (r"(?<!人工)智能", "台灣多用「智慧」"),
    (r"接口", "台灣多用「介面」或「連接埠」"),
    (r"菜單", "指軟體選單時用「選單」"),
    (r"激活", "台灣多用「啟用」"),
    (r"登錄", "指 log in 時用「登入」"),
    (r"信號", "台灣多用「訊號」"),
    (r"數字(?=信號|訊號|電路|電錶|萬用表|示波器|式)", "指 digital 時用「數位」"),
    (r"模擬(?=信號|訊號|電路|電錶|萬用表|示波器|式)", "指 analog 時用「類比」"),
]

# 例句中可以出現的公開 IP（通用公開 DNS）
PUBLIC_DNS = {
    "8.8.8.8", "8.8.4.4",            # Google
    "1.1.1.1", "1.0.0.1",            # Cloudflare
    "9.9.9.9", "149.112.112.112",    # Quad9
    "208.67.222.222", "208.67.220.220",  # OpenDNS
    "168.95.1.1", "168.95.192.1",    # HiNet
    "101.101.101.101", "101.102.103.104",  # TWNIC Quad101
}
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")

CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
IPV4_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])")
EMAIL_RE = re.compile(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)")
SECRET_RE = re.compile(r"(password|passwd|pwd|token|api[_ -]?key|密碼)\s*[:=：]\s*\S+", re.I)
URL_RE = re.compile(r"https?://[^\s\"'<>()]+", re.I)
UNC_RE = re.compile(r"\\\\[\w.-]+\\[\w$.-]+")
HEX_COLOR_RE = re.compile(r"(?<![\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})\b")
FUNC_COLOR_RE = re.compile(r"\b(?:rgba?|hsla?|hwb|oklch|oklab|lab|lch)\(", re.I)


# ---------------------------------------------------------------------------
# 回報
# ---------------------------------------------------------------------------

class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, message):
        self.errors.append((where, message))

    def warn(self, where, message):
        self.warnings.append((where, message))


def rel(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def zh_length(text):
    """中文字數：中文字、標點各算 1，一個英文單字或數字串算 1，空白不算。"""
    return len(re.findall(r"[A-Za-z0-9]+(?:['’.\-][A-Za-z0-9]+)*|\S", text))


def english_words(text):
    return len(text.split())


def norm_term(text):
    return unicodedata.normalize("NFKC", text).strip().casefold()


def term_regex(term):
    """術語本身，允許複數形（-s、-es、-y → -ies），不分大小寫，前後不能接英數字。"""
    variants = [re.escape(term) + r"(?:s|es)?"]
    if re.search(r"[^aeiou]y$", term, re.I):
        variants.append(re.escape(term[:-1]) + "ies")
    return re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(variants) + r")(?![A-Za-z0-9])", re.I)


def is_pure_acronym(term):
    """全部字母皆大寫且至少兩個字母，例如 DNS、TCP/IP、IEEE 802.11。"""
    letters = [c for c in term if c.isalpha()]
    return len(letters) >= 2 and all(c.isupper() for c in letters)


def looks_like_acronym(term):
    """大小寫混合的縮寫，例如 IPv4、QoS、SaaS（大寫字母至少兩個且占一半以上）。"""
    letters = [c for c in term if c.isalpha()]
    upper = sum(1 for c in letters if c.isupper())
    return " " not in term and upper >= 2 and upper * 2 >= len(letters)


def is_netmask(addr):
    bits = int(ipaddress.IPv4Address(addr))
    inverted = (~bits) & 0xFFFFFFFF
    return bits != 0 and (inverted & (inverted + 1)) == 0


def iter_strings(value, path=""):
    """遞迴列出 JSON 中所有字串：(位置, 字串)。"""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from iter_strings(item, "{}[{}]".format(path, i))
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(item, "{}.{}".format(path, key) if path else key)


def load_json(path, report):
    """讀取 JSON；檢查 UTF-8、BOM、語法錯誤與重複的 key。"""
    where = rel(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        report.error(where, "無法讀取檔案：{}".format(exc))
        return None
    if raw.startswith(b"\xef\xbb\xbf"):
        report.warn(where, "檔案開頭有 BOM，建議存成「UTF-8（無 BOM）」")
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        report.error(where, "不是 UTF-8 編碼：{}".format(exc))
        return None

    duplicates = []

    def hook(pairs):
        seen = {}
        for key, value in pairs:
            if key in seen:
                duplicates.append(key)
            seen[key] = value
        return seen

    try:
        data = json.loads(text, object_pairs_hook=hook)
    except json.JSONDecodeError as exc:
        report.error(where, "JSON 格式錯誤（第 {} 行第 {} 欄）：{}".format(exc.lineno, exc.colno, exc.msg))
        return None
    for key in duplicates:
        report.error(where, "同一個物件中出現重複的欄位「{}」".format(key))
    return data


# ---------------------------------------------------------------------------
# 第 2、10 節：網站結構
# ---------------------------------------------------------------------------

def project_files():
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        if path.is_file():
            yield path


def check_structure(report):
    for name in REQUIRED_FILES:
        if not (ROOT / name).exists():
            hint = "（GitHub Pages 需要它，不可刪除）" if name == ".nojekyll" else ""
            report.error(name, "缺少必要檔案{}".format(hint))
    for name in RECOMMENDED_FILES:
        if not (ROOT / name).exists():
            report.warn(name, "建議建立（CLAUDE.md 第 3 節的檔案結構有列出）")
    for name in FORBIDDEN_PATHS:
        if (ROOT / name).exists():
            report.error(name, "純靜態網站不使用套件或建置工具，請移除")

    for path in project_files():
        r = rel(path)
        suffix = path.suffix.lower()
        if suffix in (".html", ".htm") and r not in ALLOWED_HTML:
            report.error(r, "不可另外建立 HTML 檔；主題頁一律用 topic.html?t=<slug>")
        elif suffix == ".css" and r not in ALLOWED_CSS:
            report.error(r, "全站只能有 assets/style.css 一個樣式表")
        elif suffix in (".js", ".mjs", ".ts", ".jsx", ".tsx") and r not in ALLOWED_JS:
            report.error(r, "全站只能有 assets/app.js 一支程式")
        elif suffix == ".json" and r.startswith("topics/") and path.parent != ROOT / "topics":
            report.error(r, "主題檔要直接放在 topics/ 下，不要放子資料夾")


def check_front_end(report, all_topics):
    """HTML／CSS／JS：外部資源、色碼、不可放術語內容。"""
    sources = {}
    for name in sorted(ALLOWED_HTML | ALLOWED_CSS | ALLOWED_JS):
        path = ROOT / name
        if path.exists():
            sources[name] = path.read_text(encoding="utf-8", errors="replace")

    for name, text in sources.items():
        is_html = name.endswith(".html")
        is_css = name.endswith(".css")

        # 外部資源：只允許 Google Fonts
        if is_html:
            refs = re.findall(r"<(?:script|link|img|iframe|source|video|audio|embed)\b[^>]*?\s(?:src|href)\s*=\s*[\"']([^\"']+)", text, re.I)
        elif is_css:
            refs = re.findall(r"url\(\s*[\"']?([^\"')]+)", text, re.I) + re.findall(r"@import\s+[\"']([^\"']+)", text, re.I)
        else:
            refs = re.findall(r"(?:fetch|import)\s*\(\s*[\"'`]([^\"'`]+)", text) + re.findall(r"\bimport\s+[^;]*?from\s+[\"']([^\"']+)", text)
        for ref in refs:
            m = re.match(r"^(?:https?:)?//([^/:?#]+)", ref.strip(), re.I)
            if m and m.group(1).lower() not in ALLOWED_RESOURCE_HOSTS:
                report.error(name, "外部資源只能用 Google Fonts，不可載入：{}".format(ref))

        if is_html:
            for url in re.findall(r"https://fonts\.googleapis\.com/css2?\?[^\"'\s>]+", text):
                for family in re.findall(r"family=([^&:;\"']+)", url):
                    family = family.replace("+", " ")
                    if family not in ALLOWED_FONT_FAMILIES:
                        report.error(name, "只允許 Noto Sans TC 與 IBM Plex Mono 字型，不可使用：{}".format(family))

        # 色碼：只能寫在 style.css
        if not is_css:
            for m in HEX_COLOR_RE.finditer(text):
                report.error(name, "不可寫死色碼 {}（顏色請用 style.css 的 CSS 變數）".format(m.group(0)))
            for m in FUNC_COLOR_RE.finditer(text):
                report.error(name, "不可寫死顏色 {}…）（顏色請用 style.css 的 CSS 變數）".format(m.group(0)))

    # style.css 必須定義全部六個主題色
    css = sources.get("assets/style.css", "")
    for accent in ACCENTS:
        if '[data-accent="{}"]'.format(accent) not in css:
            report.error("assets/style.css", "沒有定義主題色 {}".format(accent))

    # HTML／JS 不可放術語內容
    for slug, topic in all_topics.items():
        for term in topic.get("terms", []) if isinstance(topic.get("terms"), list) else []:
            if not isinstance(term, dict):
                continue
            for key in ("zh", "explain", "example", "example_zh"):
                value = term.get(key)
                if isinstance(value, str) and len(value.strip()) >= 4:
                    for name, text in sources.items():
                        if not name.endswith(".css") and value.strip() in text:
                            report.error(name, "出現主題 {} 的術語內容（{}：{}），術語只能寫在 topics/*.json".format(slug, key, value.strip()))


# ---------------------------------------------------------------------------
# 第 4、5-1 節：topics/index.json
# ---------------------------------------------------------------------------

def check_index(report):
    path = ROOT / "topics" / "index.json"
    where = rel(path)
    if not path.exists():
        return []
    data = load_json(path, report)
    if data is None:
        return []
    if not isinstance(data, list):
        report.error(where, "必須是陣列，例如 [ { \"slug\": \"network\", \"accent\": \"blue\" } ]")
        return []

    slugs = []
    previous_accent = None
    for i, entry in enumerate(data):
        loc = "{} › [{}]".format(where, i)
        if not isinstance(entry, dict):
            report.error(loc, "每一項都必須是物件 {\"slug\": ..., \"accent\": ...}")
            previous_accent = None
            continue
        for key in entry:
            if key not in ("slug", "accent"):
                report.warn(loc, "未定義的欄位「{}」（只需要 slug 與 accent）".format(key))

        slug = entry.get("slug")
        accent = entry.get("accent")
        if not isinstance(slug, str) or not slug:
            report.error(loc, "缺少 slug")
        else:
            loc = "{} › [{}] {}".format(where, i, slug)
            if not SLUG_RE.match(slug):
                report.error(loc, "slug「{}」只能用小寫英文、數字與連字號".format(slug))
            if slug in slugs:
                report.error(loc, "slug「{}」重複登記".format(slug))
            elif not (ROOT / "topics" / (slug + ".json")).exists():
                report.error(loc, "找不到對應的主題檔 topics/{}.json".format(slug))
            slugs.append(slug)

        if not isinstance(accent, str) or not accent:
            report.error(loc, "缺少 accent")
        elif accent not in ACCENTS:
            report.error(loc, "accent「{}」不在允許清單內：{}".format(accent, "、".join(ACCENTS)))
        elif accent == previous_accent:
            report.error(loc, "與前一個主題同樣是「{}」，相鄰主題不要用同一個顏色".format(accent))
        previous_accent = accent if isinstance(accent, str) else None

    return slugs


# ---------------------------------------------------------------------------
# 第 6 節：語言與敏感資訊（套用在主題檔所有字串）
# ---------------------------------------------------------------------------

def check_language(report, where, field, text):
    simp = sorted({c for c in text if c in SIMPLIFIED_CHARS}, key=text.index)
    if simp:
        report.error(where, "{} 有簡體字：{}".format(field, "".join(simp)))

    others = sorted({c for c in text if CJK_RE.match(c) and c not in SIMPLIFIED_CHARS and not _in_big5(c)}, key=text.index)
    if others:
        report.warn(where, "{} 有 Big5 以外的字（可能是簡體字或罕見字，請確認）：{}".format(field, "".join(others)))

    for pattern, suggestion in MAINLAND_ERROR_TERMS:
        for m in re.finditer(pattern, text):
            report.error(where, "{} 使用大陸用語「{}」，請改為「{}」".format(field, m.group(0), suggestion))
    for pattern, suggestion in MAINLAND_WARNING_TERMS:
        for m in re.finditer(pattern, text):
            report.warn(where, "{} 出現「{}」，請確認：{}".format(field, m.group(0), suggestion))


def _in_big5(char):
    try:
        char.encode("cp950")
        return True
    except UnicodeEncodeError:
        return False


def check_sensitive(report, where, field, text):
    for m in IPV4_RE.finditer(text):
        try:
            addr = ipaddress.IPv4Address(m.group(1))
        except ValueError:
            continue
        if (str(addr) in PUBLIC_DNS or addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_multicast or addr.is_unspecified or addr.is_reserved or is_netmask(addr)):
            continue
        report.error(where, "{} 出現公開 IP {}；例句只能用私有位址（192.168.x.x、10.x.x.x、172.16～172.31.x.x）或公開 DNS".format(field, addr))

    for m in EMAIL_RE.finditer(text):
        domain = m.group(1).lower()
        if not domain.endswith(ALLOWED_EMAIL_DOMAINS):
            report.error(where, "{} 出現 Email「{}」；不可放個人資料，需要時請用 example.com".format(field, m.group(0)))

    for m in SECRET_RE.finditer(text):
        report.warn(where, "{} 疑似寫入帳號密碼或金鑰：「{}」".format(field, m.group(0)))

    for m in URL_RE.finditer(text):
        host = re.sub(r"^https?://", "", m.group(0), flags=re.I).split("/")[0].lower()
        if not host.endswith(ALLOWED_EMAIL_DOMAINS):
            report.warn(where, "{} 出現網址 {}，請確認不是內部系統".format(field, m.group(0)))

    for m in UNC_RE.finditer(text):
        report.warn(where, "{} 疑似內部網路路徑「{}」".format(field, m.group(0)))


# ---------------------------------------------------------------------------
# 第 4、5-2、6 節：主題檔
# ---------------------------------------------------------------------------

def check_topic(report, path, data, template_strings):
    where = rel(path)
    stem = path.stem

    if not isinstance(data, dict):
        report.error(where, "主題檔必須是物件 { \"slug\": ..., \"terms\": [...] }")
        return

    for key in TOPIC_FIELDS_REQUIRED:
        if key not in data:
            report.error(where, "缺少必填欄位「{}」".format(key))
    for key in data:
        if key not in TOPIC_FIELDS_REQUIRED:
            report.warn(where, "未定義的欄位「{}」（拼錯了嗎？）".format(key))

    for key in ("slug", "title_zh", "title_en", "description", "updated"):
        if key in data and (not isinstance(data[key], str) or not data[key].strip()):
            report.error(where, "「{}」必須是非空字串".format(key))

    slug = data.get("slug")
    if isinstance(slug, str) and slug:
        if not SLUG_RE.match(stem):
            report.error(where, "檔名「{}」只能用小寫英文、數字與連字號".format(path.name))
        if slug != stem:
            report.error(where, "slug「{}」與檔名「{}」不一致".format(slug, path.name))

    updated = data.get("updated")
    if isinstance(updated, str) and updated:
        if not DATE_RE.match(updated):
            report.error(where, "updated「{}」格式必須是 YYYY-MM-DD".format(updated))
        else:
            try:
                day = dt.date.fromisoformat(updated)
                if day > dt.date.today():
                    report.warn(where, "updated「{}」是未來的日期".format(updated))
            except ValueError:
                report.error(where, "updated「{}」不是有效的日期".format(updated))

    title_zh = data.get("title_zh")
    if isinstance(title_zh, str) and title_zh and not CJK_RE.search(title_zh):
        report.error(where, "title_zh 必須是中文")
    title_en = data.get("title_en")
    if isinstance(title_en, str) and CJK_RE.search(title_en):
        report.error(where, "title_en 不應該有中文")

    # 還沒替換掉的範本文字
    for field, text in iter_strings({k: v for k, v in data.items() if k != "terms"}):
        if text in template_strings:
            report.error(where, "{} 還是範本預設文字「{}」".format(field, text))

    terms = data.get("terms")
    if "terms" in data and not isinstance(terms, list):
        report.error(where, "terms 必須是陣列")
        terms = []
    terms = terms or []
    if len(terms) < MIN_TERMS:
        report.error(where, "目前 {} 張卡，每個主題至少要 {} 張".format(len(terms), MIN_TERMS))

    # 先收集所有術語名稱，給重複與 related 檢查用
    names = {}       # norm → 原始寫法
    exact_names = set()
    for i, term in enumerate(terms):
        if isinstance(term, dict) and isinstance(term.get("term"), str) and term["term"].strip():
            name = term["term"]
            key = norm_term(name)
            if key in names:
                report.error("{} › terms[{}] {}".format(where, i, name), "術語重複（與「{}」相同，不分大小寫）".format(names[key]))
            else:
                names[key] = name
            exact_names.add(name)

    for i, term in enumerate(terms):
        check_term(report, where, i, term, names, exact_names, template_strings)

    # 語言與敏感資訊：主題中所有字串
    for field, text in iter_strings(data):
        loc = where
        m = re.match(r"terms\[(\d+)\]\.(.+)", field)
        if m:
            idx = int(m.group(1))
            name = terms[idx].get("term") if isinstance(terms[idx], dict) else None
            loc = "{} › terms[{}] {}".format(where, idx, name or "")
            field = m.group(2)
        check_language(report, loc.rstrip(), field, text)
        check_sensitive(report, loc.rstrip(), field, text)


def check_term(report, where, i, term, names, exact_names, template_strings):
    if not isinstance(term, dict):
        report.error("{} › terms[{}]".format(where, i), "每張卡都必須是物件")
        return

    name = term.get("term") if isinstance(term.get("term"), str) else ""
    loc = "{} › terms[{}] {}".format(where, i, name).rstrip()

    for key in TERM_FIELDS_REQUIRED:
        if key not in term:
            report.error(loc, "缺少必填欄位「{}」".format(key))
    for key in term:
        if key not in TERM_FIELDS_ALL:
            report.warn(loc, "未定義的欄位「{}」（拼錯了嗎？）".format(key))
    for key in ("term", "full", "zh", "explain", "example", "example_zh", "note"):
        if key in term:
            value = term[key]
            if not isinstance(value, str) or not value.strip():
                report.error(loc, "「{}」必須是非空字串（選填欄位不需要時請直接刪除）".format(key))
            elif value != value.strip():
                report.warn(loc, "「{}」前後有多餘空白".format(key))

    for key, value in term.items():
        if isinstance(value, str) and value in template_strings:
            report.error(loc, "{} 還是範本預設文字「{}」".format(key, value))

    def text(key):
        value = term.get(key)
        return value.strip() if isinstance(value, str) else ""

    name = text("term")
    full = text("full")
    zh = text("zh")
    explain = text("explain")
    example = text("example")
    example_zh = text("example_zh")
    note = text("note")

    # term
    if name:
        if CJK_RE.search(name):
            report.error(loc, "term 必須是英文")
        elif name[0].isalpha() and name[0].islower():
            report.warn(loc, "term「{}」首字是小寫（一般名詞首字大寫，品牌或特殊寫法可忽略）".format(name))

    # full：縮寫才寫
    if name and not full:
        if is_pure_acronym(name):
            report.error(loc, "「{}」是縮寫，必須填寫 full（完整英文）".format(name))
        elif looks_like_acronym(name):
            report.warn(loc, "「{}」看起來像縮寫，如果是請填寫 full".format(name))
    if name and full:
        if not is_pure_acronym(name) and not looks_like_acronym(name):
            report.warn(loc, "「{}」看起來不是縮寫，不是縮寫就不要寫 full".format(name))
        if CJK_RE.search(full):
            report.error(loc, "full 必須是英文")
        if norm_term(full) == norm_term(name):
            report.error(loc, "full 與 term 相同，不是縮寫就不要寫 full")

    # zh：最多兩個說法，用「、」分隔
    if zh:
        if not CJK_RE.search(zh):
            report.error(loc, "zh 必須是中文譯名")
        parts = [p.strip() for p in zh.split("、")]
        if len(parts) > 2:
            report.error(loc, "zh 最多兩個說法（目前 {} 個）".format(len(parts)))
        if any(not p for p in parts):
            report.error(loc, "zh 的「、」前後不能是空的")
        if len(set(parts)) != len(parts):
            report.error(loc, "zh 有重複的說法")
        if re.search(r"[,，/／;；]", zh):
            report.warn(loc, "zh 有兩種說法時請用「、」分隔")
    else:
        parts = []

    # explain：40 字以內、不要只重複中文譯名
    if explain:
        n = zh_length(explain)
        if n > MAX_EXPLAIN:
            report.error(loc, "explain {} 字，超過 {} 字上限".format(n, MAX_EXPLAIN))
        bare = re.sub(r"[\s。，、．.!！?？；;：:「」『』()（）]", "", explain)
        if bare and (bare == re.sub(r"[\s、]", "", zh) or bare in parts):
            report.error(loc, "explain 只重複了中文譯名，請寫白話解釋")
        if not CJK_RE.search(explain):
            report.error(loc, "explain 必須用中文寫")

    # example：必須包含 term、25 個英文字以內
    if example:
        if name and not term_regex(name).search(example):
            report.error(loc, "example 沒有包含術語「{}」本身（不分大小寫，可為複數形）".format(name))
        n = english_words(example)
        if n > MAX_EXAMPLE_WORDS:
            report.error(loc, "example {} 個英文字，超過 {} 字上限".format(n, MAX_EXAMPLE_WORDS))
        if CJK_RE.search(example):
            report.error(loc, "example 必須是英文例句（中文翻譯寫在 example_zh）")

    if example_zh:
        if not CJK_RE.search(example_zh):
            report.error(loc, "example_zh 必須是中文翻譯")
        elif example and example_zh == example:
            report.error(loc, "example_zh 與 example 相同")

    # note：60 字以內
    if note:
        n = zh_length(note)
        if n > MAX_NOTE:
            report.error(loc, "note {} 字，超過 {} 字上限".format(n, MAX_NOTE))

    # related：必須是同主題中已存在的術語
    if "related" in term:
        related = term["related"]
        if not isinstance(related, list):
            report.error(loc, "related 必須是陣列，例如 [\"Gateway\"]")
        else:
            seen = set()
            for item in related:
                if not isinstance(item, str) or not item.strip():
                    report.error(loc, "related 的每一項都必須是術語名稱字串")
                    continue
                key = norm_term(item)
                if key in seen:
                    report.warn(loc, "related 重複列出「{}」".format(item))
                seen.add(key)
                if name and key == norm_term(name):
                    report.error(loc, "related 不可以指向自己")
                elif item not in exact_names:
                    if key in names:
                        report.error(loc, "related「{}」大小寫與術語不一致，請寫成「{}」".format(item, names[key]))
                    else:
                        report.error(loc, "related「{}」不是這個主題中已存在的術語".format(item))


# ---------------------------------------------------------------------------
# templates/topic-template.json
# ---------------------------------------------------------------------------

def check_template(report):
    """範本本身不檢查內容，只確認格式正確、欄位齊全。回傳範本中的字串（用來偵測沒替換的範本文字）。"""
    path = ROOT / "templates" / "topic-template.json"
    where = rel(path)
    if not path.exists():
        return set()
    data = load_json(path, report)
    if not isinstance(data, dict):
        if data is not None:
            report.error(where, "範本必須是物件")
        return set()
    for key in TOPIC_FIELDS_REQUIRED:
        if key not in data:
            report.error(where, "範本缺少欄位「{}」".format(key))
    terms = data.get("terms")
    if not isinstance(terms, list) or not terms or not isinstance(terms[0], dict):
        report.error(where, "範本的 terms 至少要有一張示範卡")
    else:
        for key in TERM_FIELDS_ALL:
            if key not in terms[0]:
                report.error(where, "範本的示範卡缺少欄位「{}」".format(key))
    return {text for _, text in iter_strings(data) if len(text) >= 4}


# ---------------------------------------------------------------------------
# 主程式
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="檢查術語卡專案是否符合 CLAUDE.md 的規則。")
    parser.add_argument("--strict", action="store_true", help="警告也視為錯誤")
    args = parser.parse_args()

    # Windows 終端機或重新導向時，避免中文（尤其簡體字）無法輸出
    for stream in (sys.stdout, sys.stderr):
        try:
            if not stream.isatty() or (stream.encoding or "").lower().replace("-", "") != "utf8":
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    report = Report()
    check_structure(report)
    template_strings = check_template(report)
    registered = check_index(report)

    topics = {}
    topic_dir = ROOT / "topics"
    topic_files = sorted(p for p in topic_dir.glob("*.json") if p.name != "index.json") if topic_dir.is_dir() else []
    for path in topic_files:
        if path.stem not in registered:
            report.error(rel(path), "沒有登記在 topics/index.json（新主題請加在陣列最後）")
        data = load_json(path, report)
        if data is None:
            continue
        check_topic(report, path, data, template_strings)
        if isinstance(data, dict):
            topics[path.stem] = data

    check_front_end(report, topics)

    # ---- 輸出 ----
    print("術語卡規則檢查（{}）".format(ROOT))
    print("主題：{} 個已登記、{} 個主題檔、共 {} 張卡".format(
        len(registered), len(topic_files),
        sum(len(t.get("terms", [])) for t in topics.values() if isinstance(t.get("terms"), list))))
    if not topic_files and not registered:
        print("（目前還沒有任何主題）")
    print()

    # 依「檔案出現順序 → 卡片編號」排序，同一張卡的問題排在一起
    file_order = {}
    for where, _ in report.errors + report.warnings:
        file_order.setdefault(where.split(" › ")[0], len(file_order))

    def sort_key(item):
        where = item[0]
        m = re.search(r"terms\[(\d+)\]", where)
        return (file_order[where.split(" › ")[0]], int(m.group(1)) if m else -1)

    for label, items in (("錯誤", report.errors), ("警告", report.warnings)):
        if not items:
            continue
        items = sorted(items, key=sort_key)
        print("【{}】{} 項".format(label, len(items)))
        for where, message in items:
            print("  ✗ " if label == "錯誤" else "  ! ", end="")
            print("{}：{}".format(where, message))
        print()

    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    if failed:
        print("未通過：請修正以上{}後再執行一次。".format("錯誤與警告" if args.strict else "錯誤"))
        return 1
    if report.warnings:
        print("通過（有 {} 項警告，請人工確認）。".format(len(report.warnings)))
    else:
        print("全部通過。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
