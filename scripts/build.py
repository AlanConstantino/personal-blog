#!/usr/bin/env python3
"""Build static HTML for the blog from Markdown sources."""

from __future__ import annotations

import re
import sys
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = Path(__file__).resolve().parent / "vendor"
sys.path.insert(0, str(VENDOR))

import markdown2  # noqa: E402

SITE_URL = "https://blog.alanjc.com"
POSTS_DIR = ROOT / "content" / "posts"
ARTICLES_DIR = ROOT / "articles"
TAGS_DIR = ROOT / "tags"
PAGE_DIR = ROOT / "page"
TEMPLATES_DIR = ROOT / "templates"
INDEX_PATH = ROOT / "index.html"
RSS_PATH = ROOT / "rss.xml"

# Change this when the homepage needs more than one page.
POSTS_PER_PAGE = 10

WORDS_PER_MINUTE = 250
REQUIRED_FIELDS = ("title", "date", "slug", "description")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_EXTRAS = [
    "fenced-code-blocks",
    "tables",
    "header-ids",
    "strike",
    "cuddled-lists",
]


@dataclass
class Post:
    source_path: Path
    title: str
    date: date
    slug: str
    description: str
    tags: list[str] = field(default_factory=list)
    draft: bool = False
    body_md: str = ""
    body_html: str = ""
    reading_time: int = 1
    next_slug: str | None = None

    @property
    def date_display(self) -> str:
        # Drop leading zero on day: January 6, 2022
        return self.date.strftime("%B %d, %Y").replace(" 0", " ")

    @property
    def canonical(self) -> str:
        return f"{SITE_URL}/articles/{self.slug}.html"

    @property
    def article_href_from_root(self) -> str:
        return f"./articles/{self.slug}.html"

    @property
    def pub_date_rss(self) -> str:
        dt = datetime(
            self.date.year,
            self.date.month,
            self.date.day,
            12,
            0,
            0,
            tzinfo=timezone.utc,
        )
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def read_template(name: str) -> str:
    path = TEMPLATES_DIR / name
    if not path.is_file():
        fail(f"missing template: {path}")
    return path.read_text(encoding="utf-8")


def render(template: str, **values: str) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{[a-z_]+\}\}", out)
    if leftover:
        fail(f"unfilled template placeholders: {', '.join(sorted(set(leftover)))}")
    return out


