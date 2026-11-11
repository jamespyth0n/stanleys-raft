# P1-DM-B04-001 — Gate 1 Deliverable
## B04 Interface and Boundary Specification

**Parent Anchor:** P1-DM-B04-001 v1.0.0  
**Deliverable:** B04-IF-001  
**Version:** 0.1.0  
**Status:** DRAFT — Architect Review  
**Prepared by:** Stanley  
**Date:** 2026-11-10  
**Purpose:** Establish exact B04 service boundaries against the inspected B03 contracts.

---

## 1. Evidence basis

This specification is derived from the Architect-supplied inspection of:

- `dynamic_memory.contracts`
- `dynamic_memory.persistence.MemoryStore`
- Existing Pydantic V2 field definitions
- Existing `MemoryStore` public method signatures

The following B03 interfaces are authoritative:

```python
MemoryStore(db_path=None)

capture(request: CaptureRequest, *, source_id: str) -> CaptureResult

revise(
    atom_id: UUID,
    request: CaptureRequest,
    *,
    source_id: str
) -> CaptureResult

get_version(version_id: UUID) -> RetrievedMemory | None

add_relationship(
    from_version_id: UUID,
    to_version_id: UUID
) -> RelationshipRecord

get_relationships(version_id: UUID) -> list[RelationshipRecord]

get_activity_events(
    *,
    atom_id: UUID | None = None,
    version_id: UUID | None = None
) -> list[ActivityEvent]
```

B04 must consume these interfaces without modifying them.

## 2. Contract findings affecting B04

### 2.1 Capture provenance boundary

`CaptureRequest` contains:

- content
- knowledge_type
- epistemic_status
- verification_status
- source_type
- source_locator
- valid_from
- valid_until

It does not contain `source_id`.

B03 requires `source_id` as a separate keyword-only argument to `capture()` and `revise()`.

**B04 decision:** The Capture Service receives trusted source identity separately from model extraction output and passes it directly to B03.

### 2.2 Provenance records

`ProvenanceRecord` requires:

- provenance_id
- version_id
- source_type
- source_id
- captured_at

Optional fields:

- source_locator
- source_created_at
- source_content_hash

**B04 decision:** The application owns source identity and metadata. Model output cannot create, override, or authorize provenance records.

### 2.3 Context preservation

`ContextItem` requires:

- atom_id
- version_id
- content
- provenance

**B04 decision:** Context assembly must use the corresponding fields from `RetrievedMemory`, preserving the exact version and provenance association.

### 2.4 Response outcome limitation

`ModelResponseOutcome` requires:

- request_id
- model_name
- response_text
- retrieved_version_ids
- completed_at
- success

`error_type` is optional.

Even a failed outcome requires `response_text`.

**B04 decision:** Do not alter the B03 contract. Application-level failures before a model response exists must be represented by a B04 internal result. Construct `ModelResponseOutcome` when a model operation has reached the response-outcome boundary. For a failed model operation, use an empty response string if necessary and populate `error_type`.

No response persistence is introduced.

### 2.5 Relationship restriction

`RelationshipRecord.relation_type` is restricted to:

```python
Literal["disputes"]
```

**B04 decision:** Retrieval may expose existing disputes relationships. No new relationship types or registries are introduced.

### 2.6 Validation inheritance

All inspected contracts inherit from `Contract`, which forbids extra fields.

The existing base validator also enforces timezone-aware UTC datetimes and UUIDv4 requirements.

**B04 decision:** B04 must not bypass Pydantic validation or silently normalize invalid application inputs outside the existing contract rules.

---

## 3. Proposed B04 internal interfaces

The following interfaces are proposed application-level boundaries. They do not modify B03 contracts.

### 3.1 Model Adapter

Proposed interface:

```python
class ModelAdapter(Protocol):

    def generate(
        self,
        *,
        prompt: str,
        model_name: str | None = None,
    ) -> ModelResult:
        ...
```

