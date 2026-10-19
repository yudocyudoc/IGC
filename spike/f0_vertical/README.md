# F0 vertical spike

This is a **wiring probe**, not a validated scientific model. Its only empirical input is a synthetic text fixture. The Modelica toy stock uses invented constants and must never be interpreted as data about a real system.

Run from the repository root:

```powershell
python scripts/f0_spike.py
```

The command writes `artifacts/f0/run.json`. It exits with code `2` when any stage is pending, stubbed, or not run, so an incomplete path cannot appear green. If OpenModelica (`omc`) is installed, the runner attempts to execute `F0ToyStock.mo` and records its log and CSV. It does not convert a missing RDF, SHACL, SPARQL, or ATMS implementation into a pass.

## Implemented in this spike

- Reads the synthetic source and claim fixture.
- Checks the quote anchor against the exact source text and computes the source SHA-256.
- Emits a Web Annotation-shaped JSON object as a **draft only**.
- Checks local availability of required RDF/SHACL/SPARQL and ATMS components; unavailable engines remain `PENDING`.
- Attempts the real OpenModelica compile/simulation only when `omc` is found; otherwise records `PENDING`.

## Explicitly not demonstrated

No CRMinf/PROV graph validation, SPARQL query, SHACL evaluation, ATMS inference, Cloudflare persistence, causal conclusion, or completed integration gate is claimed by this spike.
