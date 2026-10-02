# Pipeline.md — Optimizer Execution Specification

## 1. Pipeline Overview

```text
UPLOAD
  ↓
VALIDATE
  ↓
SECURE DECODE
  ↓
CANONICALIZE
  ↓
ANALYZE
  ↓
BUILD FINITE Θ(job)
  ↓
STAGE 0: SIZE PREDICTION
  ↓
STAGE 1: COARSE SWEEP
  ↓
STAGE 2: PROXY EVALUATION + PRUNING
  ↓
STAGE 3: ADAPTIVE QUALITY SEARCH
  ↓
STAGE 4: FINALISTS
  ↓
FULL-RES BUTTERAUGLI
  ↓
STAGE 5: LOCAL REFINEMENT
  ↓
INDEPENDENT FINAL ENCODE
  ↓
EXACT VERIFICATION
  ↓
COMPLETED / TERMINATION STATUS
```

---

## 2. Job Model

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TargetRange:
    min_bytes: int
    max_bytes: int

@dataclass(frozen=True)
class SearchBudget:
    max_total_encodes: int = 40
    max_parallel_encodes_per_job: int = 4
    max_coarse_candidates: int = 18
    max_quality_searches: int = 12
    max_finalists: int = 4
    max_resolution_trials: int = 5
    max_wall_clock_ms: int = 10_000
    max_memory_mb_per_worker: int = 4096
```

---

## 3. Candidate Schema

```python
@dataclass(frozen=True)
class CandidateParams:
    format: str
    scale: float
    width: int
    height: int
    quality: int | float
    chroma: str | None
    progressive: bool | None
    metadata_policy: str
    color_policy: str

@dataclass
class CandidateRecord:
    params: CandidateParams
    predicted_size_bytes: int | None
    actual_size_bytes: int | None
    proxy_quality: float | None
    butteraugli_distance: float | None
    ssim: float | None
    ms_ssim: float | None
    psnr_db: float | None
    delta_e: float | None
    feasible: bool | None
    guardrail_flags: list[str]
    encoded_path: str | None
```

---

## 4. Finite Search Space Construction

The search space is generated once per job.

```python
ALLOWED_SCALES = (1.0, 0.8, 0.5)
ALLOWED_CHROMA = ("420", "444")
ALLOWED_PROGRESSIVE = (False, True)

# Quality values are bounded by codec-specific configuration.
QUALITY_RANGE = range(1, 101)
```

The production implementation should use codec-specific legal ranges rather than assuming a common 1–100 scale internally.

A candidate-builder applies hard constraints before a candidate reaches the encoder.

Example hard filters:

```text
JPEG + alpha required       → reject
Unsupported ICC policy      → reject
Unsupported chroma          → reject
Unsupported progressive     → reject
Explicit format mismatch   → reject
Scale below min scale       → reject
```

`Theta(job)` after filtering must remain enumerable.

---

## 5. Canonicalization Pipeline

```text
source bytes
   ↓
secure decoder
   ↓
orientation resolution
   ↓
ICC validation
   ↓
canonical color-managed representation
   ↓
alpha preservation
   ↓
normalized metadata state
```

### Provenance invariant

All candidates originate from this canonical representation or deterministic preprocessing from it.

Never do:

```text
candidate A encoded
      ↓
resize candidate A
      ↓
candidate B
```

Always do:

```text
canonical master
      ↓
resize to candidate B scale
      ↓
encode candidate B
```

---

## 6. Comparison Space

The optimizer declares a comparison-space configuration, for example:

```text
comparison_space:
    transfer: sRGB
    channels: RGB
    bit_depth: 8
```

or a configured linear-RGB equivalent.

The canonical reference and decoded candidate must undergo symmetric conversion into that space.

The comparison-space identifier is persisted with the job.

---

## 7. Stage 0 — Size Prediction

Purpose: seed searches without performing unnecessary full encodes.

Pseudo-interface:

```python
def seed_quality_search(source, cell, target):
    prediction = encoder.predict_size(source, cell.request)

    if prediction is None:
        return default_quality_seed(cell, target)

    return infer_quality_bracket(prediction, target)
```

Predictions are advisory only.

No candidate is marked feasible from prediction.

---

## 8. Stage 1 — Coarse Candidate Sweep

The coarse stage is bounded before execution.

```python
coarse_candidates = generate_coarse_candidates(theta)
coarse_candidates = coarse_candidates[:budget.max_coarse_candidates]
```

A practical coarse policy is to sample:

- a bounded number of formats;
- scales such as 1.0, 0.8, 0.5 where applicable;
- content-appropriate chroma choices;
- three codec-specific quality checkpoints per cell.

The coarse budget is the hard maximum, not a target.

Each candidate is encoded at most once in Stage 1.

---

## 9. Stage 2 — Proxy Evaluation and Pareto Pruning

For coarse candidates:

```text
encode
  ↓
measure exact bytes
  ↓
decode
  ↓
downscale reference/candidate to proxy resolution
  ↓
