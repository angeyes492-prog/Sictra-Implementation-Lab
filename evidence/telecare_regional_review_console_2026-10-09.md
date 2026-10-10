# Regional scope in official research review — 2026-10-09 UTC

Scope: explicit, read-only, agent-configured laboratory research. This is a
source-review aid, not source approval, statistical revision, corroboration,
runtime admission or an architecture gate.

## Current original-byte chain

Four fixed Eurostat GETs succeeded with no redirect or retry: 674,954 total
retained bytes, below the 100-request / 100-MiB cycle and 8-MiB-file limits.
The ignored quarantine root is `.runtime/research-quarantine-2026-10-09-review/`.
Every receipt expires at most 24 hours after acquisition; the review's
earliest deadline is epoch `1791646629` (2026-10-10T15:37:09Z).

| Original | Candidate ID | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [Eurostat reuse notice](https://ec.europa.eu/eurostat/help/copyright-notice) | `bab9ce014088626f208f57bf3808c68461427051d8d628af4b35b590d90fd111` | 178,723 | `c7aafdc2de47247ee62acc3eeee570f879e2b5e57539718c7e0b9f28078db63c` |
| [Generic maritime metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/mar_esms.htm) | `4d2fd5891333b9d5e3c74374af65db702214a58a584f600e96a1b9d9dd56fe84` | 263,911 | `03e9bd88d73ed405e0bd4d74a3eee802de5b555b0ec69d210d0ae934a06c125b` |
| [Regional freight data](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tran_r_mago_nm?lang=EN&freq=A&tra_meas=FR_LD_NLD&unit=THS_T&geo=BE&sinceTimePeriod=2023&untilTimePeriod=2024) | `1942f11a6d8819134ccf231cf3091e7b6cc504941cd105e500bd0a6d7163ef3c` | 2,647 | `5525b2ac0f59d6439f62829ecda9a2bc7727d91486e6a3475fbda3965c8a6175` |
| [Regional transport metadata](https://ec.europa.eu/eurostat/cache/metadata/en/tran_r_esms.htm) | `cd6b44ba8d7830826478c0a708435f1c8f2703ae2f05f3a81ff71b15553d08e1` | 229,673 | `691449ac5aba1ea41e1ed6eab3e1c60c11f7df8d46b9b01ecb16ad23ce5d0db8` |

The statistical response's original-byte hash is unchanged from the prior
capture. That is a same-release recapture, not a second publication.
The generic metadata bytes changed, but no causal or release-specific
revision is inferred from that HTML delta. The regional section SHA-256 is
`ade168da5116dcc6d40ca6bc20adefeb9b03161951bef6c673a5e41bc6ce7d77`;
the literal review label is `EXPLICIT_MAIN_PORTS_ONLY`. This does not establish
that Statbel's port universe is equivalent or explain either numeric gap.

`research_admission` produced fingerprint
`683ed1b31418468bbd1d438ef6e23f4914d8cf37cdbc704ac3c84d2b26105149`
for the current data/generic-metadata/rights chain, with `reviewer_id=null`,
`decision=PENDING`, `NOT_ADMITTED` and runtime `NONE`. The regional document is
an additional review dependency in the read-only console, **not** a new grant
or a silently changed admission contract. A real source authority must review
rights, series-specific scope and exact binding before an attested source can
enter the statistical store.

## Executable increment and remaining boundary

`ResearchReview` report 0.2.0 optionally carries a current regional review
under the same terms receipt and hash, reopens all originals on each read,
uses the earliest expiry, and withdraws HTML/JSON when stale. The HTML escapes
publisher text and states the limit. Absence is labelled unconfirmed. A
clock-tick test first failed because the nested regional report included its
observation time; the repair compares invariant input fields while preserving
double reads and final fences. Positive/rejection tests cover exact scope,
wrong recipe, different rights lineage, tamper, restart, clock tick and HTTP
expiry withdrawal. Focused research-review tests passed 14/14.

The first full regression failed 1/1025 in the pre-existing operations HTTP
control test, after its two-dossier snapshot request timed out at the test
client's five-second limit. Isolated reproduction failed the same way. Timed
diagnostics measured the two full integrity snapshots at about 2.4–2.8
seconds each; the server intentionally performs both before success headers.
No source or state mismatch was proved. The test-only client timeout was
raised to 15 seconds for that scenario, with the second read, semantic
assertions and failure fences unchanged. Its isolated rerun passed 1/1 in
14.618 seconds. The clean serial full regression then passed 1025/1025 in
1365.001 seconds. JavaScript passed 18/18; source compilation succeeded.
Changed-tree preflight passed 24/24 with product completion
`NOT_DEMONSTRATED`. The failed first run remains recorded, not counted as a
pass.

The material code commit is `a83fbd1d7df5b7fbd645d4bfc0e4e4629fb7af4b`.
Clean-checkout preflight on that SHA passed 24/24; [GitHub Actions run
37960580703](https://github.com/angeyes492-prog/Sictra-Implementation-Lab/actions/runs/37960580703)
completed successfully on the exact SHA. This validates the candidate
increment's tested behavior, not source admission or product completion.

Remaining source decision: the generic metadata review alone is not a
series-specific coverage approval. The standalone admission bridge still
requires an authorized approval/binding; its current contract does not consume
this optional regional review. Any change to that admission authority or
retained runtime consumer needs a separate contract/MAR. The watchlist already
classifies versions in fixtures but cannot make this unadmitted recapture a
real operational release. No gate is promoted by this increment.

The [Eurostat API introduction](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction)
states that its database exposes the latest data only and does not version or
document past statistical-dataset versions. This explains why querying the
same API today cannot retrieve a genuine earlier release; structural metadata
versioning is a different matter. A real two-release watchlist must retain
successive publications prospectively under approved scope or use another
official publisher with a verifiable release archive. Different years within
one response and repeated downloads are not substitutes.
