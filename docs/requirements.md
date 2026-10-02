# Requirement.md — Adaptive High-Quality Image Optimization System

## 1. Purpose

The system shall accept an image and a user-defined target file-size interval and produce the highest-quality visually faithful representation found within that interval, subject to an explicitly finite and bounded search space and explicit computational budgets.

The problem is a constrained optimization problem:

$$
\theta^* = \arg\min_{\theta \in \Theta(job)} D_{primary}(I, Decode(Encode(I,\theta)))
$$

subject to:

$$
B_{min} \le B(\theta) \le B_{max}
$$

where lower perceptual distance is better, `D_primary` is Butteraugli in the declared comparison space, and `B(θ)` is the exact encoded output size in bytes.

---

## 2. Scope

### In scope

- Image upload and secure validation.
- JPEG, WebP, AVIF, and PNG support through pluggable encoders.
- Automatic format selection.
- Joint search over format, scale, quality, chroma, progressive mode, metadata policy, and color policy.
- Exact byte-size enforcement.
- Perceptual-quality evaluation.
- Adaptive search with explicit budgets.
- Color-profile management.
- Candidate caching.
- Asynchronous job processing.
- Result verification and reporting.
- Production observability, security isolation, and horizontal scaling.

### Out of scope for the first implementation

- Video optimization.
- Animated-image optimization unless explicitly added as a separate codec path.
- User-trained perceptual models.
- Automatic subjective-human-quality calibration at deployment time.
- Exact bit-for-bit reproducibility across heterogeneous CPU architectures.

---

## 3. Functional Requirements

### FR-01 — Job creation

The API shall create an optimization job from:

- source image
- `target_min_bytes`
- `target_max_bytes`
- requested format (`auto` or explicit)
- quality mode
- metadata policy
- dimension policy
- optional processing budget profile

The API shall reject malformed ranges where `target_min_bytes <= 0`, `target_max_bytes <= 0`, or `target_min_bytes > target_max_bytes`.

### FR-02 — Secure ingestion

The system shall validate uploaded content using content inspection rather than filename extension alone.

Validation shall include:

- upload byte limit
- MIME sniffing
- magic-byte validation
- decoder-open test
- maximum dimensions
- maximum pixel count
- decompression-bomb protection
- resource limits
- optional malware scanning

### FR-03 — Canonical master

Every accepted image shall be decoded into exactly one canonical color-managed master for the job.

The canonical master shall account for:

- orientation
- ICC/profile state
- alpha channel
- supported bit depth
- normalized image metadata state

The canonical master is the source of truth for candidate generation.

### FR-04 — Provenance invariant

Every candidate shall be produced from the canonical master or a deterministic preprocessing of it.

No candidate may be generated from another candidate's encoded output.

This requirement shall be enforced by architecture and covered by automated tests.

### FR-05 — Comparison-space invariant

Quality evaluation shall occur in one explicitly declared comparison space for the job.

The canonical reference and every decoded candidate shall undergo symmetric color/transfer conversion before perceptual comparison.

The selected comparison space shall be recorded in job metadata.

### FR-06 — Image analysis

The analyzer shall provide, where available:

- format
- width and height
- pixel count
- channels
- alpha presence
- bit depth
- color profile presence/validity
- entropy estimate
- edge-density estimate
- image/content class
- relevant metadata characteristics

### FR-07 — Color policy

The system shall implement an explicit color policy:

- Preserve a valid input ICC profile when the selected output format supports it and preservation is allowed.
- Convert to a defined fallback working/output space when ICC is missing or malformed.
- Record all profile handling decisions.

Color conversion shall be deterministic within the pinned execution environment.

### FR-08 — Candidate search space

For each job, the optimizer shall construct a finite enumerable `Θ(job)`.

Conceptually:

```text
Θ(job) = {
  format,
  scale,
  quality,
  chroma,
  progressive,
  metadata_policy,
  color_policy
}
```

Every dimension shall be drawn from an explicitly bounded finite set.

No implementation may silently introduce an unbounded search dimension.

### FR-09 — Joint optimization

No parameter dimension shall have a hardcoded quality-priority ordering such as “always reduce quality before resolution”.

