# Prompt: Incremental Codebase Refactoring

## Your Task

You are refactoring this codebase toward the architecture described in `design.md`. Work incrementally using **atoms** — small, self-contained changes that preserve behavior.

---

## Step 1: Understand the Concept of an Atom

An **atom** is the smallest self-contained change that moves the codebase toward the target design while satisfying:

1. **Behavior preserved** — existing functionality unchanged
2. **Tests updated only at call sites** — if API changes, tests update how they call, not what they assert
3. **New tests may be added** — for new functionality or coverage
4. **`ruff check` passes**
5. **`kiss check .` passes**
6. **All tests pass**:
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 PYTHONPATH=src pytest -sv tests
   ```

An atom should be:
- **Focused** — one logical change
- **Reviewable** — easy to verify correctness
- **Reversible** — can be undone if needed

---

## Step 2: Read the Current State

Read `state.md` to understand:
- What refactoring has been completed
- The current architecture
- File structure and key classes

---

## Step 3: Propose the Next Atom

1. Read `design.md` to understand the target architecture
2. Compare the current codebase to `design.md`
3. Identify the next incremental step
4. Write `atom.md` with:
   - **Goal** — what this atom achieves
   - **Context** — current state and why change is needed
   - **Changes** — specific files and modifications
   - **Why atomic** — why this preserves behavior
   - **Acceptance criteria** — tests/checks that must pass

---

## Step 4: Implement the Atom

1. Make the proposed changes
2. Run all checks:
   ```bash
   ruff check
   kiss check .
   KMP_DUPLICATE_LIB_OK=TRUE OMP_NUM_THREADS=1 PYTHONPATH=src pytest -sv tests
   ```
3. Fix any issues until all checks pass

---

## Step 5: Update State

After the atom is complete:
1. Update `state.md` to reflect the new state
2. Update `atom.md` to mark the atom as completed
3. Optionally propose the next atom

---




## Example Atom Workflow

```
1. Read state.md → "TR configs are done, init strategy is done"
2. Read design.md → "§6 says SurrogateConfig should have build()"
3. Check codebase → "Surrogate construction uses if/elif"
4. Write atom.md → "Create SurrogateConfig hierarchy"
5. Implement → Create ABC, concrete classes, wire into optimizer
6. Verify → ruff, kiss, pytest all pass
7. Update state.md → Add "SurrogateConfig hierarchy" to completed list
```