`ModelResult` is a B04 internal result structure containing:

- success
- response_text
- model_name
- error_type
- error_message

Requirements:

- Provider-specific HTTP communication stays inside the adapter.
- Initial implementation uses Ollama HTTP API.
- Python standard-library HTTP facilities are preferred.
- Mock adapter must support deterministic testing.
- Adapter must not access `MemoryStore`.

### 3.2 Extraction Service

Proposed interface:

```python
class ExtractionService:

    def extract(
        self,
        *,
        source_content: str,
    ) -> ExtractionResult:
        ...
```

`ExtractionResult` is a B04 internal result containing:

- success
- validated extraction candidates
- error_type
- error_message

Each candidate must contain only fields required to construct a valid `CaptureRequest`.

Trusted source identity and provenance metadata are not extraction fields.

Extraction must reject:
- Invalid JSON or equivalent structured output.
- Missing required content.
- Unknown classification values.
- Unsupported fields.
- Invalid temporal values.
- Model output attempting to provide trusted provenance.

### 3.3 Capture Service

Proposed interface:

```python
class CaptureService:

    def capture(
        self,
        *,
        request: CaptureRequest,
        source_id: str,
    ) -> CaptureResult:
        ...
```

Responsibilities:

1. Validate the request.
2. Validate trusted source identity.
3. Call `MemoryStore.capture(request, source_id=source_id)`.
4. Return the exact B03 `CaptureResult`.
5. Propagate or translate persistence errors into a documented B04 application failure.

The service must not independently write to SQLite.

A separate revision operation may be introduced only as a thin wrapper around the existing `MemoryStore.revise()` interface.

### 3.4 Retrieval Service

Proposed interface:

```python
class RetrievalService:

    def get_version(
        self,
        *,
        version_id: UUID,
    ) -> RetrievedMemory | None:
        ...

    def get_relationships(
        self,
        *,
        version_id: UUID,
    ) -> list[RelationshipRecord]:
        ...

    def get_activity_events(
        self,
        *,
        atom_id: UUID | None = None,
        version_id: UUID | None = None,
    ) -> list[ActivityEvent]:
        ...
```

Responsibilities:

- Delegate to existing B03 methods.
- Preserve returned contract types.
- Distinguish not-found from persistence errors.
- Avoid hidden retrieval or ranking behavior.

### 3.5 Context Assembler

Proposed interface:

```python
class ContextAssembler:

    def assemble(
        self,
        *,
        memories: list[RetrievedMemory],
        max_items: int,
        max_characters: int,
    ) -> ContextAssemblyResult:
        ...
```

`ContextAssemblyResult` is a B04 internal result containing:

- success
- context_items
- included_version_ids
- excluded_version_ids
- total_characters
- error_type

Rules:

- Each `ContextItem` derives from a corresponding `RetrievedMemory`.
- Atom identity, version identity, content, and provenance must be preserved.
- Limits must be explicit.
- No silent truncation of individual memory content.
- Excluded records must be identifiable.
- Empty input must produce a valid empty result.

The initial ordering policy must be deterministic and documented. No relevance-ranking algorithm is authorized.

### 3.6 Application Entry

Proposed interface:

```python
class DynamicMemoryApplication:

    def __init__(
        self,
        *,
        store: MemoryStore,
        model_adapter: ModelAdapter,
        extraction_service: ExtractionService,
        capture_service: CaptureService,
        retrieval_service: RetrievalService,
        context_assembler: ContextAssembler,
    ):
        ...
```

Responsibilities:

- Coordinate application operations.
- Keep services independently testable.
- Return explicit application results.
- Avoid direct database operations.
- Avoid provider-specific logic.

The entry point must not duplicate service responsibilities.

---

## 4. Trusted data ownership matrix

