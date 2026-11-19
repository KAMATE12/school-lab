import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from school_lab.ast_features import prepare_ast_code as features
from school_lab.ast_comparison import PreparedAstSubmission, compare_ast_submissions as compare
from school_lab.ast_cli import main
from school_lab.errors import SubmissionError
from school_lab.validation import parse_submission

# RU: Создаём независимые учебные работы для проверок.
# EN: Create independent learning submissions for the checks.
def raw(identifier="a", student="s1", code="value = 2\n"):
    return dict(schema_version=1, submission_id=identifier, student_id=student,
                assignment_id="task", submitted_at="2026-10-10T17:00:00+00:00",
                text="", code=code, template_id=None,
                ai_declaration=dict(used=False, tool=None, purpose=None, verified_by_student=True))

def prepared(identifier="a", student="s1", code="value = 2\n", template=""):
    return PreparedAstSubmission(parse_submission(raw(identifier, student, code)), features(code, template))

class AstMethodTests(unittest.TestCase):
    # RU: Проверяем результаты нормализации и границы областей.
    # EN: Check normalization results and scope boundaries.
    def test_renaming_formatting_and_comprehension(self):
        a="def solve(values):\n    return sum(x*x for x in values if x>=0)\n"
        b="# Comment\ndef compute(items):\n    return sum(item * item for item in items if item >= 0)\n"
        self.assertEqual(features(a).keys, features(b).keys)
        result=compare(prepared(code=a),prepared("b","s2",b))
        self.assertEqual(result.score,1.0)
        self.assertEqual(result.second_matches[0].start_line,2)

    def test_operator_and_repeated_variable_remain_distinct(self):
        base=features("def f(a,b):\n return a*b\n").keys
        for code in ("def f(a,b):\n return a+b\n","def f(a,b):\n return a*a\n"):
            self.assertNotEqual(base,features(code).keys)

    def test_scopes_are_independent(self):
        a="def f(x):\n return x*2\ndef g(x):\n return x+1\n"
        b="def a(value):\n return value*2\ndef b(number):\n return number+1\n"
        self.assertEqual(features(a).keys,features(b).keys)

    def test_capture_differs_from_shadowing(self):
        a="def f(x):\n def g(y):\n  return x+y\n return g\n"
        b="def f(x):\n def g(y):\n  return y+y\n return g\n"
        self.assertNotEqual(features(a).keys,features(b).keys)
        c="def outer(a):\n def inner(b):\n  return a+b\n return inner\n"
        self.assertEqual(features(a).keys,features(c).keys)

    def test_external_functions_and_import_paths_preserved(self):
        self.assertNotEqual(features("x=sum(values)").keys,features("x=max(values)").keys)
        self.assertNotEqual(features("import os\nx=os.name").keys,features("import sys\nx=sys.name").keys)
        self.assertEqual(features("import math as m\nx=m.pi").keys,features("import math as maths\ny=maths.pi").keys)

    def test_defaults_resolve_in_parent_scope(self):
        a="x=2\ndef f(x=x):\n return x\n"
        b="outer=2\ndef g(inner=outer):\n return inner\n"
        self.assertEqual(features(a).keys,features(b).keys)

    def test_lambda_and_first_comprehension_iterable(self):
        a="xs=[1,2]\ny=[xs*2 for xs in xs]\nf=lambda x:x+1\n"
        b="items=[1,2]\nresult=[item*2 for item in items]\ng=lambda value:value+1\n"
        self.assertEqual(features(a).keys,features(b).keys)

    def test_assignment_is_known_before_first_use(self):
        # RU: Анализ не доказывает выполнимость программы.
        # EN: Analysis does not prove that the program can run successfully.
        a="def f():\n print(x)\n x=1\n"
        b="def g():\n print(value)\n value=1\n"
        self.assertEqual(features(a).keys,features(b).keys)

    def test_empty_and_template_only_have_no_features(self):
        self.assertFalse(features("# Comment\n").keys)
        self.assertFalse(features("x=1\n","x=1").keys)
        a=prepared(code="# Comment\n")
        self.assertIsNone(compare(a,prepared("b","s2","# Other\n")).score)
        self.assertEqual(compare(a,prepared("b","s2")).score,0.0)

    def test_template_exclusion_preserves_source_positions(self):
        f=features("header=0\nvalue=2\n","header=0")
        self.assertEqual(f.template_lines,(1,))
        self.assertEqual([(o.start_line,o.end_line) for o in f.occurrences],[(2,2)])
        self.assertEqual(f.keys,features("other=2\n").keys)
        f=features("def f(x):\n    marker=0\n    return x+1\n","    marker=0")
        self.assertEqual([(o.start_line,o.end_line) for o in f.occurrences],[(3,3)])

    def test_configuration_changes_and_ineligible_pairs(self):
        a=prepared()
        different=replace(prepared("b","s2"),submission=replace(a.submission,
                          submission_id="b",student_id="s2",assignment_id="other"))
        for b,expected in ((a,"self_match"),(prepared("b","s1"),"same_student"),
                           (different,"assignment_mismatch"),
                           (prepared("b","s2",template="# Teacher"),"configuration_mismatch")):
            with self.subTest(expected=expected):
                with self.assertRaises(SubmissionError) as caught: compare(a,b)
                self.assertEqual(caught.exception.code,expected)

    def test_syntax_and_unsupported_constructs_are_explicit(self):
        for code,expected in (("def bad(\n","invalid_code"),("class A: pass","unsupported_ast"),
                              ("global x\nx=1","unsupported_ast"),("x=(y:=1)","unsupported_ast")):
            with self.subTest(code=code):
                with self.assertRaises(SubmissionError) as caught: features(code)
                self.assertEqual(caught.exception.code,expected)

    def test_comparison_is_symmetric_and_does_not_reparse(self):
        a,b=prepared(),prepared("b","s2","other=3\n")
        before=copy.deepcopy((a,b))
        with patch("school_lab.ast_features.ast.parse",side_effect=AssertionError("Unexpected parse")):
            forward,backward=compare(a,b),compare(b,a)
        self.assertEqual(forward.score,backward.score)
        self.assertEqual((a,b),before)
        self.assertTrue(0<=forward.score<=1)

    def test_cli_continues_after_errors_and_protects_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);catalog=root/"assignments.json";source=root/"input.jsonl";output=root/"output.jsonl"
            catalog.write_text(json.dumps([dict(assignment_id="task",allowed_template="",requirements=[])]))
            source.write_text("\n".join([json.dumps(raw()),json.dumps(raw()),"{broken",
                json.dumps(raw(code="value=9\n")),json.dumps(raw("bad","s3","def invalid(\n")),
                json.dumps(raw("b","s2")),json.dumps(raw("c","s1"))]),encoding="utf-8")
            args=[str(source),"--assignments",str(catalog),"--output",str(output)]
            out,err=io.StringIO(),io.StringIO()
            with redirect_stdout(out),redirect_stderr(err):status=main(args)
            self.assertEqual(status,1)
            self.assertEqual(json.loads(out.getvalue()),dict(accepted=4,prepared=3,duplicate=1,errors=3,comparisons=2,insufficient=0))
            records=[json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual([(r["first_id"],r["second_id"]) for r in records],[("a","b"),("b","c")])
            self.assertEqual(records[0]["score"],1.0)
            before=output.read_bytes()
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):self.assertEqual(main(args),2)
            self.assertEqual(output.read_bytes(),before)

if __name__=="__main__":unittest.main()
