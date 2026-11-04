# HTTP responses: status codes for every web handler atom recognises

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/372 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | Entries of [callsites-corpus.corpus.json](callsites-corpus.corpus.json), listed under "How work is checked" |

## Why

The OpenAPI documents that atom-tools builds from atom's usages slice list one response per
operation. The status is guessed from the HTTP verb (GET 200, POST 201, DELETE 204) and, for Spring
only, from the names of `ResponseEntity` builder calls. AppThreat/atom#244 proposed scanning each
controller method for `HttpStatus.X` field accesses inside the usages slicer, so that atom-tools
could list the other codes. The idea is right. The codes a handler can return are part of its
contract, they matter for API inventories and for security review (which endpoints answer 401 or
403 at all), and the graph already holds what is needed to recover them.

The pull request itself should not be merged. Evaluated on current code, it has four problems:

1. It reports nothing on today's javasrc2cpg. The query filters `<operator>.fieldAccess` calls by
   `methodFullName(".*HttpStatus.*")`, but those calls carry `methodFullName` =
   `<operator>.fieldAccess`.
2. Its earlier form (any field access whose argument names `HttpStatus`) reports every constant
   that appears in a handler, including comparisons such as
   `r.getStatusCode() == HttpStatus.SERVICE_UNAVAILABLE` on a downstream response. A handler that
   only checks a remote status would be documented as returning 503.
3. It runs per declaration inside the usages slicer, the cost the review warned about, and it ties
   the feature to `usages`, whose future is being decided in AppThreat/atom#344.
4. It covers one framework of one language, while the same question applies to every framework
   that atom tags routes for.

To measure where things stand, small applications were written for five languages (about 70
handlers, each application with a client-side twin that reads statuses without sending them) and
run through atom `feat/callsites-tranche8` (afa681a), chen main (d72616a), atom-parsetools main
(1128009, version 2.0.0) and atom-tools main (a98798b):

| Language and frameworks | Endpoints found | Status recall | Status precision |
| --- | --- | --- | --- |
| Java: Spring, JAX-RS, Micronaut, servlet | 8 of 15 | 0.18 | 0.62 |
| JavaScript/TypeScript: Express, Koa, Fastify, NestJS, Next.js, Hono | 7 of 16 | 0.00 | none reported |
| Python: Flask, flask-restx, FastAPI, Django, DRF | 8 of 14 | 0.00 | none reported |
| PHP: Laravel, Symfony, Slim | atom-tools rejects `-t php` | | |
| Ruby: Rails, Sinatra | 0 of 7 | 0.00 | none reported |

The five Java hits are verb defaults that happen to match. The evaluation also showed that the
handler itself is often not identified, so there is nothing to attach a status to:

- chen's JavaScript route pattern (`JsRoutesCallPattern` in `ChennaiTagsPass`) is compiled without
  `DOTALL` and matched against the call's `code`, so a route registration that spans more than one
  line, the usual shape with an inline handler, is never tagged. 4 of the 11 Express, Koa, Fastify
  and Hono routes in the fixture are tagged.
- Apart from NestJS controllers and Next.js route files, no JavaScript handler function gets
  `framework-route`, and none gets `route-path` or `http-method`.
- Flask and FastAPI handlers carry `route-path`; Django views do not, and no Python handler
  carries `http-method`.
- Laravel and Rails controller actions are not tagged as handlers at all, because their routes are
  declared in `routes/*.php` and `config/routes.rb`. Symfony actions are tagged but have no
  `route-path`.
- Micronaut handlers have no `route-path` or `http-method`; servlet `doGet`/`doPost` have no
  `http-method`.
- `atom usages -l javascript --extract-endpoints` fails with "No language frontend supported for
  language ''". `--extract-endpoints`, `--include-source` and `--min-num-calls` rebuild the config
  with `copy`, which resets a `-l` given before them. The same trap was fixed for `memory-safety`.

## Scope

In scope: Java source (Spring MVC and WebFlux annotations, JAX-RS and Jakarta REST, Micronaut,
servlets), JVM bytecode where the Java recognisers apply to `-l jar`, JavaScript and TypeScript
(Express, Koa, Fastify, NestJS, Next.js route handlers, Hono), Python (Flask, flask-restx, FastAPI
and Starlette, Django, Django REST framework, aiohttp), PHP (Laravel, Symfony, Slim) and Ruby
(Rails, Sinatra). For each framework the work identifies the handler, records the route path and
verb where the framework states them, and records the status codes the handler can produce
together with the code that produces each one.

