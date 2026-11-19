import unittest
from dataclasses import replace
from unittest.mock import patch

from school_lab.ast_comparison import PreparedAstSubmission
from school_lab.ast_features import prepare_ast_code
from school_lab.corpus_pairs import PreparedSubmission
from school_lab.errors import SubmissionError
from school_lab.models import AIDeclaration, Submission
from school_lab.prepared_code import prepare_token_code
from school_lab.ranking import rank_ast_candidates, rank_token_candidates


# RU: Проверяем одни и те же контракты для двух методов.
# EN: Check the same contracts for both methods.
class RankingTests(unittest.TestCase):
    def cases(self):
        return (
            (rank_token_candidates, PreparedSubmission, prepare_token_code),
            (rank_ast_candidates, PreparedAstSubmission, prepare_ast_code),
        )

    def submission(self, identifier, student, code="x=1\n", assignment="task"):
        return Submission(1, identifier, student, assignment,
                          "2026-10-10T17:00:00+00:00", "", code, None,
                          AIDeclaration(False, None, None, True))

    def test_filtering_happens_before_comparison(self):
        for rank, wrapper, prepare in self.cases():
            with self.subTest(method=rank.__name__):
                query=wrapper(self.submission("q","s1"),prepare("x=1\n"))
                # RU: Другая конфигурация исключённых кандидатов не должна сравниваться.
                # EN: Ineligible candidates with another configuration must not be compared.
                other_features=prepare("x=1\n","# different configuration")
                candidates=[query,
                    wrapper(self.submission("version","s1"),other_features),
                    wrapper(self.submission("other","s2",assignment="other"),other_features),
                    wrapper(self.submission("valid","s2"),query.features)]
                result=rank(query,iter(candidates),3)
                self.assertEqual([m.candidate_id for m in result.matches],["valid"])
                self.assertEqual((result.compared,result.excluded,result.insufficient),(1,3,0))
                self.assertTrue(result.matches[0].comparison.first_matches)

    def test_ties_are_deterministic_and_limit_is_respected(self):
        for rank,wrapper,prepare in self.cases():
            with self.subTest(method=rank.__name__):
                f=prepare("x=1\n");query=wrapper(self.submission("q","s1"),f)
                candidates=[wrapper(self.submission(i,"s2"),f) for i in ("c","a","b")]
                a=rank(query,candidates,2);b=rank(query,reversed(candidates),2)
                self.assertEqual(a,b)
                self.assertEqual([m.candidate_id for m in a.matches],["a","b"])
                self.assertEqual(a.compared,3)

    def test_scores_are_sorted_descending(self):
        for rank,wrapper,prepare in self.cases():
            with self.subTest(method=rank.__name__):
                query=wrapper(self.submission("q","s1"),prepare("x=1\n"))
                candidates=[wrapper(self.submission("low","s2","y=2\n"),prepare("y=2\n")),
                            wrapper(self.submission("high","s3"),query.features)]
                result=rank(query,candidates,2)
                self.assertEqual([m.candidate_id for m in result.matches],["high","low"])
                self.assertEqual([m.score for m in result.matches],[1.0,0.0])

    def test_none_is_skipped_but_zero_is_ranked(self):
        for rank,wrapper,prepare in self.cases():
            with self.subTest(method=rank.__name__):
                empty=prepare("# empty\n")
                query=wrapper(self.submission("q","s1","# empty\n"),empty)
                candidates=[wrapper(self.submission("empty","s2","# empty\n"),empty),
                            wrapper(self.submission("full","s3"),prepare("x=1\n"))]
                result=rank(query,candidates,5)
                self.assertEqual([m.candidate_id for m in result.matches],["full"])
                self.assertEqual(result.matches[0].score,0.0)
                self.assertEqual((result.compared,result.insufficient),(2,1))

    def test_invalid_k_is_rejected_before_reading_input(self):
        def unreadable():
            raise AssertionError("Input must not be read")
            yield
        for rank,wrapper,prepare in self.cases():
            query=wrapper(self.submission("q","s1"),prepare("x=1\n"))
            for value,error in ((True,TypeError),(1.5,TypeError),("2",TypeError),(0,ValueError),(-1,ValueError)):
                with self.subTest(method=rank.__name__,k=value),self.assertRaises(error):
                    rank(query,unreadable(),value)

    def test_duplicate_ids_and_incompatible_configuration_are_rejected(self):
        for rank,wrapper,prepare in self.cases():
            query=wrapper(self.submission("q","s1"),prepare("x=1\n"))
            candidate=wrapper(self.submission("a","s2"),query.features)
            with self.subTest(method=rank.__name__):
                with self.assertRaises(SubmissionError) as caught:rank(query,[candidate,candidate])
                self.assertEqual(caught.exception.code,"duplicate_input")
                bad=replace(candidate,features=prepare("x=1\n","# other"))
                with self.assertRaises(SubmissionError) as caught:rank(query,[bad])
                self.assertEqual(caught.exception.code,"configuration_mismatch")

    def test_empty_candidates_return_empty_ranking(self):
        for rank,wrapper,prepare in self.cases():
            query=wrapper(self.submission("q","s1"),prepare("x=1\n"))
            result=rank(query,[],3)
            self.assertEqual(result.matches,())
            self.assertEqual((result.compared,result.excluded,result.insufficient),(0,0,0))

    def test_prepared_features_are_not_recomputed(self):
        for rank,wrapper,prepare in self.cases():
            query=wrapper(self.submission("q","s1"),prepare("x=1\n"))
            candidate=wrapper(self.submission("a","s2"),query.features)
            with patch("ast.parse",side_effect=AssertionError("Unexpected parse")):
                result=rank(query,[candidate],1)
            self.assertEqual(result.matches[0].score,1.0)

if __name__=="__main__":
    unittest.main()
