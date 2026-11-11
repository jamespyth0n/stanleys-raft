# B04 Gate 3 — Remediation Evidence Ledger

**Document ID:** P1-DM-B04-G3-EL-001  
**Version:** 1.0.0  
**Date:** 2026-11-10  
**Project:** Stanley's Raft — Dynamic Memory  
**Repository:** `D:\Satori_IDE_codebase\stanleys-raft`  
**Authority:** Architect  
**Status:** RATIFIED — EVIDENCE REGISTER BASELINE  
**Gate Status:** GATE 3 ACCEPTANCE PENDING

---

## 1. Purpose

This ledger records the implementation and regression evidence for B04 Gate 3 remediation packages RP-01 through RP-06.

It provides traceability between the ratified B04 implementation specification, remediation plan, production changes, test results, backup records, and remaining limitations.

This ledger is an evidence register. It does not independently establish semantic correctness, live-provider reliability, or formal Gate 3 closure.

## 2. Governing authority

| Reference | Authority |
|---|---|
| P1-DM-B04-001 | B04 Assembly Layer — Build Sub-Anchor and Implementation Control Specification, v1.0.0 RATIFIED |
| P1-DM-B04-G3-RP-001 | Gate 3 Remediation Plan; RP-01 through RP-06 authorized |
| B04-IF-001 | B04 interface baseline, v0.1.0 |
| B03 contracts and persistence | Existing ratified foundation; preservation required |

The Architect retains sole ratification authority.

No Gate 4 implementation or B05 work is authorized by this ledger.

## 3. Remediation register

| Package | Scope | Recorded disposition |
|---|---|---|
| RP-01 | Extraction error taxonomy | Implemented; targeted tests passed |
| RP-02 | Ollama provider error handling | Implemented; targeted tests passed |
| RP-03 | Unexpected internal failure classification | Covered by RP-01 implementation and extraction tests |
| RP-04 | Adversarial trust-boundary tests | Implemented; targeted tests passed |
| RP-05 | Trusted metadata consistency | Implemented; targeted tests passed |
| RP-06 | Integration failure propagation | Implemented; targeted tests passed |

### RP-01 — Error taxonomy

Extraction failures are distinguished across validation, timeout, provider, malformed provider response, malformed extraction output, contract validation, and unexpected internal failure categories.

Production file: `src/dynamic_memory/application/extraction.py`

- Original SHA256: `4170D10FCE0C10FE27A8BDAA144FC6620492C751EFB9535BAEC64467BF22A794`
- Resulting SHA256: `26C4A466C5527D63668A7FB316EA7C33473B1ED6F77A1163087882C651C664F7`
- Backup: `src/dynamic_memory/application/extraction.py.bak_RP01_20261110_155335`

Test file: `tests/test_b04_extraction.py`

- Resulting SHA256 after RP-01: `90DE061EF4294CB38032141237C83E247311061EDBF9498F92EC8441D63BED37`
- Backup: `tests/test_b04_extraction.py.bak_RP01_20261110_155727`

### RP-02 — Ollama provider error handling

The adapter explicitly detects Ollama error responses and distinguishes provider errors from malformed response structures.

Production file: `src/dynamic_memory/application/ollama_adapter.py`

- Original SHA256: `8B1D33027AD5B24F8EDF51744480EBEE4F8DC39D9825D728BF9FE2915B6AAB32`
- Resulting SHA256: `D46B9A66CB6D7E78BDAD01E0027D372086B17D925CD62052B7A724F7E0F1D925`
- Backup: `src/dynamic_memory/application/ollama_adapter.py.bak_RP02_20261110_160207`

Test file: `tests/test_b04_ollama_adapter.py`

- Resulting SHA256: `5446D1FF46C0BF49E423C7BC3D64CCC13C4FB051E42C88723ADD7EDE318B9343`
- Backup: `tests/test_b04_ollama_adapter.py.bak_RP02_20261110_160326`
- Targeted result: 13/13 passed.