Out of scope: response bodies and schemas (atom-tools already derives DTO names for Java), headers
and media types, and Scala, whose endpoints come from scalasem's rules in atom-parsetools; adding
statuses there is a separate change to plan after this one. Go, Rust, Kotlin and C# are not parsed
by atom. cdxgen and dep-scan are not changed, since the CycloneDX service model has no field for
status codes. A status thrown more than two calls below the handler, or computed from data the
analysis cannot resolve, is recorded as unresolved rather than guessed.

## Approach

### Where the work happens

Recognition happens once, in chen's framework taggers, when the graph is built. atom only reads
tags. This keeps the cost out of the slicers, where #244 put it, and gives one result to every
consumer: the usages slice today, and whatever carries OpenAPI support after #344 is decided. Each
language's response recogniser lives in its own file, so the language deliverables can be worked
on in parallel without touching the same code.

### Vocabulary

Key/value tags, following the existing `route-path` and `http-method`:

- `http-status` = `404`: a status the handler sets or returns in code. It goes on the handler
  METHOD (one tag per distinct code) and on the node that produces it: the call, the annotation's
  literal, the return or the assignment.
- `http-status-exception` = `404`: produced by an exception that the framework maps to a status.
- `http-status-documented` = `404`: declared in a decorator or schema (`responses={404: ...}`,
  `@ns.response(404)`, Fastify `schema.response`, `@ApiResponse(responseCode = "404")`), whether
  or not the code sets it.
- `http-status-implicit` = `200`: the framework's default when the handler returns normally
  without setting a status (see the table below).
- `http-status-dynamic` on a site whose status is computed and cannot be resolved.
  `res.status(err.status || 500)` gives `http-status` 500 and `http-status-dynamic`.

Global error handlers (Spring `@ExceptionHandler` in a `@ControllerAdvice`, Flask
`errorhandler`, FastAPI `exception_handler`, Express four-argument middleware, Rails `rescue_from`)
get the same tags on their own method, plus `http-error-handler` = the handled exception type.
atom links them to handlers (see Output), because the link needs the exception types that a
handler can throw.

### Status names

One table in x2cpg maps names to codes: the IANA status registry, in the spellings frameworks use
(`NOT_FOUND`, `NotFound`, `notFound`, `not_found`, `:not_found`, `HTTP_404_NOT_FOUND`,
`SC_NOT_FOUND`, `HTTP_NOT_FOUND`, `HttpStatusCode.valueOf(404)`) and integer literals from 100 to
599. The table is consulted only after a framework recogniser has decided that a value sits in a
status position. It never makes that decision itself.

### Precision rule

A value counts only where a recognised response API puts a status:

- a known argument position or keyword of a known call (`res.status(...)`,
  `ResponseEntity.status(...)`, `abort(...)`, `HTTPException(status_code=...)`,
  `render ..., status:`);
- a builder whose name is a status (`ResponseEntity.notFound()`, `Response.noContent()`,
  `HttpResponse.notFound()`, `c.notFound()`);
- a known annotation or decorator member (`@ResponseStatus`, `@HttpCode`, `@Status`,
  `status_code=`);
- a framework return shape (Flask `return body, 201`, a Rack triple);
- an assignment to a known status property (Koa `ctx.status = 201`);
- a mapped exception.

A constant that is only compared, switched on, logged or passed somewhere else is not a status.
Every fixture has a twin that reads statuses without sending them, and nothing may be reported for
it.

### Resolving values

Literals and known constants resolve directly. An identifier resolves through its reaching
definitions in the same method, and a conditional or `||` contributes each branch that resolves
(`full ? HttpStatus.OK : HttpStatus.PARTIAL_CONTENT` gives 200 and 206). Module-level constants
resolve one hop (`const GONE = 410`). Anything else is `http-status-dynamic`.

### Attributing a site to a handler

