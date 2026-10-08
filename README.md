<!-- SPDX-License-Identifier: MIT -->
# svarog-evals

Task corpora for the measurements of
[svarog](https://github.com/TheArkadiuszGrzelka/svarog). They live here so the
plugin itself stays small; the harness, the method and every report stay in
the svarog repository under `docs/svarog/evals/`.

| Path | Used by |
|---|---|
| `t5/cases/` | `docs/svarog/evals/t5/stage.sh` (the `claude plugin eval` cases and the pinned task snapshots under `t5/cases/_tasks/`) |
| `v03/tasks/` | `docs/svarog/evals/v03/driver.py` (heavy, large and escape-suite tasks) |

## Use

Check this repository out next to svarog, or point `SVAROG_EVALS` at it:

```
git clone https://github.com/TheArkadiuszGrzelka/svarog.git
git clone https://github.com/TheArkadiuszGrzelka/svarog-evals.git
svarog/docs/svarog/evals/t5/stage.sh /tmp/t5-stage
SVAROG_EVALS=/elsewhere/svarog-evals svarog/docs/svarog/evals/v03/driver.py prove
```

The tasks, what each one seeds and how a run is scored are described in
svarog's `docs/svarog/evals/t5/README.md` and `docs/svarog/evals/v03/README.md`.

## Licence

MIT, see `LICENSE`, except the vendored third-party snapshots listed in
`NOTICE`, which keep their own licences.