The extraction boundary test also confirmed that a provider error is classified as `provider_failure`.

### RP-03 — Unexpected internal failures

The extraction boundary distinguishes unexpected adapter exceptions and invalid adapter results from expected provider failures.

Evidence is included in the RP-01 implementation and final extraction test results.

No separate production change or backup is recorded for RP-03.

### RP-04 — Adversarial trust tests

Integration tests cover hostile source content and forged authority fields.

The tests establish that:

- Source content is passed unchanged into the extraction prompt.
- The prompt explicitly treats source material as untrusted.
- Forged provenance and verification fields are rejected structurally.
- Rejected extraction output does not reach capture.

Test file: `tests/test_b04_extraction_integration.py`

- Pre-RP-04 SHA256: `C9F269FA058231BD17BEBB6E0D6369D97E5BD37FB603D984E66FC8BB5AD96E2E`
- Resulting SHA256 after RP-04: `CFC627525F39CEA04B2C3B64CC9A75A892519C9F0C7766A8357FACAF4AD87EC5`
- Backup: `tests/test_b04_extraction_integration.py.bak_RP04_20261110_161033`

**Limitation:** These tests establish prompt construction and application-level structural enforcement. They do not prove resistance to prompt injection by a live model.

### RP-05 — Trusted metadata consistency

`CaptureService` now rejects whitespace-only trusted `source_type` values before delegating to persistence.

Production file: `src/dynamic_memory/application/capture_service.py`

- Original SHA256: `23D2F215E4216D7D25D286D37A5B9FF85CF5C591627C961C01BA3C4BBFC5BA6D`
- Resulting SHA256: `C06992D0F6030A8B106C96644BA6B17D624A5606E7938821CBF1D06C76D191C5`
- Backup: `src/dynamic_memory/application/capture_service.py.bak_RP05_20261110_161139`

Test file: `tests/test_b04_trusted_capture_handoff.py`

- Original and backup SHA256: `F166412456E09B3CF6C9C3EA81A9E05FD6600EA75DE5BD83B03897C4DCFC23B8`
- Backup: `tests/test_b04_trusted_capture_handoff.py.bak_RP05_20261110`
- Resulting SHA256: `1659AA2F8A0D34A753C767420B7DB315A50D6A0B33CFCD9A70129CFFEC6318CD`
- Targeted result: 9/9 passed.

No B03 contract or persistence changes were made for this remediation.

### RP-06 — Integration failure propagation

Integration tests verify that provider errors, malformed extraction output, and unexpected adapter exceptions propagate as failures and do not produce candidates or trigger capture.

Test file: `tests/test_b04_extraction_integration.py`

- Pre-RP-06 SHA256: `CFC627525F39CEA04B2C3B64CC9A75A892519C9F0C7766A8357FACAF4AD87EC5`
- Resulting SHA256: `B4F28FB42AB74AB45A545D42F4CB13CC70C4B313EC6247DB87E9FDB15AAD18C5`
- Backup: `tests/test_b04_extraction_integration.py.bak_RP06_20261110`
- Targeted result: 11/11 passed.

No production changes were required for RP-06.

## 4. Regression evidence

### B04 regression

| Test module | Passed |
|---|---:|
| `test_b04_foundation.py` | 15 |
| `test_b04_model_adapter.py` | 5 |
| `test_b04_ollama_adapter.py` | 13 |
| `test_b04_extraction.py` | 24 |
| `test_b04_extraction_integration.py` | 11 |
| `test_b04_trusted_capture_handoff.py` | 9 |
| **Total** | **77/77** |

All six B04 modules passed in the reported regression run.

### Canonical B03 regression