compute proxy quality
```

A candidate outside the maximum acceptable size may be retained only if it is needed to establish a search bracket; otherwise it can be discarded.

Dominance rule for pruning:

Candidate A dominates B when A is no worse than B on the declared coarse criteria and strictly better in at least one criterion, according to the configured pruning policy.

The pruning relation is intentionally a screening tool, not the final selection rule.

---

## 10. Stage 3 — Adaptive Quality Search

For every surviving `(format, scale, chroma, progressive, metadata, color)` cell:

```text
identify quality bracket
        ↓
encode midpoint/interpolated quality
        ↓
measure exact size
        ↓
update bracket
        ↓
repeat until:
    target feasibility established or
    search interval exhausted or
    quality-search budget exhausted
```

Binary search is appropriate when the encoder's size/quality relation behaves monotonically over the selected interval.

If monotonicity is violated, the controller shall fall back to bounded local sampling/interpolation.

The optimizer must not assume global monotonicity without checking sampled observations.

---

## 11. Feasibility Tracking

Maintain:

```python
min_verified_size = +inf
max_verified_size = -inf
best_feasible = None
```

For every verified candidate:

```python
min_verified_size = min(min_verified_size, candidate.size)
max_verified_size = max(max_verified_size, candidate.size)

if target.min_bytes <= candidate.size <= target.max_bytes:
    best_feasible = update_best(candidate)
```

Important: these observed extrema are not automatically the extrema of the complete search space `Theta(job)`.

An unreachability status may be emitted only if the controller has exhausted or otherwise validly established the relevant accepted boundary of `Theta(job)`.

---

## 12. Stage 4 — Finalist Selection

Select at most:

```text
max_finalists = 4
```

Finalists should represent different potentially optimal cells rather than four arbitrary highest-scoring coarse candidates.

Each finalist must have exact size and proxy-quality measurements.

---

## 13. Full-Resolution Perceptual Evaluation

For each finalist:

```text
canonical reference
      ↓
comparison-space conversion
      ↓
Butteraugli reference

finalist bytes
      ↓
decode
      ↓
comparison-space conversion
      ↓
Butteraugli candidate
```

Secondary metrics may also be calculated:

- SSIM
- MS-SSIM
- PSNR
- ΔE/color error

These are diagnostics/guardrails, not weighted components of the primary objective.

---

## 14. Lexicographic Selection

```python
def select_best(candidates):
    feasible = [
        c for c in candidates
        if c.size_bytes is not None
        and B_MIN <= c.size_bytes <= B_MAX
    ]

    if not feasible:
        return None

    # Primary: lowest Butteraugli distance.
    min_butter = min(c.butteraugli_distance for c in feasible)
    near = [c for c in feasible if is_near_tie(c.butteraugli_distance, min_butter)]

    # Secondary: preserve more pixels.
    max_pixels = max(c.params.width * c.params.height for c in near)
    near = [c for c in near if c.params.width * c.params.height == max_pixels]

    # Tertiary: configured diagnostics/guardrails.
    near = apply_near_tie_diagnostics(near)

    # Final tie-breaker: processing cost.
    return min(near, key=processing_cost)
```

`is_near_tie()` must be calibrated empirically and is not an architectural constant.

---

## 15. Stage 5 — Local Refinement

When budget remains:

```text
winner quality q
    ↓
q-2, q-1, q, q+1, q+2
```

subject to codec legality and total candidate budget.

For each local candidate:

- encode from canonical source path;
- measure exact bytes;
- verify feasibility;
- evaluate primary metric as needed;
- replace winner only when lexicographic rules improve it.

---

## 16. Final Independent Encode

The final artifact must be produced independently from the canonical master.

```text
canonical master
      ↓
selected parameters
      ↓
final encoder invocation
      ↓
final artifact
```

It must not simply copy an internal temporary candidate as the public result if the finalization path could alter bytes or metadata.

---

## 17. Verification

```python
def verify_final_artifact(path, target, expected):
    actual_size = stat(path).size
    decoded = secure_decode(path)

    assert actual_size == expected.recorded_size
    assert decoded.format == expected.format
    assert decoded.width == expected.width
    assert decoded.height == expected.height
    assert target.min_bytes <= actual_size <= target.max_bytes

    return sha256(path), actual_size
```

Verification failure is terminal:

```text
OUTPUT_VERIFICATION_FAILURE
```

---

## 18. Termination Logic

A simplified controller is:

```python
def optimize(job):
    start_timer()
    enforce_job_budget(job)

    source = secure_decode(job.source)
    master = canonicalize(source, job.color_policy, job.metadata_policy)
    analysis = analyze(master)
    theta = build_finite_theta(job, analysis)

    run_stage_0_predictions(master, theta, job)
    coarse = run_stage_1(master, theta, job.budget)
    survivors = run_stage_2_prune(coarse, job.budget)
    searched = run_stage_3_quality_search(master, survivors, job)
    finalists = choose_finalists(searched, job.budget.max_finalists)

    evaluated = evaluate_full_resolution(master, finalists, job)
    winner = lexicographic_select(evaluated)

    if budget_remaining(job):
        winner = local_refine(master, winner, job)

    if winner is not None:
        final = independent_final_encode(master, winner.params, job)
        verification = verify_final_artifact(final, job.target, winner)
        return completed_result(final, verification)

    status = determine_termination_status(job, theta)
    return termination_result(status)