A site belongs to the handler whose body contains it, including lambdas and closures defined in
that body (`orElseThrow(() -> new UserNotFoundException(id))`). It also belongs to the handler when
it sits in a project method that the handler calls, up to two calls deep, if that method receives
the response object (`sendError(res, 404)`) or returns a response type (a private `badRequest(...)`
that returns `ResponseEntity`). When a handler is registered through a wrapper
(`catchAsync(async (req, res) => ...)`, `asyncHandler(fn)`), the function argument is the handler.
Each attribution records how it was reached (`direct`, `lambda`, `helper` or `wrapper`), so a
consumer can filter. The response object is found by its position in the handler's signature, not
by its name (`res`, `reply`, `ctx` and `c` are conventions only).

### Implicit defaults

| Framework | Normal return | Replaced by |
| --- | --- | --- |
| Spring MVC and WebFlux | 200 | `@ResponseStatus` on the method |
| JAX-RS | 200 with an entity, 204 for `void` or `null` | |
| Micronaut | 200 | `@Status` |
| Servlet | 200 | |
| Express, Koa, Fastify, Hono | 200 | `res.redirect` gives 302 |
| NestJS | 200, and 201 for POST | `@HttpCode` |
| Next.js route handlers | 200 | |
| Flask, Django, Django REST framework, aiohttp | 200 | |
| FastAPI | 200 | decorator `status_code` |
| Laravel, Symfony, Slim | 200 | `redirect()` gives 302 |
| Rails | 200 when it renders; 204 when an API controller renders nothing | `redirect_to` gives 302 |
| Sinatra | 200 | `redirect` gives 302 |

The implicit status is recorded only where the default can apply: the handler's return type does
not carry a status (`ResponseEntity`, JAX-RS `Response` and Micronaut `HttpResponse` do), and, in
untyped languages, at least one body-sending call or return sets none. The table records the
framework version each row was checked against.

### Output

atom adds an `endpoints` array at the top level of the usages slice. It is written only when the
atom has handlers, so the slice for a project without handlers stays the same byte for byte. One
record per handler:

```json
{
  "handler": "com.example.spring.UserController.get:org.springframework.http.ResponseEntity(java.lang.String)",
  "fileName": "src/main/java/com/example/spring/UserController.java",
  "lineNumber": 20,
  "httpMethods": ["GET"],
  "routePaths": ["/users/{id}"],
  "responses": [
    {"status": "200", "kind": "explicit", "via": "direct", "lineNumber": 26, "code": "ResponseEntity.ok(u.get())"},
    {"status": "404", "kind": "explicit", "via": "direct", "lineNumber": 24, "code": "ResponseEntity.notFound()"}
  ]
}
```

`kind` is one of `explicit`, `exception`, `documented`, `implicit`, `advice` and `dynamic`. Advice
entries come from global error handlers: Spring advice and Rails `rescue_from` are matched by the
exception types the handler can throw, while Express error middleware and Flask
`errorhandler(404)` apply to every handler registered on the same application. The array is built
from tags in one pass over the methods tagged `framework-route`, with no per-declaration queries.
The record shape goes into `specification/atom.proto`, the generated `UsageSlice.json` schema and
the bindings.

The section depends on tags, not on the object slices in usages. If #344 retires usages, the same
records move to the command that keeps OpenAPI support, and #344's decision should say so.

### atom-tools

