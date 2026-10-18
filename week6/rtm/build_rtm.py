import csv, sys
ids = {l.strip() for l in open("ai_test_ids.txt") if "::" in l}
classes = {"::".join(i.split("::")[:2]) for i in ids}
R = [
 ("R01","Parse any valid TOML 1.1 document into a TOMLDocument whose values match the spec types","README (\"1.1.0-compliant\"); CHANGELOG 0.15.0 #456","High",
  ["test_ai_parser.py::TestKeys","test_ai_parser.py::TestStrings","test_ai_parser.py::TestIntegers","test_ai_parser.py::TestFloats","test_ai_parser.py::TestDates","test_ai_parser.py::TestTables","test_ai_parser.py::TestArrayOfTables"],
  "Covered (unit)","Integration: run toml-test valid corpus through parse→unwrap (Wk 9); Property: Hypothesis value round-trip (Wk 7)"),
 ("R02","parse() then dumps() on an unmodified document returns the identical string (comments, whitespace, order preserved)","README (\"preserves all comments, indentations, whitespace and internal element ordering\")","High",
  ["test_ai_api.py::TestRoundTrip","test_ai_parser.py::TestArrays::test_multiline_trailing_comma_and_comments","test_ai_parser.py::TestWhitespaceAndNewlines::test_crlf_newlines"],
  "Covered (unit, 8 fixed examples)","Property: Hypothesis parse→dumps identity on generated docs (Wk 7); BDD scenario 'Unchanged file is byte-identical' (Wk 8)"),
 ("R03","Editing a parsed document changes only the edited value; untouched comments and layout are preserved","README (\"accessible and editable via an intuitive API\")","High",
  ["test_ai_container.py::TestEditingPreservesStyle","test_ai_items.py::TestIntegerFloat::test_integer_keeps_trivia_comment","test_ai_toml_file.py::TestTOMLFile::test_edit_and_write"],
  "Partial: Container.append/_insert_after/_replace_at largely unexecuted (see coverage gaps)","Manual unit tests from Wk 7 surviving mutants; BDD 'Bump a version keeps comments' (Wk 8)"),
 ("R04","Malformed input raises a ParseError subclass that reports the line and column of the problem","Code: exceptions.py, parser.py (parse_error)","High",
  ["test_ai_parser.py::TestErrorPositions","test_ai_parser.py::TestStrings::test_control_char_rejected","test_ai_parser.py::TestKeys::test_missing_key"],
  "Partial: ~25 negative tests assert only ParseError; D3 inline duplicate key escapes ParseError","Manual: assert exact subclass + line/col per error type (decision table, Wk 7); integration with toml-test invalid corpus (Wk 9)"),
 ("R05","dumps() serialises Mapping/Table/Container input, honours sort_keys, and raises TypeError for anything else","Docstring: api.dumps; CHANGELOG #482","Medium",
  ["test_ai_api.py::TestDumps","test_ai_api.py::TestEncoders::test_register_and_unregister"],
  "Covered (unit); sort_keys ignored on wrapper path not tested","Manual: wrapper + sort_keys case (Wk 7)"),
 ("R06","load()/dump() work with text and binary file-like objects","Docstring: api.load, api.dump","Medium",
  ["test_ai_api.py::TestFileLikeIO"],"Covered (unit)","Integration: dump→file→load round trip with real file (Wk 9)"),
 ("R07","TOMLFile.read/write round-trips a file and preserves LF, CRLF and mixed line endings","Code: toml_file.py","Medium",
  ["test_ai_toml_file.py::TestTOMLFile"],"Covered (unit, 98% stmt)","Integration test with real filesystem + edit (Wk 9)"),
 ("R08","date()/time()/datetime() factories return the right item type and reject strings of another kind","Docstring: api.date (\"only accepts date strings\")","Medium",
  ["test_ai_api.py::TestDateTimeFactories"],"FAILS: D1 date() accepts datetime strings (xfail)","Fix via TDD cycle #1 (Wk 8); Hypothesis over generated datetime strings (Wk 7)"),
 ("R09","item() converts supported Python types to TOML items, raises ConvertError otherwise, and consults registered custom encoders","Docstring: items.item, api.register_encoder","Medium",
  ["test_ai_items.py::TestItemConversion","test_ai_api.py::TestEncoders"],"Covered (unit); many checks are type-only","Property: Hypothesis item(x).unwrap() == x for generated JSON-like data (Wk 7)"),
 ("R10","string() applies TOML escaping for basic strings, supports literal/multiline forms, and rejects sequences invalid for the chosen form","Docstring: api.string; TOML spec §String; CHANGELOG (leading-newline fix)","Medium",
  ["test_ai_api.py::TestStringFactory","test_ai_items.py::TestStringFromRaw","test_ai_utils.py::TestEscapeString"],"Covered (unit)","Property: string(s) re-parses to s for arbitrary text (Wk 7)"),
 ("R11","Arithmetic on Integer/Float/Date/DateTime items returns TOML items of the same kind and keeps trivia","Code: items.py (Integer.__add__ etc.)","Low",
  ["test_ai_items.py::TestIntegerFloat","test_ai_items.py::TestDates"],"Covered (unit)","—"),
 ("R12","Array editing (append/insert/delete/set/add_line) yields valid, re-parseable output; slice assignment is rejected","Docstring: Array.add_line; CHANGELOG #499, #527; commit #600","High",
  ["test_ai_items.py::TestArray"],"Partial: Array.__delitem__ and insert edge paths unexecuted","Manual BVA tests on index 0 / -1 / len; state-transition tests for comma placement (Wk 7)"),
 ("R13","Out-of-order and dotted-key tables can be read, edited and deleted; re-serialisation follows the documented limitation","README §Limitations; CHANGELOG #261, #536, #545","High",
  ["test_ai_container.py::TestDottedAndOutOfOrder","test_ai_parser.py::TestTables::test_out_of_order_tables_round_trip"],"Partial: OutOfOrderTableProxy.__setitem__ / _merge_aot_fragment unexecuted","Integration: proxy + container + renderer scenarios (Wk 9)"),
 ("R14","Comments created through the API always produce valid TOML; line breaks are rejected or split","Docstring: api.comment; CHANGELOG #449, commit #544","Medium",
  ["test_ai_api.py::TestTriviaFactories::test_multiline_comment","test_ai_items.py::TestItemDecorations::test_comment_rejects_newline","test_ai_items.py::TestArray::test_add_line_comment_with_newline_rejected"],"FAILS for \\r: D6 comment('a\\rb') writes unparseable TOML (no AI test caught it)","Manual: \\r and \\r\\n cases (Wk 7); TDD fix (Wk 8)"),
 ("R15","Keys built with key() always serialise to a valid, re-parseable key","Docstring: api.key; reverse-engineered from code","Low",
  ["test_ai_api.py::TestKeyFactory"],"FAILS: D5 key([]) serialises as ' = 1' (no AI test caught it)","Manual BVA: empty / one / many segments (Wk 7)"),
 ("R16","Parsing time grows roughly linearly with document size (no quadratic blow-up)","CHANGELOG 0.15.1 #479, #503, #517, #525 (performance fixes); Risk R5","Medium",
  [],"UNTESTED by AI suite","Light-touch performance test with Locust/pytest-benchmark on large lock-file style input (Wk 9)"),
]
bad = []
for r in R:
    for t in r[4]:
        if t not in ids and t not in classes: bad.append(t)
if bad: sys.exit(f"missing test refs: {bad}")
with open("rtm_week6.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["Req ID","Requirement","Source","Risk priority","AI-baseline tests (tests_ai/)","Status after AI baseline","Planned tests (level, week)"])
    for r in R: w.writerow([r[0],r[1],r[2],r[3],"; ".join(r[4]) or "—",r[5],r[6]])
print("ok", len(R), "requirements; covered:", sum(1 for r in R if r[5].startswith("Covered")), "partial:", sum(1 for r in R if r[5].startswith("Partial")), "fails:", sum(1 for r in R if r[5].startswith("FAILS")), "untested:", sum(1 for r in R if r[5].startswith("UNTESTED")))
