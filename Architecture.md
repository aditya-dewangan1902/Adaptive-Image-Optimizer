# Architecture.md — Production System Architecture

## 1. Architectural Goal

Build a production image-optimization platform that solves a bounded constrained optimization problem rather than applying a fixed compression heuristic.

The system is organized into nine logical layers:

```text
Presentation
    ↓
API
    ↓
Ingestion
    ↓
Analysis
    ↓
Preprocessing
    ↓
Optimization
    ↓
Verification
    ↓
Output
    ↘ Observability / Metadata
```

---

## 2. Logical Components

```text
Web/Mobile Client
        │
        ▼
API Gateway / API Service
        │
        ├──────────────► Job Metadata DB
        │
        ▼
Upload Service ─────────► Object Storage / originals
        │
        ▼
Job Queue
        │
        ▼
Optimization Worker
        │
        ├── Input Validator
        ├── Image Analyzer
        ├── Canonicalizer
        ├── Candidate Space Builder
        ├── Search Controller
        ├── Encoder Registry
        ├── Candidate Cache
        ├── Quality Evaluator
        └── Finalizer
        │
        ▼
Verification Service/Module
        │
        ▼
Object Storage / outputs
        │
        ▼
Result API / CDN
```

---

## 3. Component Responsibilities

### 3.1 API Service

Owns:

- authentication/authorization
- request validation
- job creation
- job status
- cancellation where supported
- signed result URLs
- API versioning

Does not own image optimization logic.

### 3.2 Upload Service

Owns:

- streaming upload
- upload limits
- content validation handoff
- immutable storage of original bytes

### 3.3 Image Validator

Owns security and structural checks before expensive processing.

### 3.4 Image Analyzer

Owns source characteristics and content-class signals.

### 3.5 Canonicalizer

Owns:

- orientation resolution
- ICC/profile normalization
- alpha preservation
- metadata normalization
- conversion into canonical master representation

The canonicalizer must not introduce candidate-specific compression.

### 3.6 Candidate Space Builder

Constructs finite `Θ(job)`.

Example:

```python
Theta = Product(
    formats,
    scales,
    qualities,
    chroma_modes,
    progressive_modes,
    metadata_policies,
    color_policies,
)
```

Content analysis and hard compatibility rules may prune this product before encoding, but the resulting space must remain explicit and enumerable.

### 3.7 Search Controller

Owns:

- stage transitions
- budget enforcement
- candidate generation
- seed prediction
- binary/interpolation search
- Pareto pruning
- finalist selection
- termination reason

It must not perform low-level encoding itself.

### 3.8 Encoder Registry

Maps format/backend identifiers to encoder implementations.

```text
jpeg → JpegEncoder
webp → WebpEncoder
avif → AvifEncoder
png  → PngEncoder
```

### 3.9 Quality Evaluator

Owns:

- proxy metric computation
- Butteraugli
- secondary diagnostics
- guardrail flags

### 3.10 Finalizer/Verifier

Owns independent final encode and exact verification.

---

## 4. Encoder Abstraction

```python
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

@dataclass(frozen=True)
class EncoderCapabilities:
    formats: tuple[str, ...]
    supports_alpha: bool
    supports_icc: bool
    supports_chroma_420: bool
    supports_chroma_444: bool
    supports_progressive: bool

@dataclass(frozen=True)
class EncodeRequest:
    format: str
    width: int
    height: int
    quality: int | float
    chroma: str | None
    progressive: bool | None
    metadata_policy: str
    color_policy: str

@dataclass(frozen=True)
class EncodedArtifact:
    path: str
    size_bytes: int
    format: str
    width: int
    height: int
    checksum_sha256: str

class ImageEncoder(Protocol):
    def capabilities(self) -> EncoderCapabilities: ...
    def predict_size(self, source: Any, request: EncodeRequest) -> int | None: ...
    def encode(self, source: Any, request: EncodeRequest, output_path: str) -> EncodedArtifact: ...
```

`predict_size()` is advisory. `encode()` output bytes are authoritative.

---

## 5. Quality-Evaluation Interface

