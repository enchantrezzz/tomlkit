# Survivor root-cause notes — mutation v2

Selected from the 956 v2 survivors by function-level survivor count
(`survivor_candidates.csv`) and risk concentration. Diffs are from `mutmut show`;
the raw output is in `selected_diffs.txt`.

## 1. `Parser._parse_table` — mutmut_10 (58 survivors in this function)

```diff
-        raise self.parse_error(UnexpectedEofError)
+        raise self.parse_error(None)
```

**Why it survives:** tests assert that malformed input raises a `ParseError`,
but not the specific subclass or cause. Passing `None` still produces a
`ParseError`, so the suite cannot see the lost error type.
**Verdict:** test gap. **Test:** parse `"[table"` at EOF and assert
`UnexpectedEofError` (or its exact message/cause). **Priority:** high.

## 2. `AoT.insert` — mutmut_10 (48 survivors)

```diff
-    if index < 0:
+    if index <= 0:
         index += length
```

**Why it survives:** tests cover append and negative insertion, but not
insertion at index 0. At index 0 the mutant shifts the index by `length`,
producing a different order.
**Verdict:** boundary gap. **Test:** insert a table at index 0 and assert order,
length and round-trip. **Priority:** high.

## 3. `Container.append` — mutmut_109 (36 survivors)

```diff
-                            self._validate_out_of_order_table(key)
+                            self._validate_out_of_order_table(None)
```

**Why it survives:** out-of-order validation is exercised indirectly, but no
test appends a table whose key conflicts with a later out-of-order table and
expects the validation error.
**Verdict:** argument-dropped gap. **Test:** append a conflicting table and
assert `KeyAlreadyPresent`/`TOMLKitError`. **Priority:** high.

## 4. `InlineTable.as_string` — mutmut_102 (35 survivors)

```diff
-            needs_separator = False
+            needs_separator = None
```

**Why it survives:** `None` is falsy, so the rendered output is unchanged.
**Verdict:** likely equivalent. **Test:** none; confirm by dataflow. **Priority:** low.

## 5. `Container._validate_table_candidate` — mutmut_10 (34 survivors)

```diff
-                raise TOMLKitError("Redefinition of an existing table")
+                raise TOMLKitError("redefinition of an existing table")
```

**Why it survives:** the test asserts the exception type, not the exact message.
**Verdict:** message gap. **Test:** assert the exact message for a dotted-table
redefinition. **Priority:** medium.

## 6. `Array.__delitem__` — mutmut_101 (27 survivors)

```diff
-                        group.indent._s = group.indent.s.replace(",", "", 1)
+                        group.indent._s = group.indent.s.replace(",", "", )
```

**Why it survives:** the suite deletes single commas; no test uses an indent
containing two commas, where removing all commas changes the output.
**Verdict:** boundary gap. **Test:** construct an array whose trivia contains
two commas, delete an element, assert only the first comma is removed and the
result reparses. **Priority:** high.

## 7. `Container._replace_at` — mutmut_10 (20 survivors)

```diff
-    dotted_to_header = k.is_dotted() and (
+    dotted_to_header = k.is_dotted() or (
         isinstance(value, AoT)
         or (isinstance(value, Table) and not value.is_super_table())
     )
```

**Why it survives:** no test replaces a non-dotted key with a `Table`/`AoT`,
where the `and`/`or` difference changes the header.
**Verdict:** boolean-logic gap. **Test:** replace a non-dotted key with a table
or AoT; assert the rendered header and round-trip. **Priority:** high.

## 8. `Array.add_line` — mutmut_11 (20 survivors)

```diff
-        raise ValueError("Comment cannot contain line breaks")
+        raise ValueError("XXComment cannot contain line breaksXX")
```

**Why it survives:** the test asserts `ValueError` only, not the message.
**Verdict:** message gap. **Test:** assert the exact message for
`add_line(comment="a\nb")`. **Priority:** medium.

## 9. `Parser._parse_string` — mutmut_103 (20 survivors)

```diff
-            close = ""
+            close = None
```

**Why it survives:** `close` is reassigned on the multiline path; the mutated
value appears unreachable in the tested paths.
**Verdict:** likely equivalent. **Test:** none unless dataflow shows a reachable
path. **Priority:** low.

## 10. `Container._render_table` — mutmut_26 (19 survivors)

```diff
-            open_, close = "[[", "]]"
+            open_, close = None
```

**Why it survives:** no test renders an AoT element through `as_string()` and
asserts the exact `[[...]]` header.
**Verdict:** test gap. **Test:** render a document containing an AoT; assert the
exact header and reparse. **Priority:** high.

## 11. `Parser._parse_comment_trail` — mutmut_29 (17 survivors)

```diff
-                    raise self.parse_error(InvalidControlChar, code, "comments")
+                    raise self.parse_error(InvalidControlChar, code, None)
```

**Why it survives:** the error is raised, but the message loses the
"comments" context. The suite checks the exception type, not the exact message.
**Verdict:** message/context gap. **Test:** parse a comment containing a control
character and assert the exact message. **Priority:** medium.

## 12. `InvalidControlChar.__init__` — mutmut_11 (12 survivors)

```diff
-    display_code += hex(char)[2:]
+    display_code += hex(char)[3:]
```

**Why it survives:** the exact hex code in the message is not asserted; dropping
the first hex digit changes `0x0f` to `f`, for example.
**Verdict:** message gap. **Test:** assert the exact message for control codes
at the `0x0f`/`0x10` boundary. **Priority:** medium.

---

## Summary

| Verdict | Cases |
|---|---|
| Test gap (boundary/logic/message) | 8 |
| Likely equivalent | 2 |
| Additional message/context gaps | 2 |

The dominant residual pattern is **exact oracle weakness**: the suite often
asserts an exception type or a semantic value but not the exact message,
header or formatting detail. The second pattern is **boundary positions**
(index 0, multi-comma trivia, AoT rendering).

No claim is made that these twelve cases are a random sample. They are the
highest-survivor functions, selected to show actionable failure modes.
