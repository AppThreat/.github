# callsites for Java source, JVM bytecode and Android

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/307 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

**Java source (javasrc2cpg).** `usages` finds a median 0.46 of external use sites on four Java
projects (mall: 0.18) because it is declaration-shaped: it reports objects that have calls, not every
external call. A measurement prototype that reads resolved calls, constructors, annotations and
heritage reaches 0.64–0.93 recall at 0.98–1.00 precision (mall 0.87 / 0.998, petclinic 0.93 /
0.995). The misses and errors come from the frontend:

- `@Override` resolved as `javax.websocket.Override` or `javax.servlet.Override`: the
  single-wildcard-import guess beats `java.lang`;
- calls in static field initialisers are missing (`private static final Logger log =
  LoggerFactory.getLogger(X.class)`);
- chained calls on external return types stay unresolved (Spring Security and Swagger builders);
- parameter annotations (`@RequestParam`, `@RequestBody`) are missing or unnamed;
- method references (`StringUtils::trim`) are resolved `METHOD_REF` nodes that no slice reads;
- Lombok-generated members (`log` from `@Slf4j`) are unresolved without delombok;
- Java type recovery is never run (`JavaSrc2Cpg.typeRecoveryPasses` has no callers).

**JARs (Kotlin, Scala bytecode) and Android (jimple2cpg).** Against a bytecode oracle (`javap` /
`dexdump` instruction owners and line tables) on four F-Droid APKs and three jars:

| input | usages R | prototype R / P |
| --- | ---: | ---: |
| termux-api, termux, NewPipe, AppManager (APK) | 0.00–0.004 | 0.83–0.99 / 1.00 |
| detekt-formatting (Kotlin jar) | 0.57 | 0.99 / 1.00 |
| two Scala 2.13/3 apps | 0.86–0.88 | 0.97–1.00 / 1.00 |

- `usages` reports almost no library calls in APKs although the graph has them (termux-api: 20,639
  `androidx.*` calls).
- Bundled libraries are application code to jimple2cpg (termux-api: 41,506 internal methods for 398
  app classes), so external cannot be read from `isExternal`; the app boundary must come from the
  manifest package, the BOM or an explicit prefix list.
- Inherited library members called through an app subclass are named on the app class
  (AppManager: 872 `androidx.fragment` sites such as `Fragment.startActivity`).
- R8 line compaction makes line tables synthetic (NewPipe), so line-level matching degrades to file
  level; `invokedynamic` string concatenation appears as `soot.dummy.InvokeDynamic`.
- `--android-sdk` needs the `android.jar` file, not the platform directory; AppManager needs 12.7 GB
  and 216 s for usages, writing a 398 MB slice.
- Jar inputs name a temporary path or a class name instead of a source file.

## Scope

javasrc2cpg and jimple2cpg in chen, Java and bytecode `CallSiteSource`s in atom. Kotlin and Scala
sources have no atom frontend; they are covered through their bytecode (cdxgen's kosi and scalasem
plugins cover sources).

## Deliverables

### D1. javasrc2cpg resolution fixes (chen)

java.lang before wildcard guesses; static field initialisers; return types of external methods
through the fetched dependency jars; parameter annotations with full names; Lombok and other
generated members modelled, or delombok by default (generated code counts, decision 0001); wire Java type recovery in if it measurably helps, else delete it. Twins for
each.

### D2. Java source adapter (atom)

Calls, constructors, annotations, heritage, static field reads, class literals and method references
whose class is not a project TYPE_DECL. `module` = class FQN. Done at ≥ 0.92 recall, ≥ 0.98
precision on the Java corpus.

### D3. Application boundary for bytecode (atom, chen)

App packages from the APK manifest, the input jar's manifest, the BOM, or `--app-prefix`; library
classes inside an APK or fat jar are dependencies. Done when termux-api's slice has no androidx
method as project code.

### D4. Bytecode adapter (atom)

Owner classes outside the app boundary, walking the class hierarchy for inherited library members;
method handles and `invokedynamic` targets; real source file names for jar inputs (from the
`SourceFile` attribute and package). Done at ≥ 0.95 recall on the APK and jar corpus.

### D5. Android specifics (atom, chen)

`--android-sdk` accepts the platform directory; synthetic (R8) line tables are detected and
reported, and records fall back to method-level positions; memory and slice size on large APKs.

### D6. Class → artifact mapping (atom)

From the fetched jars (javasrc) or the APK's `META-INF/*.version` and `pom.properties` files, so
records can carry `purl`.

## Risks and open questions

- Obfuscated APKs (R8 renaming) cannot be attributed beyond package prefixes that survive; records
  for renamed owners are uncertain.
- Kotlin inline functions and coroutines leave no call to the library in bytecode; those uses are
  invisible to any bytecode slice.
- Shaded and relocated classes (`org.apache.http.shaded…`) belong to the jar that shades them.
- Java truth for multi-module projects needs the projects' builds (risks B1).