| Test module | Passed |
|---|---:|
| `test_b03_contracts.py` | 19 |
| `test_b03_serialization.py` | 10 |
| `test_b03_persistence_v2.py` | 10 |
| `test_b03_uuidv4.py` | 4 |
| `test_b03_f05.py` | 8 |
| `test_b03_relationships.py` | 9 |
| `test_b03_activity_events.py` | 11 |
| **Total** | **71/71** |

All seven canonical B03 modules passed in the reported regression run.

### Combined result

**148/148 reported regression tests passed.**

This result is limited to the listed modules. It is not a claim that unrestricted unittest discovery is clean. The known legacy `test_b03_persistence.py` Windows SQLite teardown issue remains excluded from the canonical B03 suite.

## 5. Architectural preservation

The remediation was constrained to B04 application and test boundaries.

The following preservation requirements remain binding:

- B03's five-table architecture remains unchanged.
- No unauthorized B03 schema, contract, or persistence redesign.
- No modification of the protected external Satori `rag.db`.
- No autonomous verification or promotion by the model.
- Verification status remains application-owned.
- No additional dependency introduced.
- No Gate 4 or B05 implementation.

**Final preservation verification:** Pending explicit final source-hash comparison against the ratified B03 baseline. Earlier source reconnaissance reported no unauthorized B03/schema/persistence changes, but this ledger does not represent a new final hash audit.

## 6. Limitations and outstanding evidence

1. No live Ollama execution has been demonstrated. Adapter tests used deterministic fake openers and mock responses.
2. Prompt-injection tests demonstrate application controls, not live-model security guarantees.
3. Final source-hash comparison for all protected B03 files remains outstanding.
4. The recorded RP-01 through RP-06 hash inventory is not yet a complete repository-wide hash manifest.
5. The existing context-assembler character-limit and greedy-selection interpretation findings require reconciliation against the governing B04 acceptance specification before Gate 3 closure.
6. The legacy B03 persistence test remains outside the canonical regression suite due to its known Windows SQLite teardown issue.

No limitation above is silently treated as passed.

## 7. Acceptance disposition

| Item | Disposition |
|---|---|
| RP-01 through RP-06 targeted implementation and tests | Completed |
| B04 regression | 77/77 passed |
| Canonical B03 regression | 71/71 passed |
| Combined reported regression | 148/148 passed |
| Live Ollama proof | Not demonstrated |
| Final protected-source hash audit | Pending |
| Remaining acceptance interpretation findings | Pending reconciliation |
| Gate 3 formal closure | Not yet established |
| Gate 4 authorization | Not granted |

## 8. Ratification record

**Architect's decision:** RATIFIED.

The Architect ratifies this document as the authoritative B04 Gate 3 remediation evidence register baseline, version 1.0.0, with the limitations and outstanding items explicitly retained.

This ratification confirms the evidence-register structure, recorded remediation disposition, and reported regression results. It does not waive outstanding evidence, certify live-provider behavior, or constitute Gate 3 closure.

Only the Architect may subsequently accept the outstanding evidence and declare Gate 3 closed.

**Gate 4 remains unauthorized.**

---

**End of document.**

---

## ASSEMBLY 1 — CONTEXT ASSEMBLER ACCEPTANCE

**Date:** 2026-11-10  
**Component:** B04 Assembly 1 — ContextAssembler  
**Disposition:** IMPLEMENTATION TESTING ACCEPTED — Architect ratification of policy recorded.

### Architect-ratified context assembly policy

1. `max_characters` counts only `len(memory.content)`.
2. Records are evaluated in supplied input order.
3. A record that exceeds the remaining character budget is excluded whole.
4. Evaluation continues with subsequent records after an exclusion.
5. Included records retain their original relative input order.
6. Individual memory content is never truncated.
7. No ranking or serialized-payload character accounting is performed.

### Test coverage increment

Two tests were added to `tests/test_b04_foundation.py`:

- `test_character_limit_counts_content_only`
- `test_continues_after_excluding_non_fitting_record`

Focused ContextAssembler suite: **9/9 PASS**.

