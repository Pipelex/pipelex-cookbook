# From an address to a web app you deploy

An address is a whole method, and one command turns it into a web app. The initializer of [`pipelex-method-apps`](https://github.com/Pipelex/pipelex-method-apps) writes a Next.js app whose form and result view both come from the method's contract, so you write no form field and no result markup, and the app calls the method by its address with your key kept on the server. This recipe makes the app for the cookbook's [energy diagnostic (DPE) extraction](https://github.com/Pipelex/pipelex-cookbook/tree/v0.20.0/methods/extract_dpe) method, which reads a French energy performance diagnostic into the record a letting agency files: its form takes a PDF, which the browser sends straight to Pipelex storage through a one-time upload grant.

It shows what an app on a published method is made of:

- **The address is the method.** Nothing is copied into the app but a `method.json` naming `github.com/Pipelex/pipelex-cookbook/extract_dpe@v0.20.0`, and the types generated from it. The tag pins the method, so the app runs it as it was at that release until you move the tag.
- **The key is a server secret.** The app's Server Actions call the Pipelex API with `PIPELEX_API_KEY` from the server's environment, and the browser never sees it: `.env.local` on your machine, a secret in your host's environment once deployed, and never a `NEXT_PUBLIC_` variable, which Next.js would ship to every browser.
- **Nothing checks who is calling.** Anyone who can reach the app runs the method on your key, so the app listens only on this machine until you say otherwise, and a deployment belongs behind an access control of its own.

## What it needs

- Node.js 22.12 or later, `make`, `git`, and `lsof`, which `make serve` uses to check the server it starts: macOS ships it, and on Linux it comes from your distribution's packages.
- A Pipelex API key, from [app.pipelex.com](https://app.pipelex.com), in `PIPELEX_API_KEY`. Creating the app reads the method's contract from the API with it, which spends no credit.
- Credit on your Pipelex account: each run from the app's form is one run on the hosted API.

## Run it

```bash
export PIPELEX_API_KEY=…                               # from app.pipelex.com
npm create @pipelex/method-app@latest dpe-app -- --method github.com/Pipelex/pipelex-cookbook/extract_dpe@v0.20.0
make -C dpe-app serve
```

The first command writes the app into `dpe-app/`, commits the template as it came, and then generates the method's part of it, which it leaves uncommitted for you to read before you commit it. The second starts the development server in the background and prints its URL once the page answers. Open it, drop the [sample DPE](https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/v0.20.0/assets/extract_dpe/synthetic_dpe.pdf), a fictional one made for the example, on the form and run it. `make -C dpe-app stop` stops the server.

Your agent does the same with `/pipelex-scaffold` from the Pipelex plugin: ask it to make an app for the address.

### Build it for production

```bash
make -C dpe-app build
make -C dpe-app start
```

`make build` is the production build, and `make start` serves it on `127.0.0.1:4300`, which only this machine can reach. `APP_PORT` changes the port, and `APP_HOST=0.0.0.0` opens the server to the network, for a container or a host that routes traffic to it; the Makefile warns each time a server starts beyond loopback. `make all` checks, tests and builds the app, and needs neither a key nor a network.

### Deploy it

The app is a standard Next.js app, so any host that runs `npm run build` and `npm run start` serves it; follow your host's own guide for a Next.js app. Two things are yours to set there:

- **The key**, as `PIPELEX_API_KEY` in the host's environment for the server, marked secret where the host has a notion of one. It is read at run time, so it never needs to be present at build time.
- **An access control in front of the app**, such as your host's password protection or single sign-on. The template's section [Where the app listens](https://github.com/Pipelex/pipelex-method-apps/tree/main/webapp-js#where-the-app-listens) says why: "nothing authenticates the browser that calls them, so anyone who can reach the server runs methods billed to your key". An app that more than one person uses also has to decide who may read which run's files, which its [input form guide](https://github.com/Pipelex/pipelex-method-apps/blob/main/webapp-js/docs/input-form.md) explains.

## What you get

Creating the app streams the output of `make create`, which scaffolds the method, installs the packages, and checks, tests and builds the app, then ends on one verdict line, after a warning about the license's copyright line, which `--license-holder` claims. With `--quiet`, the output of `make create` goes to a log instead. Its beginning and its end:

```text
create-method-app: writing webapp-js 0.5.5 (67c67d5f3f768152a2412f74f205e14c14fa361b) into …/dpe-app
create-method-app: wrote 143 files
create-method-app: running make create in …/dpe-app
…
create: done — Extract DPE (extract-dpe) runs method_ref github.com/Pipelex/pipelex-cookbook/extract_dpe@v0.20.0.
…
warnings from make create:
  warning: LICENSE copyright line left untouched — pass --license-holder to claim it.
git: made a repository on main and committed the template as 03da3a467c2f, "Start from Pipelex/pipelex-method-apps/webapp-js 0.5.5 (67c67d5f3f768152a2412f74f205e14c14fa361b)".
created …/dpe-app; next: cd …/dpe-app && make serve
```

`make serve` prints the page's URL and its title. It takes the first port from 4300 to 4309 that no other directory holds, 4302 on the machine that proved this recipe:

```text
starting the dev server on port 4302 (process group 93098, log .serve/server.log)
serving http://127.0.0.1:4302/ — "Extract DPE" (log .serve/server.log); stop it with: make stop
```

The page is the method's form: one document field, described as "A French energy performance diagnostic (DPE) of a dwelling, as a PDF", and a "Run extract DPE" button. On the sample, the run took about half a minute, and the result view showed what the method read, the figures printed on the diagnostic, and what its class means for letting the dwelling:

| Field | Value |
|---|---|
| Address | 18 rue des Exemples, 69003 LYON 3EME (Étage 3 ; Porte gauche ; N° de lot : 27) |
| Dpe number | 2669E0000000X |
| Date of issue | 2026-06-18 |
| Date of expiration | 2036-06-17 |
| Energy efficiency class | F |
| Per year per m2 consumption | 342 |
| Co2 emission class | E |
| Per year per m2 co2 emissions | 61 |
| Yearly energy costs min | 1380 |
| Yearly energy costs max | 1870 |
| Energy prices as of | 2025-01-01 |
| Letting status | Rent frozen; no new or renewed lease from 1 January 2028 |
| No new lease from | 2028-01-01 |

Above it, a Download button and a "JSON" view beside the result view; below it, the run's id, `run_…`, with a Copy button, and what the run consumed behind a closed "Usage and cost" disclosure.

## How it is built

The recipe is two commands and the app they write, so it carries no code of its own: the [initializer](https://github.com/Pipelex/pipelex-method-apps/tree/main/initializers/js#readme) and the [`webapp-js`](https://github.com/Pipelex/pipelex-method-apps/tree/main/webapp-js#readme) template do the work.

- **The method's slice.** `make create`, which the initializer runs, writes `methods/extract-dpe/method.json` naming the address, the types generated from the method in `src/generated/extract-dpe/` with their lock, a typed reader of the output in `src/types/`, the Server Actions that run the method in `src/actions/`, and the form in `src/components/ExtractDpeForm.tsx`, then registers it in `src/methods.ts`. It names the app after the method, in `package.json` and in `src/site.ts`, which holds the page's title and description; pass `--name`, `--title` and `--description` to choose them yourself.
- **The run.** The form stores the PDF as soon as it is dropped, through an upload grant the Server Action asks for, and the action checks the inputs against the method's contract before it starts the run, since a Server Action is a public endpoint. The app runs the method durably by default: it starts the run and polls it, so a method that takes minutes does not hit the hosted API's limit on a synchronous call.
- **The types stay the method's.** `make check`, within `make all`, fails when the generated types no longer match `method.json`, and `npm run codegen:verify` asks the API whether they still match the method at its tag. [Codegen](https://github.com/Pipelex/pipelex-method-apps/blob/main/webapp-js/docs/codegen.md) explains both.
- **A second method becomes a second tab**, as the [second-tab recipe](../second-tab/) shows.