When `endpoints` is present, atom-tools takes paths and verbs from `routePaths` and `httpMethods`
(which also gives Spring paths their class prefix, AppThreat/atom#143) and responses from
`responses`, and stops guessing statuses by verb for those operations. Each response keeps its
evidence (kind, via, file and line) in an `x-atom-responses` extension. Older slices keep today's
behaviour, and `php` becomes an accepted origin type.

## Deliverables

The deliverables are tracked as rows of the table in the epic rather than as sub-issues. D1 and D2
come first. D3 to D7 can then run in parallel, one per language. D8 can start once D3 has landed,
D9 follows D8, and D10 closes the work.

### D1. Two bugs found during the evaluation

chen: route registrations that span lines are tagged (match the callee name and receiver rather
than the whole `code`, or compile the pattern with `DOTALL`), with a test for a multi-line Express
route. This changes route tags on JavaScript projects, and the pull request lists the change per
corpus project. atom: the `usages` options that use `copy` keep `-l`, `--with-data-deps` and the
output paths, with a CLI test that passes `-l` before each of them. Done when both tests pass and
`atom usages -l javascript --extract-endpoints` works with the options in either order.

### D2. Shared core in x2cpg

The status-name table, the value resolver, handler attribution (lambda, helper, wrapper, depth
two), the tag names, and a test helper that reads a fixture's expected-responses file and compares
it with the tags. Done when unit tests cover every spelling in the table, every attribution path
including a negative case just beyond depth two, and the resolver's conditional and module-constant
cases.

### D3. Java and JVM bytecode

Handlers: `route-path` and `http-method` for Micronaut, and `http-method` for servlets from the
`doGet`/`doPost` names (Spring and JAX-RS are complete). Responses: Spring (`ResponseEntity`
builders and constructor, `status(...)` with an enum, an integer or `HttpStatusCode.valueOf`,
`@ResponseStatus` on methods and on exception classes, `ResponseStatusException`,
`@ExceptionHandler` in `@ControllerAdvice`), JAX-RS (`Response` builders and `Response.Status`,
`WebApplicationException` with an integer or a status, the `jakarta.ws.rs` and `javax.ws.rs`
exception subclasses), Micronaut (`HttpResponse` builders, `@Status`), servlets (`setStatus`,
`sendError`, `sendRedirect`, `SC_*` constants) and springdoc or Swagger `@ApiResponse` as
documented. Done when the Java fixture matches its expected file, and the same fixture compiled to
a jar gives the same responses with `-l jar`, or the differences are listed with their cause.

### D4. JavaScript and TypeScript

Handlers: route registrations are linked to the handler function, whether it is inline, a named
function, an imported member (`authController.register`) or a wrapper argument, including
`router.route('/x').get(...).post(...)` chains and mount prefixes (`app.use('/api', router)`).
The handler gets `framework-route`, `route-path` and `http-method`. Responses: Express
(`res.status`, `res.sendStatus`, `res.redirect`, `next(createError(n))`), the `http-status` and
`http-status-codes` constants, Koa (`ctx.status =`, `ctx.throw`), Fastify (`reply.code`,
`reply.status`, `schema.response` as documented), NestJS (`@HttpCode`, the built-in `*Exception`
classes, `HttpException(..., HttpStatus.X)`), Next.js (`NextResponse.json(..., {status})`,
`new Response(..., {status})`, `NextResponse.redirect`), Hono (`c.json`, `c.text` and `c.body`
with a status, `c.notFound()`), and project error classes whose constructor takes a status
(`new ApiError(httpStatus.NOT_FOUND, ...)`). Done when the JavaScript fixture matches, and the
node-express-boilerplate handlers registered through `catchAsync` are found with their statuses.

### D5. Python

Handlers: `http-method` for every recognised framework (decorator verb, `methods=[...]`,
`require_http_methods`, `@api_view([...])`, and method names on flask-restx resources and
`MethodView`), and `route-path` for Django views from `urls.py` (with `include()` prefixes) and for
flask-restx resources. Responses: Flask (`abort`, tuple returns, `make_response`,
`Response(status=...)`), flask-restx (`api.abort`, `@ns.response` as documented), FastAPI and
Starlette (decorator `status_code`, `responses={...}` as documented, `HTTPException`,
`JSONResponse` and `Response` with `status_code`, `status.HTTP_*`), Django (`HttpResponse` and its
subclasses, `status=`, `Http404`, `PermissionDenied`, `get_object_or_404`), Django REST framework
(`Response(status=...)`, `status.HTTP_*`, `APIException` subclasses) and aiohttp
(`web.json_response(status=...)`, the `web.HTTP*` exceptions). Done when the Python fixture
matches.

### D6. PHP

Handlers: Laravel route files (`Route::get('/x', [Controller::class, 'm'])`, `'Controller@m'`,
`Route::resource`, group prefixes) mark the controller method as the handler with `route-path` and
`http-method`; Symfony `#[Route]` gives the path and `methods:`, with a class-level prefix composed
as for Spring. Responses: Laravel (`abort`, `abort_if`, `abort_unless`,
`response()->json($data, n)`, `response($data, n)`, `->noContent()`, `->setStatusCode()`,
`findOrFail` as 404), Symfony (`new Response` or `new JsonResponse` with a status,
`$this->json($data, n)`, `Response::HTTP_*`, `createNotFoundException`,
`createAccessDeniedException`, `HttpException` subclasses) and Slim and PSR-7 (`withStatus`).
php2atom resolves an unqualified Laravel helper to the controller's namespace
(`App\Http\Controllers\abort`) when it cannot find the function, so the recogniser matches the last
name segment when the project defines no function of that name. Done when the PHP fixture matches.

### D7. Ruby

Handlers: Rails actions are the public methods of a class that inherits from `ApplicationController`,
`ActionController::Base` or `ActionController::API`, and `config/routes.rb` gives `route-path` and
`http-method` (`resources`, `resource`, `get 'x', to: 'c#a'`, `namespace`, `scope`). Sinatra
blocks already carry `framework-route` and get `route-path` and `http-method`. Responses: Rails
(`render ... status:` with a symbol or an integer, `head :symbol`, `redirect_to`, `rescue_from ...
with:` applied to that controller's actions, `ActiveRecord::RecordNotFound` as 404) and Sinatra
(`status n`, `halt n`, `error n`, a Rack triple as the block's value, `redirect`). Rails symbols
map through Rack's status symbol table. Done when the Ruby fixture matches.

### D8. atom output

The `endpoints` section, the proto, schema and bindings, the docs (`docs/docs/slicing.md` and the
usages lesson), tests on every language fixture, and an equivalence test showing that the slices
of projects without handlers are byte-identical to main. Done when every fixture's `endpoints`
matches its expected file.

### D9. atom-tools

Read `endpoints`, accept `php`, stop verb guessing where atom states the responses, keep older
slices working, and test with slices recorded from D8. Done when every endpoint in the fixtures is
found and the status pairs score recall of at least 0.95 and precision of 1.0.

### D10. Corpus check and performance

For each corpus project, a hand-checked sample of 20 handlers (or all of them, when there are
fewer) with their expected statuses, scored for recall and precision, and the tagging time measured
before and after. Done when precision is at least 0.98 for every language, and the tagging phase is
at most 5% slower on juice-shop, DefectDojo, mastodon and spring-petclinic.

## How work is checked

The gates are the ones in [callsites-overview.md](callsites-overview.md): tests with bad and good
twins, a mutation table in every pull request (removing a recogniser branch must fail a test), and
equivalence tests wherever output must not change. The route-tag changes from D1 and from the
handler parts of D3 to D7 are intended, and each pull request lists them per corpus project.

Fixtures: one small application per language that covers every shape named in D3 to D7, plus a
client that reads statuses without sending them, with an expected-responses file (handler, verb,
path, status, kind) next to it. They go into the test resources of each chen frontend and into
atom's tests.

Corpus, by id in [callsites-corpus.corpus.json](callsites-corpus.corpus.json): `java-petclinic`,
`java-sec-code`, `java-webgoat`, `java-mall` (it puts statuses in the body, so implicit 200s are
the right answer), `js-juice-shop`, `js-express-boilerplate`, `js-express-realworld`,
`js-nestjs-realworld`, `py-fastapi-template`, `py-microblog`, `py-dvpwa`, `py-defectdojo`,
`php-symfony-demo`, `php-koel`, `php-bookstack`, `rb-mastodon`, `rb-railsgoat` and `rb-maybe`.

## Risks and open questions

- A status set far from the handler, such as a service that throws a project error three calls
  down or a central error converter, is beyond the depth bound and shows as unresolved. Raising
  the bound is a measured change, not a default.
- Rails `rescue_from` and Express error middleware apply by class or by application. Inherited
  controllers and mounted sub-applications need the class and mount hierarchy, which ruby2atom and
  jssrc2cpg give only in part. Their records say `advice`, so consumers can treat them as weaker.
- Framework defaults change between versions (NestJS POST 201, Rails API controllers 204 when
  nothing is rendered), which is why the implicit table records the versions it was checked
  against.
- Where `endpoints` lives depends on #344. If usages is retired first, D8 lands on the command
  that replaces it.
- The author of #244 did not share the project behind it, so the corpus may miss shapes they
  needed. The Spring builder and enum forms they described are in the fixture.

## Credits

The idea comes from AppThreat/atom#244 by Abdul-levo. Commits that implement it carry:

```
Helped-by: Abdul-levo <263549126+abdul-levo@users.noreply.github.com>
Link: https://github.com/AppThreat/atom/pull/244
```

## Outcome

Filled in when the work ends.
