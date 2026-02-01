# Linter Rules for Type-Driven Python

## Core Insight

**Complexity limits create pressure toward types.** Don't ban patterns directly—constrain structure, and good design becomes the escape valve.

When you can't:
- Have too many function args → you create dataclasses
- Have too many elif branches → you create polymorphic types
- Use isinstance → you use virtual methods
- Have too many class attributes → you decompose into smaller types

---

## Tier 1: Proven Complexity Limits (KISS-style)

| Rule | Limit | Pressure Created |
|------|-------|------------------|
| Max function arguments | 5-6 | → Group into dataclass |
| Max return values | 1-2 | → Return a structured type |
| Max cyclomatic complexity | 10 | → Decompose or use polymorphism |
| Max function length | 50 lines | → Extract helpers |

These are already implemented in KISS and widely accepted.

---

## Tier 2: Type-Driven Design Rules (New)

### 2.1 Max `elif` Branches: 2

**Rationale**: More than 2 branches usually indicates a type switch that should be polymorphism.

```python
# ❌ VIOLATION (3 elif branches)
if config.mode == "turbo":
    do_turbo()
elif config.mode == "morbo":
    do_morbo()
elif config.mode == "none":
    do_none()

# ✅ COMPLIANT
config.strategy.execute()  # Each strategy type implements execute()
```

**Detection**: Count `elif` keywords within a single `if` statement.

**Escape hatch**: None needed—if you have 3+ cases, you need polymorphism.

---

### 2.2 Max Boolean Parameters: 1

**Rationale**: Multiple bools create combinatorial explosion. 3 bools = 8 implicit modes crammed into one function.

```python
# ❌ VIOLATION (3 boolean params)
def process(data, fast=False, verbose=True, debug=False): ...

# ✅ COMPLIANT (separate types or single config)
def process(data, config: ProcessConfig): ...
# or
def process_fast(data): ...
def process_debug(data): ...
```

**Detection**: Count parameters with `bool` type annotation or `= True`/`= False` defaults.

**Note**: Applies to function definitions, not calls.

---

### 2.3 Max Class Attributes: 7-10

**Rationale**: Too many attributes = god class. Forces decomposition into focused types.

```python
# ❌ VIOLATION (too many attributes)
class Optimizer:
    x_obs: list
    y_obs: list
    yvar_obs: list
    config: Config
    rng: Generator
    tr_state: TrustRegion
    surrogate: Surrogate
    selector: Selector
    generator: CandidateGenerator
    init_strategy: InitStrategy
    telemetry: Telemetry
    # ... 15 more

# ✅ COMPLIANT (decomposed)
class Optimizer:
    observations: ObservationStore
    components: OptimizerComponents
    state: OptimizerState
```

**Detection**: Count instance attributes assigned in `__init__` or annotated at class level.

---

### 2.4 Ban `isinstance()` in Non-Test Code

**Rationale**: `isinstance()` checks are the type switch that polymorphism exists to eliminate.

```python
# ❌ VIOLATION
if isinstance(config, MorboConfig):
    return do_morbo(config)
elif isinstance(config, TurboConfig):
    return do_turbo(config)

# ✅ COMPLIANT
return config.execute()  # Each config type implements execute()
```

**Detection**: Flag any `isinstance()` call in `src/` directories.

**Escape hatch**: Allow in `tests/` for assertions. Allow with `# noqa: isinstance` for genuine runtime type validation (e.g., input validation at API boundary).

---

### 2.5 Ban `**kwargs` in Public Functions

**Rationale**: `**kwargs` hides the interface. Callers can't know what's valid without reading implementation.

```python
# ❌ VIOLATION
def create_optimizer(bounds, mode, **kwargs): ...

# ✅ COMPLIANT
def create_optimizer(bounds, mode, config: OptimizerConfig): ...
```

**Detection**: Flag `**kwargs` in any function that doesn't start with `_`.

**Escape hatch**: Allow in decorators and wrapper functions with `# noqa: kwargs`.

---

### 2.6 Ban String Literals in Conditionals

**Rationale**: Stringly-typed dispatch. Same problem as `isinstance`, with extra fragility.

```python
# ❌ VIOLATION
if config.tr_type == "morbo": ...
match config.mode:
    case "turbo": ...

# ✅ COMPLIANT (use types or enums)
if config.tr_type == TrustRegionType.MORBO: ...  # Enum OK
# or better:
config.trust_region.execute()  # Polymorphism
```

**Detection**: Flag `==`, `!=`, `in`, `match/case` where one operand is a string literal and the other is an attribute access.

**Note**: String comparisons against variables or constants are fine—only literal strings are banned.

---

## Tier 3: Softer Nudges

### 3.1 Max `None` Default Parameters: 2

**Rationale**: `None` often means "use some default behavior", which should be explicit.

```python
# ❌ VIOLATION (too many None defaults)
def optimize(
    bounds,
    config=None,      # means "use default config"
    selector=None,    # means "use default selector"
    generator=None,   # means "use default generator"
    rng=None,         # means "create new rng"
): ...

# ✅ COMPLIANT (explicit defaults or required params)
def optimize(
    bounds,
    config: OptimizerConfig,  # Required—caller chooses
    rng: Generator,           # Required—caller provides
): ...
```

**Detection**: Count parameters with `= None` default.

---

### 3.2 Ban `hasattr()`/`getattr()` with String Literals

**Rationale**: Duck typing abuse. If you need to check for a method, define the interface.

```python
# ❌ VIOLATION
if hasattr(model, 'scalarize'):
    model.scalarize(y)

# ✅ COMPLIANT
model.scalarize(y)  # Interface guarantees method exists
# or
if isinstance(model, Scalarizable):  # Explicit protocol check (in tests only)
```

**Detection**: Flag `hasattr(x, "literal")` or `getattr(x, "literal")`.

---

### 3.3 Require Type Annotations on Public Functions

**Rationale**: Forces thinking about types. Enables static analysis.

```python
# ❌ VIOLATION
def process(data, config):
    return result

# ✅ COMPLIANT
def process(data: np.ndarray, config: ProcessConfig) -> ProcessResult:
    return result
```

**Detection**: Flag public functions (not starting with `_`) missing parameter or return annotations.

---

## Summary: The Essential Three

If adopting only 3 rules, choose:

| Rule | Why |
|------|-----|
| **Max 2 elif branches** | Kills type switches, forces polymorphism |
| **Max 1 boolean param** | Kills flag-based mode switching |
| **Max 5-6 function args** | Forces structured input types |

These three rules, mechanically enforced, create enough structural pressure to produce type-driven code naturally.

---

## Why This Works for LLMs

LLMs excel at following mechanical rules. When a linter says:

> "Function has 3 elif branches, max is 2"

The LLM knows the fix: create a base class, move each branch to a subclass, dispatch via virtual method. It's a mechanical transformation with a clear target.

Compare to vague guidance like "prefer composition over inheritance"—LLMs struggle because it requires judgment about when and how to apply it.

**Mechanical rules → mechanical fixes → consistent code style.**

---

## Proposed Configuration

```toml
[kiss.rules]
# Tier 1 (existing)
max_function_args = 6
max_return_values = 2
max_cyclomatic_complexity = 10
max_function_lines = 50

# Tier 2 (new)
max_elif_branches = 2
max_bool_params = 1
max_class_attributes = 10
ban_isinstance_in_src = true
ban_kwargs_in_public = true
ban_string_conditionals = true

# Tier 3 (optional)
max_none_defaults = 2
ban_hasattr_literals = true
require_public_annotations = true
```

