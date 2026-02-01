# Codebase State: Polymorphic Trust Region Architecture

*Last updated: January 2026*

## Summary

The codebase has been fully refactored to follow the **Polymorphic Trust Region Architecture** outlined in `design.md`. The core principle is **polymorphism over conditionals**: dispatch happens via virtual method calls, not `isinstance` or `if/elif` ladders.

---

## Completed Refactoring

### 1. Polymorphic Config Hierarchies

Seven config hierarchies with `build()` / `build_impl()` factory methods:

| Hierarchy | Config Classes | Runtime Classes |
|-----------|----------------|-----------------|
| **TrustRegion** | `NoTRConfig`, `TurboTRConfig`, `MorboTRConfig` | `NoTrustRegion`, `TurboTrustRegion`, `MorboTrustRegion` |
| **IncumbentSelector** | `MaxYSelectorConfig`, `MaxMuSelectorConfig`, `ChebyshevYSelectorConfig`, `ChebyshevMuSelectorConfig` | `MaxYSelector`, `MaxMuSelector`, `ChebyshevYSelector`, `ChebyshevMuSelector` |
| **InitStrategy** | `LHDInitConfig`, `LHDInitForeverConfig`, `NoInitConfig` | `LHDInitStrategy`, `LHDInitForeverStrategy`, `NoInitStrategy` |
| **CandidateGenerator** | `RAASPSobolCandidateConfig`, `RAASPUniformCandidateConfig` | `RAASPSobolCandidateGenerator`, `RAASPUniformCandidateGenerator` |
| **Acquisition** | `ParetoAcquisitionConfig`, `UCBAcquisitionConfig`, `ThompsonAcquisitionConfig` | `ParetoAcquisition`, `UCBAcquisition`, `ThompsonAcquisition` |
| **Surrogate** | `NoSurrogateConfig`, `ENNSurrogateConfig`, `GPSurrogateConfig` | `NoSurrogate`, `ENNSurrogate`, `GPSurrogate` |
| **ModeImpl** | `TurboOneConfig`, `TurboZeroConfig`, `TurboENNConfig`, `LHDOnlyConfig` | `TurboOneImpl`, `TurboZeroImpl`, `TurboENNImpl`, `LHDOnlyImpl` |

All located in `src/enn/turbo/config/`.

### 2. Config-Driven Impl Construction

`TurboConfig` subclasses have `build_impl()` method. The `TurboMode` enum has been **removed entirely**:

```python
# Config is required and drives all behavior
optimizer = TurboOptimizer(bounds, TurboENNConfig(), rng=rng)
```

### 3. Polymorphic Properties

No more `isinstance` checks for behavior dispatch:
- `TrustRegionConfig.num_metrics` → derived polymorphically
- `TrustRegionConfig.supports_multi_objective` → polymorphic property
- `AcquisitionConfig.requires_num_fit_samples` → polymorphic property

### 4. No Magic Strings

All `Literal` string parameters eliminated:
- `tr_type` → direct `TrustRegionConfig` injection
- `candidate_rv` → direct `CandidateGeneratorConfig` injection
- `acq_type` → direct `AcquisitionConfig` injection

### 5. Complete Surrogate Hierarchy

New `SurrogateConfig` hierarchy with unified interface:

```python
class Surrogate(ABC):
    def fit(x, y, yvar, ...) -> SurrogateFitResult: ...
    def predict(x) -> (mu, sigma) | None: ...
    def estimate_y(x, y_observed) -> mu: ...
```

Implementations:
- `NoSurrogate` - passthrough (for TURBO_ZERO, LHD_ONLY)
- `ENNSurrogate` - ENN-based predictions
- `GPSurrogate` - GP-based predictions

### 6. Shared Helpers

Common utilities extracted to `impl_helpers.py`:
- `as_2d()` - array reshaping
- `get_x_center_fallback()` - incumbent selection
- `estimate_y_passthrough()` - observation passthrough

---

## File Structure

```
src/enn/turbo/
├── config/
│   ├── __init__.py                    # Exports all config classes
│   ├── trust_region_config.py         # TrustRegionConfig hierarchy
│   ├── incumbent_selector_config.py   # IncumbentSelectorConfig hierarchy
│   ├── init_strategy_config.py        # InitStrategyConfig hierarchy
│   ├── candidate_generator_config.py  # CandidateGeneratorConfig hierarchy
│   ├── acquisition_config.py          # AcquisitionConfig hierarchy
│   └── surrogate_config.py            # SurrogateConfig hierarchy
├── turbo_config.py                    # TurboConfig + mode subclasses with build_impl()
├── turbo_optimizer.py                 # Main optimizer (config required)
├── turbo_mode_impl.py                 # TurboModeImpl protocol
├── turbo_one_impl.py                  # GP-based implementation
├── turbo_enn_impl.py                  # ENN-based implementation
├── turbo_zero_impl.py                 # No-surrogate implementation
├── lhd_only_impl.py                   # LHD-only baseline
├── impl_helpers.py                    # Shared utilities (as_2d, etc.)
├── turbo_trust_region.py              # TuRBO trust region
├── morbo_trust_region.py              # MORBO trust region
└── no_trust_region.py                 # No-op trust region
```

**Removed files:**
- `turbo_mode.py` — TurboMode enum (no longer needed)
- `turbo_mode_registry.py` — Mode-to-impl registry (replaced by `config.build_impl()`)

---

## Usage Examples

### Config-First Usage (New)
```python
from enn import TurboOptimizer
from enn.turbo.turbo_config import TurboENNConfig
from enn.turbo.config import MorboTRConfig

config = TurboENNConfig(
    trust_region=MorboTRConfig(num_metrics=2),
)
optimizer = TurboOptimizer(bounds, rng=rng, config=config)
```

### Direct Surrogate Usage
```python
from enn.turbo.config import GPSurrogateConfig

config = GPSurrogateConfig()
surrogate = config.build(num_dim=5, num_metrics=1)
surrogate.fit(x_train, y_train, None, num_dim=5, gp_num_steps=50, rng=rng)
mu, sigma = surrogate.predict(x_test)
```

---

## Remaining Opportunities (Optional)

| Item | Description | Scope |
|------|-------------|-------|
| Refactor impls to use Surrogate | Have impls delegate to Surrogate rather than embedding logic | Medium |

---

## Design Principles (from design.md)

1. **No `isinstance` dispatch** — use `config.build()` virtual methods ✓
2. **Config as source of truth** — behavioral flags live on configs ✓
3. **Null-object pattern** — use `NoTRConfig`, `NoSurrogateConfig` instead of `None` ✓
4. **Explicit over implicit** — no sentinel values or magic defaults ✓
5. **Liberal shape assertions** — verify array shapes at component boundaries ✓
6. **Polymorphic properties** — `num_metrics`, `requires_num_fit_samples` ✓
7. **Config-driven impl construction** — `config.build_impl()` replaces mode registry ✓
8. **Surrogate abstraction** — GP/ENN/None unified under `Surrogate` interface ✓
