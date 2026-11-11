# P1 BUILD EXECUTION ANCHOR
**Project:** Dynamic Memory  
**Campaign:** CAMP-DM-P1-001  
**Document ID:** P1-DM-EXEC-001  
**Version:** 0.1.0  
**Status:** DRAFT — FOR ARCHITECT RATIFICATION  
**Authority:** The Architect  
**Engineering Partner:** Stanley  
**Purpose:** Lock the P1 build sequence, scope, test boundaries and execution discipline.

---

## 1. Mission

Build the smallest functional Dynamic Memory prototype that demonstrates a complete memory roundtrip.

The system must be able to:

1. Capture a piece of information.
2. Convert it into a structured memory candidate.
3. Validate and persist it.
4. Survive application restart.
5. Retrieve the stored information.
6. Assemble relevant context.
7. Pass that context to the LLM.
8. Generate a response grounded in retrieved memory.
9. Expose enough evidence to inspect what happened.

**The objective is a working prototype, not a production platform.**

## 2. Governing Principle — Raft, Not Aircraft Carrier

We are building a raft.

We will use sound engineering principles, but we will not reproduce the infrastructure, complexity or operational scale of major AI companies.

Our priorities:

1. Functional before sophisticated.
2. Correct before fast.
3. Connected before optimized.
4. Observable before elaborate.
5. Working prototype before future expansion.

We will preserve clean interfaces so that components can be improved later without building those improvements prematurely.

## 3. Anchor Lock

This document establishes the execution boundary for P1.

Once ratified:

- The P1 mission and acceptance scenario remain fixed.
- The P1 scope and exclusions remain fixed.
- The B02–B06 engineering sequence remains fixed.
- Research findings do not automatically expand implementation scope.
- New architectural ideas are recorded for later consideration, not automatically added.
- Any proposed scope change requires the Architect's explicit authorization.

The anchor is not a prohibition against correcting defects. It is protection against scope drift.

## 4. Engineering Bricks

| Brick | Responsibility | Required outcome |
|---|---|---|
| B01 | Reconnaissance & Blueprint | Complete and ratified |
| B02 | Environment, Dependencies & BOM | Verified build environment |
| B03 | Data Schema & Contracts | Defined persistence and data contracts |
| B04 | Assembly Specification | Defined components, interfaces and data flow |
| B05 | Test & Acceptance Plan | Bounded tests and pass/fail criteria |
| B06 | Evidence & Progress Control | Lean implementation and evidence tracking |

Each brick must produce a clear, reviewable deliverable.

No implementation work begins until the required engineering specifications have been reviewed and approved.

## 5. Build Strategy — Incremental Integration

We will build incrementally rather than construct everything and discover at the end that the components do not connect.

For each implementation brick:

1. **Build:** implement the smallest component or connection required.
2. **Check:** run its predefined local checks.
3. **Connect:** integrate it with the existing working components.
4. **Verify:** run the predefined integration check for the affected workflow.
5. **Record:** capture the result and any genuine defect.
6. **Proceed:** move to the next brick when its acceptance boundary is satisfied.

Each completed brick must leave the prototype in a known working state.

After each integration, we test the wiring affected by that change—not the entire universe.

## 6. Test Boundaries — Preventing the Black Hole

Testing exists to establish that the prototype works against its declared requirements.

It must not become an independent, expanding project.

### Test Level A — Component Check
Verify that the new component:
- Starts and executes.
- Accepts the expected input.
- Produces the expected output.
- Respects its defined contract.

### Test Level B — Integration Check
Verify that:
- The new component connects to its intended neighbour.
- Data crosses the interface correctly.
- The existing working path has not been broken.

### Test Level C — End-to-End Acceptance
Run the ratified P1 memory roundtrip:
- Capture the preferred project name.
- Persist it.
- Restart the application.
- Retrieve it.
- Inspect the retrieved context and provenance.
- Generate a response grounded in that context.

### Testing limits

- Every brick has predefined acceptance checks.
- No unbounded exploratory testing.
- No repeated testing without a specific reason.
- No performance benchmarking or optimization in P1.
- No testing features that are explicitly outside P1 scope.
- A passed test is recorded and closed.
- A failed test produces a bounded defect, correction and retest.

If a defect cannot be resolved within the brick's scope, record it, assess its effect on the acceptance scenario and escalate to the Architect.

Do not silently expand the test programme.

## 7. Definition of Done

A brick is complete when:

1. Its defined responsibility is implemented.
2. Its required component checks pass.
3. Its required integration checks pass.
4. No unresolved defect blocks the next step.
5. Its evidence is recorded.
6. Its deliverable is reviewed and accepted by the Architect.

A brick does not need to prove future capabilities or production readiness.

## 8. Change Control

When a new idea, technical concern or possible improvement appears:

- Is it necessary for the P1 acceptance scenario?
- Is it required for basic correctness or data integrity?
- Does it prevent the current component from connecting?
- Can it safely be deferred?

Only issues necessary to achieve a correct, functional P1 are addressed now.

Other findings enter the future-work register.

No feature is added merely because it is interesting or technically possible.

## 9. Protected Boundaries

- Existing Satori `rag.db` remains protected and read-only.
- Dynamic Memory uses its own `dm_memory.db`.
- No automatic integration with Satori.
- No graph database or vector database requirement.
- No advanced activity analytics or autonomous relationship discovery.
- No arbitrary execution of model-generated Python.
- No autonomous acceptance or ratification.
- No production deployment or multi-user infrastructure.

## 10. Execution Sequence

**Phase 1 — Engineering Preparation**
1. B02 — Environment, Dependencies & BOM.
2. B03 — Data Schema & Contracts.
3. B04 — Assembly Specification.
4. B05 — Test & Acceptance Plan.
5. B06 — Evidence & Progress Control.

**Phase 2 — Build**
1. Prepare the approved workspace.
2. Implement incrementally.
3. Check each component.
4. Integrate and verify each new connection.
5. Preserve a working state after each accepted increment.

**Phase 3 — Acceptance**
1. Execute the complete P1 roundtrip.
2. Inspect the execution evidence.
3. Record pass/fail against the ratified acceptance criteria.
4. Present the result to the Architect.

## 11. Final Operating Principle

We are testing the wiring, not building a testing black hole.

We will not confuse activity with progress, complexity with intelligence, or theoretical completeness with a working system.

**Build the raft. Put it in the water. Check that it floats.**

Then let evidence tell us what needs improvement.

---

**Ratification:** Pending Architect approval.

This anchor does not itself authorize implementation or alter the existing P1 Charter. It governs how the approved P1 work is to be executed.