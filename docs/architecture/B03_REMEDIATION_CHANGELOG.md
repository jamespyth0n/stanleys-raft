# B03 Remediation Changelog

**Campaign:** CAMP-DM-P1-001  
**Brick:** B03 — Memory Schema and Contracts  
**Governing technical package:** P1-DM-B03-TP-001 v0.2.0  
**Authority:** Architect  
**Working mode:** BUILD  
**Repository:** `D:\Satori_IDE_codebase\stanleys-raft`

## Purpose

This changelog preserves the B03 remediation sequence, source-file changes,
test evidence, outstanding findings, and next actions. It is intended as a
continuity and handoff record when work resumes in a later session.

The Architect retains sole ratification authority. A passing test suite is
verification evidence; it does not independently ratify a finding or close
B03.5.

## Operating constraints

- Keep scope within P1 and the ratified B03 technical package.
- Preserve append-only memory version behavior.
- Preserve provenance and evidence lineage.
- Do not modify the protected Satori `rag.db`.
- Do not change the five-table schema without a demonstrated requirement
  and Architect authorization.
- Use `.venv\Scripts\python.exe` for project tests.
- Use `PYTHONPATH=src` when running unittest discovery from the repository root.
- No Git repository is currently in use. Preserve local backups, hashes,
  test logs, and evidence artifacts.
- Do not claim verification without recorded execution evidence.

## Remediation ledger

### F-01 — UUIDv4 contract enforcement

**Status:** VERIFIED BY TESTS

**File changed:** `src/dynamic_memory/contracts.py`

The base Pydantic contract validator was extended to reject UUID values
that are not UUIDv4, including UUID values contained in lists. Existing
timezone-aware datetime normalization to UTC was retained.

**Backup:**
`evidence/backups/contracts.py.pre_F01_20261110_133529.bak`

**Backup SHA-256:**
`2C8A53249A3EA01CC596502095D22AE08A6C69A2E15D7E505AD41E59EC6434AD`

**Post-F-01 source SHA-256:**
`FC060F64ECECE2CBE7D1B8D330A560F7A4D1465719BDF2EEC44F011573BC5106`

**Test file:** `tests/test_b03_uuidv4.py`

**Evidence:**
- UUIDv4 focused tests: 4/4 passed.
- Original canonical B03 regression set: 43/43 passed.
- Full unittest discovery also exposed 10 teardown errors in the legacy
  `test_b03_persistence.py` harness due to SQLite handles remaining open
  during Windows temporary-directory cleanup. These are recorded separately
  and were not silently treated as passing tests.
- The corrected `test_b03_persistence_v2.py` suite passed.

### F-05 — Cross-object provenance consistency

**Status:** VERIFIED BY TESTS

**File changed:** `src/dynamic_memory/contracts.py`

The contracts now enforce:
- `CaptureResult.provenance_ids` must contain at least one UUID.
- `RetrievedMemory.provenance` must contain at least one record.
- Each `RetrievedMemory` provenance record must reference the parent
  memory's `version_id`.
- `ContextItem.provenance` must contain at least one record.
- Each `ContextItem` provenance record must reference the parent
  context item's `version_id`.

These controls enforce structural provenance linkage. They do not establish
the truthfulness or reliability of the source itself.

**Post-F-05 source SHA-256 observed during reconnaissance:**
`2E940C33CAC1C39D7D83E8B34E4411E6AF39A5D98281854CF3049621558205BE`

**Test file:** `tests/test_b03_f05.py`

**Evidence:**
- F-05 focused tests: 8/8 passed.
- Combined canonical regression set including F-05: 51/51 passed.
- The F-01 and F-05 modifications both reside in `contracts.py`.
- F-05 backup path/hash should be retained from the original patch execution
  output if separately available.

### F-02 — Disputes relationship persistence

**Status:**VERIFIED BY TESTS — 9/9 FOCUSED; 71/71 CANONICAL REGRESSION

**File changed:** `src/dynamic_memory/persistence.py`

The F-02 patch adds:
- `MemoryStore.add_relationship(from_version_id, to_version_id)`
- `MemoryStore.get_relationships(version_id)`

The intended behavior:
- Only the existing `disputes` relationship type is supported.
- Both endpoint versions must exist.
- Self-relationships are rejected.
- Relationship IDs are generated as UUIDv4.
- Creation timestamps are generated as timezone-aware UTC.
- Insert operations use parameterized SQL and an explicit
  `BEGIN IMMEDIATE` transaction.
- Failed inserts roll back.
- Retrieval includes incoming and outgoing relationships.
- Retrieval reconstructs `RelationshipRecord` contracts.
- No schema modification or automatic reciprocal relationship is introduced.
- Duplicate relationships remain permitted because the existing schema
  does not define a uniqueness constraint.

**Pre-patch persistence SHA-256:**
`DF1DE4B1B60AC73666CB0995681060947F7995D2041875FA2C9F10E5C8B4C45F`

**Test file:** `tests/test_b03_relationships.py`

**Expected focused tests:** 9.

**Verification command:**
```powershell
$env:PYTHONPATH = Join-Path (Get-Location) "src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_b03_relationships.py" -v
Remove-Item Env:\PYTHONPATH
```

After focused tests pass, run the complete canonical regression set:
- `test_b03_contracts.py`
- `test_b03_serialization.py`
- `test_b03_persistence_v2.py`
- `test_b03_uuidv4.py`
- `test_b03_f05.py`
- `test_b03_relationships.py`

Expected total after F-02: 60 tests. This is a target, not a result,
until terminal output confirms it.