The optimizer shall evaluate competing combinations of scale and encoding parameters and select among feasible candidates using the defined lexicographic objective.

### FR-10 — Format selection

The format strategy engine shall generate compatible candidates among supported formats, subject to image characteristics and explicit user constraints.

In `auto` mode, format selection shall be determined by evaluated candidate quality under the target-size constraint rather than a fixed format preference.

### FR-11 — Chroma search

Chroma subsampling shall be a first-class candidate dimension where supported.

At minimum, the implementation shall support the configured modes for the applicable codecs, such as 4:2:0 and 4:4:4.

The coarse strategy may prune unsupported or implausible chroma options based on content class, but the pruning policy itself must be bounded and documented.

### FR-12 — JPEG progressive mode

JPEG shall default to progressive encoding where supported by the selected backend.

Progressive versus baseline evaluation may be introduced as a search dimension when it materially affects feasibility or quality under the active budget.

### FR-13 — Size prediction

Where reliable encoder-side size prediction is available, the optimizer shall use the prediction to seed candidate quality searches.

Predicted size shall never be used as final feasibility proof.

### FR-14 — Exact size measurement

The exact final artifact byte size shall be measured from the actual encoded artifact.

Only exact bytes may establish size-constraint feasibility.

### FR-15 — Perceptual evaluation

Butteraugli shall be the primary perceptual decision metric.

SSIM, MS-SSIM, PSNR, and color-difference measurements may be used as diagnostics and guardrails but shall not be aggregated into an arbitrary weighted score.

### FR-16 — Two-stage evaluation

The optimizer shall use:

1. inexpensive proxy evaluation during coarse search;
2. full-resolution Butteraugli evaluation on a small finalist set.

The exact proxy metric and downscale factor are configuration/calibration parameters, not architectural constants.

### FR-17 — Lexicographic selection

Selection among verified feasible candidates shall be lexicographic:

1. satisfy `B_min <= size <= B_max`;
2. minimize Butteraugli distance;
3. maximize pixel count;
4. use secondary diagnostics only for declared near-tie cases/guardrails;
5. minimize processing cost.

No weighted scalar quality score shall be required for primary ranking.

### FR-18 — Budget enforcement

The optimizer shall enforce these budgets before the associated work begins:

```yaml
max_total_encodes: 40
max_parallel_encodes_per_job: 4
coarse.max_candidates: 18
refinement.max_quality_searches: 12
finalists.max_finalists: 4
max_resolution_trials: 5
max_wall_clock_ms: 10000
max_memory_mb_per_worker: 4096
```

These are defaults and may be adjusted by a bounded deployment profile.

### FR-19 — No budget-to-impossibility conversion

A time or candidate budget exhaustion shall never by itself produce an unreachability status.

The optimizer may report a budget status with the best verified candidate found so far.

### FR-20 — Unreachability semantics

For finite accepted search space `Θ(job)`:

```text
CONSTRAINT_UNREACHABLE_MIN  iff maxB(Θ) < B_min
CONSTRAINT_UNREACHABLE_MAX  iff minB(Θ) > B_max
```

These statuses may be emitted only when the relevant bound has actually been established within the defined accepted search space.

### FR-21 — No container padding

The optimizer shall not add arbitrary padding solely to cross `B_min`.

### FR-22 — Final independent encode

The final selected artifact shall be independently encoded from the canonical master/deterministic preprocessing path, not copied from an intermediate candidate buffer that could have been modified by later steps.

### FR-23 — Final verification

Before a job becomes `COMPLETED`, the system shall:

- verify artifact existence;
- measure exact bytes;
- reopen/decode the artifact;
- verify format;
- verify dimensions;
- verify integrity;
- verify size interval;
- compute checksum;
- persist the verified result.

### FR-24 — Result reporting

The result API shall provide, at minimum:

- output location/URL
- exact file size in bytes
- human-readable file size
- format
- dimensions
- selected quality/quantizer parameter
- chroma mode when applicable
- progressive mode when applicable
- metadata policy
- color policy
- comparison-space identifier
- primary perceptual metric
- diagnostic metrics where computed
- optimizer/pipeline/encoder versions
- processing duration
- status

