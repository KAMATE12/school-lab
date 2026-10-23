# RU: Проверяем общие контракты и пограничные случаи.
# EN: Verify common contracts and boundary cases.
import copy
import json
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from school_lab.analysis_service import ANALYZER_FACTORIES, analyze_submission
from school_lab.assignments import parse_assignments
from school_lab.errors import SubmissionError
from school_lab.models import AnalysisContext, Assignment
from school_lab.report_validation import validate_report
from school_lab.serialization import canonical_json, submission_hash
from school_lab.validation import parse_submission


class FinalContracts(unittest.TestCase):
    def setUp(self) -> None:
        # RU: Используем отдельную синтетическую работу.
        # EN: Use a separate synthetic submission.
        self.raw = dict(schema_version=1, submission_id='contract-1', student_id='student-1',
            assignment_id='assignment-01', submitted_at='2026-10-10T17:00:00+00:00',
            text='Explanation.', code='print(1)\n\nprint(2)', template_id=None,
            ai_declaration=dict(used=False, tool=None, purpose=None, verified_by_student=True))
        self.submission = parse_submission(self.raw)
        self.context = AnalysisContext(Assignment('assignment-01', 'print(1)', ('Explain.',)))

    def test_shared_analyzer_contract(self) -> None:
        # RU: Один набор проверок применяется ко всем анализаторам.
        # EN: Apply one set of checks to all analyzers.
        for name in ('length', 'template', 'ai_declaration'):
            with self.subTest(analyzer=name):
                before = copy.deepcopy((self.submission, self.context))
                first = analyze_submission(self.submission, self.context, name)
                second = analyze_submission(self.submission, self.context, name)
                validate_report(first, self.submission, self.context, name)
                self.assertEqual(first.findings, second.findings)
                self.assertEqual(first.config_hash, second.config_hash)
                self.assertEqual(first.submission_hash, submission_hash(self.submission))
                self.assertNotEqual(first.report_id, second.report_id)
                self.assertEqual((self.submission, self.context), before)

    def test_mutating_analyzer_cannot_change_original(self) -> None:
        class MutatingAnalyzer:
            def analyze(self, submission, context):
                # RU: Намеренно обходим frozen для проверки защиты сервиса.
                # EN: Intentionally bypass frozen to test service protection.
                object.__setattr__(submission, 'code', 'changed')
                return None
        with patch.dict(ANALYZER_FACTORIES, {'mutating': MutatingAnalyzer}):
            with self.assertRaises(SubmissionError) as caught:
                analyze_submission(self.submission, self.context, 'mutating')
        self.assertEqual(caught.exception.code, 'analyzer_mutation')
        self.assertEqual(self.submission.code, self.raw['code'])

    def test_invalid_metadata_is_rejected(self) -> None:
        report = analyze_submission(self.submission, self.context, 'length')
        for change in ({'config_hash':'bad'}, {'created_at':'2026-01-01'}, {'review_required':1},
                       {'analyzer_version':''}, {'findings':[]}):
            with self.subTest(change=change), self.assertRaises(SubmissionError):
                validate_report(replace(report, **change), self.submission, self.context, 'length')

    def test_template_configuration_changes_hash(self) -> None:
        first = analyze_submission(self.submission, self.context, 'template')
        other = replace(self.context, assignment=replace(self.context.assignment, allowed_template='print(2)'))
        second = analyze_submission(self.submission, other, 'template')
        self.assertNotEqual(first.config_hash, second.config_hash)

    def test_direct_invalid_ai_declaration_is_rejected(self) -> None:
        bad = replace(self.submission, ai_declaration=replace(self.submission.ai_declaration, used=True))
        with self.assertRaises(SubmissionError) as caught:
            analyze_submission(bad, self.context, 'ai_declaration')
        self.assertEqual(caught.exception.code, 'schema_error')

    def test_assignment_catalog_validation(self) -> None:
        data = [dict(assignment_id='assignment-01', allowed_template='', requirements=['Explain.'])]
        self.assertEqual(parse_assignments(data)['assignment-01'].requirements, ('Explain.',))
        for invalid in ({}, data + data, [dict(data[0], requirements='wrong')]):
            with self.subTest(data=invalid), self.assertRaises(SubmissionError):
                parse_assignments(invalid)

    def test_nested_schema_and_wrong_root(self) -> None:
        cases = [([], 'submission')]
        for key, value in [('used', 1), ('verified_by_student', 'true')]:
            data = copy.deepcopy(self.raw); data['ai_declaration'][key] = value
            cases.append((data, 'ai_declaration.' + key))
        data = copy.deepcopy(self.raw); del data['ai_declaration']['used']
        cases.append((data, 'ai_declaration.used'))
        for data, field in cases:
            with self.subTest(field=field), self.assertRaises(SubmissionError) as caught:
                parse_submission(data)
            self.assertEqual(caught.exception.field, field)

    def test_import_cli_stdout_is_json(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory)/'input.jsonl'
            path.write_text(canonical_json(self.raw)+'\n', encoding='utf-8')
            result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'school_lab.cli', str(path)],
                capture_output=True, text=True, encoding='utf-8', cwd=directory, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), dict(accepted=1, duplicate=0, errors=0))

    def test_analysis_cli_uses_assignment_catalog(self) -> None:
        with TemporaryDirectory() as directory:
            folder = Path(directory); source = folder/'input.jsonl'; catalog=folder/'assignments.json'; output=folder/'reports.jsonl'
            source.write_text(canonical_json(self.raw)+'\n', encoding='utf-8')
            catalog.write_text(json.dumps([dict(assignment_id='assignment-01', allowed_template='print(1)', requirements=['Explain.'])]), encoding='utf-8')
            result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'school_lab.analyze_cli',str(source),
                '--assignment-id','assignment-01','--assignments',str(catalog),'--analyzer','template','--output',str(output)],
                capture_output=True,text=True,encoding='utf-8',cwd=directory,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['findings'][0]['evidence'][0]['start_line'],1)

if __name__ == '__main__':
    unittest.main()