Full B04 regression:

- `test_b04_foundation.py`: 17/17
- `test_b04_model_adapter.py`: 5/5
- `test_b04_ollama_adapter.py`: 13/13
- `test_b04_extraction.py`: 24/24
- `test_b04_extraction_integration.py`: 11/11
- `test_b04_trusted_capture_handoff.py`: 9/9

**B04 regression total: 79/79 PASS.**

Canonical B03 regression:

- `test_b03_contracts.py`: 19/19
- `test_b03_serialization.py`: 10/10
- `test_b03_persistence_v2.py`: 10/10
- `test_b03_uuidv4.py`: 4/4
- `test_b03_f05.py`: 8/8
- `test_b03_relationships.py`: 9/9
- `test_b03_activity_events.py`: 11/11

**B03 regression total: 71/71 PASS.**

**Combined reported regression: 150/150 PASS.**

### Integrity and scope

- Test file: `tests/test_b04_foundation.py`
- Original test-file backup: `tests/test_b04_foundation.py.bak_ASSEMBLY1_20261110`
- Original and backup SHA256: `3B785D54A10D1B8ADEC1B0DC07EE4CA5BC73829D1477999F77462722C71555A3`
- Updated test-file SHA256: `D886B6E9A2559C7C924B4C812BA6D22E1463CE19BE51921565F88BCDE09B7446`
- No ContextAssembler production-code changes were made.
- No B03 production, schema, or persistence changes were made.

### Acceptance boundary

Assembly 1 has passed focused testing and the reported B04/B03 regression suites. This evidence does not independently declare B04 Gate 3 closed. Gate 4 remains unauthorized. Formal Gate 3 acceptance and closure remain under the Architect's authority.

**End of Assembly 1 acceptance addendum.**

## Gate 4 — Integrated Workflow Evidence Consolidation

**Evidence date:** 2026-11-10  
**Controlling implementation authorization:** P1-DM-B04-G4-001 v1.0.0  
**Controlling implementation plan:** B04-G4-PLAN-001 v1.0.0  
**Evidence register:** This append-only section supplements the historical Gate 3 record.  
**Status:** Gate 4 implementation and reported regression evidence consolidated; Gate 4 closure remains subject to separate Architect review and ratification.

### 1. Scope and authority

Gate 4 implementation was authorized for the B04 application integration boundary. The implementation connects extraction, explicit approval and capture, B03 persistence, retrieval, context assembly, provider-neutral response generation, and construction of the existing B03 ModelResponseOutcome.

The implementation does not authorize changes to B03 persistence contracts or schema, response persistence, automatic candidate approval, autonomous verification or promotion, B05 work, or modification of the protected external Satori rag.db.

The existing Gate 3 evidence and its historical status statements are retained unchanged. This section records subsequent Gate 4 evidence and does not retroactively alter Gate 3 history.

### 2. Integration test evidence

**Test module:** `tests/test_b04_workflow_integration.py`

**Reported focused result:** 13/13 passed.

The module uses a temporary SQLite database initialized from the authoritative B03 schema and a real B03 MemoryStore. Its complete success-path test exercises extraction, explicit application-controlled approval and capture, retrieval, context assembly, response generation, and response outcome construction.

The success-path assertions verify:
- Extraction proposes a candidate without persisting it.
- Capture occurs only through an explicit application-controlled call.
- Persisted and retrieved atom, version, and content-hash identities remain consistent.
- Retrieved verification status remains UNVERIFIED.
- Trusted provenance survives persistence and retrieval.
- Context contains the captured version.
- The response prompt includes the caller request and memory identity/provenance context.
- Memory content is represented as data, not instructions.
- The existing B03 ModelResponseOutcome is constructed with the expected response and retrieved version identity.
- Response generation does not create or modify B03 persistence rows.

#### 2.1 Required failure-path mapping