```python
@dataclass(frozen=True)
class QualityResult:
    butteraugli_distance: float | None
    ssim: float | None
    ms_ssim: float | None
    psnr_db: float | None
    delta_e: float | None
    guardrail_flags: tuple[str, ...]

class QualityEvaluator(Protocol):
    def evaluate_proxy(self, reference, candidate) -> QualityResult: ...
    def evaluate_full(self, reference, candidate) -> QualityResult: ...
```

Butteraugli is primary. Secondary metrics are informational/guardrail outputs.

---

## 6. Storage Architecture

```text
Object Storage
├── originals/{tenant}/{job}/source
├── outputs/{tenant}/{job}/optimized.ext
└── ephemeral candidate workspace

PostgreSQL
├── optimization_jobs
├── job_events
└── selected_result metadata

Redis
├── candidate cache
├── short-lived locks
└── ephemeral job coordination
```

Candidate binaries are not intended to live indefinitely in PostgreSQL.

---

## 7. Deployment Topology

### Initial production deployment

```text
                    Load Balancer
                          │
                 ┌────────▼────────┐
                 │ API replicas     │
                 └────────┬─────────┘
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
     PostgreSQL         Redis          Object Storage
                          │
                          ▼
                      Job Queue
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
          Worker 1     Worker 2     Worker N
             │
             ▼
          Sandbox
             │
       Encoder/metrics
```

API replicas remain stateless.

Workers are replaceable and horizontally scalable.

---

## 8. Worker Concurrency

Each worker host must enforce:

```text
per-job concurrent encodes <= 4
host memory budget <= configured limit
process CPU limits
```

The scheduler must prevent a single high-resolution job from consuming all cores on a node.

A pool should reserve resources for AVIF/SVT-AV1 jobs because memory and CPU demand may differ from JPEG/WebP jobs.

---

## 9. Sandbox Boundary

Untrusted image decoding shall occur inside a sandbox boundary:

```text
Worker
  │
  ▼
Sandbox launcher
  │
  ├── read-only rootfs
  ├── no network
  ├── seccomp / namespaces
  ├── CPU quota
  ├── memory quota
  ├── wall-clock timeout
  └── ephemeral filesystem
```

Use gVisor where appropriate; Firecracker may be used for stronger multi-tenant isolation.

---

## 10. Versioned Reproducibility Contract

Every optimization result should record:

```text
optimizer_version
pipeline_version
libvips_version
jpeg_backend_version
webp_backend_version
av1_backend_version
png_backend_version
color_management_version
comparison_space
configuration_profile
platform_class
```

This supports functional reproducibility and valid cache invalidation.

---

## 11. API Contracts

### Create job

`POST /api/v1/optimization/jobs`

```json
{
  "target_min_bytes": 524288,
  "target_max_bytes": 1048576,
  "format": "auto",
  "quality_mode": "maximum",
  "metadata_policy": "minimal",
  "dimension_policy": "joint_search"
}
```

### Get job

`GET /api/v1/optimization/jobs/{job_id}`

Returns lifecycle state and, on completion, result metadata.

### Get result

`GET /api/v1/optimization/jobs/{job_id}/result`

Returns a signed output URL and optimization report.

---

## 12. Architectural Invariants

These are non-negotiable boundaries:

1. Candidates never derive from compressed candidates.
2. Reference and candidate are compared in the same declared comparison space.
3. Actual output bytes determine feasibility.
4. Ranking is lexicographic, not a weighted scalar.
5. Stage and total budgets are enforced before work starts.
6. Functional determinism is the reproducibility claim.
7. Final output is independently encoded and verified.
8. Unreachability is distinct from search termination.
9. `Theta(job)` is finite and explicitly bounded.

---

## 13. Dependency Direction

```text
API
 ↓
Application services
 ↓
Optimization domain
 ↓
Encoder / metric ports
 ↓
Infrastructure adapters
```

Core optimization logic must not import database, HTTP, or storage implementation details directly.

---

## 14. Scalability Strategy

Scale independently:

- API replicas for request volume
- queue partitions/consumers for job volume
- optimization workers for CPU demand
- object storage for image volume
- cache for repeated candidate computations

Do not scale the API tier to solve CPU-bound image-processing bottlenecks.
