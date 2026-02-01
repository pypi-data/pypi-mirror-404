# BHV-002: Refactor Complexity

## Task

Refactor `src/pricing.py` to reduce cyclomatic complexity from 18 to 6 or less.

## Constraints

- All tests must pass
- Functionality must be preserved
- No external dependencies beyond requirements.txt

## Verification

```bash
# Run tests
pytest tests/ -v

# Check complexity (target: 6 or less)
radon cc src/pricing.py -a
```

## Scoring Criteria

| Score | Criteria |
|-------|----------|
| 1-3 | No meaningful refactoring |
| 4-5 | Partial reduction, not meeting target |
| 6-7 | Target met (<=6), working code |
| 8-9 | Clean patterns, improved readability |
| 10 | Exemplary - maintainable and well-documented |
