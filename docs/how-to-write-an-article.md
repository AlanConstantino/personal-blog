# How to write and publish an article

This guide shows how to add a post to this blog.
The blog stores each post as Markdown.
A Python build turns that Markdown into HTML.

You need Python 3 on your machine.
You do not need pip packages for the build.

## What you need before you start

1. Open a terminal.
2. Go to the root of this repository.
3. Make sure `python3` runs.

## Post file layout

Store each post here:

`content/posts/`

Use one Markdown file per post.
The file name can differ from the public URL.
The public URL comes from the `slug` field in the file.

Example path:

`content/posts/my-first-post.md`

## Front matter

Start every post with front matter.
Front matter is a short metadata block at the top of the file.

Required fields:

- `title` — page title and main heading
- `date` — publish date in `YYYY-MM-DD` form
- `slug` — URL name, lowercase letters, digits, and hyphens only
- `description` — short summary for the home card, meta tag, and RSS

Optional fields:

- `tags` — comma-separated labels, for example `python, terminal`
- `draft` — set `true` to skip the post in the public build

### Example

~~~~markdown
---
title: Creating Aliases on Linux and Mac
date: 2021-01-12
slug: creating-aliases-on-linux-and-mac
description: Learn how to create shell aliases on Linux and Mac.
tags: linux, macos, terminal
draft: false
---

## Why aliases help

Long commands are hard to remember.
An alias gives a short name to a long command.

    alias ll='ls -la'
~~~~

## Body rules

Write the body in Markdown under the front matter.

Supported Markdown includes:

- headings
- paragraphs
- bold and italic text
- links and images
- lists
- tables
- fenced code blocks

Image paths for article pages use the `articles/` folder as the base.
Link site images like this:

`![Alt text](../images/folder/file.png)`

Keep the `slug` stable after you publish.
A new slug creates a new URL.

## Draft posts

Set this line in the front matter:

`draft: true`

The build skips draft posts.
Draft posts do not appear on the home page, tag pages, or RSS feed.

Set `draft: false` or remove the field when you want to publish.

## Build the site

From the repository root, run:

```bash
make build
```

This command runs `python3 scripts/build.py`.

The build reads every file in `content/posts/`.
It writes:

- `articles/{slug}.html` for each published post
- the card list inside `index.html`
- `tags/` pages for filters
- `rss.xml`
- `page/{n}.html` when the post count needs more than one home page

The build does not run `git commit` for you.

## Check the result

1. Open `articles/{slug}.html` in a browser.
2. Open `index.html` and check the new card.
3. Open `tags/` if you set tags.
4. Open `rss.xml` if you use RSS.

If the page looks wrong, edit the Markdown file.
Run the build again.
Repeat until the page looks correct.

## Publish with git

After you accept the HTML output, commit the source and the generated files.

Example:

```bash
git add content/posts/my-first-post.md
git add articles/my-first-post.html index.html rss.xml tags
git add page
git commit -m "Add post: my first post"
git push
```

Add only the paths that changed.
GitHub Pages serves the HTML files in the repository.

## Edit an existing post

1. Open the Markdown file in `content/posts/`.
2. Change the body or the front matter.
3. Keep the `slug` the same unless you want a new URL.
4. Run `make build`.
5. Check the HTML in a browser.
6. Commit the Markdown file and the generated files.

## Tags

Add tags in front matter:

`tags: python, web`

The build normalizes tags to lowercase labels.
Spaces become hyphens.

The build creates:

- `tags/index.html` — full tag list
- `tags/{tag}.html` — posts for one tag

Home cards and article headers link to those tag pages.

## Pagination

The build uses a page size set in `scripts/build.py`.

Current value:

`POSTS_PER_PAGE = 10`

When the published post count is greater than that value, the build creates extra pages under `page/`.
The home page shows the newest posts first.
Older posts move to page 2 and beyond.

You do not create page files by hand.

## Article footer behavior

Each article footer has:

- **Back** — home page
- **Top** — top of the article
- **Next** — next older post, when one exists

The build sets the Next link from the post dates.
You do not set Next by hand.

## Files you edit by hand

Edit these when you change site chrome or style:

- `index.html` outside the `POSTS` and `PAGER` markers
- `templates/` for layout shells
- `css/`
- `images/`
- `donate.html`

Do not hand-edit generated article bodies in `articles/` if the post has a Markdown source.
Edit the Markdown file, then run the build.

## Common build errors

Missing field:

The build stops if `title`, `date`, `slug`, or `description` is missing.

Bad date:

Use `YYYY-MM-DD` only.

Bad slug:

Use lowercase letters, digits, and hyphens only.
Example of a valid slug: `creating-aliases-on-linux-and-mac`.

Duplicate slug:

Two posts cannot share the same slug.

## Quick checklist

1. Create `content/posts/your-file.md`.
2. Fill `title`, `date`, `slug`, and `description`.
3. Add optional `tags` and set `draft` if needed.
4. Write the Markdown body.
5. Run `make build`.
6. Check the HTML output in a browser.
7. Commit the Markdown source and the generated HTML.
8. Push the commit to publish.
