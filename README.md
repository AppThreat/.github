<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="profile/AppThreat_Emblem_NoBorder_DarkTheme_v01_R01-01.png">
    <img src="profile/AppThreat_Emblem_NoBorder_LightTheme_v01_R01-01.png" width="130" alt="AppThreat">
  </picture>
</p>

# AppThreat

## Open Security Intelligence

Most security findings never matter in your code. We build two orchestrators that find the ones that do: [chennai](https://github.com/AppThreat/chennai) proves which risks are real in your code and binaries, and [dep-scan](https://github.com/owasp-dep-scan/dep-scan) shows what your dependencies expose you to and what to fix first. Both, and every toolkit behind them, are free and open source under permissive licenses such as MIT and Apache-2.0.

## chennai

Trace untrusted input from where it enters to where it is used, across your code and your dependencies, and get findings backed by paths you can check yourself. An optional AI agent does the legwork, and every claim it makes must survive the same proof. Runs offline, on your machine.

- [atom](https://github.com/AppThreat/atom) turns a whole codebase into a queryable map of calls and data flows, so "is this weakness reachable" gets an answer instead of a guess. Built on the [chen](https://github.com/AppThreat/chen) analysis library.
- [blint](https://github.com/owasp-dep-scan/blint) tells you what a shipped executable, Android, or iOS app contains and can do, without ever running it. [multi-demangle](https://github.com/AppThreat/multi-demangle) restores readable symbol names, and [blint-db](https://github.com/AppThreat/blint-db) recognizes components inside stripped binaries.
- [dosai](https://github.com/owasp-dep-scan/dosai) delivers the same evidence for .NET, whether you have the source or only the assemblies.

## dep-scan

Point it at a project or a container image and get a ranked risk report: every component inventoried, every known vulnerability and license conflict surfaced, and a clear order for what to upgrade first. It also writes the paperwork auditors ask for, VDR and CSAF VEX documents, so the same scan feeds both the fix list and the EU Cyber Resilience Act file. Runs offline against your own copy of the data.

- [cdxgen](https://github.com/cdxgen/cdxgen) is the software transparency toolchain behind the inventory: bills of materials for applications, containers, and operating systems, crypto bills, and signed, attestable output. It inventories AI systems as AI-BOMs covering models, prompts, and MCP tools, publishes and fetches BOMs over the Transparency Exchange protocol, and validates a BOM against CRA requirements.
- [cdxgen-plugins-bin](https://github.com/cdxgen/cdxgen-plugins-bin) adds the golem, rusi, and kosi slicers, which show which parts of a dependency your program actually exercises.
- [caxa](https://github.com/cdxgen/caxa) packages everything into standalone executables, and [safer-exec](https://github.com/cdxgen/safer-exec) is our upcoming sandbox for safely running untrusted commands and seeing exactly what they open, load, and talk to.
- [vulnerability-db](https://github.com/AppThreat/vulnerability-db) merges every advisory from NVD, OSV, GitHub, and the Linux distributions into one offline database you own.

## Services

Beyond the tools, we take on custom security tool development, architecture reviews and security assessments, product security risk work, and hands-on training in code analysis and secure coding.

## Contact

Write to [hello@appthreat.com](mailto:hello@appthreat.com) or visit [www.appthreat.com](https://www.appthreat.com/).
