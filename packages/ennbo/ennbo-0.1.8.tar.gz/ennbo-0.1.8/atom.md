# Session Summary: Polymorphic Architecture Refactoring

## Completed Atoms

### Atom 1: Remove Dead Candidate Generation Code
- Removed `MorboTrustRegion.generate_candidates()` method
- Removed `tr_helpers.generate_tr_candidates()` function
- Eliminated last `Literal["sobol", "uniform"]` usage

### Atom 2: Config-Driven Multi-Output Dispatch
- Replaced runtime shape detection in `TurboOneImpl.select_candidates()`
- Now uses `self._config.trust_region.supports_multi_objective`

### Atom 3: Polymorphic Properties
- Added `TrustRegionConfig.num_metrics` property
- Added `AcquisitionConfig.requires_num_fit_samples` property
- Eliminated all `isinstance` checks for behavior dispatch

### Atom 4: Config-Driven Impl Construction
- Added `build_impl()` method to all config classes
- Made `TurboMode` parameter optional in `TurboOptimizer`
- Config is now the source of truth for impl construction

### Atom 5: Complete SurrogateConfig Hierarchy
- Created `Surrogate` ABC with unified interface:
  - `fit(x, y, yvar, ...) -> SurrogateFitResult`
  - `predict(x) -> (mu, sigma) | None`
  - `estimate_y(x, y_observed) -> mu`
- Implemented three surrogates:
  - `NoSurrogate` - passthrough (null-object pattern)
  - `ENNSurrogate` - ENN-based predictions
  - `GPSurrogate` - GP-based predictions
- Extracted shared `as_2d()` helper to avoid duplication

## Verification

All checks pass:
- `ruff check` ✓
- `pytest -sv tests` (292 passed) ✓
- `kiss check .` (NO VIOLATIONS) ✓
- Notebook tests (3 passed) ✓

## Files Changed

### New Files
- `src/enn/turbo/config/surrogate_config.py` - Complete Surrogate hierarchy

### Modified Files
- `src/enn/turbo/turbo_config.py` - Added `build_impl()`, polymorphic properties
- `src/enn/turbo/turbo_optimizer.py` - Made `mode` optional
- `src/enn/turbo/turbo_one_impl.py` - Uses `supports_multi_objective`
- `src/enn/turbo/turbo_mode_registry.py` - Delegates to `config.build_impl()`
- `src/enn/turbo/config/__init__.py` - Exports new classes
- `src/enn/turbo/impl_helpers.py` - Added `as_2d()` helper
- `src/enn/turbo/morbo_trust_region.py` - Removed dead `generate_candidates`
- `src/enn/turbo/tr_helpers.py` - Removed dead `generate_tr_candidates`
- `tests/test_config_classes.py` - Added surrogate tests
- `tests/test_trust_region.py` - Updated for new API
- `tests/test_turbo_tr.py` - Updated for new API
