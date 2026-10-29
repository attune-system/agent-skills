#!/usr/bin/env python3
"""Check skill packaging, local links, examples, and optional live docs links."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urldefrag, urlsplit
from urllib.request import Request, urlopen

import yaml


FENCES = re.compile(r"^```([^\n]*)\n(.*?)^```[ \t]*$", re.M | re.S)
LINKS = re.compile(r"\[[^\]\n]+\]\(([^\s)]+)\)")


class PageIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        self.ids.update(value for key, value in attrs if key == "id")


def check_page(entry):
    url, fragments = entry
    try:
        request = Request(url, headers={"User-Agent": "attune-agent-skills-link-check"})
        with urlopen(request, timeout=30) as response:
            if urlsplit(response.url).hostname != "docs.attunedev.org":
                return [f"Unexpected docs redirect: {url} -> {response.url}"]
            parser = PageIds()
            parser.feed(response.read(4 * 1024 * 1024).decode("utf-8"))
        return [f"Missing docs fragment: {url}#{fragment}"
                for fragment in sorted(fragments) if fragment not in parser.ids]
    except Exception as error:
        return [f"Cannot fetch {url}: {error}"]


def check(root, check_urls=False):
    errors = []
    skills = sorted(root.glob("*/SKILL.md"))
    if not skills:
        errors.append("No root skill directories found")
    readme = root / "README.md"
    index_links = set(LINKS.findall(FENCES.sub("", readme.read_text())))
    for path in skills:
        if path.relative_to(root).as_posix() not in index_links:
            errors.append(f"{readme}: skill missing from index: {path.parent.name}")
        text = path.read_text()
        match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
        if not match:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        try:
            metadata = yaml.safe_load(match[1])
            if not isinstance(metadata, dict):
                raise ValueError("frontmatter must be a mapping")
            if metadata.get("name") != path.parent.name:
                errors.append(f"{path}: name must match directory")
            description = metadata.get("description")
            if not isinstance(description, str) or not description.strip():
                errors.append(f"{path}: missing description")
            if "https://docs.attunedev.org/" not in text:
                errors.append(f"{path}: missing public documentation pointer")
            interface_path = path.parent / "agents/openai.yaml"
            if interface_path.exists():
                interface = yaml.safe_load(interface_path.read_text())["interface"]
                if f"${path.parent.name}" not in interface["default_prompt"]:
                    errors.append(f"{interface_path}: starter prompt references wrong skill")
        except (yaml.YAMLError, KeyError, TypeError, ValueError) as error:
            errors.append(f"{path}: invalid metadata: {error}")

    docs = [readme]
    docs.extend(path for skill in skills for path in skill.parent.rglob("*.md"))
    pages = {}
    examples = 0
    for path in docs:
        text = path.read_text()
        skill_root = next((skill.parent for skill in skills
                           if path.is_relative_to(skill.parent)), None)
        if len(re.findall(r"^```", text, re.M)) % 2:
            errors.append(f"{path}: unclosed code fence")
        for match in FENCES.finditer(text):
            language, body = match.groups()
            if language.strip() in {"yaml", "yml", "json"}:
                examples += 1
                try:
                    if language.strip() == "json":
                        json.loads(body)
                    else:
                        yaml.safe_load(body)
                except (yaml.YAMLError, ValueError) as error:
                    line = text[:match.start()].count("\n") + 1
                    errors.append(f"{path}:{line}: invalid {language} example: {error}")
        prose = FENCES.sub("", text)
        for link in LINKS.findall(prose):
            url, fragment = urldefrag(link)
            parsed = urlsplit(url)
            if parsed.scheme:
                if parsed.hostname == "docs.attunedev.org":
                    if parsed.scheme != "https":
                        errors.append(f"{path}: docs link must use HTTPS: {link}")
                    pages.setdefault(url, set())
                    if fragment:
                        pages[url].add(unquote(fragment))
            elif url:
                target = (path.parent / unquote(url)).resolve()
                if skill_root and not target.is_relative_to(skill_root.resolve()):
                    errors.append(f"{path}: link leaves independently installable skill: {link}")
                if not target.exists():
                    errors.append(f"{path}: broken local link: {link}")

    if check_urls:
        with ThreadPoolExecutor(max_workers=6) as executor:
            for failures in executor.map(check_page, sorted(pages.items())):
                errors.extend(failures)
    return errors, len(skills), examples, len(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-urls", action="store_true",
                        help="fetch docs.attunedev.org pages and check linked fragments")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors, skills, examples, pages = check(args.root.resolve(), args.check_urls)
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Checked {skills} skills, {examples} YAML/JSON examples, {pages} docs pages. "
          f"Errors: {len(errors)}. Live URLs: {'checked' if args.check_urls else 'not requested'}.")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