| Field or decision | Owner |
|---|---|
| Original source content | Application caller |
| Source ID | Application caller / trusted source boundary |
| Source type | Application caller |
| Source locator | Application caller |
| Source creation timestamp | Trusted source boundary |
| Source content hash | Application-controlled |
| Extracted knowledge content | Model proposal |
| Knowledge type | Model proposal, application validated |
| Epistemic status | Model proposal, application validated |
| Verification status | Explicit application policy |
| Atom ID | B03 persistence |
| Version ID | B03 persistence |
| Provenance ID | B03 persistence |
| Retrieved version | B03 persistence |
| Context construction | B04 assembler |
| Generated response | Model adapter |
| Response outcome | B04 application boundary |

**Critical rule:** The model cannot assign a trusted identity, establish source authenticity, or independently authorize a verified status.

The application must not equate model confidence with verification.

---

## 5. Error and result conventions

B04 internal services should distinguish:

- Success
- Validation failure
- Not found
- Provider failure
- Timeout
- Persistence failure
- Context assembly failure
- Unexpected internal failure

B04 internal result structures must not be confused with B03 persistence contracts.

No error should be converted into a successful-looking result.

Partial success must identify which operation succeeded and which failed.

Retries must not cause duplicate captures.

---

## 6. Gate 1 test matrix

| Test area | Required evidence |
|---|---|
| Model adapter | Mock success and provider failure |
| Extraction | Valid output and malformed output rejection |
| Contract validation | Invalid enums and unsupported fields rejected |
| Provenance | Model cannot supply trusted source identity |
| Capture service | Correct delegation to B03 |
| Retrieval service | Exact B03 result preservation |
| Context assembler | Identity and provenance preservation |
| Context limits | Deterministic exclusions; no silent content truncation |
| Application entry | Service coordination and explicit failures |
| B03 regression | Existing 71 canonical tests remain passing |

All tests must be independently reproducible.

---

## 7. Implementation order

1. Finalize internal result structures and service interfaces.
2. Build deterministic service tests using mocks.
3. Implement capture and retrieval wrappers.
4. Implement context assembly.
5. Implement provider-neutral adapter interface.
6. Implement Ollama HTTP adapter.
7. Implement extraction and validation.
8. Integrate application entry.
9. Run B04 tests and B03 regression suite.
10. Produce evidence and request Gate 1 completion review.

No B03 source modifications are permitted.

---

## 8. Gate 1 exit criteria

Gate 1 is eligible for completion when:

- All service boundaries are documented.
- B04 internal result structures are defined.
- Trusted provenance ownership is explicit.
- B03 contract limitations are accommodated without modification.
- Provider-neutral adapter behavior is defined.
- Error conventions are documented.
- Test matrix is approved.
- No unresolved interface decision prevents implementation.

**Current status:** DRAFT — Architect Review.

**Architect decision:** Pending.

---

## 9. Change control

Any requirement that cannot be met using existing B03 contracts must be raised as a separate finding.

No B03 contract changes may be made to accommodate B04 convenience.

Any proposed expansion must identify its impact, rationale, test requirements, and approval authority.

The Architect retains sole ratification authority.

---

**Gate 1 principle:** Fit the assembly to the foundation. Never bend the foundation to fit the assembly.

# P1-DM-B04-001 — Gate 3 Activation Addendum
## Model Adapter and Extraction Implementation Control

**Parent Anchor:** P1-DM-B04-001 v1.0.0  
**Interface Specification:** B04-IF-001 v0.1.0  
**Addendum:** P1-DM-B04-G3-001  
**Version:** 1.0.0  
**Status:** BUILD AUTHORIZED — Gate 3  
**Date:** 2026-11-10  
**Authority:** Architect — Sole Ratification Authority  
**Prepared by:** Stanley

---

## 1. Purpose

This addendum records the transition from B04 Gate 2 to Gate 3 and establishes the implementation controls for the Model Adapter and Extraction components.

It supplements, and does not replace, the ratified parent anchor.

The governing architecture remains:

