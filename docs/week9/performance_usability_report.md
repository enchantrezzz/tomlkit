# Week 9 Light-Touch Performance and Usability Report

## 1. Performance Check

### Objective

Measure a representative tomlkit workflow consisting of parsing, modifying, serializing, and reparsing a TOML document while verifying round-trip correctness.

### Environment

- Timestamp: 2026-10-25 13:18:07 CAT
- Platform: Darwin 25.6.0 arm64
- Processor: Apple M2
- Logical CPUs: 8
- Python: 3.14.7
- tomlkit: 0.15.1

### Method

- Operations per repeat: 5,000
- Repeats: 5
- Total operations: 25,000
- Each operation parsed a TOML document, changed a scalar value, appended an array value, serialized the document, reparsed the output, and asserted that the changed value survived the round trip.

### Results

- Repeat 1: 2.130827 seconds, 2,346.51 operations/second
- Repeat 2: 2.122317 seconds, 2,355.92 operations/second
- Repeat 3: 2.075538 seconds, 2,409.01 operations/second
- Repeat 4: 2.076870 seconds, 2,407.47 operations/second
- Repeat 5: 2.072806 seconds, 2,412.19 operations/second
- Total measured time: 10.478358 seconds
- Mean repeat time: 2.095672 seconds
- Median repeat time: 2.076870 seconds
- Minimum repeat time: 2.072806 seconds
- Maximum repeat time: 2.130827 seconds
- Overall throughput: 2,385.87 operations/second
- Correctness check: all round-trip assertions passed

### Interpretation and Limitations

The benchmark provides a light-touch performance baseline for one representative workload on the recorded machine. The five repeat results were similar, and every correctness assertion passed. The result is not a formal performance guarantee because it used one machine, one document shape, one process, and a short synthetic workload.

## 2. Usability Check

The usability observations and top three issues will be recorded after completing the developer-facing heuristic evaluation.

### Evaluation Scope

A developer-facing heuristic evaluation was performed using common parsing, error-handling, array-modification, and help-discovery tasks. The evaluation considered Nielsen principles that are applicable to a Python library API, particularly consistency and standards, error prevention, visibility of outcomes, and help and documentation.

### Positive Finding: Error Diagnosis

Four invalid TOML inputs were tested: a leading-zero integer, an unterminated string, an invalid escape, and a duplicate key. Each input produced a specific exception with a descriptive message and line and column information. This supports the heuristic of helping users recognize, diagnose, and recover from errors.

### Top Three Usability Issues

#### Issue 1: Beginning insertion produces inconsistent array spacing

**Heuristic:** Consistency and standards.

For the conventionally formatted array `[1, 2]`, inserting `3` at position 0 produced `[3,1, 2]`. In comparison:

- Appending rendered `[1, 2, 3]`.
- Middle insertion rendered `[1, 3, 2]`.
- Replacing the first item rendered `[3, 2]`.
- Deleting the first item rendered `[2]`.

All outputs reparsed correctly, so the issue affects formatting consistency rather than semantic correctness.

**Impact:** Users relying on tomlkit to preserve human-readable formatting can receive inconsistent output after an otherwise normal array modification. Repeated beginning insertions can extend the inconsistent no-space section.

**Severity:** Medium.

**Recommendation:** Preserve the existing separator style when inserting before the first item. Add a regression test requiring insertion into `[1, 2]` to render as `[3, 1, 2]`.

#### Issue 2: Array insertion index clamping is not explained by built-in help

**Heuristic:** Help and documentation; match between the system and the real world.

The tested behavior was:

- Position `-99` inserted at the beginning.
- Position `-1` inserted before the final item.
- Position `99` inserted at the end.
- Every call returned `None`.

This is consistent with Python-style sequence insertion and is not classified as a functional defect. However, the built-in docstring only states `insert value before index` and does not explain how indexes outside the array bounds are handled.

**Impact:** A developer unfamiliar with Python list insertion rules may expect an out-of-range error or may be uncertain where the item was inserted.

**Severity:** Low.

**Recommendation:** Expand the `Array.insert()` documentation to state that indexes below the valid range are clamped to the beginning and indexes above the valid range are clamped to the end.

#### Issue 3: Common modification methods provide limited formatting guidance

**Heuristic:** Help and documentation.

The built-in help for `Array.insert()` and `Array.append()` consists of short sequence-style descriptions. The help does not explain whether these operations preserve existing whitespace, comments, commas, or multiline layout. In contrast, `Array.add_line()` has a longer docstring with parameters and an example showing exact rendered output.

**Impact:** Developers must experiment or inspect output to understand the formatting consequences of common modifications, even though formatting preservation is a central use case for tomlkit.

**Severity:** Low.

**Recommendation:** Add short formatting examples to the documentation for `insert()`, `append()`, replacement, and deletion. Clarify which existing formatting elements are expected to be preserved.

### Usability Conclusion

The tested parser error messages were specific and actionable. Common array modifications also preserved semantic values and generated reparsable TOML. The principal usability weakness was inconsistent spacing after insertion at the beginning of a conventionally spaced array. Two lower-severity documentation issues concerned undisclosed index clamping and limited guidance about formatting preservation.

## 3. Overall Conclusion

The light-touch benchmark completed 25,000 parse-modify-serialize-reparse operations in 10.478358 seconds, with an overall throughput of 2,385.87 operations per second on the recorded Apple M2 environment. All round-trip correctness assertions passed.

The usability evaluation identified one medium-severity formatting-consistency issue and two low-severity documentation issues. Error diagnosis was a strength because the tested invalid inputs produced descriptive exceptions with line and column information.

## Evidence Files

- `performance_environment.txt`
- `performance_check.py`
- `performance_results.txt`
- `usability_error_check.txt`
- `usability_api_misuse_check.txt`
- `usability_insert_check.txt`
- `usability_modification_check.txt`
- `usability_help_check.txt`