Record the final persistence source hash, backup hash, and test result
after verification.

## Remaining findings and next gates

### F-03 — Activity-event retrieval

**Status:** VERIFIED BY TESTS — 11/11 FOCUSED; 71/71 CANONICAL REGRESSION

Activity events are written during capture and revision, but the persistence
layer does not yet reconstruct and retrieve them as `ActivityEvent` contracts.

Next action:
- Inspect the activity-event DDL and existing insertion behavior.
- Define the smallest retrieval API.
- Test event reconstruction, details JSON parsing, ordering, missing
  references, and connection cleanup.
- Preserve existing event writes and transaction behavior.

### F-04 — ModelResponseOutcome persistence

**Status:**RESOLVED — ARCHITECT-RATIFIED SECTION 6.3 CLARIFICATION

The `ModelResponseOutcome` contract exists, but persistence capability
has not been demonstrated.

Next action:
- Reconcile the B03 acceptance requirement for minimal execution outcome
  recording against the existing five-table schema.
- Determine whether an existing table/API can satisfy it.
- Do not introduce a sixth table or redesign without explicit architectural
  justification and Architect authorization.

### F-06 — Optional provenance metadata

**Status:**DEFERRED — ARCHITECT-RATIFIED; NON-BLOCKING FOR P1

`ProvenanceRecord` supports `source_created_at` and `source_content_hash`,
but `CaptureRequest` does not currently expose these fields and persistence
writes NULL for both.

Next action:
- Reconcile whether these fields are required for P1 or are optional
  metadata that may remain unavailable.
- Preserve the distinction between missing metadata and fabricated metadata.
- Do not expand the request contract without checking the ratified package.

## Historical test baseline

Before F-02:
- Contracts: 19 passed.
- Serialization: 10 passed.
- Persistence v2: 10 passed.
- UUIDv4: 4 passed.
- F-05: 8 passed.
- Combined canonical total: 51 passed.

The legacy `test_b03_persistence.py` teardown issue remains a separately
documented test-harness limitation. Do not modify it as part of unrelated
finding remediation.

## B03.5 closure requirements

Before recommending B03.5 closure:
1. Reassess F-01 through F-06 against the ratified technical package.
2. Verify all accepted remediation tests.
3. Record source and backup hashes for every changed source file.
4. Record any residual limitations and deferred decisions.
5. Preserve the distinction between test verification and Architect
   ratification.
6. Obtain the Architect's explicit disposition.

**Current working sequence:** F-02 → F-03 → F-04 assessment → F-06
disposition → regression/evidence consolidation → B03.5 reassessment.

**No B03.5 closure or ratification is implied by this changelog.**
## F-03 - Activity-event retrieval

**Finding:** Activity events were persisted by capture and revision, but no retrieval operation reconstructed them into the `ActivityEvent` contract.

**Implementation:** Added `MemoryStore.get_activity_events()` to retrieve all events or filter by `atom_id`, `version_id`, or both. Results are ordered deterministically by `occurred_at` and `event_id`. UUIDs, timestamps, and JSON details are reconstructed through the existing contract and datetime utilities.

**Data-integrity behavior:**
- SQL `NULL` details remain `None`.
- Malformed JSON raises a `ValueError` identifying the event.
- JSON values that are not objects raise a `ValueError` identifying the event.
- Database connections close after retrieval.
- SQL filters are parameterized.

**Files changed:**
- `src/dynamic_memory/persistence.py`
- `tests/test_b03_activity_events.py`

**Verification status:** VERIFIED. Focused tests passed 11/11. Canonical regression suite passed 71/71 across all seven test modules. Evidence supplied by Architect on 2026-11-10.

**Baseline evidence before F-03:** F-01, F-05, and F-02 remediation tests had passed in the Architect-supplied canonical regression run: 60/60 tests.

**Scope controls:** No schema changes, no database writes, no changes to the protected Satori `rag.db`, and no P2 features.

---

## B03 final reconciliation — 2026-11-10 14:17:42 -06:00

**Regression disposition:** PASS — 71/71 tests across all seven canonical modules.

**Execution evidence:** Architect-supplied terminal output, 2026-11-10.
The corrected execution explicitly set PYTHONPATH to the repository's
src directory. All seven modules imported and executed successfully.

| Test module | Result |
|---|---:|
| test_b03_contracts.py | 19/19 |
| test_b03_serialization.py | 10/10 |
| test_b03_persistence_v2.py | 10/10 |
| test_b03_uuidv4.py | 4/4 |
| test_b03_f05.py | 8/8 |
| test_b03_relationships.py | 9/9 |
| test_b03_activity_events.py | 11/11 |
| **Total** | **71/71** |

**Finding dispositions:**

- F-01: UUIDv4 contract enforcement — verified.
- F-02: Disputes relationship persistence — verified.
- F-03: Activity-event retrieval — verified.
- F-04: No B03 persistence defect; Section 6.3 clarification ratified by Architect.
- F-05: Cross-object provenance consistency — verified.
- F-06: Optional source metadata — deferred by Architect; non-blocking for P1.

**Architecture:** Retain the ratified five-table SQLite schema.
No sixth table, P2 expansion, or protected Satori rag.db modification.

**Verification limitation:** The earlier reconciliation collector run
reported four import failures because PYTHONPATH was not set. The corrected
terminal run subsequently passed all seven modules. The earlier collector
failure is retained as historical instrumentation evidence, not counted
as a source regression.

**Authority boundary:** Test verification is evidence, not ratification.
B03.5 closure and the next-brick release remain subject to the Architect's
explicit disposition.