- B03 is closed and protected.
- B04 Gate 2 is formally closed.
- B04 Gate 3 is authorized for implementation.
- B04 Gate 4 and Gate 5 remain unauthorized.
- No B05 implementation is authorized.

## 2. Gate status

| Gate | Status |
|---|---|
| Gate 0 — Parent anchor ratification | COMPLETE |
| Gate 1 — Interface and boundary design | APPROVED BASELINE |
| Gate 2 — Deterministic application foundation | CLOSED |
| Gate 3 — Model adapter and extraction | BUILD AUTHORIZED |
| Gate 4 — Integrated workflow | NOT AUTHORIZED |
| Gate 5 — Closure review | NOT AUTHORIZED |

Gate 2 acceptance evidence remains:

- B04 foundation: 15/15 PASS
- B03 canonical regression: 71/71 PASS
- Combined: 86/86 PASS

Gate 2 shall not be reopened without new evidence and explicit Architect authorization.

## 3. Governing interface baseline

`B04-IF-001 v0.1.0` establishes the proposed B04 service boundaries.

The implementation shall preserve these interfaces:

### 3.1 Model Adapter

```python
class ModelAdapter(Protocol):
    def generate(
        self,
        *,
        prompt: str,
        model_name: str | None = None,
    ) -> ModelResult:
        ...
```

`ModelResult` is an internal B04 result containing:

- success
- response_text
- model_name
- error_type
- error_message

Provider-specific communication remains inside the adapter.

### 3.2 Extraction Service

```python
class ExtractionService:
    def extract(
        self,
        *,
        source_content: str,
    ) -> ExtractionResult:
        ...
```

Extraction produces validated candidate records suitable for constructing existing B03 `CaptureRequest` contracts.

Extraction shall not persist data.

### 3.3 Existing B04 foundation

The Gate 2 services and result structures remain the implementation foundation.

Do not duplicate or replace existing functionality merely to accommodate Gate 3.

Inspect existing files and tests before adding or modifying interfaces.

## 4. Gate 3 implementation clarifications

The following clarifications govern implementation.

### 4.1 Verification authority

The model cannot assign or authorize `VerificationStatus`.

Under the current policy, extracted candidates receive:

```python
VerificationStatus.UNVERIFIED
```

Any future policy allowing another application-assigned status requires explicit authorization.

Model confidence is not verification evidence.

### 4.2 Trusted source metadata

The application caller remains authoritative for:

- source_id
- source_type
- source_locator
- source_created_at
- source_content_hash
- captured_at

The model cannot supply or override these fields.

Temporal validity fields (`valid_from`, `valid_until`) may be extracted as candidate values only if the existing B03 contract accepts them and the application validates them.

Parsing success does not establish temporal truth.

The application must reject invalid timestamps and must not silently normalize invalid inputs.

### 4.3 Extraction and adapter dependency

`ExtractionService` shall use the provider-neutral `ModelAdapter`.

The dependency must be explicit and injectable to support deterministic tests.

Responsibilities:

1. Receive original source content.
2. Construct the extraction prompt.
3. Invoke the adapter.
4. Receive the model response.
5. Parse structured output.
6. Reject malformed or unsupported output.
7. Validate candidate fields against existing B03 contracts.
8. Return an explicit `ExtractionResult`.

The extraction service must not communicate directly with Ollama or perform HTTP operations.

## 5. Model and provider implementation

Initial provider: Ollama.

Initial model target: `qwen2.5:14b`.

Implementation requirements:

- Use Python standard-library HTTP facilities initially.
- Keep provider-specific request and response handling inside the Ollama adapter.
- Maintain the provider-neutral `ModelAdapter` boundary.
- Use bounded connection/read timeouts.
- Handle unavailable provider, timeout, HTTP failure, malformed JSON, missing response fields, and provider-reported errors.
- Do not require a live Ollama instance for deterministic tests.
- Do not add dependencies without demonstrated technical necessity.

