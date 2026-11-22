# AHA-0008 lane: the evolucean SubEpics - state read statically

**Lane:** evolucean SubEpics - home instance, deepseek seat (`656cf2f6`), read-only
**Output:** this document, for `_grid4d/story/AHA-0008-lane-evolucean-subepics.md` (delivered in chat for the writer to commit)
**Read:** the evolucean Epic, `origin/main` = `df08cd4bbfdb7941343d0c459671bc514c619992`, 2026-10-24 22:53:07 +0200; read 2026-10-26 06:53Z
**Method:** static reading only. Files were read as text; no code was executed, no repository file was written, no worktree was created.

**Revision:** v5, 2026-10-26. v2 cut the closed-zone document names (row 1249), moving the item list to the method's owners (section 8). v3 carried the primary review's first two fixes to this lane: the three collaboration story ids that survived v2 at section 6 were removed, and the 14-day commit count was swapped (1324 to 1323). That swap was a reading of a rule that moves - `--since=2026-10-10` is a plain date, and git anchors its missing time of day at the clock the command runs at, so the same command read 1324 before 07:57Z and 1323 in the hours after, and neither number was wrong. v5 fixes the anchor instead of the reading (section 1). v4 carries the eight remaining findings of the same verdict, each re-measured at the pin here before the edit: nine SubEpics own no `issue/` folder, not eight (section 2); the last-touch group and the remainder row are nine, not eleven and ten (section 6); one SubEpic's newest own document is 2026-10-23, not 2026-10-16 (section 6); all fourteen identity documents carry the 2026-10-23 approval line, twelve of them by the standard sentence (section 6); the archive range in `story/` is 1 to 3, not 2 to 3 (sections 6 and 9); the prefix remainder is 166, not 165 (section 10); the evolucean-object tokens number four, not three (section 7); and the open bucket now names `proposed`, which is what separates 132 from 128 at the root (sections 2 and 4). v4 also puts two sentences about moving states into the past tense - section 1's local-tree lag and section 7's branch head - because both were true of the reading moment and neither is true now. v5 changes the 14-day window to the tip-relative instant and the number to **1242** of 3724 (33.4%) in sections 1 and 6, and the revision range in section 11; counts, tables and findings are otherwise unchanged.

**On closed-zone names:** the ahabase identity's rule is "Links point inward" - a document of that open Epic "links only to documents of this repository and **names no document of the closed zone**". The name of the Epic is not a document and is explicitly wanted in plain text; a document of it is not. So this document names no evolucean document - no issue, idea or story stem, no story id, no document path - and names only the Epic and the SubEpic scopes (folder names, not documents). v1 named closed-zone documents in plain text while claiming that not linking was enough; the rule's second half says otherwise, and this revision is that correction.

## 0. Read against inferred - how to tell them apart

**Read.** - the value is taken from a field of a document at the pinned tree, from a file list, or from git. Every number in this document is read unless said otherwise, and every number names the population it was counted over.
**Inferred.** - my classifier, my grouping, my reading of intent. Every such place is marked, and the rule is printed so the reader can re-bucket.

The inline marks used below are "(READ)" and "(INFERRED)" at the start of the relevant sentence or block.

## 1. The tree and the moment

READ:

- The evolucean Epic has 3724 commits on `origin/main`; the first is 2026-08-16. **1242** of them (33.4%) are within the 14 days ending at the tip. The rule, so the number can be re-derived: `git rev-list --count --since=2026-10-10T20:53:07Z --until=2026-10-24T22:53:07+02:00 <tip>` - the tip is `df08cd4b`, its own committer time is 2026-10-24T22:53:07+02:00, and the window runs from exactly 14 days before that time to that time. Both ends are written instants, so the number does not move with the clock the command runs at. Earlier revisions printed 1324, 1323 and 1322 under a plain `--since=2026-10-10`, which git anchors at the hour of the run; those were three readings of one moving window, and that rule is withdrawn.
- The local `main` tree on this machine sat at `e35a8970` (2026-10-23), **57 commits behind** the tip, when this was read; it has since been brought to the tip. A reading taken from the working tree would therefore have been a reading of a state that no longer holds; the reading below was taken from an archive of `origin/main` (`git archive origin/main _grid4d`), so that the tree named above and the tree read are the same tree. Dates are read from git (`git log -1 --date=short origin/main -- <path>`), not from the filesystem.
- The local tree also carried one uncommitted modification, in a SubEpic ontology file. It is not mine, it is not part of the tip, and it is not in this reading.