### FR-25 — Candidate cache

Candidate cache identity shall include at least:

```text
source_hash
params_hash
encoder_version
libvips_version
pipeline_version
```

Cache entries shall have bounded retention/eviction and/or object-store lifecycle policy.

### FR-26 — Job lifecycle

The system shall implement the explicit job state machine:

```text
UPLOADING
VALIDATING
ANALYZING
PREPROCESSING
GENERATING_CANDIDATES
OPTIMIZING
VERIFYING
COMPLETED
```

plus failure/termination statuses defined in the status contract.

---

## 4. Status Contract

```text
COMPLETED
CONSTRAINT_UNREACHABLE_MIN
CONSTRAINT_UNREACHABLE_MAX
TIME_BUDGET_EXCEEDED
CANDIDATE_BUDGET_EXCEEDED
INPUT_INVALID
DECODER_FAILURE
ENCODER_FAILURE
OUTPUT_VERIFICATION_FAILURE
```

Semantic rule:

```text
UNREACHABLE      = property of Θ(job)
BUDGET_EXCEEDED  = property of the search process
COMPLETED        = property of the verified result
```

---

## 5. Non-Functional Requirements

### NFR-01 — Security isolation

Image decoding and untrusted codec operations shall execute in a sandboxed subprocess or microVM with:

- read-only root filesystem
- no outbound network
- seccomp/namespaces and equivalent restrictions, or stronger isolation such as gVisor/Firecracker
- CPU quota
- memory quota
- wall-clock timeout
- ephemeral working directory

### NFR-02 — Scalability

The API tier shall be stateless. Optimization shall execute in horizontally scalable worker processes.

### NFR-03 — Reliability

Jobs shall be idempotent or safely retryable.

### NFR-04 — Functional determinism

Given identical source content, accepted search space, configuration, encoder versions, library versions, and platform class, the optimizer shall produce behavior within the same functional size/quality class, subject to platform floating-point/SIMD differences.

### NFR-05 — Observability

System metrics shall cover:

- job throughput
- queue latency/depth
- processing latency p50/p95/p99
- encode count/job
- candidate count/job
- cache hit rate
- status distribution
- target-feasibility success rate
- average compression ratio
- quality distributions
- worker CPU/memory
- decoder/encoder failures

### NFR-06 — Cost control

Maximum encodes, memory, time, and per-job parallelism shall be enforceable limits.

### NFR-07 — Auditability

Every completed optimization shall be traceable to:

- source checksum
- optimizer/pipeline version
- encoder versions
- selected parameters
- comparison space
- evaluated candidate metadata sufficient for reproduction/diagnosis

---

## 6. Acceptance Criteria

A job is accepted as `COMPLETED` only when:

```text
actual_output_size >= B_min
actual_output_size <= B_max
output_decodes_successfully
output_metadata is consistent with policy
selected artifact matches recorded format/dimensions
verification checksum is persisted
```

The following properties shall be enforced in automated tests:

```text
P1: A candidate is never derived from another compressed candidate.
P2: Final feasibility uses actual bytes.
P3: Budget exhaustion never implies unreachability without bound proof.
P4: Θ(job) is finite and enumerable.
P5: Final output is independently encoded and verified.
P6: The declared comparison space is used symmetrically.
P7: max_total_encodes is never exceeded.
P8: max_parallel_encodes_per_job is never exceeded.
```

---

## 7. Implementation Notes

The initial deployment should favor a modular monolith plus asynchronous workers rather than premature microservice fragmentation.

Recommended initial stack:

- API: FastAPI or equivalent
- Image processing: pyvips/libvips
- JPEG backend: jpegli or mozjpeg+trellis
- AVIF backend: libavif with SVT-AV1
- WebP backend: libwebp
- PNG backend: libpng/oxipng-equivalent toolchain
- Queue: Dramatiq or Arq
- Database: PostgreSQL
- Cache: Redis
- Binary storage: S3-compatible object storage
- Sandbox: gVisor or stronger isolation where required

Exact versions must be pinned in the deployment manifest and included in cache identity.