```

---

## 19. Correct Termination Semantics

### `COMPLETED`

At least one independently verified final artifact satisfies the requested size interval.

### `CONSTRAINT_UNREACHABLE_MIN`

The complete accepted search space has been sufficiently exhausted/established to prove:

```text
maxB(Theta) < B_min
```

### `CONSTRAINT_UNREACHABLE_MAX`

The complete accepted search space has been sufficiently exhausted/established to prove:

```text
minB(Theta) > B_max
```

### `TIME_BUDGET_EXCEEDED`

The search terminated because wall-clock budget was exhausted and the relevant infeasibility bound was not proven.

### `CANDIDATE_BUDGET_EXCEEDED`

The search terminated because candidate/encode budget was exhausted and the relevant infeasibility bound was not proven.

---

## 20. Important Feasibility Edge Cases

### Target already contains source size

A high-quality near-lossless candidate may satisfy the interval without aggressive optimization.

### Target below any accepted candidate

```text
minB(Theta) > B_max
→ CONSTRAINT_UNREACHABLE_MAX
```

The system may return the smallest verified accepted candidate as a best-effort artifact/report if product policy allows.

### Target above every accepted candidate

```text
maxB(Theta) < B_min
→ CONSTRAINT_UNREACHABLE_MIN
```

Do not add arbitrary padding.

### Budget exhaustion

Do not infer either unreachability status solely from incomplete search.

---

## 21. Candidate Cache Key

```text
SHA256(
    source_hash,
    params_hash,
    encoder_version,
    libvips_version,
    pipeline_version,
    color_management_version,
    comparison_space_version
)
```

Cache storage should be bounded using Redis eviction and/or object-store lifecycle rules.

---

## 22. Ephemeral Artifact Lifecycle

Candidate binaries belong in ephemeral worker storage:

```text
/job/{job_id}/candidates/{candidate_hash}
```

Deletion policy:

```text
job completes/fails
      ↓
cleanup
      ↓
TTL-based safety sweep
```

Only the original and selected output have durable retention unless a diagnostic/audit mode explicitly retains additional candidates.

---

## 23. Search Pseudocode — More Explicit

```python
def search(job, master, theta):
    budget = job.budget
    ledger = CandidateLedger(budget)

    # Stage 0
    seeds = predict_and_bracket(master, theta, job.target)

    # Stage 1
    coarse = materialize_bounded_coarse_candidates(
        theta,
        seeds,
        max_candidates=budget.max_coarse_candidates,
    )
    ledger.reserve(len(coarse))
    coarse_results = parallel_encode(
        master,
        coarse,
        max_parallel=budget.max_parallel_encodes_per_job,
    )

    # Stage 2
    proxy_results = proxy_evaluate(master, coarse_results)
    survivors = pareto_prune(proxy_results)

    # Stage 3
    refined = []
    for cell in bounded_cells(survivors):
        while ledger.quality_searches < budget.max_quality_searches:
            if budget_exhausted(job):
                return terminate_budget(ledger)

            candidate = next_quality_probe(cell)
            result = encode_and_measure(master, candidate)
            ledger.record(result)
            update_cell_bracket(cell, result)

            if cell.search_complete:
                break

        refined.extend(cell.verified_candidates)

    # Stage 4
    finalists = choose_diverse_finalists(refined, budget.max_finalists)

    full = full_resolution_evaluate(master, finalists)
    winner = lexicographic_select(full)

    # Stage 5
    if winner and budget_remaining(job):
        winner = local_refine(master, winner, ledger, job)

    return winner, ledger
```

---

## 24. Guardrails

A candidate may be flagged, not automatically rejected, when diagnostics show behavior inconsistent with its primary metric.

Examples:

```text
extreme SSIM drop
large ΔE/color shift
unexpected edge degradation
alpha mismatch
incorrect ICC interpretation
```

Guardrail policy is content- and calibration-dependent.

---

## 25. Testing as Executable Invariants

Property tests should include:

```python
@given(job, candidate_space)
def test_theta_is_finite(theta):
    assert len(theta) <= configured_theta_bound


def test_budget_does_not_imply_unreachable(result):
    if result.status in {TIME_BUDGET_EXCEEDED, CANDIDATE_BUDGET_EXCEEDED}:
        assert not result.unreachable_proven


def test_successful_size_constraint(result):
    if result.status == COMPLETED:
        assert B_MIN <= result.actual_size <= B_MAX
```

Additional integration tests must verify provenance by tracking the source object identity/hash used by every candidate encode.
