# File_structure.md — Repository and Module Boundaries

## 1. Repository Layout

```text
ImageOptimizer_Portable/
│
├── launch_gui.bat                 # Primary Windows Desktop Application launcher
├── launch_web.bat                 # Direct Web Browser launcher
├── launch_gui.py                  # Dual Desktop / Web launcher
├── runtime/                       # Bundled portable Python runtime
│
├── apps/
│   ├── desktop/
│   │   ├── __init__.py
│   │   └── modern_app.py          # Bright Minimalist Standalone Windows App (In-Process, Zero Server)
│   │
│   ├── api/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── jobs.py
│   │   │   └── results.py
│   │   ├── schemas/
│   │   │   ├── jobs.py
│   │   │   └── results.py
│   │   ├── middleware/
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   └── request_id.py
│   │   └── static/
│   │       ├── index.html         # Responsive web GUI
│   │       ├── style.css          # Responsive dark styling for web
│   │       ├── app.js             # Interactive client for web mode
│   │       └── samples/           # Benchmark sample images
│   │
│   └── worker/
│       ├── main.py
│       ├── consumers.py
│       ├── tasks.py
│       └── sandbox.py
│
├── src/
│   ├── domain/
│   │   ├── models/
│   │   │   ├── job.py
│   │   │   ├── candidate.py
│   │   │   ├── image.py
│   │   │   └── result.py
│   │   ├── policies/
│   │   │   ├── optimization_policy.py
│   │   │   ├── budget_policy.py
│   │   │   └── color_policy.py
│   │   └── errors/
│   │       └── statuses.py
│   │
│   ├── optimization/
│   │   ├── orchestrator.py
│   │   ├── search_controller.py
│   │   ├── candidate_space.py
│   │   ├── candidate_generator.py
│   │   ├── candidate_ledger.py
│   │   ├── predictor.py
│   │   ├── pareto.py
│   │   ├── refinement.py
│   │   ├── selection.py
│   │   ├── feasibility.py
│   │   └── termination.py
│   │
│   ├── image/
│   │   ├── validation.py
│   │   ├── decoding.py
│   │   ├── canonicalization.py
│   │   ├── analysis.py
│   │   ├── metadata.py
│   │   ├── resize.py
│   │   └── color_management.py
│   │
│   ├── encoders/
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── jpeg.py
│   │   ├── webp.py
│   │   ├── avif.py
│   │   └── png.py
│   │
│   ├── quality/
│   │   ├── base.py
│   │   ├── proxy.py
│   │   ├── butteraugli.py
│   │   ├── ssim.py
│   │   ├── ms_ssim.py
│   │   ├── psnr.py
│   │   ├── delta_e.py
│   │   └── guardrails.py
│   │
│   ├── infrastructure/
│   │   ├── storage/
│   │   │   ├── object_store.py
│   │   │   └── signed_urls.py
│   │   ├── queue/
│   │   │   ├── client.py
│   │   │   └── worker.py
│   │   ├── cache/
│   │   │   └── candidate_cache.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   ├── repositories.py
│   │   │   └── migrations/
│   │   └── telemetry/
│   │       ├── metrics.py
│   │       ├── tracing.py
│   │       └── logging.py
│   │
│   └── services/
│       ├── job_service.py
│       ├── optimization_service.py
│       ├── result_service.py
│       └── verification_service.py
│
├── tests/
│   ├── unit/
│   │   ├── optimization/
│   │   ├── image/
│   │   ├── encoders/
│   │   └── quality/
│   ├── integration/
│   │   ├── api/
│   │   ├── worker/
│   │   ├── storage/
│   │   └── end_to_end/
│   ├── property/
│   │   ├── test_budgets.py
│   │   ├── test_feasibility.py
│   │   └── test_provenance.py
│   ├── regression/
│   │   ├── fixtures/
│   │   └── test_quality_regressions.py
│   └── performance/
│       ├── benchmark_encoders.py
│       ├── benchmark_metrics.py
│       └── benchmark_search.py
│
├── configs/
│   ├── base.yaml
│   ├── development.yaml
│   ├── staging.yaml
│   ├── production.yaml
│   └── optimization_profiles/
│       ├── fast.yaml
│       ├── balanced.yaml
│       └── max_quality.yaml
│
├── deployments/
│   ├── docker/
│   ├── kubernetes/
│   └── sandbox/
│
├── scripts/
│   ├── package_release.py             # 1-click packager for GitHub Releases ZIP
│   ├── verify_environment.py          # Diagnostics for encoder backends and PIL plugins
│   └── secure_core.py                 # Core integrity loader & security wrapper
│
├── docs/
│   ├── Requirement.md
│   ├── Architecture.md
│   ├── Pipeline.md
│   └── File_structure.md
│
├── pyproject.toml
├── uv.lock / poetry.lock
├── Dockerfile.api
├── Dockerfile.worker
├── docker-compose.yml
└── README.md
```

---

## 2. Boundary Ownership

### `apps/api`

HTTP/API concerns only.

Must not contain optimizer algorithms.

### `apps/worker`