## 2. The corpus

READ:

- **14** directories under `_grid4d/subepic/` at the tip: body, claude-code, collaboration, data, distribution, ha, llm, mcp, ml, oracle, pr, software, <enterprise-tool>cli, trust.
- A SubEpic may own: an identity document in its `story/` (named with the SubEpic's own prefix), issues (`issue/`), ideas (`idea/`), stories (`story/`, each as four documents: the story, `-tests`, `-knowledge-map`, `-artifact-map`), patterns (`pattern/`), ontology (`ontology/`) and implementation blueprints (`implementation/`).
- **SubEpic-owned issue and idea documents: 278** (166 in `issue/`, 112 in `idea/`). This is the population every per-SubEpic number below is counted over.
- Nine SubEpics own no `issue/` folder at all (data, ha, mcp, ml, oracle, pr, software, <enterprise-tool>cli, trust); four own neither `issue/` nor `idea/` (data, oracle, pr, <enterprise-tool>cli).
- For the contrast the root scope carries **410** issues and **177** ideas. Root numbers are given here only as the contrast; the root lane belongs to the work seat.
- The status field is a free-text field with no schema. Over the 278 SubEpic-owned documents the first word takes **14 distinct values**: open 168, resolved 63, realized 12, partially-resolved 5, closed 5, crystallized 5, converted 3, superseded 1, mitigated 1, fixed 1, narrowed 1, candidate 1, founding (snapshot) 1, idea 1 - and **10 documents carry no status field at all** (2 issue, 8 idea). I bucket by first word: the open bucket is open/candidate/idea/proposed/founding, the closed bucket is resolved/realized/partially-resolved/closed/crystallized/converted/superseded/mitigated/fixed/narrowed. `proposed` appears in no document of this 278 corpus; it is named here because the root scope uses it, and section 4 counts it there. Both buckets are printed in full above so a reader who would bucket "partially-resolved" or "narrowed" differently can re-bucket without re-reading the corpus.

## 3. Per-SubEpic census

READ. Columns: issue documents = total / open / closed / no status; the same for idea documents; stories = story documents in `story/` (identity document excluded) and the statuses they declare.

| SubEpic | issue n / open / closed / none | idea n / open / closed / none | stories in `story/` |
|---|---|---|---|
| evolucean-body | 7 / 7 / 0 / 0 | 6 / 6 / 0 / 0 | 2 (completed) |
| evolucean-claude-code | 6 / 5 / 1 / 0 | 1 / 1 / 0 / 0 | 2 (completed) |
| evolucean-collaboration | 143 / 70 / 71 / 2 | 75 / 53 / 19 / 3 | 2 (completed) |
| evolucean-data | - | - | 2 (completed) |
| evolucean-distribution | 4 / 1 / 3 / 0 | 7 / 3 / 0 / 4 | 2 (completed) |
| evolucean-ha | - | 3 / 2 / 0 / 1 | 2 (completed) |
| evolucean-llm | 6 / 6 / 0 / 0 | 8 / 7 / 1 / 0 | 3 (completed) |
| evolucean-mcp | - | 2 / 2 / 0 / 0 | 1 (completed) |
| evolucean-ml | - | 5 / 3 / 2 / 0 | 2 (completed) |
| evolucean-oracle | - | - | 1 (completed) |
| evolucean-pr | - | - | 0 |
| evolucean-software | - | 1 / 1 / 0 / 0 | 1 (completed) |
| evolucean-<enterprise-tool>cli | - | - | 8 (completed) |
| evolucean-trust | - | 4 / 4 / 0 / 0 | 2 (completed) |
| **total** | **166 / 89 / 75 / 2** | **112 / 82 / 22 / 8** | **30 (all completed)** |

READ, and the headline of the table: **171 of the 278 SubEpic-owned documents are open** (89 issue, 82 idea), 97 are closed (75 issue, 22 idea) and 10 declare no status. **`evolucean-collaboration` holds 123 of the 171** (72%) - 70 open issues and 53 open ideas, on an issue population of 143. No other SubEpic holds more than 7 open issue documents.

## 4. Priority - reported only where a document carries one

READ:

- Of the 278 SubEpic-owned documents **exactly 2 carry a `**Priority:**` field**, and **both are closed**: one claude-code issue (medium, resolved) and one collaboration issue (high, resolved); their stems are in the delivered list (section 8).
- Therefore **0 of the 171 open SubEpic-owned items carries a priority.** The lane reports no priority for the SubEpics not because none is high but because none is written: the field is not in use in this population. Priority exists at the root scope: 68 of the 185 open root issues carry one (medium 42, low 20, high 4, critical 1, and one value written out as free text - "low (zero production impact; baseline-run noise only)"), and 4 of the 132 open root ideas do (medium 3, high 1). The one `critical` is a root issue about plugged-in Epic content leaving its boundary; its stem is in the delivered list.
- So a reader who wants "the SubEpics' open work by priority" cannot have it from the documents: the only ordering available in this population is the document's own status text, and the SubEpic that would matter most by volume (collaboration, 123 open items) carries no priority on any of them.
- READ, and a reconciliation the synthesis will need: the root figures above are my reading under the bucketing rule of section 2. The root lane of this story, reading the same tree, bands "partially-resolved" separately from "resolved" and reports the same **185** open root issues; for ideas it reports **116** open where my open bucket gives **132**. The difference is my bucket adding the documents that say `proposed` (4), `candidate` (8) and `idea` (4), which the literal word "open" does not cover - leave the `proposed` clause out and the same rule gives **128**, so the two figures a reader may meet are 128 and 132, and section 2 names `proposed` so that 132 can be re-derived. Where the two readings differ it is the bucket, not the corpus: both count 410 issues and 177 ideas.

## 5. Open items - what the list says

READ. The full list of open SubEpic-owned items, by document stem, is delivered to the method's owners rather than carried here (section 8). Two things that list says:

- The collaboration SubEpic's open ideas carry the team's own working model (roles, escalation, seat identity, review loops) alongside mechanics; its open issues are mostly measurement and routing defects of the collaboration layer itself.
- The other SubEpics' open items are almost all about their own projections and documents - a body projection rendering seven of twelve systems, an llm connection-projection rework chain, claude-code hooks whose lineage never worked - i.e. the SubEpic layer's open work is largely the *lineage and projection* question that this very story AHA-0008 is about. INFERRED from reading titles; no count is claimed for it.

## 6. Stalled work

READ, last commit reachable from `origin/main` that touches the SubEpic directory:

| SubEpic | last commit touching it | date | what that commit is |
|---|---|---|---|
| evolucean-trust | `df08cd4b` | 2026-10-24 | its own story completion |
| evolucean-claude-code | `ab51d7e4` | 2026-10-24 | "chore: archive old stories to history/" - housekeeping |
| evolucean-collaboration, evolucean-data, evolucean-<enterprise-tool>cli | `5941d0a9` | 2026-10-23 | another SubEpic's docs commit |
| the remaining 9 SubEpics | `7df8c104` | 2026-10-23 | a cross-cutting documentation sweep |

READ, INFERRED in the classification: **9 of the 14 SubEpics were last touched by the same cross-cutting commit** `7df8c104` (2026-10-23), and three more by another SubEpic's docs commit. So the SubEpic knowledge folders' most recent change is, for 13 of 14, not work of that SubEpic.

READ, newest own issue/idea document per SubEpic (the population is that SubEpic's own `issue/` + `idea/` files):

| newest own document | SubEpic |
|---|---|
| 2026-10-08 | ml |
| 2026-10-11 | claude-code |
| 2026-10-16 | llm |
| 2026-10-21 | body |
| 2026-10-23 | collaboration, distribution, ha, mcp, software, trust |
| - (no own issue/idea document) | data, oracle, pr, <enterprise-tool>cli |

READ, story state: **every story document in every `subepic/*/story/` folder reads `completed`** - 30 story documents over 13 SubEpics (pr has none) and no story in flight at the tip. All 14 SubEpic identity documents carry an approval line dated 2026-10-23: twelve by the standard Contribution sentence, and pr and trust by their founding sentence, which records the same date while placing their founding in the story before that one.

READ, and a limit of this reading to state plainly: the three collaboration stories actually in flight on the two instances as I write this are on their own feature branches and are **not** at the tip, so a tip reading cannot show them. Their absence from this document is not evidence that they do not exist.

INFERRED: the Epic as a whole is not stalled - 1242 commits in the 14 days to the tip - while the SubEpic document folders are quiet: the last SubEpic-specific work in this window is `evolucean-trust` on 2026-10-24 and nothing the day after. Read together, the quiet is breadth of one sweep, not idleness of the Epic.

### Anomalies in the story folders (READ, named for the owners)

- `evolucean-<enterprise-tool>cli` keeps **8** story documents in `story/` and has **no** `history/` folder, while the 8 SubEpics that do have one archive down to 1 to 3 stories in `story/` (history counts, counted as story main documents in `history/` with the `-tests`, `-knowledge-map` and `-artifact-map` companions excluded: collaboration 79, body 27, llm 13, distribution 11, claude-code 5, software 5, data 3, ml 1). The root identity declares `StoryHistoryKeep: 2`; the SubEpic identities declare only `Type`, `Inherits` and `StoryPrefix`, so no SubEpic field is being violated - this is a measured difference in what the folders hold, not an assertion about which rule applies.
- The same folder mixes story-number widths: six stories numbered with three digits beside two numbered with four. The older six also differ in shape - they write their Epic link with the `.md` extension, where the newer two write it without - and only the newer two of the eight carry an `-artifact-map` document.
- `evolucean-pr` owns only its identity and a `pattern/` folder: no issue, no idea, no story of its own at the tip.

## 7. What ahabase depends on in the SubEpics

READ at the other side of the join: the ahabase tree at `d4436a799b14f9379f73b7307e2dd2bd09a4bf00` (this story's mint head), 58 markdown documents under `_grid4d/` plus `wiki.yml`.

READ, and stated because the branch has moved since: the lane branch stood at `c5172f9a69d282ecdad9d3562b1a14ed06d914bc` when this section was written, and its `_grid4d/` then held 62 markdown documents - the four added since the mint head are the three lane documents that landed before this one (ahabase state, evolucean root, plan realism) and the story's tests file. The branch has moved again since; none of those added documents changes any count or claim in this section, which was read at the mint head named above.

- **The declared dependency is on the evolucean Epic, not on any SubEpic.** The ahabase identity carries `**Inherits:** evolucean`, and it is the only structural dependency line in the whole tree.
- **No document of the ahabase tree declares a dependency on any SubEpic** - neither by naming one in a dependency position nor by linking a SubEpic document. Measured over all 58 documents, the tokens that name evolucean objects are four, in fourteen occurrences: one SubEpic story id (once in each of 7 `-artifact-map` documents); one SubEpic name (5 occurrences, all in the released AHA-0001 story and its tests, one of them a markdown link); a second SubEpic story id (once, in AHA-0001, as plain text naming a SubEpic story that "comes next"); and a SubEpic-prefixed file name (once, in the changed-file list of an archived artifact map). The four tokens are in the delivered list (section 8).
- **Where those mentions come from matters.** The generated "Parallel session window" blockquote, which every artifact map carries, names one evolucean story id and one evolucean issue (both in the delivered list) and describes itself as the lines the instance-wide snapshot diff carries from the story's window but not owned by it - context, not blast radius. Seven of the fourteen occurrences are that line. The path list printed under it in one archived artifact map accounts for one more: a file name carrying a SubEpic prefix, listed among lines the snapshot diff carried but the story did not own - the fourth token. So the SubEpic-attributed text inside the ahabase tree arrives through the artifact-map generator; it is neither a dependency nor anything maintainable by hand. The remaining six occurrences are in the released AHA-0001 story and its tests: five of one SubEpic identity name (one of them a markdown link) and one plain-text mention of a second SubEpic story id. AHA-0001 is a released story - the identity's rule says released stories keep their text - and it calls that SubEpic "a parallel story".
- **What ahabase actually uses from the closed side** (READ, occurrence counts over the same 58 documents): `knowledge-usage` 18, `knowledge-usage-cli` 13 - the story workflow tool, pinned in AHA-0006's and AHA-0007's tests as an absolute path into `~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/`; `grid4d` 8 - the format; and 1 - the name of the story-pattern document the ahabase identity declares in its `**StoryPattern:**` line, which exists as a pattern document at the tip on the evolucean side. The tool is the Epic root's artefact; the machine layer around it is `evolucean-distribution`'s.

**The honest answer to the lane's question:** nothing in ahabase declares a dependency on a SubEpic, and the SubEpic-attributed text that is there is generator output plus one released link. The dependencies that would have to move for the inheritance to turn - the story workflow, the format, the story pattern - are held by the evolucean **Epic root** and by `evolucean-distribution`, not spread across the SubEpics. INFERRED, and stated as a limit: I did **not** measure the overlap between ahabase's ontology and the SubEpics' ontologies; that is a two-tree concept reading and belongs to the transparency lane, and I claim no count for it.

## 8. Where the item list went

The list of every open SubEpic-owned item by document stem - the evidence behind the counts in sections 3, 4, 5 and 6 - is **not carried in this document**, because it names closed-zone documents and the ahabase identity's rule forbids that here. It was delivered to the method's owners through the home coordinator (chat row 3362, 2026-10-26), together with the story ids and document paths that this revision removes. v1 carried it as this section's appendix.

Every count in this document can still be checked against that list - 278 SubEpic-owned documents, 171 open, 97 closed, 10 without status, 123 of the open ones in evolucean-collaboration. The check moved with the list; it did not disappear. One further closed-zone name - the SubEpic-prefixed worktree file name that is section 7's fourth token - was not part of that delivery; it went to the same owners in a supplementary row.

## 9. What I would route to the evolucean owners

INFERRED - these are readings of the state, not defects I can prove, and per R_docs they belong to the evolucean owners as issues sent through the team, not written into the closed zone from here. Each names the population it rests on.

1. **The SubEpic issue and idea folders do not use priority.** 0 of 171 open SubEpic-owned items carries the field; at the root scope 68 of 185 open issues do. If prioritisation is wanted at SubEpic level, it is not being written - and `evolucean-collaboration`, with 123 of the 171 open items, is the population where its absence costs most.
2. **`evolucean-<enterprise-tool>cli`'s story folder holds 8 completed stories and no `history/` archive**, where the 8 SubEpics that have a `history/` folder keep 1 to 3 stories in `story/`; the same folder mixes three- and four-digit story numbering and only its two newest stories carry an artifact map. Measured difference, offered for the owners to rule on rather than asserted as a rule violation.
3. **The artifact-map "Parallel session window" line carries a foreign Epic's story id and issue name into a public Epic's documents** (an evolucean story id and an evolucean issue name, in 7 of the ahabase tree's artifact maps, and - in one archived map - the path of a SubEpic-prefixed worktree file, in the list of lines the snapshot diff carried but the story did not own; all in the delivered list). The receiving end is already logged in ahabase as `open-zone-documents-link-into-the-closed-zone`; this is the emitting end, and it will keep crossing the boundary after that issue is fixed if only the receiving end is treated.
4. **Four SubEpics capture nothing in issue or idea form** - data, oracle, pr and <enterprise-tool>cli. For oracle and pr that may be right (one story, none). `evolucean-<enterprise-tool>cli` has completed 8 stories and no issue document at all; either it met no defect in eight stories, or defects met there are not being written where this lane could find them.
5. **The SubEpic layer's own open work is disproportionately about lineage and projections** (titles about a body projection rendering seven of twelve systems, an llm connection-projection rework chain, empty collaboration SubEpic projections, and claude-code hooks whose lineage never worked). INFERRED from titles, no count claimed - but it is the same subject as this story's transparency lane, met from the other side, which suggests the two should be read together in the synthesis rather than as separate workstreams.

## 10. Limits of this reading

- **Static only.** No code was executed and no behaviour was observed; everything above is what the files say at the named commit.
- **The tip is 2026-10-24 22:53:07 +0200.** Anything merged after it, including the stories now in flight, is outside this reading.
- **The partition is by location.** Root documents carry no SubEpic field, so a root item's SubEpic cannot be read - only guessed from its name prefix. I therefore do not add root items to any per-SubEpic number. (For the record as an INFERRED secondary view: of the 185 open root issues, 8 start with `collab-`, 5 with `llm-`, 2 with `containment-`, 2 with `distribution-`, 1 with `oracle-`, 1 with `<enterprise-tool>-`, and 166 carry no SubEpic-like prefix at all - the 19 plus the 166 is the 185; of the 132 open root ideas, 12 carry such a prefix and 120 do not. This is naming, not attribution.)
- **Status is a free vocabulary** of 14 first-word values plus 10 documents with no status; my bucketing rule is printed in section 2 so it can be redone.
- **I did not measure whether any open item is already fixed in code.** That is a code reading against a pin, not a document reading, and it was not this lane.

## 11. How this lane's output was delivered

Offered a choice of route, I send this document in chat for the writer to commit rather than pushing it to the branch myself. The reason is a limit of my seat, not a judgement of the branch: pushing from here needs the embedded credential, whose exposure is still an open Human decision on my side, and my seat is read-only on repository files. Delivered in chat with the sha256 and byte count of the exact text, so the committed file can be verified byte-for-byte against what I wrote, and with a copy to the home coordinator. Revisions 2 to 5 (the closed-zone name cut, the verdict-4 repairs, the past-tense corrections and the count anchor) travel the same way; the names v2 removed went to the method's owners through the home coordinator in a separate row (3362), and section 7's fourth token followed in a supplementary row.

- seat `656cf2f6`, read-only