| Gate 4 failure requirement | Integration test |
|---|---|
| Capture failure blocks downstream processing | `test_capture_failure_prevents_retrieval_and_response_generation` |
| Retrieval not-found is explicit | `test_missing_memory_returns_not_found_and_preserves_capture_result` |
| Retrieval exception is distinct from not-found | `test_retrieval_exception_is_distinct_from_not_found` |
| Context assembly exception preserves completed stages | `test_context_assembly_exception_preserves_capture_and_retrieval` |
| Captured version excluded from context blocks generation | `test_captured_version_excluded_from_context_blocks_generation` |
| Missing response adapter is explicit | `test_missing_response_adapter_preserves_completed_stages` |
| Unsuccessful model/provider result is reported | `test_model_declared_failure_becomes_explicit_response_outcome` |
| Response adapter exception is explicit | `test_response_adapter_exception_preserves_context` |
| Invalid response adapter result is rejected | `test_invalid_response_adapter_result_is_rejected` |
| Response outcome construction failure is explicit | `test_response_outcome_construction_failure_is_reported` |

All ten failure scenarios listed in the Gate 4 sub-anchor §9.2 have an explicit corresponding integration test in the supplied module.

Additional defensive integration tests:
- `test_invalid_retrieval_object_is_rejected`
- `test_invalid_context_items_block_generation`

The integration module contains 13 tests in total: one complete success-path test and twelve failure or defensive-validation tests.

### 3. Regression results

The following results were reported by the Architect from local PowerShell test executions:

| Test scope | Result | Execution evidence |
|---|---:|---|
| Focused B04 integration module | 13/13 passed | Dedicated module run |
| Full B04 test suite | 92/92 passed | `unittest discover -s tests -p "test_b04*.py" -v` |
| Canonical B03 regression suite | 71/71 passed | Seven designated B03 modules, run individually |
| Combined reported total | 163/163 passed | Arithmetic across the separate B04 and B03 executions |

The 163/163 figure is a combined reported total, not a single combined test invocation.

The seven canonical B03 modules were:
- `test_b03_contracts.py` — 19 passed
- `test_b03_serialization.py` — 10 passed
- `test_b03_persistence_v2.py` — 10 passed
- `test_b03_uuidv4.py` — 4 passed
- `test_b03_f05.py` — 8 passed
- `test_b03_relationships.py` — 9 passed
- `test_b03_activity_events.py` — 11 passed

The legacy `test_b03_persistence.py` was intentionally excluded because of the previously identified Windows SQLite teardown/unclosed-connection issue. No claim is made that unrestricted full unittest discovery is clean.

### 4. Protected source and implementation integrity

The Architect supplied the following SHA-256 results during the Gate 4 integrity audit:

| File | SHA-256 |
|---|---|
| `src/dynamic_memory/schema.sql` | `40F609358C7B8EE87ADB6F2CA127ABFCD82187E9D0AB08EA9D4FB725D89AC444` |
| `src/dynamic_memory/contracts.py` | `2E940C33CAC1C39D7D83E8B34E4411E6AF39A5D98281854CF3049621558205BE` |
| `src/dynamic_memory/persistence.py` | `BC0B7F11F483CD450A419CA263EDDC7580C546FDFA9C8E701E162CFE7CF8D31E` |
| `src/dynamic_memory/application/results.py` | `554CCA42F47C1B97440F37F614E8532605B3F0334D23BA53003083BE46C2898C` |
| `src/dynamic_memory/application/entry.py` | `C108DB3F24876E6F42A5229C9DE24E6D80DEB59F169D25028869C166E2E89295` |
| `src/dynamic_memory/application/__init__.py` | `D03B580DF99B0AE79396B52926D4D59E976871C317F4A2E6CF6DF3C3C780F755` |
| `tests/test_b04_workflow_integration.py` | `A05CC7D1E428FC92440267D4EE483474A79D322961030C1C9107966985D53090` |
| `docs/architecture/P1-DM-B04-G4-001_v1.0.0.md` | `9BCF44DE1FE98A92E38D26B739C7CDA736CF31892AF4D2AB7F5757C129B15B63` |
| `docs/architecture/B04-G4-PLAN-001_v1.0.0.md` | `570090AC113994042FA9D7E5687D476422371B556AFC029514A968E72E5FCCA2` |