Queue consumption, worker lifecycle, resource enforcement, sandbox invocation.

Must not contain domain policy.

### `src/domain`

Pure domain contracts and invariants.

Preferred dependency direction:

```text
domain → nothing infrastructure-specific
```

### `src/optimization`

Owns search and selection logic.

May depend on domain interfaces and ports, not concrete PostgreSQL/S3/Redis clients.

### `src/image`

Owns validation, decoding, canonicalization, metadata and color transformations.

### `src/encoders`

Owns codec adapters.

Encoder implementations shall conform to the common encoder interface.

### `src/quality`

Owns metric adapters and guardrails.

### `src/infrastructure`

Contains concrete infrastructure integrations.

### `src/services`

Application-level orchestration joining domain logic to infrastructure ports.

---

## 3. Dependency Rule

Preferred dependency direction:

```text
API
 ↓
Application Services
 ↓
Domain / Optimization
 ↓
Ports / Interfaces
 ↓
Infrastructure Adapters
```

Avoid:

```text
Domain
 ↓
PostgreSQL client
```

or:

```text
Encoder adapter
 ↓
FastAPI route
```

These reverse dependencies create coupling and make benchmarking/testing difficult.

---

## 4. Suggested Core Interfaces

### Encoder

`src/encoders/base.py`

```python
class ImageEncoder(Protocol):
    def capabilities(self): ...
    def predict_size(self, source, request): ...
    def encode(self, source, request, output_path): ...
```

### Quality evaluator

`src/quality/base.py`

```python
class QualityEvaluator(Protocol):
    def evaluate_proxy(self, reference, candidate): ...
    def evaluate_full(self, reference, candidate): ...
```

### Storage

`src/infrastructure/storage/object_store.py`

```python
class ObjectStore(Protocol):
    def put(self, key, stream, metadata): ...
    def get(self, key): ...
    def delete(self, key): ...
    def signed_url(self, key, ttl_seconds): ...
```

### Candidate cache

`src/infrastructure/cache/candidate_cache.py`

```python
class CandidateCache(Protocol):
    def get(self, key): ...
    def put(self, key, value, ttl_seconds): ...
```

---

## 5. Job State Ownership

`src/domain/errors/statuses.py` should define the status enum:

```python
class JobStatus(str, Enum):
    COMPLETED = "COMPLETED"
    CONSTRAINT_UNREACHABLE_MIN = "CONSTRAINT_UNREACHABLE_MIN"
    CONSTRAINT_UNREACHABLE_MAX = "CONSTRAINT_UNREACHABLE_MAX"
    TIME_BUDGET_EXCEEDED = "TIME_BUDGET_EXCEEDED"
    CANDIDATE_BUDGET_EXCEEDED = "CANDIDATE_BUDGET_EXCEEDED"
    INPUT_INVALID = "INPUT_INVALID"
    DECODER_FAILURE = "DECODER_FAILURE"
    ENCODER_FAILURE = "ENCODER_FAILURE"
    OUTPUT_VERIFICATION_FAILURE = "OUTPUT_VERIFICATION_FAILURE"
```

The state-transition rules belong in `job_service.py` or a dedicated state machine module.

---

## 6. Versioning Strategy

The repository must explicitly version:

```text
optimizer_version
pipeline_version
configuration_profile_version
encoder versions
libvips version
color-management version
metric implementation version
```

The cache key must change when any output-affecting component changes.

A deployment artifact should also include a machine-readable software bill of materials or equivalent dependency inventory.

---

## 7. Configuration Ownership

Keep deployment and optimization settings separate.

```text
configs/base.yaml
    infrastructure defaults

configs/production.yaml
    deployment-specific limits

configs/optimization_profiles/*.yaml
    search-space and budget profiles
```

Do not hardcode codec parameters inside the search controller.

---

## 8. Test Ownership

```text
unit/
    local behavior

integration/
    service and infrastructure boundaries

property/
    frozen invariants

regression/
    quality and artifact regressions

performance/
    encode/metric/search benchmarks
```

The following invariants require dedicated property tests:

```text
provenance invariant
comparison-space invariant
hard byte-size constraint
budget enforcement
finite Θ(job)
budget ≠ unreachability
final independent encode
final verification
```

---

## 9. Benchmark Dataset Organization

Keep benchmark inputs outside production source code:

```text
benchmarks/
├── photographs/
├── screenshots/
├── graphics/
├── transparency/
├── wide_gamut/
├── high_resolution/
└── resized_outputs/
```

For each benchmark image record:

```text
source hash
class
format
width
height
color profile
alpha
```

Store benchmark outputs and measurements separately from production artifacts.

---

## 10. Implementation Sequence

Recommended sequence:

```text
1. domain models + invariants
2. secure decoding + canonicalization
3. encoder interface + one JPEG backend
4. exact size verification
5. bounded candidate space
6. adaptive quality search
7. proxy/full quality evaluation
8. WebP/AVIF/PNG backends
9. queue + worker orchestration
10. cache + observability
11. sandbox hardening
12. benchmark calibration
13. load testing
```

This sequence intentionally validates correctness before optimizing distributed throughput.
