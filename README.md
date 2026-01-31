# February of Code

A one‑month build challenge focused on shipping small, real products.
Throughout February, I build one scoped project per day. Each project is designed to:

* solve a real, concrete problem
* exercise a specific engineering skill
* be finished, documented, and reviewed the same day

---

## Why this exists

Most “X days of code” challenges optimize for streaks and screenshots. This one optimizes for **engineering judgment**.

Every project here:

* has a clearly defined user
* makes explicit tradeoffs
* stops deliberately short of over‑engineering

The constraint of one day forces hard decisions.

---

## How to read this repo

Each project lives in its own folder:

```
/day-01-project-name
/day-02-project-name
...
```

Inside each folder you’ll typically find:

* `README.md` - problem definition, approach, tradeoffs
* `src/` - implementation
* `tests/` - lightweight tests where appropriate
* `data/` - sample inputs/outputs (small and local)

Projects are intentionally self‑contained. There is no shared framework or monorepo abstraction, a deliberate choice to keep scope tight and reasoning clear.

### Honest tradeoffs

Every README includes a short section on:

* known limitations
* what I’d change with more time

---

## What this repo is *not*

* a production‑ready codebase
* a framework
* a collection of polished SaaS products

Each project is a finished slice, not a startup.

Some projects may later be expanded into dedicated repos. When that happens, this repo remains as the original, time‑boxed version as a record of the initial design decisions.

---

## Tech choices

* Language: Python (chosen for speed, clarity, and ecosystem)
* Tooling: minimal by design
* Storage: simple formats unless complexity is justified

Libraries are used pragmatically. If the standard library is sufficient, it’s preferred.


