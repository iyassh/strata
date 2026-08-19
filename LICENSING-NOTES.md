# Licensing notes (T2 decision record, 2026-08-19)

**STRATA's own code is MIT** (see LICENSE). Three third-party boundaries a
user or packager must know about:

## 1. pm4py is AGPL-3.0 — the one strong-copyleft dependency

`pm4py` (process discovery + conformance) is AGPL-3.0 (Process Intelligence
Solutions; a commercial license is sold separately). Our source is MIT, but
a distribution that BUNDLES pm4py is effectively AGPL-encumbered, and
network-service use of a combined work triggers AGPL §13. Decision:

- **Now (Tier A/B):** pm4py remains a hard dependency, declared and
  disclosed. `pip install`-ing pulls pm4py under ITS license from PyPI —
  standard practice — and this file is the disclosure. Consultants or
  vendors embedding STRATA in closed products must either obtain pm4py's
  commercial license or wait for item (b).
- **Phase 9 (T3 facade):** pm4py imports move behind lazy import guards so
  the channels that never touch discovery (rules, residual, frequency,
  oscillation, rate) run WITHOUT pm4py installed. Packaging then splits:
  `pip install strata-fdd` = MIT-clean calibrated channels;
  `pip install strata-fdd[discovery]` = adds pm4py (AGPL) for the model
  and device conformance strata.
- **Phase 12:** native inductive-miner + token-replay for our restricted
  event-log class (tiny alphabets, day traces) removes the dependency
  entirely; pm4py becomes an optional cross-validation extra.

## 2. LBNL datasets are CC BY 4.0

Loaders, benchmark manifests, and (if we later bundle) fault-free sample
slices are permitted with attribution: Granderson, Lin et al.,
DOI 10.25984/1881324. The `strata benchmark lbnl-*` command must print the
citation.

## 3. System Graphviz

`pm4py`'s visualisations call the Graphviz *binary* (EPL) — a system
dependency, not linked code; no license interaction. Detection never needs
it.

Everything else in the dependency tree (pandas, numpy, scipy, scikit-learn,
pyyaml, typer, rdflib) is BSD/MIT-family — no conflicts with MIT.
