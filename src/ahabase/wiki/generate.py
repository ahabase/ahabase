"""Wiki navigation generation - sidebar and home content builders.

The content builders are pure functions of the config, so the rendered
markdown is unit-tested without touching the wiki tree; the rendered
bytes are the graduated contract (the parity row compares them with the
method side's output on the same fixture). Collapsible sections, raw
content, images and stats tables ride along.

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-projection
"""

from __future__ import annotations

from pathlib import Path

import click


def build_sidebar_lines(sidebar_config: list) -> list[str]:
    """Render sidebar section lines from the sidebar config.

    Supports section headers (bold text or a linked heading), a
    ``header_link`` rendering the header as a clickable heading,
    ``collapsible`` wrapping the section in ``<details><summary>``,
    item lists, and ``separator`` rules.
    """
    lines = []
    for section in sidebar_config:
        section_name = section.get("section")
        header_link = section.get("header_link")
        items = section.get("items", [])
        collapsible = section.get("collapsible", False)
        separator = section.get("separator", False)

        if separator:
            lines.append("***")
            continue

        if collapsible and section_name:
            lines.append(f"<details>\n<summary>{section_name}</summary>\n")
        elif section_name and header_link:
            lines.append(f"### [{section_name}]({header_link})")
        elif section_name:
            lines.append(f"\n**{section_name}**")

        for item in items:
            label = item.get("label", "")
            target = item.get("target", "")
            external = item.get("external", False)

            if external or target.startswith("http"):
                lines.append(f"- [{label}]({target})")
            elif section_name is None:
                lines.append(f"**[{label}]({target})**")
            else:
                lines.append(f"- [{label}]({target})")

        if collapsible and section_name:
            lines.append("\n</details>")
    return lines


def build_home_lines(home_config: dict) -> list[str]:
    """Render home page lines from the home config.

    Supports raw ``content`` markdown, an ``image`` (``src``/``alt``),
    a link+description ``table``, a ``stats`` summary table and a
    ``blockquote`` block.
    """
    lines = []

    lines.append(f"# {home_config.get('title', 'Wiki')}")
    lines.append("")
    lines.append(home_config.get("subtitle", ""))
    lines.append("")

    for section in home_config.get("sections", []):
        title = section.get("title")
        if title:
            lines.append(f"## {title}")
            lines.append("")

        if "content" in section:
            content = section["content"]
            lines.append(content.rstrip())
            lines.append("")

        if "image" in section:
            img = section["image"]
            src = img.get("src", "")
            alt = img.get("alt", "")
            lines.append(f"![{alt}]({src})")
            lines.append("")

        if "blockquote" in section:
            for line in section["blockquote"].split("\n"):
                lines.append(f"> {line}")
            lines.append("")

        if "description" in section:
            lines.append(section["description"])
            lines.append("")

        if "table" in section:
            lines.append("| Resource | Description |")
            lines.append("|----------|-------------|")
            for row in section["table"]:
                label = row.get("label", "")
                target = row.get("target", "")
                desc = row.get("description", "")
                lines.append(f"| [{label}]({target}) | {desc} |")
            lines.append("")

        if "stats" in section:
            stats = section["stats"]
            lines.append("| Phase | Status |")
            lines.append("|-------|--------|")
            lines.append(f"| Concepts | {stats.get('concepts', 0)} implemented |")
            lines.append(f"| Relationships | {stats.get('relationships', 0)} implemented |")
            lines.append(f"| Tests | {stats.get('tests', 0)}/{stats.get('tests', 0)} passing |")
            lines.append(f"| Data Stories | {stats.get('data_stories', 0)} documented |")
            lines.append("")
    return lines


def _write_or_preview(path: Path, content: str, label: str, dry_run: bool):
    """Write generated content, or print a preview on dry run."""
    if dry_run:
        preview = content[:500] + "..." if len(content) > 500 else content
        click.echo(f"  Would generate {label}:")
        click.echo(preview)
    else:
        with open(path, "w") as f:
            f.write(content)
        click.echo(f"  Generated: {label}")


def generate_navigation(wiki_path: Path, config: dict, dry_run: bool) -> None:
    """Generate ``_Sidebar.md`` and ``Home.md`` from the config.

    The config's absence was already settled at load time (defaults,
    ``{}``): an unconfigured Epic renders the empty navigation - the
    default title, no sections - rather than refusing.
    """
    click.echo(f"Generating navigation for: {wiki_path}")

    click.echo("\n=== Generating _Sidebar.md ===")
    sidebar_content = "\n".join(
        build_sidebar_lines(config.get("sidebar", []))).strip() + "\n"
    _write_or_preview(wiki_path / "_Sidebar.md", sidebar_content,
                      "_Sidebar.md", dry_run)

    click.echo("\n=== Generating Home.md ===")
    home_content = "\n".join(build_home_lines(config.get("home", {})))
    _write_or_preview(wiki_path / "Home.md", home_content,
                      "Home.md", dry_run)

    if dry_run:
        click.echo("\n(Dry run - no changes made)")