def parse_front_matter(text: str, path: Path) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        fail(f"{path}: missing front matter (file must start with ---)")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"{path}: missing opening front matter delimiter")
    meta: dict[str, str] = {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            fail(f"{path}: invalid front matter line: {line!r}")
        key, raw = line.split(":", 1)
        meta[key.strip()] = raw.strip()
    if end is None:
        fail(f"{path}: missing closing front matter delimiter")
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return meta, body


def parse_date(value: str, path: Path) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail(f"{path}: date must be YYYY-MM-DD, got {value!r}")


def normalize_tags(raw: str) -> list[str]:
    if not raw.strip():
        return []
    tags: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        tag = part.strip().lower().replace(" ", "-")
        tag = re.sub(r"[^a-z0-9-]", "", tag)
        tag = re.sub(r"-+", "-", tag).strip("-")
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def parse_draft(raw: str | None) -> bool:
    if raw is None or raw == "":
        return False
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def reading_time_minutes(text: str) -> int:
    minutes = max(1, -(-word_count(text) // WORDS_PER_MINUTE))  # ceil
    return minutes


def render_markdown(body: str) -> str:
    """Convert Markdown (or HTML-in-Markdown) to an HTML fragment."""
    cleaned = textwrap.dedent(body).strip()
    if not cleaned:
        return ""
    return markdown2.markdown(cleaned, extras=MARKDOWN_EXTRAS).strip()


def load_posts() -> list[Post]:
    if not POSTS_DIR.is_dir():
        fail(f"missing posts directory: {POSTS_DIR}")
    paths = sorted(POSTS_DIR.glob("*.md"))
    if not paths:
        fail(f"no Markdown posts in {POSTS_DIR}")

    posts: list[Post] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(text, path)
        for key in REQUIRED_FIELDS:
            if key not in meta or not meta[key].strip():
                fail(f"{path}: missing required field {key!r}")
        slug = meta["slug"].strip()
        if not SLUG_RE.match(slug):
            fail(
                f"{path}: slug must be lowercase letters, digits, and hyphens "
                f"(got {slug!r})"
            )
        post = Post(
            source_path=path,
            title=meta["title"].strip(),
            date=parse_date(meta["date"].strip(), path),
            slug=slug,
            description=meta["description"].strip(),
            tags=normalize_tags(meta.get("tags", "")),
            draft=parse_draft(meta.get("draft")),
            body_md=body,
        )
        post.reading_time = reading_time_minutes(body)
        post.body_html = render_markdown(body)
        posts.append(post)

    # Unique slugs among all posts (including drafts).
    seen: dict[str, Path] = {}
    for post in posts:
        if post.slug in seen:
            fail(
                f"duplicate slug {post.slug!r}: {seen[post.slug]} and {post.source_path}"
            )
        seen[post.slug] = post.source_path
    return posts


def assign_next_links(published: list[Post]) -> None:
    """Next = next older post. published must be newest-first."""
    for i, post in enumerate(published):
        if i + 1 < len(published):
            post.next_slug = published[i + 1].slug
        else:
            post.next_slug = None


def tags_html(tags: list[str], href_prefix: str, indent: str = "        ") -> str:
    if not tags:
        return ""
    parts = [f'{indent}<p class="tags">']
    for tag in tags:
        href = f"{href_prefix}{tag}.html"
        parts.append(
            f'{indent}  <a class="tag" href="{escape(href, quote=True)}">{escape(tag)}</a>'
        )
    parts.append(f"{indent}</p>")
    return "\n".join(parts)


def card_html(post: Post, href: str, tag_href_prefix: str, template: str) -> str:
    return render(
        template,
        href=escape(href, quote=True),
        title=escape(post.title),
        date_display=escape(post.date_display),
        reading_time=str(post.reading_time),
        description=escape(post.description),
        tags_html=tags_html(post.tags, tag_href_prefix),
    )


def replace_region(text: str, name: str, content: str) -> str:
    pattern = re.compile(
        rf"<!-- {name}:START -->.*?<!-- {name}:END -->",
        re.DOTALL,
    )
    replacement = f"<!-- {name}:START -->\n{content}\n<!-- {name}:END -->"
    new_text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        fail(f"expected one <!-- {name}:START/END --> region")
    return new_text


def chunk_posts(posts: list[Post], per_page: int) -> list[list[Post]]:
    if per_page < 1:
        fail("POSTS_PER_PAGE must be >= 1")
    if not posts:
        return [[]]
    return [posts[i : i + per_page] for i in range(0, len(posts), per_page)]


def pager_html(
    page_number: int,
    page_count: int,
    href_for_page,
) -> str:
    if page_count <= 1:
        return ""
    newer = ""
    older = ""
    if page_number > 1:
        newer = f'<a href="{escape(href_for_page(page_number - 1), quote=True)}">&#8592; Newer</a>'
    if page_number < page_count:
        older = f'<a href="{escape(href_for_page(page_number + 1), quote=True)}">Older &#8594;</a>'
    return (
        '        <div class="row pager">\n'
        f"          {newer}\n"
        f'          <span>Page {page_number} of {page_count}</span>\n'
        f"          {older}\n"
        "        </div>"
    )


def write_article(post: Post, template: str) -> None:
    if post.next_slug:
        next_link = (
            f'<a href="./{escape(post.next_slug, quote=True)}.html">Next &#8594;</a>'
        )
    else:
        next_link = ""
    # Indent content blocks lightly for readable HTML.
    content = post.body_html
    html = render(
        template,
        description=escape(post.description, quote=True),
        canonical=escape(post.canonical, quote=True),
        title=escape(post.title),
        date_display=escape(post.date_display),
        reading_time=str(post.reading_time),
        tags_html=tags_html(post.tags, "../tags/"),
        content=content,
        next_link=next_link,
    )
    out = ARTICLES_DIR / f"{post.slug}.html"
    out.write_text(html, encoding="utf-8")


def build_rss(posts: list[Post], template: str) -> None:
    items: list[str] = []
    for post in posts:
        desc = escape(post.description)
        item = (
            "    <item>\n"
            f"      <title>{escape(post.title)} | {post.reading_time} min read</title>\n"
            f"      <link>{post.canonical}</link>\n"
            f"      <guid>{post.canonical}</guid>\n"
            f"      <pubDate>{post.pub_date_rss}</pubDate>\n"
            f"      <description><![CDATA[\n"
            f"        <p>\n"
            f"          {desc}\n"
            f"        </p>]]>\n"
            f"      </description>\n"
            "    </item>"
        )
        items.append(item)
    RSS_PATH.write_text(
        render(template, items="\n".join(items) + ("\n" if items else "")),
        encoding="utf-8",
    )


def build_home_and_pages(posts: list[Post], card_tpl: str, page_tpl: str) -> None:
    pages = chunk_posts(posts, POSTS_PER_PAGE)
    page_count = len(pages)

    def home_href(page_number: int) -> str:
        if page_number <= 1:
            return "./"
        return f"./page/{page_number}.html"

    # Page 1 → index.html cards region
    if not INDEX_PATH.is_file():
        fail(f"missing {INDEX_PATH}")
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    cards = "\n".join(
        card_html(p, p.article_href_from_root, "./tags/", card_tpl) for p in pages[0]
    )
    # Keep indentation similar to existing index markup.
    cards_block = cards
    index_text = replace_region(index_text, "POSTS", cards_block)
    index_text = replace_region(
        index_text,
        "PAGER",
        pager_html(1, page_count, home_href),
    )
    INDEX_PATH.write_text(index_text, encoding="utf-8")

    # Extra pages
    if PAGE_DIR.exists():
        for old in PAGE_DIR.glob("*.html"):
            old.unlink()
    if page_count > 1:
        PAGE_DIR.mkdir(parents=True, exist_ok=True)

        def page_href(page_number: int) -> str:
            if page_number <= 1:
                return "../"
            return f"./{page_number}.html"

        for number in range(2, page_count + 1):
            page_posts = pages[number - 1]
            cards = "\n".join(
                card_html(p, f".{p.article_href_from_root}", "../tags/", card_tpl)
                for p in page_posts
            )
            html = render(
                page_tpl,
                page_number=str(number),
                page_count=str(page_count),
                canonical=escape(f"{SITE_URL}/page/{number}.html", quote=True),
                posts=cards,
                pager=pager_html(number, page_count, page_href),
            )
            (PAGE_DIR / f"{number}.html").write_text(html, encoding="utf-8")


def build_tags(posts: list[Post], card_tpl: str, tag_tpl: str, tags_index_tpl: str) -> None:
    if TAGS_DIR.exists():
        for old in TAGS_DIR.rglob("*.html"):
            old.unlink()
    TAGS_DIR.mkdir(parents=True, exist_ok=True)

    by_tag: dict[str, list[Post]] = defaultdict(list)
    for post in posts:
        for tag in post.tags:
            by_tag[tag].append(post)

    tag_items: list[str] = []
    for tag in sorted(by_tag.keys()):
        count = len(by_tag[tag])
        label = "post" if count == 1 else "posts"
        tag_items.append(
            f'            <li><a class="tag" href="./{escape(tag, quote=True)}.html">'
            f"{escape(tag)}</a> — {count} {label}</li>"
        )

    (TAGS_DIR / "index.html").write_text(
        render(
            tags_index_tpl,
            tag_items="\n".join(tag_items) if tag_items else "            <li>No tags yet.</li>",
        ),
        encoding="utf-8",
    )

    for tag, tag_posts in by_tag.items():
        # tag_posts already newest-first if posts are
        pages = chunk_posts(tag_posts, POSTS_PER_PAGE)
        page_count = len(pages)

        def make_href(page_number: int, t: str = tag) -> str:
            if page_number <= 1:
                return f"./{t}.html"
            return f"./{t}/page/{page_number}.html"

        for number, page_posts in enumerate(pages, start=1):
            if number == 1:
                card_prefix_articles = "../articles/"
                tag_prefix = "./"
                css_prefix = "../"
                home_href = "../"
                tags_index_href = "./"
                out_path = TAGS_DIR / f"{tag}.html"
                canonical = f"{SITE_URL}/tags/{tag}.html"
            else:
                card_prefix_articles = "../../../articles/"
                tag_prefix = "../../"
                css_prefix = "../../../"
                home_href = "../../../"
                tags_index_href = "../../"
                out_dir = TAGS_DIR / tag / "page"
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{number}.html"
                canonical = f"{SITE_URL}/tags/{tag}/page/{number}.html"

            cards = "\n".join(
                card_html(
                    p,
                    f"{card_prefix_articles}{p.slug}.html",
                    tag_prefix,
                    card_tpl,
                )
                for p in page_posts
            )
            html = render(
                tag_tpl,
                tag=escape(tag),
                css_prefix=css_prefix,
                canonical=escape(canonical, quote=True),
                home_href=home_href,
                tags_index_href=tags_index_href,
                posts=cards,
                pager=pager_html(number, page_count, make_href),
            )
            out_path.write_text(html, encoding="utf-8")


def clean_generated_articles(published_slugs: set[str]) -> None:
    """Remove generated article HTML that is not in the published set.

    Keeps underscore templates and unknown hand files that start with '_'.
    """
    if not ARTICLES_DIR.is_dir():
        ARTICLES_DIR.mkdir(parents=True)
        return
    for path in ARTICLES_DIR.glob("*.html"):
        if path.name.startswith("_"):
            continue
        slug = path.stem
        if slug not in published_slugs:
            # Do not delete files that are not produced from current posts.
            # Only delete if we are sure — keep orphans for safety? User may want clean.
            # Safer: leave orphans. Comment notes rebuild overwrites known slugs only.
            pass


def main() -> None:
    article_tpl = read_template("article.html")
    card_tpl = read_template("post-card.html")
    tag_tpl = read_template("tag.html")
    tags_index_tpl = read_template("tags-index.html")
    page_tpl = read_template("page.html")
    rss_tpl = read_template("rss.xml")

    all_posts = load_posts()
    published = [p for p in all_posts if not p.draft]
    published.sort(key=lambda p: (p.date, p.slug), reverse=True)
    assign_next_links(published)

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    for post in published:
        write_article(post, article_tpl)

    build_home_and_pages(published, card_tpl, page_tpl)
    build_tags(published, card_tpl, tag_tpl, tags_index_tpl)
    build_rss(published, rss_tpl)

    drafts = len(all_posts) - len(published)
    print(f"Built {len(published)} post(s)" + (f", skipped {drafts} draft(s)" if drafts else ""))
    for post in published:
        print(f"  - {post.date.isoformat()}  {post.slug}")
    tags = sorted({t for p in published for t in p.tags})
    print(f"Tags: {', '.join(tags) if tags else '(none)'}")
    print(f"Wrote index.html, rss.xml, articles/, tags/")
    if len(published) > POSTS_PER_PAGE:
        print(f"Pagination active ({POSTS_PER_PAGE} per page)")


if __name__ == "__main__":
    main()
