# Open-Source Business Models

> Where the line between open and closed lies decides how an open project lives. This is research input for drawing that line in Ahabase.

**Status:** open
**Source:** the Human's question, 2026-10-30 ([AHA-0011](AHA-0011), note 6)

## Two axes

1. **Where the boundary lies:**
   - in the architecture: an open core with closed extensions (GitLab, Mattermost), or a closed core with an open plugin ecosystem (Obsidian, Figma), which is a proprietary platform and not open source;
   - in a service: open code, paid hosting or sync (WordPress with Automattic, Supabase, Nextcloud);
   - in support and certification (Red Hat, Canonical, SUSE);
   - in the licence: dual licensing (Qt, formerly MySQL), or source-available licences such as BSL, SSPL and FSL. Hard licence changes tended to provoke community forks (OpenTofu, Valkey), and some projects later added an open licence back.
   - in funding: foundations, sponsors and public grants.
2. **Who pays, and for what.**

## For Ahabase

The traces in this Epic point to a hybrid:
- an open core with organization-specific extension points (the `organization` signer adapter);
- the decisive boundary drawn by trust zones over knowledge, not by licence over code ("open tools, closed knowledge", AHABASE.md Vision);
- reciprocity, so that those who share gain the most.

Recent licence changes should be checked against current sources before any decision, because this note reflects knowledge with a cutoff date.

## Open question: core or landscape

The Human (2026-10-31, consolidation session): is ahabase an **open core** - one base with closed extensions built on it - or an **open landscape** - one base that many methods, communities and distributions build on, where the boundary is drawn by trust zones over knowledge rather than by what is closed? The hybrid traces above lean core; the landscape reading treats the base as shared ground that grows more valuable with every method on it, and the graduation path already points that way (one base, many plugins).

## Related

- [AHABASE](AHABASE) - Vision
- [graduation-criteria](graduation-criteria)
