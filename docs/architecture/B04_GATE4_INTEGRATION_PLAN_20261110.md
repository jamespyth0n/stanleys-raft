# P1-DM-B04-001 — Gate 4 Integration Plan

**Project:** Stanley's Raft — Dynamic Memory  
**Anchor:** P1-DM-B04-001 v1.0.0  
**Interface Baseline:** B04-IF-001 v0.1.0  
**Related Addendum:** P1-DM-B04-G3-001 v1.0.0  
**Document ID:** B04-G4-PLAN-001  
**Version:** 1.0.0  
**Status:** ARCHITECT-RATIFIED — GATE 4 IMPLEMENTATION CONTROL  
**Date:** 2026-11-10  
**Authority:** Architect — Sole Ratification Authority  
**Prepared by:** Stanley

---

## 1. Purpose

This plan governs B04 Gate 4 — Integrated Application Workflow.

Gate 4 demonstrates that the existing B04 components work together across the approved application boundaries and that the integrated workflow reports success and partial failure accurately.

The governing principle remains:

**Fit the assembly to the foundation. Never bend the foundation to fit the assembly.**

This plan does not authorize changes to B03 or commencement of B05.

## 2. Gate 4 scope

The integrated workflow shall demonstrate:

1. Extraction through the application and provider-neutral adapter.
2. Capture using trusted application metadata.
3. Persistence through the existing B03 `MemoryStore` API.
4. Retrieval of the persisted version through B04.
5. Context assembly using the existing `ContextAssembler`.
6. Response generation through the model adapter.
7. Construction and validation of the existing `ModelResponseOutcome`.
8. Accurate reporting of partial failures.

Capture-only and retrieval-only operations remain independently usable.

## 3. Explicit boundaries

### Included

- Integrated application workflow.
- Existing B03 persistence API.
- Existing B04 application services.
- Provider-neutral model adapter.
- Existing extraction and validation boundary.
- Context assembly and identity/provenance preservation.
- Response outcome construction.
- Deterministic integration and failure-path tests.

### Excluded

- B03 schema, contract, or persistence changes.
- New database tables or persistence paths.
- Persistence across application restart as a Gate 4 acceptance requirement.
- Vector databases, embeddings, semantic search, or ranking.
- Autonomous verification or promotion.
- Response persistence.
- Conversation-history subsystem.
- GUI, web application, cloud providers, or deployment infrastructure.
- B05 implementation.

B05 retains responsibility for the complete operational roundtrip, including restart-survival acceptance.

## 4. Successful workflow test

The primary integration test shall use:

- A temporary SQLite database.
- The existing authoritative B03 schema and persistence API.
- The existing `DynamicMemoryApplication`.
- The existing `MockModelAdapter`.
- Trusted source metadata supplied independently by the test caller.

### Required sequence

1. Submit source content through application extraction.
2. Confirm extraction returns a validated candidate.
3. Supply trusted source metadata independently.
4. Capture the candidate through the existing B04 capture boundary.
5. Confirm persistence through B03.
6. Retrieve the persisted version through B04.
7. Assemble context from the retrieved memory.
8. Submit the assembled context through the model adapter.
9. Construct and validate the existing `ModelResponseOutcome`.

### Required assertions

- Capture uses the existing B03 persistence API.
- Atom and version identities are preserved.
- Provenance is preserved through retrieval and context assembly.
- Verification remains `UNVERIFIED`.
- Model output cannot assign trusted provenance or verification authority.
- Context contains valid `ContextItem` records.
- Context preserves content, atom identity, version identity, and provenance.
- Context ordering and size behavior conform to the Architect-ratified assembly policy.
- Generation receives the assembled context.
- The response outcome conforms to the existing B03 contract.
- No response persistence is introduced.

## 5. Failure-path acceptance

Integration tests shall demonstrate explicit and attributable failure behavior.

| Failure point | Required behavior |
|---|---|
| Extraction | Failed or invalid extraction cannot proceed to capture |
| Capture | Persistence failure cannot appear as successful capture |
| Retrieval | Not-found is distinguishable from persistence failure |
| Context assembly | Assembly failure is explicit |
| Generation | Provider failure and timeout cannot appear as successful generation |
| Response construction | Invalid outcome cannot be represented as valid |
| Later-stage failure | Earlier successful operations remain accurately reported |

### Partial-success requirement

If capture succeeds but a later operation fails, the application must report:

- The capture operation succeeded.
- The later operation failed.
- The failure stage and category.
- The workflow did not complete successfully.

No failure may be converted into a successful-looking result.

No automatic capture retries shall be introduced.

Retry behavior must not create duplicate captures or obscure the original failure.

## 6. Existing evidence baseline

At Gate 4 entry:

| Test group | Result |
|---|---:|
| B04 foundation | 17/17 PASS |
| B04 model adapter | 5/5 PASS |
| B04 Ollama adapter | 13/13 PASS |
| B04 extraction | 24/24 PASS |
| B04 extraction integration | 11/11 PASS |
| B04 trusted capture handoff | 9/9 PASS |
| **B04 total** | **79/79 PASS** |
| Canonical B03 regression | 71/71 PASS |
| **Combined regression** | **150/150 PASS** |

The baseline is existing component and partial integration evidence. It does not, by itself, establish Gate 4 completion.

The legacy `tests.test_b03_persistence.py` module remains excluded from claims of a clean canonical regression.

## 7. Known evidence gaps

The following evidence remains necessary:

1. One deterministic integrated workflow test from extraction through response outcome.
2. Integrated proof of identity and provenance preservation.
3. Explicit retrieval not-found versus persistence-failure behavior.
4. Explicit capture and later-stage partial-success reporting.
5. Integrated response-generation failure handling.
6. Verification that the existing `ModelResponseOutcome` contract is used without modification.

These are evidence gaps pending contract reconciliation, not automatically confirmed production defects.

## 8. Contract reconciliation before implementation

Before proposing source changes, inspect the exact current definitions and behavior of:

- `ModelResponseOutcome` in `contracts.py`.
- Existing B04 result structures in `application/results.py`.
- `DynamicMemoryApplication` in `application/entry.py`.
- Existing capture, retrieval, context, extraction, and adapter interfaces.

Determine the minimum application coordination required to demonstrate the approved workflow.

Do not introduce a new orchestration framework or duplicate existing services merely to create an end-to-end test.

Determine how partial outcomes can be represented using existing contracts and authorized B04 result structures.

Any conflict with the ratified B03 or B04 contracts must be raised as a finding.

## 9. Implementation controls

1. Reconcile the exact contracts and interfaces.
2. Define the minimum integrated workflow interface.
3. Define partial-success reporting against existing result structures.
4. Identify the minimum required test additions.
5. Present the proposed file-level change list for Architect review.
6. Back up each affected file before an authorized edit.
7. Modify one file at a time.
8. Run focused tests after each change.
9. Run the complete approved B04 regression.
10. Run the canonical B03 regression.
11. Verify protected B03 production-file hashes.
12. Append reproducible evidence to the evidence ledger.

No source edits are authorized merely by ratification of this plan. Source changes require the agreed review and authorization process.

## 10. Protected boundaries

The following remain unchanged:

- `src/dynamic_memory/contracts.py`
- `src/dynamic_memory/persistence.py`
- `src/dynamic_memory/schema.sql`
- Existing B03 persistence behavior and contracts.
- Protected external Satori `rag.db`.

No new dependencies are authorized without demonstrated technical necessity and approval.

No Gate 5 or B05 work is authorized by this plan.

## 11. Gate 4 exit evidence

Gate 4 may be submitted for review when:

- The integrated workflow is reproducibly tested.
- Capture is demonstrated through B03.
- Retrieval of the persisted version is demonstrated.
- Identity and provenance are preserved.
- Context assembly produces valid `ContextItem` objects.
- Response generation uses the provider-neutral adapter.
- The existing `ModelResponseOutcome` is constructed and validated.
- Partial failures are accurately reported.
- Approved B04 tests pass.
- Canonical B03 regression remains 71/71 PASS.
- No unauthorized B03, schema, dependency, or persistence changes exist.
- Evidence is recorded and reproducible.

Passing tests does not automatically close Gate 4.

The Architect retains sole ratification authority.

## 12. Gate 5 boundary

Gate 5 is the B04 closure review.

It shall review:

- Implementation against P1-DM-B04-001 v1.0.0.
- B03 regression status.
- Protected contracts, schema, and persistence boundaries.
- Reproducible test evidence.
- Known limitations and outstanding findings.
- Completion and handoff documentation.

Gate 5 requires separate authorization and an explicit Architect closure decision.

B04 completion does not imply B05 acceptance.

## 13. Ratification record

**Document:** B04-G4-PLAN-001  
**Version:** 1.0.0  
**Status:** ARCHITECT-RATIFIED — GATE 4 IMPLEMENTATION CONTROL  
**Ratification Authority:** Architect  
**Ratification Date:** 2026-11-10  
**Gate 4 Authorization:** GRANTED  
**B03 Modification Authorization:** NOT GRANTED  
**Gate 5 Authorization:** NOT GRANTED BY THIS PLAN  
**B05 Implementation Authorization:** NOT GRANTED

---

**Build motto:** Preserve the foundation. Control the boundary. Assemble the capability. Prove the roundtrip.

**Architect's direction:** The raft is ready to sail.