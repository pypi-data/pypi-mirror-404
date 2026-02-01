"""Verification tests for hypothesis strategies

This module contains basic tests to verify that the custom hypothesis
strategies generate valid entities that pass all validation rules.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.crawler.domain.entities.enums import SubmissionStatus
from tests.strategies import (
    accepted_submission_strategy,
    difficulty_strategy,
    example_strategy,
    examples_list_strategy,
    failed_submission_strategy,
    percentiles_strategy,
    problem_strategy,
    problem_with_difficulty_strategy,
    problem_with_platform_strategy,
    problems_list_strategy,
    submission_for_problem_strategy,
    submission_strategy,
    submissions_list_strategy,
)


class TestValueObjectStrategies:
    """Test that value object strategies generate valid objects"""

    @given(example_strategy())
    @settings(max_examples=50)
    def test_example_strategy_generates_valid_examples(self, example):
        """Verify example strategy generates valid Example objects"""
        assert example.input
        assert example.output
        # Explanation can be None or a string
        assert example.explanation is None or isinstance(example.explanation, str)

    @given(difficulty_strategy())
    @settings(max_examples=50)
    def test_difficulty_strategy_generates_valid_difficulties(self, difficulty):
        """Verify difficulty strategy generates valid Difficulty objects"""
        assert difficulty.level in ["Easy", "Medium", "Hard"]

    @given(percentiles_strategy())
    @settings(max_examples=50)
    def test_percentiles_strategy_generates_valid_percentiles(self, percentiles):
        """Verify percentiles strategy generates valid Percentiles objects"""
        assert 0.0 <= percentiles.runtime <= 100.0
        assert 0.0 <= percentiles.memory <= 100.0


class TestEntityStrategies:
    """Test that entity strategies generate valid entities"""

    @given(problem_strategy())
    @settings(max_examples=50)
    def test_problem_strategy_generates_valid_problems(self, problem):
        """Verify problem strategy generates valid Problem entities"""
        # Check required fields are not empty
        assert problem.id
        assert problem.platform in ["leetcode", "hackerrank", "codechef", "codeforces"]
        assert problem.title
        assert problem.difficulty.level in ["Easy", "Medium", "Hard"]
        assert problem.description
        assert len(problem.description) >= 10

        # Check lists
        assert len(problem.topics) >= 1
        assert len(problem.examples) >= 1

        # Check acceptance rate
        assert 0.0 <= problem.acceptance_rate <= 100.0

    @given(submission_strategy())
    @settings(max_examples=50)
    def test_submission_strategy_generates_valid_submissions(self, submission):
        """Verify submission strategy generates valid Submission entities"""
        # Check required fields are not empty
        assert submission.id
        assert submission.problem_id
        assert submission.language
        assert submission.code
        assert len(submission.code) >= 10

        # Check status is valid
        assert isinstance(submission.status, SubmissionStatus)

        # Check runtime and memory format
        assert "ms" in submission.runtime
        assert "MB" in submission.memory

        # Check timestamp is non-negative
        assert submission.timestamp >= 0

        # Percentiles can be None or valid
        if submission.percentiles:
            assert 0.0 <= submission.percentiles.runtime <= 100.0
            assert 0.0 <= submission.percentiles.memory <= 100.0

    @given(accepted_submission_strategy())
    @settings(max_examples=50)
    def test_accepted_submission_strategy_generates_accepted_submissions(self, submission):
        """Verify accepted submission strategy generates ACCEPTED submissions"""
        assert submission.status == SubmissionStatus.ACCEPTED

    @given(failed_submission_strategy())
    @settings(max_examples=50)
    def test_failed_submission_strategy_generates_failed_submissions(self, submission):
        """Verify failed submission strategy generates non-ACCEPTED submissions"""
        assert submission.status != SubmissionStatus.ACCEPTED
        assert submission.status in [
            SubmissionStatus.WRONG_ANSWER,
            SubmissionStatus.TIME_LIMIT_EXCEEDED,
            SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
            SubmissionStatus.RUNTIME_ERROR,
            SubmissionStatus.COMPILE_ERROR,
        ]


class TestSpecializedStrategies:
    """Test specialized strategies that generate entities with specific properties"""

    @given(problem_with_platform_strategy(platform="leetcode"))
    @settings(max_examples=50)
    def test_problem_with_platform_strategy_generates_correct_platform(self, problem):
        """Verify problem with platform strategy generates correct platform"""
        assert problem.platform == "leetcode"

    @given(problem_with_difficulty_strategy(difficulty_level="Hard"))
    @settings(max_examples=50)
    def test_problem_with_difficulty_strategy_generates_correct_difficulty(self, problem):
        """Verify problem with difficulty strategy generates correct difficulty"""
        assert problem.difficulty.level == "Hard"

    @given(problem_strategy(), st.data())
    @settings(max_examples=50)
    def test_submission_for_problem_strategy_matches_problem_id(self, problem, data):
        """Verify submission for problem strategy uses correct problem ID"""
        from tests.strategies import submission_for_problem_strategy

        # Generate a submission for the given problem using data.draw()
        submission = data.draw(submission_for_problem_strategy(problem=problem))
        # Verify the submission's problem_id matches the problem's id
        assert submission.problem_id == problem.id


class TestListStrategies:
    """Test list strategies that generate lists of entities"""

    @given(problems_list_strategy(min_size=2, max_size=5))
    @settings(max_examples=50)
    def test_problems_list_strategy_generates_valid_lists(self, problems):
        """Verify problems list strategy generates valid lists"""
        assert 2 <= len(problems) <= 5
        for problem in problems:
            assert problem.id
            assert problem.title

    @given(submissions_list_strategy(min_size=2, max_size=5))
    @settings(max_examples=50)
    def test_submissions_list_strategy_generates_valid_lists(self, submissions):
        """Verify submissions list strategy generates valid lists"""
        assert 2 <= len(submissions) <= 5
        for submission in submissions:
            assert submission.id
            assert submission.code

    @given(examples_list_strategy(min_size=1, max_size=3))
    @settings(max_examples=50)
    def test_examples_list_strategy_generates_valid_lists(self, examples):
        """Verify examples list strategy generates valid lists"""
        assert 1 <= len(examples) <= 3
        for example in examples:
            assert example.input
            assert example.output
