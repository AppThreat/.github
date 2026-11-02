# SootUp upstream work for the migration

| | |
| --- | --- |
| Epic | AppThreat/chen (opened with this plan) |
| Owner | @prabhu |
| AI use | Assist: agents prepare reproducers and patches; a maintainer files and signs off what goes upstream |
| Corpus | [sootup.corpus.json](sootup.corpus.json) |

## Why

The migration depends on fixes that are on SootUp's develop branch but not released, and on fixes
nobody has made yet. Fixing them in SootUp helps everyone who uses it, and costs less over time
than patching around them in chen. SootUp is LGPL-2.1, actively developed (develop is 485 commits
ahead of 3.0.1), and has 140 open issues.

## Scope

Issues and pull requests to soot-oss/SootUp, and the build of SootUp chen depends on. Patching
SootUp's sources inside chen is out of scope; a workaround in chen is allowed only with an upstream
issue linked in the code.

## Deliverables

### D1. Report what the spike found

With a minimal input and the IR probe output for each:

- DEX line numbers attributed to the wrong statements on R8-optimised dex (verified against
  `dexdump` on NewPipe), if the develop build still shows it.
- DEX locals typed `unknown` with the default dex interceptors, and `this` typed `java.lang.Object`
  once `TypeAssigner` runs.
- Half of the debug-info local names lost on NewPipe.
- In 3.0.1, a broken control flow graph makes `BlockGraphIterator.hasNext` build a debugging URL
  that iterates the same graph again, which recurses until the stack overflows (gone in the
  2026-10-08 snapshot; reported only if develop still has it).

### D2. A release with the October fixes

Ask for a release that contains the fixes the migration needs: PRs #1763, #1767, #1746, #1754,
#1755, #1787, #1788 and the dex fixes #1776, #1836, #1845, #1849. If none appears before the jvm
plan's D4 starts, publish a build of a pinned develop commit to AppThreat's GitHub Packages (the
overview's first decision), with the commit id in the version and the LGPL notice.

### D3. A JDK location that does not scan the JDK

`ViewTypeHierarchy` loads every class of every input location. Propose a way to mark a location as
resolve-on-demand (or to scope the hierarchy to Application locations plus what they reference),
with the scala-steward numbers: more than 1 GB of heap with the JDK, 512 MB without.

### D4. Native-image friendly JDK access

`JrtFileSystemAnalysisInputLocation` opens jrt:/ in a static initialiser, which fails in a GraalVM
native image. Propose a lazily opened file system, or a location over a JDK home's `lib/modules`.

### D5. dexlib2

SootUp's APK frontend uses `org.smali:dexlib2` 2.5.2 (archived). Offer the move to
`com.android.tools.smali:smali-dexlib2` 3.x, which Soot already uses (issue #1810).

## Risks and open questions

- Upstream review takes time; every deliverable has a chen-side workaround so the migration does not
  wait on a merge.
- Public issues must not include the corpus APKs; reproducers are built from sources written for
  the purpose.

## Outcome

Filled in when the work ends.