These values are recorded as the Architect-reported integrity audit. The protected B03 schema, contracts, and persistence source hashes match the recorded baselines.

### 5. Backup and change-control record

Recorded implementation backups:

| Artifact | Backup |
|---|---|
| Workflow result contract | `evidence/backups/results.py.bak_G4_001` |
| Application entry implementation | `evidence/backups/entry.py.bak_G4_002` |
| Application entry integrity patch | `evidence/backups/entry.py.bak_G4_003` |
| Application exports | `evidence/backups/application_init.py.bak_G4_003` |
| Integration failure-path tests | `evidence/backups/test_b04_workflow_integration.py.bak_G4_FAILURE_PATHS` |

The integration test backup SHA-256 is:

`0a369711cb9df22b99fb43dab3d042083d0af518e5118921ba32047fa989daf5`

The updated integration test SHA-256 is:

`a05cc7d1e428fc92440267d4ee483474a79d322961030c1c9107966985d53090`

The integration test patch changed only the B04 integration test module. No production source modification was required for the final three failure-path tests.

### 6. Deferred evidence and operational calibration

Two areas are explicitly deferred and are not represented as passed automated tests:

1. **Extraction failure coverage:** the supplied integration module proves that extraction is proposal-only and does not persist before explicit approval. It does not independently demonstrate every extraction-failure or invalid-extraction-output scenario. This can be explored later if required by subsequent evidence or live behaviour.
2. **Hardware-dependent timeout behaviour:** the supplied integration module tests provider-declared failure and an unexpected response-adapter exception, but does not assert a specific timeout exception or duration.

The Architect reports prior Qwen testing with a 600-second timeout. This is operational calibration context, not evidence of a universal timeout guarantee or a live Ollama test in this Gate 4 run.

Timeout behaviour is deferred to actual live-model testing and calibration against the hardware, model, workload, and runtime configuration in use. A future hardware upgrade may require recalibration. This deferral does not weaken the ten explicitly tested Gate 4 §9.2 failure paths.

No claim is made that live Ollama behaviour, hostile-source resistance in a live model, or hardware-specific timeout performance has been established by these deterministic integration tests.

### 7. Gate 4 evidence assessment

The consolidated evidence supports the following findings:

- The complete B04 application workflow is exercised against real temporary B03 SQLite persistence.
- Explicit candidate approval remains an application-controlled boundary.
- Retrieved identity, provenance, and UNVERIFIED status are asserted.
- Response generation is provider-neutral through independent adapter injection.
- The existing B03 ModelResponseOutcome contract is used without extending B03 persistence.
- Completed workflow stages are preserved when later stages fail.
- All ten Gate 4 sub-anchor §9.2 failure scenarios have corresponding explicit integration tests.
- Additional invalid retrieval and context validation paths are tested.
- The reported B04 and canonical B03 regression suites pass.
- Protected B03 source hashes match their recorded baselines.
- Deferred extraction and hardware-timeout evidence is explicitly identified rather than overstated.

**Evidence consolidation is complete when this append is verified in the ledger. This statement does not itself ratify Gate 4 closure.**

### 8. Authority and next gate

Gate 4 closure remains subject to a separate Architect review and explicit ratification.

Gate 5 is not automatically authorized by this evidence consolidation. No B05 implementation, restart-persistence acceptance work, or other Gate 5 activity is authorized by this entry.

The Architect retains sole authority to accept the Gate 4 evidence, close Gate 4, and separately authorize the next gate.