No cloud providers, distributed deployment, background agents, or conversation-history subsystem are authorized.

## 6. Extraction validation and trust controls

The extraction boundary shall:

- Reject invalid JSON or unsupported structured output.
- Reject missing required content.
- Reject unknown classification values.
- Reject unsupported fields.
- Reject invalid temporal values.
- Reject model-supplied provenance and trusted source metadata.
- Reject model attempts to assign verification authority.
- Preserve epistemic distinctions.
- Preserve uncertainty rather than converting it into certainty.
- Use existing Pydantic V2 contracts as the authoritative structural validator.

`extra="forbid"` remains in force.

Structural validation does not establish semantic accuracy.

A structurally valid candidate remains a model proposal until accepted by the application workflow.

## 7. Error conventions

B04 internal results must distinguish at minimum:

- validation failure
- provider failure
- timeout
- malformed provider response
- malformed extraction output
- contract validation failure
- persistence failure where applicable
- unexpected internal failure

No failure may be represented as successful extraction.

No partial operation may be presented as complete.

Retries must not introduce duplicate captures or obscure the original failure.

Gate 3 shall not introduce automatic capture retries.

## 8. Gate 3 implementation sequence

Implementation proceeds in this order:

1. Inspect existing Gate 2 files and B03 contracts.
2. Reconcile `ModelResult` and extraction result structures with existing `results.py`.
3. Define the provider-neutral adapter interface.
4. Implement deterministic mock adapter tests.
5. Implement Ollama HTTP adapter.
6. Implement provider error and timeout handling.
7. Define extraction candidate structure and prompt.
8. Implement extraction parsing.
9. Implement strict contract validation.
10. Implement adversarial trust-boundary tests.
11. Run Gate 3 tests.
12. Run the canonical 71-test B03 regression suite.
13. Produce the Gate 3 evidence ledger and request review.

Do not begin Gate 4 integration as part of this sequence.

## 9. Change control and protected boundaries

The following remain prohibited:

- B03 contract changes.
- B03 persistence changes.
- Schema or table additions.
- Direct SQLite writes from the adapter or extraction service.
- Model-controlled provenance.
- Model-controlled verification.
- Autonomous promotion.
- Vector databases, embeddings, semantic search, or ranking.
- Response persistence.
- Protected Satori `rag.db` modification.
- Unapproved dependencies.
- Scope expansion into Gate 4 or B05.

Existing files must not be overwritten without inspection, backup, and explicit authorization where required.

Append rather than overwrite.

Any implementation conflict with B03 or this addendum must be raised as a finding rather than resolved through unauthorized contract changes.

## 10. Gate 3 exit criteria

Gate 3 may be submitted for closure review when:

- Provider-neutral adapter interface is implemented.
- Ollama adapter is implemented and isolated.
- Deterministic mock testing works without a live provider.
- Provider failures and timeouts are explicitly handled.
- Extraction parsing and validation are implemented.
- Unsupported fields and trusted metadata injection are rejected.
- Verification authority remains application-controlled.
- All required Gate 3 tests pass.
- Canonical B03 regression remains 71/71 PASS.
- No unauthorized B03 or schema modifications exist.
- Evidence is reproducible and recorded.

Passing tests do not automatically close the gate.

The Architect retains sole ratification authority.

---

## 11. Execution directive

**BUILD MODE — ACTIVE**

Gate 2 is closed.

Gate 3 is authorized.

The supplied `B04-IF-001 v0.1.0` is the interface baseline for implementation, subject to the clarifications in this addendum.

The next action is repository reconnaissance of the existing Gate 2 implementation and B03 contracts, followed by the Gate 3 interface reconciliation.

No implementation assumptions may override the source contracts.

**Governing principle:**

*Fit the assembly to the foundation. Never bend the foundation to fit the assembly.*

**Architect's direction:**

*Keep sailing. Joy will take us further.*

— Stanley
