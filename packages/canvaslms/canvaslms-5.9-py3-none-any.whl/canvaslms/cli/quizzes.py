import argparse
import csv
import difflib
import json
import os
import re
import statistics
import sys
import time
import yaml
from collections import defaultdict, Counter
from typing import Dict, List, Any

import pypandoc

import canvaslms.cli
import canvaslms.cli.courses as courses
import canvaslms.cli.assignments as assignments
import canvaslms.cli.content as content
import canvaslms.cli.modules as modules
import canvaslms.cli.utils
from rich.console import Console
from rich.markdown import Markdown

QUIZ_SCHEMA = {
    "title": {
        "default": "",
        "required": True,
        "canvas_attr": "title",
        "description": "Quiz title",
    },
    "id": {
        "default": None,
        "required": False,
        "canvas_attr": "id",
        "description": "Quiz ID (for identification during edit)",
    },
    "time_limit": {
        "default": None,
        "required": False,
        "canvas_attr": "time_limit",
        "description": "Time limit in minutes (null for unlimited)",
    },
    "due_at": {
        "default": None,
        "required": False,
        "canvas_attr": "due_at",
        "description": "Due date (ISO 8601 datetime)",
    },
    "unlock_at": {
        "default": None,
        "required": False,
        "canvas_attr": "unlock_at",
        "description": "Available from date (ISO 8601 datetime)",
    },
    "lock_at": {
        "default": None,
        "required": False,
        "canvas_attr": "lock_at",
        "description": "Available until date (ISO 8601 datetime)",
    },
    "points_possible": {
        "default": None,
        "required": False,
        "canvas_attr": "points_possible",
        "description": "Total points for the quiz",
    },
    "published": {
        "default": False,
        "required": False,
        "canvas_attr": "published",
        "description": "Whether the quiz is visible to students",
    },
    "allowed_attempts": {
        "default": 1,
        "required": False,
        "canvas_attr": "allowed_attempts",
        "description": "Number of attempts allowed (-1 for unlimited)",
    },
    "shuffle_questions": {
        "default": False,
        "required": False,
        "canvas_attr": "shuffle_questions",
        "description": "Randomize question order",
    },
    "shuffle_answers": {
        "default": False,
        "required": False,
        "canvas_attr": "shuffle_answers",
        "description": "Randomize answer choice order",
    },
    "show_correct_answers": {
        "default": True,
        "required": False,
        "canvas_attr": "show_correct_answers",
        "description": "Show correct answers after submission",
    },
    "one_question_at_a_time": {
        "default": False,
        "required": False,
        "canvas_attr": "one_question_at_a_time",
        "description": "Show one question per page",
    },
    "cant_go_back": {
        "default": False,
        "required": False,
        "canvas_attr": "cant_go_back",
        "description": "Prevent going back to previous questions",
    },
    "access_code": {
        "default": None,
        "required": False,
        "canvas_attr": "access_code",
        "description": "Password required to take the quiz",
    },
    "quiz_type": {
        "default": "assignment",
        "required": False,
        "canvas_attr": "quiz_type",
        "description": "Type: assignment, practice_quiz, graded_survey, survey",
    },
    "hide_results": {
        "default": None,
        "required": False,
        "canvas_attr": "hide_results",
        "description": "When to hide results: null, always, until_after_last_attempt",
    },
}
NEW_QUIZ_MULTIPLE_ATTEMPTS_SCHEMA = {
    "multiple_attempts_enabled": {
        "default": False,
        "description": "Whether multiple attempts are allowed",
    },
    "attempt_limit": {
        "default": True,
        "description": "Whether there is a maximum number of attempts (False = unlimited)",
    },
    "max_attempts": {
        "default": 1,
        "description": "Maximum number of attempts (only used if attempt_limit is True)",
    },
    "score_to_keep": {
        "default": "highest",
        "description": "Which score to keep: average, first, highest, or latest",
    },
    "cooling_period": {
        "default": False,
        "description": "Whether to require a waiting period between attempts",
    },
    "cooling_period_seconds": {
        "default": None,
        "description": "Required waiting time between attempts in seconds (e.g., 3600 = 1 hour)",
    },
}
NEW_QUIZ_RESULT_VIEW_SCHEMA = {
    "result_view_restricted": {
        "default": False,
        "description": "Whether to restrict what students see in results",
    },
    "display_points_awarded": {
        "default": True,
        "description": "Show points earned (requires result_view_restricted=True)",
    },
    "display_points_possible": {
        "default": True,
        "description": "Show total points possible (requires result_view_restricted=True)",
    },
    "display_items": {
        "default": True,
        "description": "Show questions in results (requires result_view_restricted=True)",
    },
    "display_item_response": {
        "default": True,
        "description": "Show student responses (requires display_items=True)",
    },
    "display_item_response_qualifier": {
        "default": "always",
        "description": "When to show responses: always, once_per_attempt, after_last_attempt, once_after_last_attempt",
    },
    "display_item_response_correctness": {
        "default": True,
        "description": "Show whether answers are correct/incorrect (requires display_item_response=True)",
    },
    "display_item_response_correctness_qualifier": {
        "default": "always",
        "description": "When to show correctness: always, after_last_attempt",
    },
    "display_item_correct_answer": {
        "default": True,
        "description": "Show the correct answer (requires display_item_response_correctness=True)",
    },
    "display_item_feedback": {
        "default": True,
        "description": "Show item feedback (requires display_items=True)",
    },
}
EXAMPLE_NEW_QUIZ_JSON = {
    "items": [
        {
            "position": 1,
            "points_possible": 1,
            "entry": {
                "title": "True/False Example",
                "item_body": "<p>Python is an interpreted programming language.</p>",
                "interaction_type_slug": "true-false",
                "interaction_data": {"true_choice": "True", "false_choice": "False"},
                "scoring_data": {"value": True},
                "scoring_algorithm": "Equivalence",
            },
        },
        {
            "position": 2,
            "points_possible": 2,
            "entry": {
                "title": "Multiple Choice Example",
                "item_body": "<p>What is the capital of Sweden?</p>",
                "interaction_type_slug": "choice",
                "interaction_data": {
                    "choices": [
                        {
                            "id": "11111111-1111-1111-1111-111111111111",
                            "position": 1,
                            "item_body": "Stockholm",
                        },
                        {
                            "id": "22222222-2222-2222-2222-222222222222",
                            "position": 2,
                            "item_body": "Gothenburg",
                        },
                        {
                            "id": "33333333-3333-3333-3333-333333333333",
                            "position": 3,
                            "item_body": "Malmö",
                        },
                        {
                            "id": "44444444-4444-4444-4444-444444444444",
                            "position": 4,
                            "item_body": "Uppsala",
                        },
                    ]
                },
                "scoring_data": {"value": "11111111-1111-1111-1111-111111111111"},
                "scoring_algorithm": "Equivalence",
            },
        },
        {
            "position": 3,
            "points_possible": 3,
            "entry": {
                "title": "Multiple Answer Example",
                "item_body": "<p>Select all prime numbers:</p>",
                "interaction_type_slug": "multi-answer",
                "interaction_data": {
                    "choices": [
                        {
                            "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                            "position": 1,
                            "item_body": "2",
                        },
                        {
                            "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                            "position": 2,
                            "item_body": "3",
                        },
                        {
                            "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                            "position": 3,
                            "item_body": "4",
                        },
                        {
                            "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
                            "position": 4,
                            "item_body": "5",
                        },
                    ]
                },
                "scoring_data": {
                    "value": [
                        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                        "dddddddd-dddd-dddd-dddd-dddddddddddd",
                    ]
                },
                "scoring_algorithm": "AllOrNothing",
            },
        },
        {
            "position": 4,
            "points_possible": 5,
            "entry": {
                "title": "Essay Example",
                "item_body": "<p>Explain the benefits of version control systems.</p>",
                "interaction_type_slug": "essay",
                "interaction_data": {"rce": True, "word_limit_enabled": False},
                "scoring_data": {"value": ""},
                "scoring_algorithm": "None",
            },
        },
        {
            "position": 5,
            "points_possible": 2,
            "entry": {
                "title": "Matching Example",
                "item_body": "<p>Match the capital cities to their countries:</p>",
                "interaction_type_slug": "matching",
                "interaction_data": {
                    "answers": [
                        "Stockholm",
                        "Oslo",
                        "Copenhagen",
                        "Helsinki",
                        "Berlin",
                    ],
                    "questions": [
                        {"id": "q1", "item_body": "Sweden"},
                        {"id": "q2", "item_body": "Norway"},
                        {"id": "q3", "item_body": "Denmark"},
                        {"id": "q4", "item_body": "Finland"},
                    ],
                },
                "properties": {"shuffle_rules": {"questions": {"shuffled": False}}},
                "scoring_data": {
                    "value": {
                        "q1": "Stockholm",
                        "q2": "Oslo",
                        "q3": "Copenhagen",
                        "q4": "Helsinki",
                    },
                    "edit_data": {
                        "matches": [
                            {
                                "answer_body": "Stockholm",
                                "question_id": "q1",
                                "question_body": "Sweden",
                            },
                            {
                                "answer_body": "Oslo",
                                "question_id": "q2",
                                "question_body": "Norway",
                            },
                            {
                                "answer_body": "Copenhagen",
                                "question_id": "q3",
                                "question_body": "Denmark",
                            },
                            {
                                "answer_body": "Helsinki",
                                "question_id": "q4",
                                "question_body": "Finland",
                            },
                        ],
                        "distractors": ["Berlin"],
                    },
                },
                "scoring_algorithm": "DeepEquals",
            },
        },
        {
            "position": 6,
            "points_possible": 2,
            "entry": {
                "title": "Ordering Example",
                "item_body": "<p>Arrange the numbers from smallest to largest:</p>",
                "interaction_type_slug": "ordering",
                "interaction_data": {
                    "choices": {
                        "ord-1": {"id": "ord-1", "item_body": "5"},
                        "ord-2": {"id": "ord-2", "item_body": "2"},
                        "ord-3": {"id": "ord-3", "item_body": "8"},
                        "ord-4": {"id": "ord-4", "item_body": "1"},
                    }
                },
                "properties": {
                    "top_label": "Smallest",
                    "bottom_label": "Largest",
                    "include_labels": True,
                    "display_answers_paragraph": False,
                },
                "scoring_data": {"value": ["ord-4", "ord-2", "ord-1", "ord-3"]},
                "scoring_algorithm": "DeepEquals",
            },
        },
        {
            "position": 7,
            "points_possible": 3,
            "entry": {
                "title": "Fill in the Blank Example",
                "item_body": "<p>The chemical symbol for water is `H2O`. "
                "Oxygen has atomic number `8`.</p>",
                "interaction_type_slug": "rich-fill-blank",
                "interaction_data": {
                    "blanks": [
                        {"id": "blank1", "answer_type": "openEntry"},
                        {"id": "blank2", "answer_type": "openEntry"},
                    ],
                    "word_bank_choices": [],
                },
                "properties": {
                    "shuffle_rules": {
                        "blanks": {
                            "children": {
                                "0": {"children": None},
                                "1": {"children": None},
                            }
                        }
                    }
                },
                "scoring_data": {
                    "value": [
                        {
                            "id": "blank1",
                            "scoring_data": {
                                "value": "H2O",
                                "blank_text": "H2O",
                                "ignore_case": True,
                            },
                            "scoring_algorithm": "TextEquivalence",
                        },
                        {
                            "id": "blank2",
                            "scoring_data": {"value": "8", "blank_text": "8"},
                            "scoring_algorithm": "TextEquivalence",
                        },
                    ],
                    "working_item_body": "<p>The chemical symbol for water is `H2O`. "
                    "Oxygen has atomic number `8`.</p>",
                },
                "scoring_algorithm": "MultipleMethods",
            },
        },
        {
            "position": 8,
            "points_possible": 5,
            "entry": {
                "title": "File Upload Example",
                "item_body": "<p>Upload a screenshot of your work.</p>",
                "interaction_type_slug": "file-upload",
                "interaction_data": {"files_count": "1", "restrict_count": False},
                "properties": {
                    "allowed_types": ".png,.jpg,.pdf",
                    "restrict_types": False,
                },
                "scoring_data": {"value": ""},
                "scoring_algorithm": "None",
            },
        },
        {
            "position": 9,
            "points_possible": 2,
            "entry": {
                "title": "Formula Example",
                "item_body": "<p>Calculate 2 + x where x is shown.</p>",
                "interaction_type_slug": "formula",
                "interaction_data": {},
                "properties": {},
                "scoring_data": {
                    "value": {
                        "formula": "2 + x",
                        "numeric": {
                            "type": "marginOfError",
                            "margin": "0",
                            "margin_type": "absolute",
                        },
                        "variables": [
                            {"max": "10", "min": "1", "name": "x", "precision": 0}
                        ],
                        "answer_count": "3",
                        "generated_solutions": [
                            {"inputs": [{"name": "x", "value": "5"}], "output": "7"},
                            {"inputs": [{"name": "x", "value": "3"}], "output": "5"},
                            {"inputs": [{"name": "x", "value": "8"}], "output": "10"},
                        ],
                    }
                },
                "scoring_algorithm": "Numeric",
            },
        },
    ]
}
EXAMPLE_CLASSIC_QUIZ_JSON = {
    "questions": [
        {
            "question_name": "True/False Example",
            "question_text": "<p>Python is an interpreted programming language.</p>",
            "question_type": "true_false_question",
            "points_possible": 1,
            "answers": [
                {"answer_text": "True", "answer_weight": 100},
                {"answer_text": "False", "answer_weight": 0},
            ],
        },
        {
            "question_name": "Multiple Choice Example",
            "question_text": "<p>What is the capital of Sweden?</p>",
            "question_type": "multiple_choice_question",
            "points_possible": 2,
            "answers": [
                {"answer_text": "Stockholm", "answer_weight": 100},
                {"answer_text": "Gothenburg", "answer_weight": 0},
                {"answer_text": "Malmö", "answer_weight": 0},
                {"answer_text": "Uppsala", "answer_weight": 0},
            ],
        },
        {
            "question_name": "Multiple Answer Example",
            "question_text": "<p>Select all prime numbers:</p>",
            "question_type": "multiple_answers_question",
            "points_possible": 3,
            "answers": [
                {"answer_text": "2", "answer_weight": 100},
                {"answer_text": "3", "answer_weight": 100},
                {"answer_text": "4", "answer_weight": 0},
                {"answer_text": "5", "answer_weight": 100},
            ],
        },
        {
            "question_name": "Short Answer Example",
            "question_text": "<p>What is the capital of France?</p>",
            "question_type": "short_answer_question",
            "points_possible": 2,
            "answers": [
                {"answer_text": "Paris", "answer_weight": 100},
                {"answer_text": "paris", "answer_weight": 100},
            ],
        },
        {
            "question_name": "Fill in Multiple Blanks Example",
            "question_text": "<p>The chemical symbol for water is [blank1]. "
            "It consists of [blank2] hydrogen atoms.</p>",
            "question_type": "fill_in_multiple_blanks_question",
            "points_possible": 2,
            "answers": [
                {"answer_text": "H2O", "answer_weight": 100, "blank_id": "blank1"},
                {"answer_text": "h2o", "answer_weight": 100, "blank_id": "blank1"},
                {"answer_text": "2", "answer_weight": 100, "blank_id": "blank2"},
                {"answer_text": "two", "answer_weight": 100, "blank_id": "blank2"},
            ],
        },
        {
            "question_name": "Multiple Dropdowns Example",
            "question_text": "<p>Sweden is located in [region] and the official "
            "language is [lang].</p>",
            "question_type": "multiple_dropdowns_question",
            "points_possible": 2,
            "answers": [
                {"answer_text": "Europe", "answer_weight": 100, "blank_id": "region"},
                {"answer_text": "Asia", "answer_weight": 0, "blank_id": "region"},
                {"answer_text": "Africa", "answer_weight": 0, "blank_id": "region"},
                {"answer_text": "Swedish", "answer_weight": 100, "blank_id": "lang"},
                {"answer_text": "Finnish", "answer_weight": 0, "blank_id": "lang"},
                {"answer_text": "Norwegian", "answer_weight": 0, "blank_id": "lang"},
            ],
        },
        {
            "question_name": "Matching Example",
            "question_text": "<p>Match the Nordic countries with their capitals:</p>",
            "question_type": "matching_question",
            "points_possible": 3,
            "matching_answer_incorrect_matches": "Helsinki\nReykjavik",
            "answers": [
                {"answer_match_left": "Sweden", "answer_match_right": "Stockholm"},
                {"answer_match_left": "Norway", "answer_match_right": "Oslo"},
                {"answer_match_left": "Denmark", "answer_match_right": "Copenhagen"},
            ],
        },
        {
            "question_name": "Numerical Example",
            "question_text": "<p>What is 7 × 8?</p>",
            "question_type": "numerical_question",
            "points_possible": 1,
            "answers": [
                {
                    "numerical_answer_type": "exact_answer",
                    "exact": 56,
                    "margin": 0,
                    "answer_weight": 100,
                }
            ],
        },
        {
            "question_name": "Calculated/Formula Example",
            "question_text": "<p>If x = [x], what is 2x + 3?</p>",
            "question_type": "calculated_question",
            "points_possible": 2,
            "formulas": [{"formula": "2*x + 3"}],
            "variables": [{"name": "x", "min": 1, "max": 10, "scale": 0}],
            "formula_decimal_places": 0,
            "answer_tolerance": 0,
        },
        {
            "question_name": "Essay Example",
            "question_text": "<p>Explain the benefits of version control systems.</p>",
            "question_type": "essay_question",
            "points_possible": 5,
        },
        {
            "question_name": "File Upload Example",
            "question_text": "<p>Upload your completed assignment as a PDF file.</p>",
            "question_type": "file_upload_question",
            "points_possible": 10,
        },
        {
            "question_name": "Instructions (Text Only)",
            "question_text": "<p><strong>Section 2:</strong> Answer the following "
            "questions about programming concepts.</p>",
            "question_type": "text_only_question",
            "points_possible": 0,
        },
    ]
}
EXAMPLE_FULL_NEW_QUIZ_JSON = {
    "quiz_type": "new",
    "settings": {
        "title": "Example Practice Quiz",
        "instructions": "<p>This is a practice quiz to test your knowledge. "
        "You can retry multiple times with a 1-hour waiting period "
        "between attempts. Your latest score will be kept.</p>"
        "<p>You will see your score but not the correct answers, "
        "so you can keep practicing until you get them all right!</p>",
        "time_limit": 1800,
        "points_possible": 20,
        "due_at": None,
        "unlock_at": None,
        "lock_at": None,
        "quiz_settings": {
            # Randomization settings
            "shuffle_answers": True,
            "shuffle_questions": False,
            # Time limit settings
            "has_time_limit": True,
            "session_time_limit_in_seconds": 1800,
            # Question display settings
            "one_at_a_time_type": "none",
            "allow_backtracking": True,
            # Calculator settings
            "calculator_type": "none",
            # Access restrictions
            "filter_ip_address": False,
            "filters": {},
            "require_student_access_code": False,
            "student_access_code": None,
            # Multiple attempts settings
            "multiple_attempts": {
                "multiple_attempts_enabled": True,
                "attempt_limit": False,
                "max_attempts": None,
                "score_to_keep": "latest",
                "cooling_period": True,
                "cooling_period_seconds": 3600,
            },
            # Result view settings - what students see after submission
            "result_view_settings": {
                "result_view_restricted": True,
                "display_points_awarded": True,
                "display_points_possible": True,
                "display_items": True,
                "display_item_response": True,
                "display_item_response_qualifier": "always",
                "display_item_response_correctness": True,
                "display_item_correct_answer": False,
                "display_item_feedback": False,
                "display_correct_answer_at": None,
                "hide_correct_answer_at": None,
            },
        },
    },
    "items": [
        {
            "position": 1,
            "points_possible": 5,
            "entry": {
                "title": "Geography: Capital Cities",
                "item_body": "<p>What is the capital of Sweden?</p>",
                "interaction_type_slug": "choice",
                "scoring_algorithm": "Equivalence",
                "interaction_data": {
                    "choices": [
                        {"position": 1, "item_body": "<p>Stockholm</p>"},
                        {"position": 2, "item_body": "<p>Gothenburg</p>"},
                        {"position": 3, "item_body": "<p>Malmö</p>"},
                        {"position": 4, "item_body": "<p>Uppsala</p>"},
                    ]
                },
                "scoring_data": {"value": 1},
            },
        },
        {
            "position": 2,
            "points_possible": 5,
            "entry": {
                "title": "Programming: Language Type",
                "item_body": "<p>Python is an interpreted programming language.</p>",
                "interaction_type_slug": "true-false",
                "scoring_algorithm": "Equivalence",
                "interaction_data": {"true_choice": "True", "false_choice": "False"},
                "scoring_data": {"value": True},
            },
        },
        {
            "position": 3,
            "points_possible": 5,
            "entry": {
                "title": "Math: Select All Correct",
                "item_body": "<p>Which of the following are prime numbers?</p>",
                "interaction_type_slug": "multi-answer",
                "scoring_algorithm": "AllOrNothing",
                "interaction_data": {
                    "choices": [
                        {"position": 1, "item_body": "<p>2</p>"},
                        {"position": 2, "item_body": "<p>4</p>"},
                        {"position": 3, "item_body": "<p>7</p>"},
                        {"position": 4, "item_body": "<p>9</p>"},
                        {"position": 5, "item_body": "<p>11</p>"},
                    ]
                },
                "scoring_data": {"value": [1, 3, 5]},
            },
        },
        {
            "position": 4,
            "points_possible": 5,
            "entry": {
                "title": "Programming: Output Question",
                "item_body": "<p>What does the following Python code print?</p>"
                "<pre>x = 5\nif x > 3:\n    print('big')\nelse:\n    print('small')</pre>",
                "interaction_type_slug": "choice",
                "scoring_algorithm": "Equivalence",
                "interaction_data": {
                    "choices": [
                        {"position": 1, "item_body": "<p>big</p>"},
                        {"position": 2, "item_body": "<p>small</p>"},
                        {"position": 3, "item_body": "<p>5</p>"},
                        {"position": 4, "item_body": "<p>Nothing is printed</p>"},
                    ]
                },
                "scoring_data": {"value": 1},
            },
        },
    ],
}
EXAMPLE_FULL_CLASSIC_QUIZ_JSON = {
    "quiz_type": "classic",
    "settings": {
        "title": "Example Classic Quiz",
        "description": "<p>Answer all questions carefully. Time limit: 60 minutes.</p>",
        "quiz_type": "assignment",
        "time_limit": 60,
        "allowed_attempts": 2,
        "shuffle_questions": True,
        "shuffle_answers": True,
        "points_possible": 100,
        "published": False,
        "due_at": None,
        "unlock_at": None,
        "lock_at": None,
    },
    "questions": [
        {
            "question_name": "Capital Question",
            "question_text": "<p>What is the capital of Sweden?</p>",
            "question_type": "multiple_choice_question",
            "points_possible": 5,
            "answers": [
                {"answer_text": "Stockholm", "answer_weight": 100},
                {"answer_text": "Gothenburg", "answer_weight": 0},
                {"answer_text": "Malmö", "answer_weight": 0},
            ],
        },
        {
            "question_name": "True/False Question",
            "question_text": "<p>Python is an interpreted language.</p>",
            "question_type": "true_false_question",
            "points_possible": 5,
            "answers": [
                {"answer_text": "True", "answer_weight": 100},
                {"answer_text": "False", "answer_weight": 0},
            ],
        },
    ],
}
import logging
from datetime import datetime, timedelta

QUIZ_ITEMS_CACHE_TTL_MINUTES = 5

logger = logging.getLogger(__name__)


def list_command(config, canvas, args):
    """Lists all quizzes in a course"""
    # Get the course list
    course_list = courses.process_course_option(canvas, args)

    if not course_list:
        canvaslms.cli.err(1, "No course found matching criteria")

    # Use filter_quizzes to get all quizzes (filter_quizzes attaches course to each quiz)
    quiz_list = list(filter_quizzes(course_list, ".*"))

    if not quiz_list:
        canvaslms.cli.err(1, "No quizzes found in the specified course(s)")

    # Keep track of quiz IDs we've already listed to avoid duplicates
    listed_quiz_ids = set()

    # Output using csv module
    writer = csv.writer(sys.stdout, delimiter=args.delimiter)
    writer.writerow(["Course Code", "Quiz Title", "Quiz Type", "Published", "Due Date"])

    for quiz in quiz_list:
        if quiz.id in listed_quiz_ids:
            continue

        # Determine quiz type
        if hasattr(quiz, "quiz_type"):
            quiz_type = getattr(quiz, "quiz_type", "quiz")
        else:
            quiz_type = "new_quiz"

        published = "Published" if getattr(quiz, "published", False) else "Unpublished"
        due_date = canvaslms.cli.utils.format_local_time(getattr(quiz, "due_at", None))

        # Use the course attached by filter_quizzes()
        writer.writerow(
            [quiz.course.course_code, quiz.title, quiz_type, published, due_date]
        )
        listed_quiz_ids.add(quiz.id)


def fetch_all_quizzes(course):
    """Fetches all quizzes (Classic and New Quizzes) in a course"""
    quizzes = []

    try:
        classic_quizzes = course.get_quizzes()
        quizzes.extend(classic_quizzes)
    except Exception as e:
        canvaslms.cli.warn(
            f"Could not fetch Classic Quizzes for " f"course {course.course_code}: {e}"
        )

    try:
        new_quizzes = course.get_new_quizzes()
        quizzes.extend(new_quizzes)
    except Exception as e:
        canvaslms.cli.warn(
            f"Could not fetch New Quizzes for " f"course {course.course_code}: {e}"
        )

    return quizzes


def filter_quizzes(course_list, regex):
    """Returns all quizzes from courses whose title or ID matches regex

    Searches both Classic Quizzes and New Quizzes. Yields Quiz objects
    with an attached course attribute for later reference.

    Args:
      course_list: List of Course objects to search
      regex: Regular expression string to match against quiz title or ID

    Yields:
      Quiz objects (both classic and new quizzes) that match the pattern
    """
    pattern = re.compile(regex, re.IGNORECASE)

    for course in course_list:
        quizzes = fetch_all_quizzes(course)
        for quiz in quizzes:
            # Match against quiz title or Canvas ID
            if pattern.search(quiz.title) or pattern.search(str(quiz.id)):
                # Attach course reference for later use (e.g., downloading reports)
                quiz.course = course
                yield quiz


def add_quiz_option(parser, required=False, suppress_help=False):
    """Adds quiz selection option to argparse parser

    Args:
      parser: The argparse parser to add options to
      required: Whether the quiz option should be required
      suppress_help: If True, hide this option from help output
    """
    # Add course option dependency (may already exist)
    try:
        courses.add_course_option(
            parser, required=required, suppress_help=suppress_help
        )
    except argparse.ArgumentError:
        # Option already added by another module
        pass

    # Use -a/--assignment for backward compatibility
    parser.add_argument(
        "-a",
        "--assignment",
        required=required,
        default=".*" if not required else None,
        help=(
            argparse.SUPPRESS
            if suppress_help
            else "Regex matching quiz title or Canvas ID, default: '.*'"
        ),
    )


def process_quiz_option(canvas, args):
    """Processes quiz option, returns a list of matching quizzes

    Args:
      canvas: Canvas API instance
      args: Parsed command-line arguments

    Returns:
      List of Quiz objects matching the criteria

    Raises:
      canvaslms.cli.EmptyListError: If no quizzes match the criteria
    """
    # First get the course list
    course_list = courses.process_course_option(canvas, args)

    # Get quiz regex pattern (from -a/--assignment argument)
    quiz_regex = getattr(args, "assignment", ".*")

    # Filter quizzes using our helper
    quiz_list = list(filter_quizzes(course_list, quiz_regex))

    if not quiz_list:
        raise canvaslms.cli.EmptyListError("No quizzes found matching the criteria")

    return quiz_list


def analyse_command(config, canvas, args):
    """Analyzes quiz or survey data from CSV file or Canvas"""
    csv_files = []
    if args.csv:
        csv_files.append(args.csv)
    else:
        try:
            # Use the unified quiz selection pattern
            quiz_list = process_quiz_option(canvas, args)

            # Download report for each matching quiz
            for quiz in quiz_list:
                import tempfile
                import requests

                # Fetch the report based on quiz type
                file_url = None

                if is_new_quiz(quiz):
                    # New Quiz - use New Quiz Reports API
                    try:
                        progress = create_new_quiz_report(
                            quiz.course, quiz.id, canvas._Canvas__requester
                        )
                        progress = poll_progress(progress)

                        if progress and hasattr(progress, "results"):
                            if isinstance(progress.results, dict):
                                file_url = progress.results.get("url")
                    except Exception as e:
                        canvaslms.cli.warn(
                            f"Error creating New Quiz report for '{quiz.title}': {e}"
                        )
                        continue
                else:
                    # Classic Quiz - use create_report()
                    try:
                        report = quiz.create_report(
                            report_type="student_analysis", includes_all_versions=True
                        )

                        # Poll until ready
                        for attempt in range(30):
                            report = quiz.get_quiz_report(report.id)
                            final_report = poll_progress(report, max_attempts=1)
                            if final_report:
                                report = final_report
                                break

                        # Extract file URL
                        if hasattr(report, "file"):
                            if hasattr(report.file, "url"):
                                file_url = report.file.url
                            elif isinstance(report.file, dict):
                                file_url = report.file.get("url")
                    except Exception as e:
                        canvaslms.cli.warn(
                            f"Error creating Classic Quiz report for '{quiz.title}': {e}"
                        )
                        continue

                if not file_url:
                    canvaslms.cli.warn(
                        f"Report file URL not available for quiz '{quiz.title}'"
                    )
                    continue

                # Download CSV to temporary file
                try:
                    response = requests.get(file_url)
                    response.raise_for_status()

                    # Create temp file and write CSV data
                    temp_fd, temp_path = tempfile.mkstemp(suffix=".csv", text=True)
                    with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                        f.write(response.content.decode("utf-8"))

                    csv_files.append(temp_path)
                except Exception as e:
                    canvaslms.cli.warn(
                        f"Error downloading report for quiz '{quiz.title}': {e}"
                    )
                    continue

        except canvaslms.cli.EmptyListError as e:
            canvaslms.cli.err(1, str(e))
        except Exception as e:
            canvaslms.cli.err(1, f"Error fetching from Canvas: {e}")

    for csv_file in csv_files:
        try:
            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    canvaslms.cli.err(1, "CSV file is empty")

                # Initialize output buffer
                output_buffer = []

                # Get all column names
                columns = list(rows[0].keys())

                # Identify question columns (they contain question IDs like "588913:")
                # Or they contain spaces.
                question_columns = []
                for col in columns:
                    if re.match(r"^\d+: ", col) or " " in col:
                        question_columns.append(col)

                if not question_columns:
                    canvaslms.cli.err(1, "No question columns found in CSV")

                # Categorize questions
                quantitative_questions = []
                qualitative_questions = []

                for qcol in question_columns:
                    # Check if the column contains mostly numeric/categorical responses
                    sample_responses = [row[qcol] for row in rows if row[qcol]]

                    if is_quantitative(sample_responses):
                        quantitative_questions.append(qcol)
                    else:
                        qualitative_questions.append(qcol)

                if quantitative_questions:
                    if args.format == "markdown":
                        output_buffer.append("\n# Quantitative Summary\n")
                    else:  # latex
                        output_buffer.append("\\section{Quantitative Summary}\n\n")

                    for qcol in quantitative_questions:
                        question_id, full_title = extract_question_id(qcol)
                        full_title, has_pre_tag = process_html_formatting(full_title)
                        has_code, formatted_full_question = detect_and_format_code(
                            full_title,
                            format_type=args.format,
                            has_pre_tag=has_pre_tag,
                            minted_lang=args.use_minted,
                        )
                        title_cleaned = clean_newlines(full_title)
                        short_title = create_short_title(title_cleaned)
                        if args.format == "markdown":
                            output_buffer.append(f"\n## {short_title}\n\n")
                            if short_title != title_cleaned or has_code:
                                output_buffer.append(
                                    f"**Full question:** {formatted_full_question}\n\n"
                                )
                        else:
                            short_title_escaped = escape_latex_complete(short_title)

                            if question_id:
                                label = f"q{question_id}"
                            else:
                                label = f"q{abs(hash(qcol)) % 100000}"

                            output_buffer.append(
                                f"\\subsection{{{short_title_escaped}}}\\label{{{label}}}\n\n"
                            )

                            if short_title != title_cleaned or has_code:
                                if not has_code:
                                    formatted_full_question = escape_latex_complete(
                                        formatted_full_question
                                    )
                                output_buffer.append(
                                    f"\\textit{{Full question:}} {formatted_full_question}\n\n"
                                )

                        raw_responses = [
                            row[qcol] for row in rows if row[qcol] and row[qcol].strip()
                        ]
                        # Process HTML entities and tags in responses before analysis
                        responses = [
                            process_html_formatting(resp)[0] for resp in raw_responses
                        ]

                        if not responses:
                            if args.format == "markdown":
                                output_buffer.append("*No responses*\n")
                            else:  # latex
                                output_buffer.append("\\textit{No responses}\n\n")
                            continue

                        has_commas = (
                            sum(1 for r in responses if "," in r) > len(responses) * 0.3
                        )
                        if has_commas:
                            all_options = extract_comma_separated_options(responses)
                            freq = Counter(all_options)

                            if args.format == "markdown":
                                output_buffer.append(
                                    f"**Total responses:** {len(responses)}  \n"
                                )
                                output_buffer.append(
                                    f"**Total selections:** {len(all_options)}  \n"
                                )
                                output_buffer.append("\n**Option distribution:**\n\n")
                                for value, count in freq.most_common():
                                    percentage = (count / len(responses)) * 100
                                    value_display = value.replace("\n", " ")
                                    output_buffer.append(
                                        f"- {value_display}: {count} ({percentage:.1f}%)\n"
                                    )
                            else:  # latex
                                output_buffer.append(
                                    f"Total responses: {len(responses)}\\\\\n"
                                )
                                output_buffer.append(
                                    f"Total selections: {len(all_options)}\\\\\n\n"
                                )
                                output_buffer.append(
                                    "\\textbf{Option distribution:}\n\\begin{itemize}\n"
                                )
                                for value, count in freq.most_common():
                                    percentage = (count / len(responses)) * 100
                                    value_escaped = escape_latex_complete(value)
                                    output_buffer.append(
                                        f"  \\item {value_escaped}: {count} ({percentage:.1f}\\%)\n"
                                    )
                                output_buffer.append("\\end{itemize}\n\n")
                        else:
                            numeric_values = []
                            for resp in responses:
                                try:
                                    numeric_values.append(float(resp))
                                except (ValueError, TypeError):
                                    pass

                            if (
                                numeric_values
                                and len(numeric_values) >= len(responses) * 0.5
                            ):
                                unique_values = set(numeric_values)

                                if len(unique_values) <= 10:
                                    freq = Counter(numeric_values)
                                    if args.format == "markdown":
                                        output_buffer.append(
                                            f"**Total responses:** {len(numeric_values)}  \n"
                                        )
                                        output_buffer.append(
                                            "\n**Value distribution:**\n\n"
                                        )
                                        for value, count in sorted(freq.items()):
                                            percentage = (
                                                count / len(numeric_values)
                                            ) * 100
                                            output_buffer.append(
                                                f"- {value}: {count} ({percentage:.1f}%)\n"
                                            )
                                    else:  # latex
                                        output_buffer.append(
                                            f"Total responses: {len(numeric_values)}\\\\\n\n"
                                        )
                                        output_buffer.append(
                                            "\\textbf{Value distribution:}\n\\begin{itemize}\n"
                                        )
                                        for value, count in sorted(freq.items()):
                                            percentage = (
                                                count / len(numeric_values)
                                            ) * 100
                                            output_buffer.append(
                                                f"  \\item {value}: {count} ({percentage:.1f}\\%)\n"
                                            )
                                        output_buffer.append("\\end{itemize}\n\n")
                                else:
                                    if args.format == "markdown":
                                        output_buffer.append(
                                            f"**Total responses:** {len(numeric_values)}  \n"
                                        )
                                        output_buffer.append(
                                            f"**Mean:** {statistics.mean(numeric_values):.2f}  \n"
                                        )
                                        output_buffer.append(
                                            f"**Median:** {statistics.median(numeric_values):.2f}  \n"
                                        )
                                        if len(numeric_values) > 1:
                                            output_buffer.append(
                                                f"**Std Dev:** {statistics.stdev(numeric_values):.2f}  \n"
                                            )
                                        output_buffer.append(
                                            f"**Min:** {min(numeric_values):.2f}  \n"
                                        )
                                        output_buffer.append(
                                            f"**Max:** {max(numeric_values):.2f}  \n"
                                        )
                                    else:  # latex
                                        output_buffer.append(
                                            f"Total responses: {len(numeric_values)}\\\\\n"
                                        )
                                        output_buffer.append(
                                            f"Mean: {statistics.mean(numeric_values):.2f}\\\\\n"
                                        )
                                        output_buffer.append(
                                            f"Median: {statistics.median(numeric_values):.2f}\\\\\n"
                                        )
                                        if len(numeric_values) > 1:
                                            output_buffer.append(
                                                f"Standard deviation: {statistics.stdev(numeric_values):.2f}\\\\\n"
                                            )
                                        output_buffer.append(
                                            f"Min: {min(numeric_values):.2f}\\\\\n"
                                        )
                                        output_buffer.append(
                                            f"Max: {max(numeric_values):.2f}\\\\\n\n"
                                        )
                            else:
                                freq = Counter(responses)
                                if args.format == "markdown":
                                    output_buffer.append(
                                        f"**Total responses:** {len(responses)}  \n"
                                    )
                                    output_buffer.append(
                                        "\n**Response distribution:**\n\n"
                                    )
                                    for value, count in freq.most_common():
                                        percentage = (count / len(responses)) * 100
                                        value_display = value.replace("\n", " ")
                                        output_buffer.append(
                                            f"- {value_display}: {count} ({percentage:.1f}%)\n"
                                        )
                                else:  # latex
                                    output_buffer.append(
                                        f"Total responses: {len(responses)}\\\\\n\n"
                                    )
                                    output_buffer.append(
                                        "\\textbf{Response distribution:}\n\\begin{itemize}\n"
                                    )
                                    for value, count in freq.most_common():
                                        percentage = (count / len(responses)) * 100
                                        value_escaped = escape_latex_complete(
                                            value.replace("\n", " ")
                                        )
                                        output_buffer.append(
                                            f"  \\item {value_escaped}: {count} ({percentage:.1f}\\%)\n"
                                        )
                                    output_buffer.append("\\end{itemize}\n\n")
                if qualitative_questions:
                    if args.format == "markdown":
                        output_buffer.append("\n# Qualitative Summary\n")
                    else:  # latex
                        output_buffer.append("\\section{Qualitative Summary}\n\n")

                    for qcol in qualitative_questions:
                        question_id, full_title = extract_question_id(qcol)
                        full_title, has_pre_tag = process_html_formatting(full_title)
                        has_code, formatted_full_question = detect_and_format_code(
                            full_title,
                            format_type=args.format,
                            has_pre_tag=has_pre_tag,
                            minted_lang=args.use_minted,
                        )
                        title_cleaned = clean_newlines(full_title)
                        short_title = create_short_title(title_cleaned)
                        if args.format == "markdown":
                            output_buffer.append(f"\n## {short_title}\n\n")
                            if short_title != title_cleaned or has_code:
                                output_buffer.append(
                                    f"**Full question:** {formatted_full_question}\n\n"
                                )
                        else:
                            short_title_escaped = escape_latex_complete(short_title)

                            if question_id:
                                label = f"q{question_id}"
                            else:
                                label = f"q{abs(hash(qcol)) % 100000}"

                            output_buffer.append(
                                f"\\subsection{{{short_title_escaped}}}\\label{{{label}}}\n\n"
                            )

                            if short_title != title_cleaned or has_code:
                                if not has_code:
                                    formatted_full_question = escape_latex_complete(
                                        formatted_full_question
                                    )
                                output_buffer.append(
                                    f"\\textit{{Full question:}} {formatted_full_question}\n\n"
                                )

                        raw_responses = [
                            row[qcol] for row in rows if row[qcol] and row[qcol].strip()
                        ]
                        # Process HTML entities and tags in responses before analysis
                        responses = [
                            process_html_formatting(resp)[0] for resp in raw_responses
                        ]

                        if not responses:
                            if args.format == "markdown":
                                output_buffer.append("*No responses*\n")
                            else:  # latex
                                output_buffer.append("\\textit{No responses}\n\n")
                            continue

                        if args.format == "markdown":
                            output_buffer.append(
                                f"\n**Individual Responses ({len(responses)} total):**\n\n"
                            )
                            for i, resp in enumerate(responses, 1):
                                output_buffer.append(f"{i}. {resp}\n\n")
                        else:  # latex
                            output_buffer.append(
                                f"\\textbf{{Individual Responses ({len(responses)} total):}}\n\n"
                            )
                            output_buffer.append("\\begin{enumerate}\n")
                            for i, resp in enumerate(responses, 1):
                                resp_escaped = escape_latex_complete(
                                    resp.replace("\n", " ")
                                )
                                output_buffer.append(f"  \\item {resp_escaped}\n")
                            output_buffer.append("\\end{enumerate}\n\n")

                        if args.ai:
                            if args.format == "markdown":
                                output_buffer.append("\n**AI-Generated Summary:**\n\n")
                            else:  # latex
                                output_buffer.append(
                                    "\\textbf{AI-Generated Summary:}\n\n"
                                )

                            try:
                                import llm

                                # Prepare the prompt based on output format
                                if args.format == "latex":
                                    prompt = f"""Please analyze the following survey responses and provide a concise summary of the main themes, concerns, and suggestions mentioned by respondents.

            Format your response in LaTeX. Use LaTeX formatting such as \\textbf{{}} for bold, \\textit{{}} for italics, and \\begin{{itemize}} for lists. Do not include section headers (like \\section or \\subsection).

            Question: {qcol}

            Responses:
            """
                                else:  # markdown
                                    prompt = f"""Please analyze the following survey responses and provide a concise summary of the main themes, concerns, and suggestions mentioned by respondents.

            Format your response in markdown. Use markdown formatting such as **bold**, *italics*, and bullet points.

            Question: {qcol}

            Responses:
            """

                                for i, resp in enumerate(responses, 1):
                                    prompt += f"\n{i}. {resp}"

                                prompt += "\n\nProvide a summary highlighting:\n1. Main themes\n2. Common concerns or issues\n3. Suggestions for improvement\n4. Overall sentiment"

                                # Get default model and generate summary
                                model = llm.get_model()
                                response = model.prompt(prompt)
                                summary_text = response.text()

                                if args.format == "markdown":
                                    output_buffer.append(f"{summary_text}\n\n")
                                else:  # latex
                                    # For LaTeX format, the AI already generated LaTeX, so don't escape
                                    output_buffer.append(f"{summary_text}\n\n")

                            except ImportError:
                                error_msg = "The 'llm' package is not installed. Install it with: pip install llm"
                                if args.format == "markdown":
                                    output_buffer.append(f"*{error_msg}*\n\n")
                                else:  # latex
                                    output_buffer.append(f"\\textit{{{error_msg}}}\n\n")
                            except Exception as e:
                                error_msg = f"Error generating AI summary: {e}\nMake sure llm is configured with: llm keys set <provider>"
                                if args.format == "markdown":
                                    output_buffer.append(f"*{error_msg}*\n\n")
                                else:  # latex
                                    output_buffer.append(f"\\textit{{{error_msg}}}\n\n")
                # Join the output buffer
                output_text = "".join(output_buffer)

                # Add LaTeX preamble/postamble if standalone mode
                if args.format == "latex" and args.standalone:
                    output_text = (
                        generate_latex_preamble(args.use_minted)
                        + output_text
                        + generate_latex_postamble()
                    )

                if args.format == "markdown":
                    # Use rich to render markdown
                    console = Console()
                    md = Markdown(output_text)

                    if sys.stdout.isatty():
                        # Output to terminal with pager
                        pager = ""
                        if "MANPAGER" in os.environ:
                            pager = os.environ["MANPAGER"]
                        elif "PAGER" in os.environ:
                            pager = os.environ["PAGER"]

                        styles = False
                        if "less" in pager and ("-R" in pager or "-r" in pager):
                            styles = True

                        with console.pager(styles=styles):
                            console.print(md)
                    else:
                        # Piped to file, output plain markdown
                        print(output_text)
                else:  # latex
                    # Output raw LaTeX (no pager, always goes to file)
                    print(output_text)
        except FileNotFoundError:
            canvaslms.cli.err(1, f"CSV file not found: {csv_file}")
        except Exception as e:
            canvaslms.cli.err(1, f"Error processing CSV: {e}")


def is_new_quiz(quiz):
    """Determine if a quiz object is a New Quiz (Quizzes.Next)"""
    # Check if it's a NewQuiz object (from get_new_quizzes())
    # vs a Quiz object (from get_quizzes())
    return quiz.__class__.__name__ == "NewQuiz"


def poll_progress(progress_obj, max_attempts=30, sleep_interval=2):
    """
    Poll a progress object until it completes.

    Args:
      progress_obj: A Progress object or report object with progress attribute
      max_attempts: Maximum number of polling attempts
      sleep_interval: Seconds to wait between polls

    Returns:
      The final progress/report object, or None if max attempts reached
    """
    import time

    for attempt in range(max_attempts):
        # Check different ways the progress might indicate completion
        is_completed = False

        if hasattr(progress_obj, "query"):
            # It's a Progress object - refresh it
            progress_obj.query()
            if hasattr(progress_obj, "workflow_state"):
                is_completed = progress_obj.workflow_state == "completed"

        # For quiz reports with embedded progress
        if hasattr(progress_obj, "progress"):
            if hasattr(progress_obj.progress, "workflow_state"):
                is_completed = progress_obj.progress.workflow_state == "completed"
            elif isinstance(progress_obj.progress, dict):
                is_completed = (
                    progress_obj.progress.get("workflow_state") == "completed"
                )
        elif hasattr(progress_obj, "workflow_state"):
            is_completed = progress_obj.workflow_state == "completed"

        if is_completed:
            return progress_obj

        if attempt < max_attempts - 1:
            time.sleep(sleep_interval)
            sleep_interval *= 1.2  # Exponential backoff

    return None


def download_csv_report(file_url):
    """
    Download a CSV report from Canvas and return a CSV reader.

    Args:
      file_url: URL to the CSV file

    Returns:
      csv.DictReader object with the CSV data
    """
    import requests
    import io

    response = requests.get(file_url)
    response.raise_for_status()

    # Explicitly decode as UTF-8 to handle international characters
    csv_data = response.content.decode("utf-8")
    return csv.DictReader(io.StringIO(csv_data))


def create_new_quiz_report(course, assignment_id, requester):
    """
    Create a student analysis report for a New Quiz.

    Args:
      course: Course object
      assignment_id: The assignment ID of the New Quiz
      requester: Canvas _requester object for making API calls

    Returns:
      Progress object for polling
    """
    import canvasapi.progress

    # Build the API endpoint
    endpoint = f"courses/{course.id}/quizzes/{assignment_id}/reports"

    # Make the POST request with form parameters
    # Note: New Quiz API expects form-encoded parameters
    try:
        response = requester.request(
            method="POST",
            endpoint=endpoint,
            _url="new_quizzes",
            **{
                "quiz_report[report_type]": "student_analysis",
                "quiz_report[format]": "csv",
            },
        )
    except Exception as e:
        canvaslms.cli.err(1, f"Error creating New Quiz report: {e}")

    # The response is a Progress object
    return canvasapi.progress.Progress(requester, response.json()["progress"])


def extract_comma_separated_options(responses: List[str]) -> List[str]:
    """Extract options from comma-separated responses using longest matches"""
    from typing import List, Tuple

    segmented: List[List[str]] = []
    for resp in responses:
        text = (resp or "").strip()
        if not text:
            segmented.append([])
            continue
        parts = [part.strip() for part in text.split(",")]
        segmented.append(parts)
    PhraseSpan = Tuple[int, int, int]
    candidate_counts: Counter[str] = Counter()
    candidate_occurrences: Dict[str, List[PhraseSpan]] = defaultdict(list)

    for resp_index, parts in enumerate(segmented):
        n = len(parts)
        for start in range(n):
            phrase = ""
            for end in range(start, n):
                if phrase:
                    phrase = f"{phrase}, {parts[end]}"
                else:
                    phrase = parts[end]
                if phrase:
                    candidate_counts[phrase] += 1
                    candidate_occurrences[phrase].append((resp_index, start, end))
    repeated_phrases = {
        phrase for phrase, count in candidate_counts.items() if count >= 2 and phrase
    }
    all_options: List[str] = []

    for resp_index, parts in enumerate(segmented):
        n = len(parts)
        if n == 0:
            continue

        occurrences: List[Tuple[str, int, int, int, int]] = []
        for phrase in repeated_phrases:
            for span_resp_index, start, end in candidate_occurrences[phrase]:
                if span_resp_index == resp_index:
                    count = candidate_counts[phrase]
                    span_len = end - start + 1
                    occurrences.append((phrase, start, end, count, span_len))

        occurrences.sort(key=lambda item: (-item[3], -item[4], -len(item[0])))
        used = [False] * n
        selected_spans: List[Tuple[int, int, str]] = []

        for phrase, start, end, _count, _span_len in occurrences:
            if any(used[index] for index in range(start, end + 1)):
                continue
            for index in range(start, end + 1):
                used[index] = True
            selected_spans.append((start, end, phrase))

        selected_spans.sort(key=lambda span: span[0])
        current_index = 0
        for start, end, phrase in selected_spans:
            if current_index < start:
                fallback = ", ".join(parts[current_index:start]).strip()
                if fallback:
                    all_options.append(fallback)
            all_options.append(phrase)
            current_index = end + 1

        if current_index < n:
            fallback = ", ".join(parts[current_index:]).strip()
            if fallback:
                all_options.append(fallback)

    return all_options


def is_quantitative(responses: List[str]) -> bool:
    """Determine if responses are quantitative or qualitative"""
    if not responses:
        return False

    comma_count = sum(1 for r in responses if "," in r)
    if comma_count > len(responses) * 0.3:
        all_options = extract_comma_separated_options(responses)
        unique_options = set(all_options)
        if len(unique_options) <= 20 and len(all_options) > len(unique_options):
            return True
    unique_responses = set(responses)
    response_counts = Counter(responses)
    responses_with_one_occurrence = sum(
        1 for count in response_counts.values() if count == 1
    )

    if (
        len(unique_responses) >= 5
        and responses_with_one_occurrence >= len(unique_responses) * 0.9
    ):
        has_overlap = False
        unique_list = list(unique_responses)
        for i, resp1 in enumerate(unique_list):
            for resp2 in unique_list[i + 1 :]:
                if len(resp1) > 10 and len(resp2) > 10:
                    shorter = resp1 if len(resp1) < len(resp2) else resp2
                    longer = resp2 if len(resp1) < len(resp2) else resp1
                    if shorter.lower() in longer.lower():
                        has_overlap = True
                        break
            if has_overlap:
                break
        if not has_overlap:
            return False
    if len(unique_responses) <= 10 and len(responses) > 3:
        return True
    numeric_count = 0
    for resp in responses:
        try:
            float(resp)
            numeric_count += 1
        except (ValueError, TypeError):
            pass

    if numeric_count > len(responses) * 0.5:
        return True
    avg_length = sum(len(str(r)) for r in responses) / len(responses)
    if avg_length < 30:
        return True

    return False


def extract_question_id(qcol):
    """
    Extract question ID and clean title from a question column name.

    Args:
      qcol: Question column name (e.g., "588913: How are you?" or "How are you?")

    Returns:
      Tuple of (question_id, title_without_id)
      - question_id: String ID or None for New Quizzes
      - title_without_id: Question text with ID prefix removed
    """
    import re

    # Check for Classic Quiz format: "588913: Question text"
    match = re.match(r"^(\d+):\s*(.+)$", qcol, re.DOTALL)
    if match:
        return match.group(1), match.group(2).strip()
    else:
        # New Quiz - no ID prefix
        return None, qcol.strip()


def create_short_title(title, max_length=80):
    """
    Create a short title by truncating at sentence boundary or max length.

    When code is detected in the title, stops at the last sentence boundary
    before the code begins.

    Args:
      title: Full question title (with newlines removed)
      max_length: Maximum characters before forced truncation

    Returns:
      Short title with ellipsis if truncated
    """
    import re

    # If already short enough, return as-is
    if len(title) <= max_length:
        return title

    # Detect code keywords that might appear in questions
    code_keywords = [
        r"\bdef\s+",  # Python function definition
        r"\bclass\s+",  # Python class definition
        r"\bimport\s+",  # Import statement
        r"\bfrom\s+",  # From import
        r"\bfor\s+\w+\s+in\s+",  # For loop
        r"\bif\s+\w+\s*[<>=!]",  # If statement with comparison
        r"\bwhile\s+",  # While loop
        r"\breturn\s+",  # Return statement
        r"\bprint\s*\(",  # Print function
    ]

    # Find the earliest position where code might start
    code_start_pos = None
    for pattern in code_keywords:
        match = re.search(pattern, title)
        if match:
            if code_start_pos is None or match.start() < code_start_pos:
                code_start_pos = match.start()

    # Determine the search boundary for sentence breaks
    if code_start_pos is not None:
        # Code detected - search for sentence boundary before code
        search_boundary = min(code_start_pos, max_length)
    else:
        # No code detected - use max_length
        search_boundary = max_length

    # Find sentence boundaries (. ? ! : ;) followed by space or end
    sentence_pattern = r"[.?!:;](?:\s|$)"
    matches = list(re.finditer(sentence_pattern, title[:search_boundary]))

    if matches:
        # Use the last sentence boundary found
        last_match = matches[-1]
        short_title = title[: last_match.end()].rstrip()

        # Add ellipsis if there's more content after
        if len(title) > last_match.end():
            short_title += "..."

        return short_title

    # No sentence boundary found before code - truncate at word boundary
    truncated = title[:search_boundary]
    last_space = truncated.rfind(" ")
    if last_space > search_boundary * 0.5:  # At least halfway through
        return truncated[:last_space] + "..."

    # Forced truncation at search_boundary
    return truncated + "..."


def process_html_formatting(text):
    """
    Convert Canvas CSV HTML formatting to plain text with newlines.

    Canvas CSV exports contain HTML that needs conversion:
    - <br> or <br/> tags → newlines
    - <pre>...</pre> → extract content, mark as code
    - HTML entities (&lt;, &gt;, &amp;, &nbsp;, etc.) → decoded characters
    - Other tags (<code>, <p>, <span>) → stripped (content kept)
    - Legacy literal \\n strings → newlines (backwards compatibility)

    Args:
      text: Text from Canvas CSV with potential HTML formatting

    Returns:
      Tuple of (plain_text, has_pre_tag)
      - plain_text: Text with HTML converted to plain text with newlines
      - has_pre_tag: True if <pre> tag was found (strong code signal)
    """
    import html
    import re

    # Detect <pre> tags (strong signal this is code/preformatted)
    has_pre_tag = bool(re.search(r"<pre\b", text, flags=re.IGNORECASE))

    # 1. Convert <br> tags to newlines (handles <br>, <br/>, <br />)
    text = re.sub(r"<br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)

    # 2. Extract <pre> content, remove tags
    text = re.sub(
        r"<pre\b[^>]*>(.*?)</pre>", r"\1", text, flags=re.IGNORECASE | re.DOTALL
    )

    # 3. Convert <p> and <div> to newlines (block elements)
    text = re.sub(r"</?p\b[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?div\b[^>]*>", "\n", text, flags=re.IGNORECASE)

    # 4. Strip inline tags (keep content): <code>, <span>, <strong>, etc.
    text = re.sub(r"</?code\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?span\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?strong\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?em\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?b\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?i\b[^>]*>", "", text, flags=re.IGNORECASE)

    # 5. Unescape HTML entities (&lt; → <, &gt; → >, &amp; → &, etc.)
    # Python's html.unescape handles all standard named and numeric entities
    text = html.unescape(text)

    # 6. Normalize whitespace and newline encodings
    # Convert non-breaking spaces to regular spaces and normalize CRLF/CR newlines
    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 7. Handle legacy literal \n strings (backwards compatibility)
    # Some older Canvas exports might still use this format
    text = text.replace("\\n", "\n")

    # 7. Convert multiple consecutive spaces to newline + spaces (indentation)
    # When code lacks proper <pre> tags, multiple spaces often indicate indentation.
    # Insert newline BEFORE the spaces so they become indentation of the next line.
    # Example: "def FIXA():  a = int(...)" → "def FIXA():\n  a = int(...)"
    text = re.sub(r"  +", r"\n\g<0>", text)

    # 8. Normalize excessive newlines (max 2 consecutive)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip(), has_pre_tag


def clean_newlines(text):
    """
    Replace newlines with spaces and normalize whitespace.

    Args:
      text: Text potentially containing \n characters

    Returns:
      Text with newlines replaced by spaces, multiple spaces collapsed
    """
    import re

    # Replace newlines and carriage returns with spaces
    cleaned = text.replace("\n", " ").replace("\r", " ")

    # Normalize multiple spaces to single space
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.strip()


def detect_and_format_code(
    text, format_type="markdown", has_pre_tag=False, minted_lang=False
):
    """
    Detect code snippets in text and format them appropriately.

    Args:
      text: Full question text that may contain code
      format_type: "markdown" or "latex"
      has_pre_tag: True if Canvas marked this with <pre> tag
      minted_lang: Language for minted syntax highlighting (e.g., "python").
                   If False, uses verbatim instead of minted.

    Returns:
      Tuple of (has_code, formatted_text)
    """
    import re

    code_patterns = [
        # High-confidence: strong indicators of code
        r"\bdef\s+\w+\s*\(",  # Python function definition
        r"\bclass\s+\w+",  # Python class definition
        r"\bimport\s+\w+",  # Import statement
        r"\breturn\s+",  # Return statement
        r"\bfor\s+\w+\s+in\s+",  # For loop
        r"\bwhile\s+\w+",  # While loop
        r"\btry\s*:",  # Try block
        r"\bexcept\s+(\w+)?:?",  # Exception handling
        r"\belif\s+",  # Elif statement
        r"\belse\s*:",  # Else block
        r":\s*\n\s{2,}\w+",  # Colon followed by indented line
        r"\w+\s*=\s*(int|float|str|input|len|range)\s*\(",  # Assignment with builtin
        # Medium-confidence: suggestive patterns
        r"\bif\s+\w+",  # If statement
        r"[a-zA-Z_]\w*\s*\([^)]*\)\s*:",  # Function call with colon
        r"\n\s{2,}\w+.*\n\s{2,}\w+",  # Multiple indented lines
        r'(print|input)\s*\(["\'].*?["\'].*?\)',  # Print/input with strings
        # Lower-confidence: need other signals
        r"\n\s{2,}\w+",  # Indented lines
        r"[a-zA-Z_]\w*\s*=\s*",  # Variable assignment
        r"[<>=!]{1,2}\s*\d+",  # Comparison operators
        r"\w+\s*[+\-*/]=?\s*\w+",  # Arithmetic operators
    ]
    force_has_code = False
    if has_pre_tag:
        has_code_patterns = any(
            re.search(pattern, text, re.MULTILINE) for pattern in code_patterns
        )
        if has_code_patterns:
            force_has_code = True

    has_code = force_has_code or any(
        re.search(pattern, text) for pattern in code_patterns
    )

    if not has_code:
        return False, text

    lines = text.split("\n")
    code_lines = []
    text_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        should_start_code = (
            re.match(r"^(def|class|import|from|try|while|for)\s+", stripped)
            or re.match(r"^(if|elif|else)\s+", stripped)
            or (len(line) - len(line.lstrip()) >= 2 and stripped)
            or re.match(r"^\w+\s*=\s*(int|float|str|input|len|range)\s*\(", stripped)
            or re.match(r"^(print|input)\s*\(", stripped)
        )

        if should_start_code:
            in_code_block = True
            code_lines.append(line)
        elif in_code_block and stripped:
            code_lines.append(line)
        elif in_code_block and not stripped:
            code_lines.append(line)
        else:
            in_code_block = False
            if code_lines and not code_lines[-1].strip():
                code_lines.pop()
            text_lines.append(line)

    if not code_lines:
        return False, text

    result_parts = []
    if text_lines:
        result_parts.append("\n".join(text_lines).strip())

    code_text = "\n".join(code_lines)

    control_keywords = r"(elif|else|except|finally)"
    code_text = re.sub(
        rf"(\S)([ \t]+)({control_keywords}\\b)",
        r"\1\n\3",
        code_text,
    )
    if format_type == "markdown":
        result_parts.append(f"\n```python\n{code_text}\n```\n")
    else:
        is_multiline = "\n" in code_text
        if is_multiline:
            if minted_lang:
                result_parts.append(
                    f"\n\\begin{{minted}}{{{minted_lang}}}\n{code_text}\n\\end{{minted}}\n"
                )
            else:
                result_parts.append(
                    f"\n\\begin{{verbatim}}\n{code_text}\n\\end{{verbatim}}\n"
                )
        else:
            if minted_lang:
                result_parts.append(f"\\mintinline{{{minted_lang}}}{{{code_text}}}")
            else:
                result_parts.append(f"\\verb|{code_text}|")

    return True, "\n".join(result_parts)


def escape_latex_complete(text):
    """
    Escape all LaTeX special characters for safe use in LaTeX output.

    Args:
      text: Text containing potential LaTeX special characters

    Returns:
      Text with all special characters properly escaped
    """
    # Order matters! Backslash must be first to avoid double-escaping
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    return text


def generate_latex_preamble(use_minted=False):
    """Generate LaTeX document preamble for standalone documents"""
    if use_minted:
        return """\\documentclass{article}
\\usepackage{minted}
\\usepackage[utf8]{inputenc}
\\begin{document}
"""
    else:
        return """\\documentclass{article}
\\usepackage{verbatim}
\\usepackage[utf8]{inputenc}
\\begin{document}
"""


def generate_latex_postamble():
    """Generate LaTeX document closing for standalone documents"""
    return """\\end{document}
"""


def create_command(config, canvas, args):
    """Creates a new quiz in a course"""
    # Handle --example flag first (doesn't require course/file)
    if getattr(args, "example", False):
        print_full_quiz_example_json()
        return

    # Validate required arguments when not using --example
    if not getattr(args, "course", None):
        canvaslms.cli.err(1, "Please specify -c/--course or use --example")
    if not getattr(args, "file", None) and not getattr(args, "title", None):
        canvaslms.cli.err(1, "Please specify -f/--file or --title or use --example")

    # Get the course
    course_list = courses.process_course_option(canvas, args)
    if len(course_list) != 1:
        canvaslms.cli.err(1, "Please specify exactly one course for quiz creation")
    course = course_list[0]

    # Read quiz data from file or use defaults
    quiz_data = {}
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                quiz_data = json.load(f)
        except FileNotFoundError:
            canvaslms.cli.err(1, f"File not found: {args.file}")
        except json.JSONDecodeError as e:
            canvaslms.cli.err(1, f"Invalid JSON in {args.file}: {e}")

    # Determine quiz type from args or JSON
    quiz_type = args.type
    if quiz_type is None:
        quiz_type = quiz_data.get("quiz_type", "new")

    # Extract settings: support both full format (with 'settings' key) and simple format
    if "settings" in quiz_data:
        quiz_params = quiz_data["settings"].copy()
    else:
        # Simple format: entire JSON is settings (excluding items/questions)
        quiz_params = {
            k: v
            for k, v in quiz_data.items()
            if k not in ("quiz_type", "items", "questions")
        }

    # Command-line title overrides file
    if args.title:
        quiz_params["title"] = args.title

    if "title" not in quiz_params:
        canvaslms.cli.err(1, "Quiz title is required (use --title or include in JSON)")

    # Create the quiz
    requester = canvas._Canvas__requester
    if quiz_type == "new":
        quiz = create_new_quiz(course, requester, quiz_params)
    else:
        quiz = create_classic_quiz(course, quiz_params)

    if not quiz:
        canvaslms.cli.err(1, "Failed to create quiz")

    quiz_id = quiz.get("id", "unknown")
    print(f"Created quiz: {quiz_params.get('title')} (ID: {quiz_id})")

    # Add questions if present in JSON
    items = quiz_data.get("items", [])
    questions = quiz_data.get("questions", [])

    if quiz_type == "new" and items:
        print(f"Adding {len(items)} question(s)...")
        success, failed = add_new_quiz_items(course, quiz_id, requester, items)
        print(f"Added {success} question(s), {failed} failed")
    elif quiz_type == "classic" and questions:
        # For classic quizzes, we need to get the quiz object to add questions
        try:
            quiz_obj = course.get_quiz(quiz_id)
            print(f"Adding {len(questions)} question(s)...")
            success, failed = add_classic_questions(quiz_obj, questions)
            print(f"Added {success} question(s), {failed} failed")
        except Exception as e:
            canvaslms.cli.warn(f"Failed to add questions: {e}")


def create_new_quiz(course, requester, quiz_params):
    """Creates a New Quiz via the New Quizzes API

    Args:
      course: Course object
      requester: Canvas API requester for direct HTTP calls
      quiz_params: Dictionary of quiz parameters, may include nested quiz_settings

    Returns:
      Dictionary with created quiz data, or None on failure
    """
    endpoint = f"courses/{course.id}/quizzes"

    # Build the request parameters, handling nested quiz_settings
    params = build_new_quiz_api_params(quiz_params)

    try:
        response = requester.request(
            method="POST", endpoint=endpoint, _url="new_quizzes", **params
        )
        return response.json()
    except Exception as e:
        canvaslms.cli.warn(f"Failed to create New Quiz: {e}")
        return None


def build_new_quiz_api_params(quiz_params):
    """Converts quiz parameters to Canvas API format

    Handles nested structures like quiz_settings.multiple_attempts by
    flattening them into the format:
      quiz[quiz_settings][multiple_attempts][key]=value

    Args:
      quiz_params: Dictionary with quiz parameters, may include nested dicts

    Returns:
      Dictionary suitable for passing to requester.request()
    """
    params = {}

    for key, value in quiz_params.items():
        if value is None:
            continue

        if key == "quiz_settings" and isinstance(value, dict):
            # Handle nested quiz_settings structure
            for settings_key, settings_value in value.items():
                if settings_value is None:
                    continue

                if isinstance(settings_value, dict):
                    # Handle doubly-nested structures like multiple_attempts, result_view_settings
                    for nested_key, nested_value in settings_value.items():
                        if nested_value is not None:
                            param_key = (
                                f"quiz[quiz_settings][{settings_key}][{nested_key}]"
                            )
                            params[param_key] = nested_value
                else:
                    # Direct quiz_settings value (e.g., shuffle_answers)
                    param_key = f"quiz[quiz_settings][{settings_key}]"
                    params[param_key] = settings_value
        else:
            # Top-level quiz parameter
            params[f"quiz[{key}]"] = value

    return params


def create_classic_quiz(course, quiz_params):
    """Creates a Classic Quiz using the canvasapi library

    Args:
      course: Course object
      quiz_params: Dictionary of quiz parameters

    Returns:
      Quiz object on success, None on failure
    """
    try:
        quiz = course.create_quiz(quiz=quiz_params)
        return {"id": quiz.id, "title": quiz.title}
    except Exception as e:
        canvaslms.cli.warn(f"Failed to create Classic Quiz: {e}")
        return None


def update_quiz_module_membership(quiz, module_regexes):
    """Update module membership for a quiz based on module regex list"""
    item_id = int(quiz.id) if is_new_quiz(quiz) else quiz.id
    added, removed = modules.update_item_modules(
        quiz.course, "Assignment", item_id, module_regexes
    )
    if added:
        print(f"  Added to modules: {', '.join(added)}", file=sys.stderr)
    if removed:
        print(f"  Removed from modules: {', '.join(removed)}", file=sys.stderr)


def detect_quiz_file_format(filepath):
    """Detect quiz file format from extension and content

    Args:
        filepath: Path to the file

    Returns:
        'json', 'yaml', or 'frontmatter'

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format cannot be determined or extension mismatches content
    """
    # Check extension
    ext = os.path.splitext(filepath)[1].lower()

    # Read file content
    with open(filepath, "r", encoding="utf-8") as f:
        file_content = f.read()

    content_stripped = file_content.lstrip()

    # Determine expected format from extension
    if ext == ".json":
        expected = "json"
    elif ext in (".yaml", ".yml"):
        expected = "yaml"
    elif ext == ".md":
        expected = "frontmatter"
    else:
        expected = None  # Auto-detect

    # Detect actual format from content
    if content_stripped.startswith("{"):
        actual = "json"
    elif content_stripped.startswith("---"):
        actual = "frontmatter"
    elif content_stripped.startswith("quiz_type:") or content_stripped.startswith(
        "settings:"
    ):
        actual = "yaml"
    else:
        # For YAML, try parsing to see if it's valid
        try:
            data = yaml.safe_load(content_stripped)
            if isinstance(data, dict) and ("settings" in data or "title" in data):
                actual = "yaml"
            else:
                raise ValueError(f"Cannot determine format of {filepath}")
        except yaml.YAMLError:
            raise ValueError(f"Cannot determine format of {filepath}")

    # Verify match if extension specified a format
    if expected and expected != actual:
        raise ValueError(
            f"File extension suggests {expected} but content looks like {actual}"
        )

    return actual, file_content


def read_quiz_from_file(filepath):
    """Read quiz data from JSON, YAML, or front matter file

    Args:
        filepath: Path to the quiz file

    Returns:
        Dictionary with:
            'format': 'json'|'yaml'|'frontmatter'
            'settings': dict of quiz settings
            'instructions': str or None (body for frontmatter format)
            'items': list or None (questions, for json/yaml)
            'quiz_type': 'new'|'classic' or None

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    format_type, file_content = detect_quiz_file_format(filepath)

    if format_type == "json":
        try:
            data = json.loads(file_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        return _parse_quiz_full_format(data, "json")

    elif format_type == "yaml":
        try:
            data = yaml.safe_load(file_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        return _parse_quiz_full_format(data, "yaml")

    else:  # frontmatter
        attributes, body = content.parse_yaml_front_matter(file_content)
        return {
            "format": "frontmatter",
            "settings": attributes,
            "instructions": body.strip() if body else None,
            "items": None,
            "quiz_type": None,
        }


def _parse_quiz_full_format(data, format_type):
    """Parse full format (JSON or YAML) quiz data

    Handles both the full format with 'settings' key and the simple format
    where the entire dict is settings.
    """
    if not isinstance(data, dict):
        raise ValueError(f"Expected a dictionary, got {type(data).__name__}")

    if "settings" in data:
        settings = data["settings"].copy()
    else:
        # Simple format: entire dict is settings (excluding metadata keys)
        settings = {
            k: v
            for k, v in data.items()
            if k not in ("quiz_type", "items", "questions")
        }

    # Extract instructions from settings if present
    instructions = settings.get("instructions")

    return {
        "format": format_type,
        "settings": settings,
        "instructions": instructions,
        "items": data.get("items") or data.get("questions"),
        "quiz_type": data.get("quiz_type"),
    }


def edit_command(config, canvas, args):
    """Edits quiz settings and instructions"""
    quiz_list = process_quiz_option(canvas, args)
    requester = canvas._Canvas__requester

    if args.file:
        try:
            quiz_data = read_quiz_from_file(args.file)
        except FileNotFoundError:
            canvaslms.cli.err(1, f"File not found: {args.file}")
        except ValueError as e:
            canvaslms.cli.err(1, f"Invalid file format: {e}")

        settings = quiz_data["settings"]
        quiz_id = settings.get("id")

        if quiz_id:
            target_quiz = None
            for quiz in quiz_list:
                if str(quiz.id) == str(quiz_id):
                    target_quiz = quiz
                    break
            if not target_quiz:
                canvaslms.cli.err(1, f"Quiz with ID {quiz_id} not found")
            quiz_list = [target_quiz]
        items = quiz_data.get("items")
        if args.replace_items and items:
            for quiz in quiz_list:
                item_success = replace_quiz_items(quiz, items, requester)
                if item_success:
                    print(f"Replaced items for quiz: {quiz.title}")
                else:
                    canvaslms.cli.warn(
                        f"Failed to replace items for quiz: {quiz.title}"
                    )
        elif items:
            print(
                f"Note: Ignoring {len(items)} items in file (use --replace-items to update)",
                file=sys.stderr,
            )
        body = quiz_data.get("instructions") or ""

        for quiz in quiz_list:
            # For JSON/YAML, instructions may be in settings; extract it for body
            if quiz_data["format"] in ("json", "yaml"):
                body = settings.get("instructions", "") or ""

            success = apply_quiz_edit(quiz, settings, body, requester, args.html)
            if success:
                print(f"Updated quiz: {quiz.title}")
                if "modules" in settings:
                    update_quiz_module_membership(quiz, settings["modules"])
            else:
                canvaslms.cli.warn(f"Failed to update quiz: {quiz.title}")
    else:
        # Confirm if multiple quizzes match
        if len(quiz_list) > 1:
            print(f"Found {len(quiz_list)} quizzes matching the pattern:")
            for quiz in quiz_list:
                quiz_type = "New Quiz" if is_new_quiz(quiz) else "Classic Quiz"
                print(f"  - {quiz.title} ({quiz_type})")
            response = input("\nEdit all? [y/N] ").strip().lower()
            if response != "y":
                print("Aborted.")
                return

        updated_count = 0
        skipped_count = 0

        for quiz in quiz_list:
            if args.full_json:
                result = edit_quiz_interactive_json(
                    quiz, requester, args.html, args.replace_items
                )
            else:
                result = edit_quiz_interactive(quiz, requester, args.html)

            if result == "updated":
                updated_count += 1
            elif result == "skipped":
                skipped_count += 1

        print(f"\nSummary: {updated_count} updated, {skipped_count} skipped")


def edit_quiz_interactive(quiz, requester, html_mode=False):
    """Edit a single quiz interactively

    Args:
      quiz: Quiz object to edit
      requester: Canvas API requester
      html_mode: If True, edit raw HTML instead of Markdown

    Returns:
      'updated', 'skipped', or 'error'
    """
    # Extract current quiz attributes including instructions
    current_attrs = extract_quiz_attributes(quiz, requester)

    # Get content from editor - instructions becomes the body
    result = content.get_content_from_editor(
        schema=QUIZ_SCHEMA,
        initial_attributes=current_attrs,
        content_attr="instructions",
        html_mode=html_mode,
    )

    if result is None:
        print("Editor cancelled. Skipping this quiz.", file=sys.stderr)
        return "skipped"

    attributes, body = result

    # Interactive confirm and edit loop
    quiz_type = "New Quiz" if is_new_quiz(quiz) else "Classic Quiz"
    title = attributes.get("title", quiz.title)
    result = content.interactive_confirm_and_edit(
        title=f"{title} ({quiz_type})",
        message=body,
        attributes=attributes,
        schema=QUIZ_SCHEMA,
        content_type="Quiz",
        content_attr="instructions",
    )

    if result is None:
        print("Discarded changes.", file=sys.stderr)
        return "skipped"

    final_attrs, final_body = result

    # Apply the changes
    success = apply_quiz_edit(quiz, final_attrs, final_body, requester, html_mode)
    if success:
        if "modules" in final_attrs:
            update_quiz_module_membership(quiz, final_attrs["modules"])
    return "updated" if success else "error"


def edit_quiz_interactive_json(quiz, requester, html_mode=False, replace_items=False):
    """Edit a quiz interactively using full JSON format

    Args:
      quiz: Quiz object to edit
      requester: Canvas API requester
      html_mode: If True, don't convert instructions (not used in JSON mode)
      replace_items: If True, also update items from the JSON

    Returns:
      'updated', 'skipped', or 'error'
    """
    import tempfile

    # Export current quiz state to JSON
    if is_new_quiz(quiz):
        original_data = export_full_new_quiz(
            quiz, requester, include_banks=True, importable=not replace_items
        )
    else:
        original_data = export_full_classic_quiz(quiz, importable=not replace_items)

    # If not replacing items, remove items from the export to simplify editing
    if not replace_items:
        original_data.pop("items", None)
        original_data.pop("questions", None)
    original_json = json.dumps(original_data, indent=2, ensure_ascii=False)

    # Create temp file with .json extension for editor syntax highlighting
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write(original_json)
        temp_path = f.name

    try:
        while True:
            # Open editor
            edited_json = open_in_editor(temp_path)
            if edited_json is None:
                print("Editor cancelled.", file=sys.stderr)
                return "skipped"

            # Parse the edited JSON
            try:
                edited_data = json.loads(edited_json)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}", file=sys.stderr)
                response = input("Edit again? [Y/n] ").strip().lower()
                if response == "n":
                    return "skipped"
                continue

            # Show diff and confirm
            result = show_json_diff_and_confirm(original_json, edited_json, quiz.title)

            if result == "accept":
                break
            elif result == "edit":
                # Update temp file with edited content for next iteration
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(edited_json)
                continue
            else:  # discard
                print("Discarded changes.", file=sys.stderr)
                return "skipped"
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass

    # Apply the changes
    success = apply_quiz_from_dict(
        quiz, edited_data, requester, replace_items=replace_items
    )
    return "updated" if success else "error"


def open_in_editor(filepath):
    """Open a file in the user's preferred editor

    Args:
      filepath: Path to the file to edit

    Returns:
      The edited file content, or None if editor failed/was cancelled
    """
    import subprocess

    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "vi"))

    try:
        subprocess.run([editor, filepath], check=True)
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        print(
            f"Editor '{editor}' not found. Set EDITOR environment variable.",
            file=sys.stderr,
        )
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except IOError:
        return None


def show_json_diff_and_confirm(original, edited, title):
    """Show a diff between original and edited JSON, ask for confirmation

    Args:
      original: Original JSON string
      edited: Edited JSON string
      title: Quiz title for display

    Returns:
      'accept', 'edit', or 'discard'
    """
    if original.strip() == edited.strip():
        print("No changes detected.")
        return "discard"

    # Generate unified diff
    original_lines = original.splitlines(keepends=True)
    edited_lines = edited.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            original_lines,
            edited_lines,
            fromfile="original",
            tofile="edited",
            lineterm="",
        )
    )

    if not diff:
        print("No changes detected.")
        return "discard"

    # Display diff with colors if terminal supports it
    print(f"\n--- Changes to: {title} ---")
    for line in diff:
        line = line.rstrip("\n")
        if line.startswith("+") and not line.startswith("+++"):
            print(f"\033[32m{line}\033[0m")  # Green for additions
        elif line.startswith("-") and not line.startswith("---"):
            print(f"\033[31m{line}\033[0m")  # Red for deletions
        elif line.startswith("@@"):
            print(f"\033[36m{line}\033[0m")  # Cyan for line numbers
        else:
            print(line)
    print()

    # Prompt for action
    while True:
        response = input("[A]ccept, [E]dit, [D]iscard? ").strip().lower()
        if response in ("a", "accept"):
            return "accept"
        elif response in ("e", "edit"):
            return "edit"
        elif response in ("d", "discard"):
            return "discard"
        print("Please enter A, E, or D.")


def apply_quiz_from_dict(quiz, data, requester, replace_items=False):
    """Apply quiz changes from a dictionary (parsed JSON/YAML)

    Args:
      quiz: Quiz object to update
      data: Dictionary with settings and optional items
      requester: Canvas API requester
      replace_items: If True, replace quiz items

    Returns:
      True on success, False on failure
    """
    # Extract settings - handle both 'settings' key and flat structure
    if "settings" in data:
        settings = data["settings"].copy()
    else:
        # Flat structure: everything except 'items' and 'quiz_type' is settings
        settings = {
            k: v
            for k, v in data.items()
            if k not in ("items", "questions", "quiz_type")
        }

    # Extract instructions/body
    body = settings.get("instructions", "") or ""

    # Apply settings
    success = apply_quiz_edit(quiz, settings, body, requester, html_mode=True)

    if not success:
        return False

    # Handle items if requested
    items = data.get("items") or data.get("questions")
    if replace_items and items:
        item_success = replace_quiz_items(quiz, items, requester)
        if not item_success:
            canvaslms.cli.warn("Settings updated but failed to replace items")
            return False

    return True


def get_quiz_submission_count(quiz, requester):
    """Get the number of student submissions for a quiz

    Args:
      quiz: Quiz object
      requester: Canvas API requester (unused for New Quizzes)

    Returns:
      Number of submissions, or -1 if unable to determine
    """
    try:
        if is_new_quiz(quiz):
            # New Quizzes are assignments - use standard Canvas API.
            # The quiz.id is actually the assignment_id.
            # Note: canvasapi returns NewQuiz.id as string (bug/inconsistency),
            # but get_assignment() requires int.
            assignment = quiz.course.get_assignment(int(quiz.id))
            submissions = list(assignment.get_submissions())
            # Count submissions that have been submitted (not just placeholder records)
            return sum(
                1
                for s in submissions
                if s.workflow_state == "submitted"
                or s.workflow_state == "graded"
                or getattr(s, "submitted_at", None) is not None
            )
        else:
            # Classic Quiz: use canvasapi
            submissions = list(quiz.get_submissions())
            # Count only actual submissions (not just generated records)
            return sum(1 for s in submissions if s.workflow_state != "settings_only")
    except Exception as e:
        canvaslms.cli.warn(f"Could not check submissions: {e}")
        return -1


def replace_quiz_items(quiz, items, requester):
    """Replace all items in a quiz with new ones

    Args:
      quiz: Quiz object
      items: List of item dictionaries (from export format)
      requester: Canvas API requester

    Returns:
      True on success, False on failure
    """
    # Check for submissions first
    submission_count = get_quiz_submission_count(quiz, requester)

    if submission_count > 0:
        print(
            f"\nWarning: This quiz has {submission_count} student submission(s).",
            file=sys.stderr,
        )
        print("Replacing items will invalidate existing responses!", file=sys.stderr)
        response = input("Continue anyway? [y/N] ").strip().lower()
        if response != "y":
            print("Item replacement cancelled.")
            return False
    elif submission_count < 0:
        print("\nWarning: Could not determine submission count.", file=sys.stderr)
        response = input("Continue with item replacement? [y/N] ").strip().lower()
        if response != "y":
            print("Item replacement cancelled.")
            return False

    # Delete existing items
    if is_new_quiz(quiz):
        delete_success = delete_all_new_quiz_items(quiz, requester)
    else:
        delete_success = delete_all_classic_quiz_questions(quiz)

    if not delete_success:
        canvaslms.cli.warn("Failed to delete existing items")
        return False

    # Create new items
    if is_new_quiz(quiz):
        create_success = add_new_quiz_items(quiz.course, quiz.id, requester, items)
    else:
        create_success = add_classic_questions(quiz, items)

    return create_success


def delete_all_new_quiz_items(quiz, requester):
    """Delete all items from a New Quiz

    Args:
      quiz: Quiz object
      requester: Canvas API requester

    Returns:
      True on success, False on failure
    """
    try:
        # Fetch existing items
        endpoint = f"courses/{quiz.course.id}/quizzes/{quiz.id}/items"
        response = requester.request(
            method="GET", endpoint=endpoint, _url="new_quizzes"
        )
        items = response.json()

        if not items:
            return True  # Nothing to delete

        # Delete each item
        for item in items:
            item_id = item.get("id")
            if item_id:
                delete_endpoint = (
                    f"courses/{quiz.course.id}/quizzes/{quiz.id}/items/{item_id}"
                )
                requester.request(
                    method="DELETE", endpoint=delete_endpoint, _url="new_quizzes"
                )

        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to delete New Quiz items: {e}")
        return False


def delete_all_classic_quiz_questions(quiz):
    """Delete all questions from a Classic Quiz

    Args:
      quiz: Classic Quiz object

    Returns:
      True on success, False on failure
    """
    try:
        questions = list(quiz.get_questions())

        for question in questions:
            question.delete()

        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to delete Classic Quiz questions: {e}")
        return False


def extract_quiz_attributes(quiz, requester=None):
    """Extract editable attributes from a quiz object

    Args:
      quiz: Quiz object (New Quiz or Classic Quiz)
      requester: Canvas API requester (needed for New Quiz settings)

    Returns:
      Dictionary of attributes matching QUIZ_SCHEMA, plus 'instructions'
      and 'quiz_settings' (for New Quizzes)
    """
    attrs = {}

    for key, spec in QUIZ_SCHEMA.items():
        canvas_attr = spec.get("canvas_attr", key)
        value = getattr(quiz, canvas_attr, spec.get("default"))

        # Normalize time_limit to minutes
        if key == "time_limit" and value is not None:
            if is_new_quiz(quiz):
                # New Quizzes store time in seconds
                value = value // 60 if value else None
            # Classic Quizzes already use minutes

        if value is not None:
            attrs[key] = value

    # Add instructions (not in schema, but needed for content_attr)
    if is_new_quiz(quiz):
        attrs["instructions"] = getattr(quiz, "instructions", "") or ""
        # Fetch quiz_settings for New Quizzes
        if requester:
            quiz_settings = fetch_new_quiz_settings(quiz, requester)
            if quiz_settings:
                attrs["quiz_settings"] = quiz_settings
    else:
        attrs["instructions"] = getattr(quiz, "description", "") or ""

    return attrs


def fetch_new_quiz_settings(quiz, requester):
    """Fetch quiz_settings from the New Quizzes API

    Args:
      quiz: Quiz object (must have .id and .course attributes)
      requester: Canvas API requester

    Returns:
      Dictionary with quiz_settings, or None if unavailable
    """
    try:
        endpoint = f"courses/{quiz.course.id}/quizzes/{quiz.id}"
        response = requester.request(
            method="GET", endpoint=endpoint, _url="new_quizzes"
        )
        data = response.json()
        return data.get("quiz_settings", None)
    except Exception as e:
        canvaslms.cli.warn(f"Failed to fetch New Quiz settings: {e}")
        return None


def apply_quiz_edit(quiz, attributes, body, requester, html_mode=False):
    """Apply edited attributes and body to a quiz

    Args:
      quiz: Quiz object to update
      attributes: Dictionary of attributes from YAML front matter
      body: Instructions/description content
      requester: Canvas API requester
      html_mode: If True, body is already HTML

    Returns:
      True on success, False on failure
    """
    # Convert body to HTML if needed
    if html_mode:
        html_body = body
    else:
        if body and body.strip():
            html_body = pypandoc.convert_text(body, "html", format="md")
        else:
            html_body = ""

    # Build API parameters
    quiz_params = quiz_attributes_to_api_params(
        attributes, is_new_quiz(quiz), html_body
    )

    # Update based on quiz type
    if is_new_quiz(quiz):
        return update_new_quiz(quiz.course, quiz.id, requester, quiz_params)
    else:
        return update_classic_quiz(quiz, quiz_params)


def quiz_attributes_to_api_params(attributes, is_new, html_body):
    """Convert schema attributes to Canvas API parameters

    Args:
      attributes: Dictionary of attributes from YAML
      is_new: True if this is a New Quiz
      html_body: HTML content for instructions/description

    Returns:
      Dictionary suitable for Canvas API (nested for New Quizzes)
    """
    params = {}

    for key, value in attributes.items():
        if key == "id":
            # Don't send ID as an update parameter
            continue

        if value is None:
            continue

        # Handle time_limit conversion
        if key == "time_limit":
            if is_new:
                # New Quizzes want seconds
                params["time_limit"] = value * 60
            else:
                # Classic Quizzes want minutes
                params["time_limit"] = value
            continue

        # Skip quiz_type for New Quizzes: New Quizzes are always graded assignments
        # and don't support the Classic Quiz distinction between assignment,
        # practice_quiz, graded_survey, and survey types.
        if key == "quiz_type" and is_new:
            continue

        # Skip hide_results for New Quizzes: result visibility is controlled
        # through quiz_settings.result_view_settings, not this parameter.
        if key == "hide_results" and is_new:
            continue

        # Pass through quiz_settings as-is for New Quizzes
        if key == "quiz_settings" and is_new:
            params["quiz_settings"] = value
            continue

        # Skip instructions - handled separately as body
        if key == "instructions":
            continue

        params[key] = value

    # Add body with appropriate field name (include even if empty to allow clearing)
    if is_new:
        params["instructions"] = html_body
    else:
        params["description"] = html_body

    return params


def update_new_quiz(course, assignment_id, requester, quiz_params):
    """Updates a New Quiz via the New Quizzes API

    Args:
      course: Course object
      assignment_id: The quiz/assignment ID
      requester: Canvas API requester
      quiz_params: Dictionary of parameters to update, may include nested quiz_settings

    Returns:
      True on success, False on failure
    """
    endpoint = f"courses/{course.id}/quizzes/{assignment_id}"

    # Build the request parameters, handling nested quiz_settings
    params = build_new_quiz_api_params(quiz_params)

    try:
        requester.request(
            method="PATCH", endpoint=endpoint, _url="new_quizzes", **params
        )
        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to update New Quiz: {e}")
        return False


def update_classic_quiz(quiz, quiz_params):
    """Updates a Classic Quiz using the canvasapi library

    Args:
      quiz: Quiz object to update
      quiz_params: Dictionary of parameters to update

    Returns:
      True on success, False on failure
    """
    try:
        quiz.edit(quiz=quiz_params)
        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to update Classic Quiz: {e}")
        return False


def delete_command(config, canvas, args):
    """Deletes a quiz"""
    # Find the quiz
    course_list = courses.process_course_option(canvas, args)
    quiz_list = list(filter_quizzes(course_list, args.assignment))

    if not quiz_list:
        canvaslms.cli.err(1, f"No quiz found matching: {args.assignment}")
    if len(quiz_list) > 1:
        canvaslms.cli.err(
            1,
            f"Multiple quizzes match '{args.assignment}'. "
            "Please use a more specific pattern.",
        )

    quiz = quiz_list[0]

    # Confirm deletion
    if not args.force:
        print(f"About to delete quiz: {quiz.title} (ID: {quiz.id})")
        try:
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                print("Cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return

    # Delete based on quiz type
    if is_new_quiz(quiz):
        result = delete_new_quiz(quiz.course, quiz.id, canvas._Canvas__requester)
    else:
        result = delete_classic_quiz(quiz)

    if result:
        print(f"Deleted quiz: {quiz.title}")
    else:
        canvaslms.cli.err(1, "Failed to delete quiz")


def delete_new_quiz(course, assignment_id, requester):
    """Deletes a New Quiz via the New Quizzes API

    Args:
      course: Course object
      assignment_id: The quiz/assignment ID
      requester: Canvas API requester

    Returns:
      True on success, False on failure
    """
    endpoint = f"courses/{course.id}/quizzes/{assignment_id}"

    try:
        requester.request(method="DELETE", endpoint=endpoint, _url="new_quizzes")
        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to delete New Quiz: {e}")
        return False


def delete_classic_quiz(quiz):
    """Deletes a Classic Quiz using the canvasapi library

    Args:
      quiz: Quiz object to delete

    Returns:
      True on success, False on failure
    """
    try:
        quiz.delete()
        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to delete Classic Quiz: {e}")
        return False


def export_command(config, canvas, args):
    """Exports a complete quiz (settings + questions) to JSON"""
    # Find the quiz
    course_list = courses.process_course_option(canvas, args)
    quiz_list = list(filter_quizzes(course_list, args.assignment))

    if not quiz_list:
        canvaslms.cli.err(1, f"No quiz found matching: {args.assignment}")

    quiz = quiz_list[0]
    requester = canvas._Canvas__requester
    include_banks = args.include_banks and not args.no_banks
    importable = getattr(args, "importable", False)

    # Build the export structure
    if is_new_quiz(quiz):
        export = export_full_new_quiz(quiz, requester, include_banks, importable)
    else:
        export = export_full_classic_quiz(quiz, importable)

    # Output as JSON
    print(json.dumps(export, indent=2, ensure_ascii=False))


def export_full_new_quiz(quiz, requester, include_banks=True, importable=False):
    """Exports a complete New Quiz with settings and items

    Args:
      quiz: Quiz object (must have .id and .course attributes)
      requester: Canvas API requester
      include_banks: If True, expand Bank/BankEntry items to include bank questions
      importable: If True, clean output for direct import

    Returns:
      Dictionary with quiz_type, settings (including quiz_settings), and items
    """
    # Extract basic settings
    settings = {
        "modules": [
            "^" + re.escape(name) + "$"
            for name in modules.get_item_modules(
                quiz.course, "Assignment", int(quiz.id)
            )
        ],
        "title": getattr(quiz, "title", ""),
        "instructions": getattr(quiz, "instructions", "") or "",
        "time_limit": getattr(quiz, "time_limit", None),
        "points_possible": getattr(quiz, "points_possible", None),
        "due_at": getattr(quiz, "due_at", None),
        "unlock_at": getattr(quiz, "unlock_at", None),
        "lock_at": getattr(quiz, "lock_at", None),
    }

    # Fetch quiz_settings from the API (contains multiple_attempts, result_view_settings, etc.)
    quiz_settings = fetch_new_quiz_settings(quiz, requester)
    if quiz_settings:
        settings["quiz_settings"] = quiz_settings

    # Get items
    items_export = export_new_quiz_items(quiz, requester, include_banks=include_banks)
    items = items_export.get("items", [])

    # Clean for import if requested
    if importable:
        items_cleaned = clean_for_import({"items": items}, quiz_type="new_quiz")
        items = items_cleaned.get("items", [])

    return {"quiz_type": "new", "settings": settings, "items": items}


def export_full_classic_quiz(quiz, importable=False):
    """Exports a complete Classic Quiz with settings and questions

    Args:
      quiz: Quiz object
      importable: If True, clean output for direct import

    Returns:
      Dictionary with quiz_type, settings, and questions
    """
    # Extract settings
    settings = {
        "modules": [
            "^" + re.escape(name) + "$"
            for name in modules.get_item_modules(quiz.course, "Assignment", quiz.id)
        ],
        "title": getattr(quiz, "title", ""),
        "description": getattr(quiz, "description", "") or "",
        "quiz_type": getattr(quiz, "quiz_type", "assignment"),
        "time_limit": getattr(quiz, "time_limit", None),
        "allowed_attempts": getattr(quiz, "allowed_attempts", 1),
        "shuffle_questions": getattr(quiz, "shuffle_questions", False),
        "shuffle_answers": getattr(quiz, "shuffle_answers", False),
        "points_possible": getattr(quiz, "points_possible", None),
        "published": getattr(quiz, "published", False),
        "due_at": getattr(quiz, "due_at", None),
        "unlock_at": getattr(quiz, "unlock_at", None),
        "lock_at": getattr(quiz, "lock_at", None),
        "show_correct_answers": getattr(quiz, "show_correct_answers", True),
        "one_question_at_a_time": getattr(quiz, "one_question_at_a_time", False),
        "cant_go_back": getattr(quiz, "cant_go_back", False),
        "access_code": getattr(quiz, "access_code", None),
    }

    # Get questions
    questions_export = export_classic_questions(quiz)
    questions = questions_export.get("questions", [])

    # Clean for import if requested
    if importable:
        questions_cleaned = clean_for_import(
            {"questions": questions}, quiz_type="classic"
        )
        questions = questions_cleaned.get("questions", [])

    return {"quiz_type": "classic", "settings": settings, "questions": questions}


def add_view_command(subp):
    """Adds the view subcommand to the quizzes command group"""
    view_parser = subp.add_parser(
        "view",
        help="View quiz content (instructions and questions)",
        description="""Displays the full content of a quiz including instructions,
  questions, and answer choices. For instructors, correct answers are marked.

  Output format depends on terminal:
  - TTY: Rich markdown rendering with pager support
  - Pipe: Plain markdown for further processing""",
    )

    view_parser.set_defaults(func=view_command)

    try:
        courses.add_course_option(view_parser, required=True)
    except argparse.ArgumentError:
        pass

    add_quiz_option(view_parser, required=True)


def view_command(config, canvas, args):
    """View quiz content including questions and answers"""
    quiz_list = process_quiz_option(canvas, args)
    requester = canvas._Canvas__requester

    output_parts = []

    for quiz in quiz_list:
        course = quiz.course if hasattr(quiz, "course") else None
        if course is None:
            # Try to get course from quiz attributes
            course_id = getattr(quiz, "course_id", None)
            if course_id:
                course = canvas.get_course(course_id)

        if is_new_quiz(quiz):
            markdown = format_new_quiz_as_markdown(quiz, course, requester)
        else:
            markdown = format_classic_quiz_as_markdown(quiz)

        output_parts.append(markdown)

    # Join all quizzes with a separator
    full_output = "\n\n---\n\n".join(output_parts)

    console = Console()
    md = Markdown(full_output)

    if sys.stdout.isatty():
        # Output to terminal with pager
        pager = ""
        if "MANPAGER" in os.environ:
            pager = os.environ["MANPAGER"]
        elif "PAGER" in os.environ:
            pager = os.environ["PAGER"]

        styles = False
        if "less" in pager and ("-R" in pager or "-r" in pager):
            styles = True

        with console.pager(styles=styles):
            console.print(md)
    else:
        # Piped to file, output plain markdown
        print(full_output)


def format_new_quiz_as_markdown(quiz, course, requester):
    """Format a New Quiz as markdown

    Args:
      quiz: NewQuiz object
      course: Course object
      requester: Canvas API requester

    Returns:
      Markdown string with quiz content
    """
    lines = []

    # Quiz header
    title = getattr(quiz, "title", "Untitled Quiz")
    lines.append(f"# {title}")
    lines.append("")

    # Quiz metadata
    points = getattr(quiz, "points_possible", None)
    if points:
        lines.append(f"**Points:** {points}")

    time_limit = getattr(quiz, "time_limit", None)
    if time_limit:
        lines.append(f"**Time limit:** {time_limit} minutes")

    if points or time_limit:
        lines.append("")

    # Instructions
    instructions = getattr(quiz, "instructions", None) or getattr(
        quiz, "description", None
    )
    if instructions:
        lines.append("## Instructions")
        lines.append("")
        # Convert HTML to plain text (basic cleanup)
        clean_instructions = html_to_markdown(instructions)
        lines.append(clean_instructions)
        lines.append("")

    # Fetch and format questions
    try:
        export_data = export_new_quiz_items(quiz, requester, include_banks=True)
        items = export_data.get("items", [])

        if items:
            lines.append("## Questions")
            lines.append("")

            for i, item in enumerate(items, 1):
                item_markdown = format_new_quiz_item(item, i)
                lines.append(item_markdown)
                lines.append("")

    except Exception as e:
        lines.append(f"*Could not fetch questions: {e}*")

    return "\n".join(lines)


def format_new_quiz_item(item, number):
    """Format a single New Quiz item as markdown

    Args:
      item: Item dictionary from export_new_quiz_items
      number: Question number for display

    Returns:
      Markdown string for the item
    """
    lines = []
    entry_type = item.get("entry_type", "Item")
    entry = item.get("entry", {})
    points = item.get("points_possible", 0)

    # Handle bank references (without embedded question content)
    # 'BankEntry (embedded)' contains actual question data with 'item_body',
    # while pure 'Bank' references only have bank metadata (title, entry_count)
    is_bank_reference = entry_type in ("Bank", "BankEntry") and "item_body" not in entry
    if is_bank_reference:
        bank_ref = item.get("bank_reference", {})
        # Fall back to entry for bank metadata if bank_reference not available
        if not bank_ref:
            bank_ref = entry
        bank_title = bank_ref.get("title", "Unknown Bank")
        sample_num = bank_ref.get(
            "sample_num", item.get("properties", {}).get("sample_num", "1")
        )
        entry_count = bank_ref.get("entry_count", bank_ref.get("item_entry_count", "?"))
        lines.append(f"### Question {number} (from Item Bank)")
        lines.append(f"*Draws {sample_num} random question(s) from: {bank_title}*")
        lines.append("")
        lines.append(
            f"*Bank contains {entry_count} questions. Actual content varies per student.*"
        )
        return "\n".join(lines)

    # Handle stimulus (reading passage)
    if entry_type == "Stimulus":
        title = entry.get("title", "Reading Passage")
        body = entry.get("body", "")
        lines.append(f"### {title}")
        lines.append("")
        lines.append(html_to_markdown(body))
        return "\n".join(lines)

    # Regular question item
    interaction_type = entry.get("interaction_type_slug", "unknown")
    title = entry.get("title", f"Question {number}")
    body = entry.get("item_body", "")

    lines.append(f"### Question {number}: {title}")
    if points:
        lines.append(f"*({points} points)*")
    lines.append("")
    lines.append(html_to_markdown(body))
    lines.append("")

    # Format answers based on question type
    interaction_data = entry.get("interaction_data", {})
    scoring_data = entry.get("scoring_data", {})

    format_new_quiz_answers(lines, interaction_type, interaction_data, scoring_data)

    return "\n".join(lines)


def format_new_quiz_answers(lines, interaction_type, interaction_data, scoring_data):
    """Format answer choices for a New Quiz item

    Args:
      lines: List to append formatted lines to
      interaction_type: The question type (choice, true-false, etc.)
      interaction_data: Question-specific data (choices, stems, etc.)
      scoring_data: Correct answer information
    """
    if interaction_type in ("choice", "multi-answer"):
        format_new_quiz_choice_answers(lines, interaction_data, scoring_data)
    elif interaction_type == "true-false":
        format_new_quiz_true_false(lines, scoring_data)
    elif interaction_type == "matching":
        format_new_quiz_matching(lines, interaction_data, scoring_data)
    elif interaction_type in ("essay", "rich-text"):
        lines.append("*(Essay response)*")
    elif interaction_type == "numeric":
        format_new_quiz_numeric(lines, scoring_data)
    elif interaction_type == "fill-in-the-blank":
        format_new_quiz_fill_blank(lines, scoring_data)
    else:
        lines.append(f"*(Question type: {interaction_type})*")


def format_new_quiz_choice_answers(lines, interaction_data, scoring_data):
    """Format multiple choice or multi-answer question choices"""
    choices = interaction_data.get("choices", [])
    correct_ids = scoring_data.get("value", [])
    if isinstance(correct_ids, str):
        correct_ids = [correct_ids]

    for choice in choices:
        choice_id = choice.get("id", "")
        # Handle both 'itemBody' (classic) and 'item_body' (new) formats
        choice_text = choice.get("itemBody") or choice.get("item_body", "")
        choice_text = html_to_markdown(choice_text)
        is_correct = choice_id in correct_ids
        marker = "✓" if is_correct else "○"
        lines.append(f"- {marker} {choice_text}")


def format_new_quiz_true_false(lines, scoring_data):
    """Format true/false question"""
    correct_value = scoring_data.get("value", "")
    for option in ["true", "false"]:
        is_correct = option == correct_value
        marker = "✓" if is_correct else "○"
        lines.append(f"- {marker} {option.capitalize()}")


def format_new_quiz_matching(lines, interaction_data, scoring_data):
    """Format matching question"""
    questions = interaction_data.get("questions", []) or interaction_data.get(
        "stems", []
    )
    correct_matches = scoring_data.get("value", {})

    lines.append("**Match the following:**")
    lines.append("")
    for q in questions:
        q_id = q.get("id", "")
        q_text = html_to_markdown(q.get("item_body", "") or q.get("body", ""))
        match_text = (
            correct_matches.get(q_id, "?") if isinstance(correct_matches, dict) else "?"
        )
        lines.append(f"- {q_text} → {match_text}")


def format_new_quiz_numeric(lines, scoring_data):
    """Format numeric question answer"""
    correct_value = scoring_data.get("value", {})
    if isinstance(correct_value, dict):
        exact = correct_value.get("exact")
        margin = correct_value.get("margin")
        range_min = correct_value.get("start")
        range_max = correct_value.get("end")
        if exact is not None:
            if margin:
                lines.append(f"**Answer:** {exact} (± {margin})")
            else:
                lines.append(f"**Answer:** {exact}")
        elif range_min is not None and range_max is not None:
            lines.append(f"**Answer:** between {range_min} and {range_max}")
    else:
        lines.append(f"**Answer:** {correct_value}")


def format_new_quiz_fill_blank(lines, scoring_data):
    """Format fill-in-the-blank question answers"""
    blanks = scoring_data.get("value", {})
    if blanks:
        lines.append("**Answers:**")
        for blank_id, answers in blanks.items():
            if isinstance(answers, list):
                lines.append(f"  - {', '.join(answers)}")
            else:
                lines.append(f"  - {answers}")


def format_classic_quiz_as_markdown(quiz):
    """Format a Classic Quiz as markdown

    Args:
      quiz: Quiz object

    Returns:
      Markdown string with quiz content
    """
    lines = []

    # Quiz header
    title = getattr(quiz, "title", "Untitled Quiz")
    lines.append(f"# {title}")
    lines.append("")

    # Quiz metadata
    points = getattr(quiz, "points_possible", None)
    if points:
        lines.append(f"**Points:** {points}")

    time_limit = getattr(quiz, "time_limit", None)
    if time_limit:
        lines.append(f"**Time limit:** {time_limit} minutes")

    question_count = getattr(quiz, "question_count", None)
    if question_count:
        lines.append(f"**Questions:** {question_count}")

    if points or time_limit or question_count:
        lines.append("")

    # Instructions/description
    description = getattr(quiz, "description", None)
    if description:
        lines.append("## Instructions")
        lines.append("")
        lines.append(html_to_markdown(description))
        lines.append("")

    # Fetch and format questions
    try:
        export_data = export_classic_questions(quiz)
        questions = export_data.get("questions", [])

        if questions:
            lines.append("## Questions")
            lines.append("")

            for i, question in enumerate(questions, 1):
                question_markdown = format_classic_question(question, i)
                lines.append(question_markdown)
                lines.append("")

    except Exception as e:
        lines.append(f"*Could not fetch questions: {e}*")

    return "\n".join(lines)


def format_classic_question(question, number):
    """Format a single Classic Quiz question as markdown

    Args:
      question: Question dictionary from export_classic_questions
      number: Question number for display

    Returns:
      Markdown string for the question
    """
    lines = []

    question_type = question.get("question_type", "unknown")
    question_name = question.get("question_name", f"Question {number}")
    question_text = question.get("question_text", "")
    points = question.get("points_possible", 0)
    answers = question.get("answers", [])

    lines.append(f"### Question {number}: {question_name}")
    if points:
        lines.append(f"*({points} points)*")
    lines.append("")
    lines.append(html_to_markdown(question_text))
    lines.append("")

    # Format answers based on question type
    format_classic_quiz_answers(lines, question_type, question, answers)

    return "\n".join(lines)


def format_classic_quiz_answers(lines, question_type, question, answers):
    """Format answer choices for a Classic Quiz question

    Args:
      lines: List to append formatted lines to
      question_type: The Canvas question type string
      question: Full question dictionary (for formulas, etc.)
      answers: List of answer dictionaries
    """
    if question_type in ("multiple_choice_question", "true_false_question"):
        format_classic_choice_answers(lines, answers)
    elif question_type == "multiple_answers_question":
        lines.append("*(Select all that apply)*")
        format_classic_choice_answers(lines, answers)
    elif question_type == "matching_question":
        format_classic_matching(lines, answers)
    elif question_type == "fill_in_multiple_blanks_question":
        format_classic_fill_blanks(lines, answers)
    elif question_type == "multiple_dropdowns_question":
        format_classic_dropdowns(lines, answers)
    elif question_type == "short_answer_question":
        format_classic_short_answer(lines, answers)
    elif question_type == "numerical_question":
        format_classic_numerical(lines, answers)
    elif question_type == "essay_question":
        lines.append("*(Essay response)*")
    elif question_type == "file_upload_question":
        lines.append("*(File upload)*")
    elif question_type == "text_only_question":
        pass  # No answers - just informational text
    elif question_type == "calculated_question":
        format_classic_calculated(lines, question, answers)
    else:
        lines.append(f"*(Question type: {question_type})*")


def format_classic_choice_answers(lines, answers):
    """Format choice answers with correct/incorrect markers"""
    for answer in answers:
        answer_text = html_to_markdown(answer.get("text", "") or answer.get("html", ""))
        weight = answer.get("weight", 0)
        is_correct = weight > 0
        marker = "✓" if is_correct else "○"
        lines.append(f"- {marker} {answer_text}")


def format_classic_matching(lines, answers):
    """Format matching question pairs"""
    lines.append("**Match the following:**")
    lines.append("")
    for answer in answers:
        left = html_to_markdown(answer.get("left", ""))
        right = html_to_markdown(answer.get("right", ""))
        lines.append(f"- {left} → {right}")


def format_classic_fill_blanks(lines, answers):
    """Format fill-in-multiple-blanks answers grouped by blank"""
    blanks = {}
    for answer in answers:
        blank_id = answer.get("blank_id", "default")
        answer_text = answer.get("text", "")
        weight = answer.get("weight", 0)
        if weight > 0:
            if blank_id not in blanks:
                blanks[blank_id] = []
            blanks[blank_id].append(answer_text)

    lines.append("**Answers:**")
    for blank_id, texts in blanks.items():
        lines.append(f"  [{blank_id}]: {', '.join(texts)}")


def format_classic_dropdowns(lines, answers):
    """Format multiple dropdowns with choices per blank"""
    blanks = {}
    for answer in answers:
        blank_id = answer.get("blank_id", "default")
        answer_text = answer.get("text", "")
        weight = answer.get("weight", 0)
        if blank_id not in blanks:
            blanks[blank_id] = []
        blanks[blank_id].append((answer_text, weight > 0))

    for blank_id, choices in blanks.items():
        lines.append(f"**[{blank_id}]:**")
        for text, is_correct in choices:
            marker = "✓" if is_correct else "○"
            lines.append(f"  {marker} {text}")


def format_classic_short_answer(lines, answers):
    """Format short answer accepted responses"""
    lines.append("**Accepted answers:**")
    for answer in answers:
        answer_text = answer.get("text", "")
        if answer_text:
            lines.append(f"  - {answer_text}")


def format_classic_numerical(lines, answers):
    """Format numerical question with exact, range, or precision answers"""
    for answer in answers:
        answer_type = answer.get("numerical_answer_type", "exact_answer")
        if answer_type == "exact_answer":
            exact = answer.get("exact", "")
            margin = answer.get("margin", 0)
            if margin:
                lines.append(f"**Answer:** {exact} (± {margin})")
            else:
                lines.append(f"**Answer:** {exact}")
        elif answer_type == "range_answer":
            start = answer.get("start", "")
            end = answer.get("end", "")
            lines.append(f"**Answer:** between {start} and {end}")
        elif answer_type == "precision_answer":
            approximate = answer.get("approximate", "")
            precision = answer.get("precision", "")
            lines.append(f"**Answer:** {approximate} (precision: {precision})")


def format_classic_calculated(lines, question, answers):
    """Format calculated question with formula and examples"""
    formulas = question.get("formulas", [])
    if formulas:
        lines.append("**Formula:**")
        for formula in formulas:
            lines.append(f"  {formula.get('formula', '')}")
    # Show sample answers (up to 3 examples)
    for answer in answers[:3]:
        variables = answer.get("variables", [])
        answer_val = answer.get("answer", "")
        if variables:
            var_str = ", ".join(f"{v['name']}={v['value']}" for v in variables)
            lines.append(f"  When {var_str}: {answer_val}")


def html_to_markdown(html_string):
    """Convert HTML to markdown using pypandoc

    Args:
      html_string: String containing HTML content

    Returns:
      Markdown string
    """
    if not html_string:
        return ""

    try:
        markdown = pypandoc.convert_text(html_string, "md", format="html")
        return markdown.strip()
    except Exception:
        # Fallback: return the string with tags stripped if pandoc fails
        import re

        text = re.sub(r"<[^>]+>", "", html_string)
        return text.strip()


def add_items_list_command(subp):
    """Registers the items list subcommand"""
    parser = subp.add_parser(
        "list",
        help="List questions in a quiz",
        description="List all questions/items in a quiz",
    )
    parser.set_defaults(func=items_list_command)

    try:
        courses.add_course_option(parser, required=True)
    except argparse.ArgumentError:
        pass

    parser.add_argument(
        "-a",
        "--assignment",
        required=True,
        help="Regex matching quiz title or Canvas ID",
    )


def add_items_add_command(subp):
    """Registers the items add subcommand"""
    parser = subp.add_parser(
        "add",
        help="Add questions to a quiz",
        description="""Add questions to a quiz from a JSON file.
The file should contain an array of questions.

Use --example to print example JSON for all supported question types.""",
    )
    parser.set_defaults(func=items_add_command)

    parser.add_argument(
        "--example",
        "-E",
        action="store_true",
        help="Print example JSON for all question types and exit",
    )

    try:
        courses.add_course_option(parser, required=False)
    except argparse.ArgumentError:
        pass

    parser.add_argument(
        "-a", "--assignment", help="Regex matching quiz title or Canvas ID"
    )

    parser.add_argument("-f", "--file", help="JSON file containing questions to add")


def add_items_edit_command(subp):
    """Registers the items edit subcommand"""
    parser = subp.add_parser(
        "edit",
        help="Edit a question in a quiz",
        description="Edit an existing question in a quiz",
    )
    parser.set_defaults(func=items_edit_command)

    try:
        courses.add_course_option(parser, required=True)
    except argparse.ArgumentError:
        pass

    parser.add_argument(
        "-a",
        "--assignment",
        required=True,
        help="Regex matching quiz title or Canvas ID",
    )

    parser.add_argument(
        "--position", "-p", type=int, help="Question position (1-based)"
    )

    parser.add_argument("--id", help="Question/item ID")

    parser.add_argument(
        "-f", "--file", required=True, help="JSON file containing updated question data"
    )


def add_items_delete_command(subp):
    """Registers the items delete subcommand"""
    parser = subp.add_parser(
        "delete",
        help="Delete a question from a quiz",
        description="Delete a question from a quiz",
    )
    parser.set_defaults(func=items_delete_command)

    try:
        courses.add_course_option(parser, required=True)
    except argparse.ArgumentError:
        pass

    parser.add_argument(
        "-a",
        "--assignment",
        required=True,
        help="Regex matching quiz title or Canvas ID",
    )

    parser.add_argument(
        "--position", "-p", type=int, help="Question position (1-based)"
    )

    parser.add_argument("--id", help="Question/item ID")

    parser.add_argument(
        "--force", "-F", action="store_true", help="Skip confirmation prompt"
    )


def add_items_export_command(subp):
    """Registers the items export subcommand"""
    parser = subp.add_parser(
        "export",
        help="Export quiz questions to JSON",
        description="""Export all questions from a quiz to JSON format.

For New Quizzes, if the quiz uses item banks (BankEntry items), the actual
questions from those banks are also exported. This allows complete backup
and migration of quiz content.""",
    )
    parser.set_defaults(func=items_export_command)

    try:
        courses.add_course_option(parser, required=True)
    except argparse.ArgumentError:
        pass

    parser.add_argument(
        "-a",
        "--assignment",
        required=True,
        help="Regex matching quiz title or Canvas ID",
    )

    parser.add_argument(
        "--include-banks",
        "-B",
        action="store_true",
        default=True,
        help="Include questions from referenced item banks (default: true)",
    )

    parser.add_argument(
        "--no-banks", action="store_true", help="Don't expand item bank references"
    )

    parser.add_argument(
        "--importable",
        "-I",
        action="store_true",
        help="Output clean JSON directly usable with 'items add' command",
    )


def items_list_command(config, canvas, args):
    """Lists all questions/items in a quiz"""
    # Find the quiz
    course_list = courses.process_course_option(canvas, args)
    quiz_list = list(filter_quizzes(course_list, args.assignment))

    if not quiz_list:
        canvaslms.cli.err(1, f"No quiz found matching: {args.assignment}")

    quiz = quiz_list[0]

    # Get items based on quiz type
    if is_new_quiz(quiz):
        items = list_new_quiz_items(quiz.course, quiz.id, canvas._Canvas__requester)
    else:
        items = list_classic_questions(quiz)

    if not items:
        print("No questions found in this quiz.")
        return

    # Output as TSV
    writer = csv.writer(sys.stdout, delimiter=args.delimiter)
    writer.writerow(["Position", "ID", "Type", "Title", "Points"])

    for item in items:
        writer.writerow(
            [
                item.get("position", ""),
                item.get("id", ""),
                item.get("type", ""),
                item.get("title", "")[:50],  # Truncate long titles
                item.get("points", ""),
            ]
        )


def list_new_quiz_items(course, assignment_id, requester):
    """Lists items in a New Quiz

    Args:
      course: Course object
      assignment_id: Quiz/assignment ID
      requester: Canvas API requester

    Returns:
      List of item dictionaries with normalized fields
    """
    endpoint = f"courses/{course.id}/quizzes/{assignment_id}/items"

    try:
        response = requester.request(
            method="GET", endpoint=endpoint, _url="new_quizzes"
        )
        data = response.json()

        items = []
        for item in data:
            entry = item.get("entry", {})
            items.append(
                {
                    "position": item.get("position"),
                    "id": item.get("id"),
                    "type": entry.get("interaction_type_slug", "unknown"),
                    "title": entry.get("title", ""),
                    "points": item.get("points_possible"),
                }
            )
        return items
    except Exception as e:
        canvaslms.cli.warn(f"Failed to list New Quiz items: {e}")
        return []


def list_classic_questions(quiz):
    """Lists questions in a Classic Quiz

    Args:
      quiz: Quiz object

    Returns:
      List of question dictionaries with normalized fields
    """
    try:
        questions = quiz.get_questions()
        items = []
        for q in questions:
            items.append(
                {
                    "position": getattr(q, "position", None),
                    "id": q.id,
                    "type": getattr(q, "question_type", "unknown"),
                    "title": getattr(q, "question_name", ""),
                    "points": getattr(q, "points_possible", None),
                }
            )
        return items
    except Exception as e:
        canvaslms.cli.warn(f"Failed to list Classic Quiz questions: {e}")
        return []


def print_example_json():
    """Prints example JSON for both New Quizzes and Classic Quizzes"""
    print("=" * 70)
    print("EXAMPLE JSON FOR NEW QUIZZES (Quizzes.Next)")
    print("=" * 70)
    print()
    print("Save this to a file (e.g., questions.json) and use with:")
    print("  canvaslms quizzes items add -c COURSE -a QUIZ -f questions.json")
    print()
    print(
        "Note: UUIDs must be unique. Generate with: python -c 'import uuid; "
        "print(uuid.uuid4())'"
    )
    print()
    print(json.dumps(EXAMPLE_NEW_QUIZ_JSON, indent=2))
    print()
    print()
    print("=" * 70)
    print("EXAMPLE JSON FOR CLASSIC QUIZZES")
    print("=" * 70)
    print()
    print("Classic Quizzes use a different format with 'questions' array.")
    print("answer_weight: 100 = correct, 0 = incorrect")
    print()
    print(json.dumps(EXAMPLE_CLASSIC_QUIZ_JSON, indent=2))


def print_full_quiz_example_json():
    """Prints example JSON for full quiz creation (settings + questions)"""
    print("=" * 70)
    print("EXAMPLE JSON FOR CREATING NEW QUIZZES (Quizzes.Next)")
    print("=" * 70)
    print()
    print("This format includes both quiz settings and questions.")
    print("Save to a file and use with:")
    print("  canvaslms quizzes create -c COURSE -f quiz.json")
    print()
    print("This is the same format produced by 'quizzes export -I'.")
    print()
    print("BASIC SETTINGS:")
    print("  title              - Quiz title")
    print("  instructions       - HTML instructions shown to students")
    print("  time_limit         - Time limit in SECONDS (or null)")
    print("  points_possible    - Total points")
    print("  due_at/unlock_at/lock_at - ISO 8601 dates (or null)")
    print()
    print("QUIZ SETTINGS (in 'settings.quiz_settings'):")
    print()
    print("  Randomization:")
    print("    shuffle_answers: true/false - Randomize answer order")
    print("    shuffle_questions: true/false - Randomize question order")
    print()
    print("  Time limit:")
    print("    has_time_limit: true/false")
    print("    session_time_limit_in_seconds: number")
    print()
    print("  Question display:")
    print("    one_at_a_time_type: 'none' or 'question'")
    print("    allow_backtracking: true/false - Can go back to previous questions")
    print()
    print("  Calculator:")
    print("    calculator_type: 'none', 'basic', or 'scientific'")
    print()
    print("  Access restrictions:")
    print("    require_student_access_code: true/false")
    print("    student_access_code: 'password' or null")
    print("    filter_ip_address: true/false")
    print("    filters: {} or IP filter rules")
    print()
    print("  Multiple attempts:")
    print("    multiple_attempts_enabled: true/false")
    print("    attempt_limit: true/false (true = limited, false = unlimited)")
    print("    max_attempts: number or null")
    print("    score_to_keep: 'highest' or 'latest'")
    print("    cooling_period: true/false (require wait between attempts)")
    print("    cooling_period_seconds: seconds (e.g., 3600 = 1 hour)")
    print()
    print("  Result view (what students see after submission):")
    print("    result_view_restricted: true/false")
    print("    display_items: true/false - Show questions")
    print("    display_item_response: true/false - Show student's answers")
    print("    display_item_response_correctness: true/false - Show right/wrong")
    print("    display_item_correct_answer: true/false - Show correct answers")
    print("    display_item_feedback: true/false - Show per-question feedback")
    print("    display_points_awarded: true/false - Show points earned")
    print("    display_points_possible: true/false - Show max points")
    print("    display_correct_answer_at: ISO date or null - When to reveal")
    print("    hide_correct_answer_at: ISO date or null - When to hide")
    print()
    print("SCORING:")
    print("  Use position numbers (1, 2, 3...) to reference correct answers.")
    print("  UUIDs are generated automatically during import.")
    print()
    print(json.dumps(EXAMPLE_FULL_NEW_QUIZ_JSON, indent=2))
    print()
    print()
    print("=" * 70)
    print("EXAMPLE JSON FOR CREATING CLASSIC QUIZZES")
    print("=" * 70)
    print()
    print("Classic Quizzes use different field names and units.")
    print()
    print("Settings (time_limit in MINUTES for Classic Quizzes):")
    print("  title, description (not instructions), quiz_type,")
    print("  time_limit, allowed_attempts, shuffle_questions,")
    print("  shuffle_answers, points_possible, published,")
    print("  due_at, unlock_at, lock_at, show_correct_answers,")
    print("  one_question_at_a_time, cant_go_back, access_code")
    print()
    print("quiz_type values: assignment, practice_quiz, graded_survey, survey")
    print("answer_weight: 100 = correct, 0 = incorrect")
    print()
    print(json.dumps(EXAMPLE_FULL_CLASSIC_QUIZ_JSON, indent=2))


def items_add_command(config, canvas, args):
    """Adds questions to a quiz from a JSON file"""
    # Handle --example flag first (doesn't require course/assignment/file)
    if getattr(args, "example", False):
        print_example_json()
        return

    # Validate required arguments when not using --example
    if not getattr(args, "course", None):
        canvaslms.cli.err(1, "Please specify -c/--course or use --example")
    if not getattr(args, "assignment", None):
        canvaslms.cli.err(1, "Please specify -a/--assignment or use --example")
    if not getattr(args, "file", None):
        canvaslms.cli.err(1, "Please specify -f/--file or use --example")

    # Find the quiz
    course_list = courses.process_course_option(canvas, args)
    quiz_list = list(filter_quizzes(course_list, args.assignment))

    if not quiz_list:
        canvaslms.cli.err(1, f"No quiz found matching: {args.assignment}")

    quiz = quiz_list[0]

    # Read questions from file
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        canvaslms.cli.err(1, f"File not found: {args.file}")
    except json.JSONDecodeError as e:
        canvaslms.cli.err(1, f"Invalid JSON in {args.file}: {e}")

    # Add items based on quiz type
    if is_new_quiz(quiz):
        items = data.get("items", [])
        if not items:
            canvaslms.cli.err(1, "No 'items' array found in JSON file")
        success, failed = add_new_quiz_items(
            quiz.course, quiz.id, canvas._Canvas__requester, items
        )
    else:
        questions = data.get("questions", [])
        if not questions:
            canvaslms.cli.err(1, "No 'questions' array found in JSON file")
        success, failed = add_classic_questions(quiz, questions)

    print(f"Added {success} question(s), {failed} failed")


def add_new_quiz_items(course, assignment_id, requester, items):
    """Adds items to a New Quiz

    Args:
      course: Course object
      assignment_id: Quiz/assignment ID
      requester: Canvas API requester
      items: List of item dictionaries

    Returns:
      Tuple of (success_count, failed_count)
    """
    import requests as req_lib

    # Build the endpoint URL using the requester's new_quizzes_url
    endpoint_url = (
        f"{requester.new_quizzes_url}courses/{course.id}/quizzes/{assignment_id}/items"
    )

    success = 0
    failed = 0

    for i, item in enumerate(items, 1):
        try:
            # Ensure UUIDs are present in the entry
            entry = ensure_uuids_in_entry(item.get("entry", {}))

            # Build the request body as JSON
            body = {
                "item": {
                    "position": item.get("position", i),
                    "points_possible": item.get("points_possible", 1),
                    "entry_type": "Item",
                    "entry": entry,
                }
            }

            # Make the request using requests library with JSON body
            headers = {
                "Authorization": f"Bearer {requester.access_token}",
                "Content-Type": "application/json",
            }

            response = req_lib.post(endpoint_url, json=body, headers=headers)
            response.raise_for_status()

            print(f"  Added: {entry.get('title', f'Question {i}')}")
            success += 1
        except req_lib.exceptions.HTTPError as e:
            entry = item.get("entry", {})
            error_msg = e.response.text if e.response else str(e)
            print(
                f"  Failed: {entry.get('title', f'Question {i}')} - {error_msg}",
                file=sys.stderr,
            )
            failed += 1
        except Exception as e:
            entry = item.get("entry", {})
            print(
                f"  Failed: {entry.get('title', f'Question {i}')} - {e}",
                file=sys.stderr,
            )
            failed += 1

    return success, failed


def ensure_uuids_in_entry(entry):
    """Ensures all choices have UUIDs, generating fresh ones if missing

    This allows importing from cleaned exports or manually created JSON.
    When scoring_data contains position indices (from cleaned exports),
    they are mapped to the newly generated UUIDs.
    """
    import uuid
    import copy

    entry = copy.deepcopy(entry)
    interaction_data = entry.get("interaction_data", {})
    scoring_data = entry.get("scoring_data", {})
    interaction_type = entry.get("interaction_type_slug", "")

    # Handle choice-based questions (choice, multi-answer)
    if "choices" in interaction_data:
        position_to_uuid = {}  # position -> new_uuid
        new_choices = []

        for i, choice in enumerate(interaction_data["choices"]):
            # Handle both dict choices (choice, multi-answer) and string choices (ordering)
            if isinstance(choice, str):
                # Ordering questions have choices as plain UUIDs/strings
                # The string itself is the ID - keep it or generate new if invalid
                if choice and len(choice) > 10:  # Looks like a UUID
                    new_id = choice
                else:
                    new_id = str(uuid.uuid4())
                position_to_uuid[i + 1] = new_id
                new_choices.append(new_id)
            else:
                # Regular choice dict
                old_id = choice.get("id")
                position = choice.get("position", i + 1)

                # Generate new UUID if missing
                if not old_id:
                    new_id = str(uuid.uuid4())
                else:
                    new_id = old_id

                position_to_uuid[position] = new_id

                new_choice = dict(choice)
                new_choice["id"] = new_id
                new_choice["position"] = position
                new_choices.append(new_choice)

        interaction_data["choices"] = new_choices
        entry["interaction_data"] = interaction_data

        # Update scoring_data to use new UUIDs
        if scoring_data and "value" in scoring_data:
            value = scoring_data["value"]

            if interaction_type == "choice":
                # Single correct answer - could be position index or UUID
                if isinstance(value, int) and value in position_to_uuid:
                    scoring_data["value"] = position_to_uuid[value]
            elif interaction_type == "multi-answer":
                # Multiple correct answers - could be position indices or UUIDs
                if isinstance(value, list):
                    new_value = []
                    for v in value:
                        if isinstance(v, int) and v in position_to_uuid:
                            new_value.append(position_to_uuid[v])
                        else:
                            new_value.append(v)
                    scoring_data["value"] = new_value

            entry["scoring_data"] = scoring_data

    return entry


def add_classic_questions(quiz, questions):
    """Adds questions to a Classic Quiz

    Args:
      quiz: Quiz object
      questions: List of question dictionaries

    Returns:
      Tuple of (success_count, failed_count)
    """
    success = 0
    failed = 0

    for i, question in enumerate(questions, 1):
        try:
            quiz.create_question(question=question)
            print(f"  Added: {question.get('question_name', f'Question {i}')}")
            success += 1
        except Exception as e:
            print(
                f"  Failed: {question.get('question_name', f'Question {i}')} - {e}",
                file=sys.stderr,
            )
            failed += 1

    return success, failed


def items_edit_command(config, canvas, args):
    """Edits a question in a quiz"""
    if not args.position and not args.id:
        canvaslms.cli.err(1, "Please specify --position or --id")

    # Find the quiz
    course_list = courses.process_course_option(canvas, args)
    quiz_list = list(filter_quizzes(course_list, args.assignment))

    if not quiz_list:
        canvaslms.cli.err(1, f"No quiz found matching: {args.assignment}")

    quiz = quiz_list[0]

    # Read update data from file
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            update_data = json.load(f)
    except FileNotFoundError:
        canvaslms.cli.err(1, f"File not found: {args.file}")
    except json.JSONDecodeError as e:
        canvaslms.cli.err(1, f"Invalid JSON in {args.file}: {e}")

    # Find the item ID if position was given
    item_id = args.id
    if args.position and not item_id:
        if is_new_quiz(quiz):
            items = list_new_quiz_items(quiz.course, quiz.id, canvas._Canvas__requester)
        else:
            items = list_classic_questions(quiz)

        for item in items:
            if item.get("position") == args.position:
                item_id = str(item.get("id"))
                break

        if not item_id:
            canvaslms.cli.err(1, f"No question found at position {args.position}")

    # Update based on quiz type
    if is_new_quiz(quiz):
        result = update_new_quiz_item(
            quiz.course, quiz.id, item_id, canvas._Canvas__requester, update_data
        )
    else:
        result = update_classic_question(quiz, item_id, update_data)

    if result:
        print(f"Updated question {item_id}")
    else:
        canvaslms.cli.err(1, "Failed to update question")


def update_new_quiz_item(course, assignment_id, item_id, requester, update_data):
    """Updates an item in a New Quiz

    Args:
      course: Course object
      assignment_id: Quiz/assignment ID
      item_id: Item ID to update
      requester: Canvas API requester
      update_data: Dictionary of fields to update

    Returns:
      True on success, False on failure
    """
    endpoint = f"courses/{course.id}/quizzes/{assignment_id}/items/{item_id}"

    params = {}
    for key, value in update_data.items():
        if key == "entry":
            for entry_key, entry_value in value.items():
                if isinstance(entry_value, dict):
                    params[f"item[entry][{entry_key}]"] = json.dumps(entry_value)
                else:
                    params[f"item[entry][{entry_key}]"] = entry_value
        elif isinstance(value, dict):
            params[f"item[{key}]"] = json.dumps(value)
        else:
            params[f"item[{key}]"] = value

    try:
        requester.request(
            method="PATCH", endpoint=endpoint, _url="new_quizzes", **params
        )
        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to update New Quiz item: {e}")
        return False


def update_classic_question(quiz, question_id, update_data):
    """Updates a question in a Classic Quiz

    Args:
      quiz: Quiz object
      question_id: Question ID to update
      update_data: Dictionary of fields to update

    Returns:
      True on success, False on failure
    """
    try:
        question = quiz.get_question(question_id)
        question.edit(question=update_data)
        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to update Classic Quiz question: {e}")
        return False


def items_delete_command(config, canvas, args):
    """Deletes a question from a quiz"""
    if not args.position and not args.id:
        canvaslms.cli.err(1, "Please specify --position or --id")

    # Find the quiz
    course_list = courses.process_course_option(canvas, args)
    quiz_list = list(filter_quizzes(course_list, args.assignment))

    if not quiz_list:
        canvaslms.cli.err(1, f"No quiz found matching: {args.assignment}")

    quiz = quiz_list[0]

    # Find the item ID if position was given
    item_id = args.id
    item_title = None
    if args.position and not item_id:
        if is_new_quiz(quiz):
            items = list_new_quiz_items(quiz.course, quiz.id, canvas._Canvas__requester)
        else:
            items = list_classic_questions(quiz)

        for item in items:
            if item.get("position") == args.position:
                item_id = str(item.get("id"))
                item_title = item.get("title")
                break

        if not item_id:
            canvaslms.cli.err(1, f"No question found at position {args.position}")

    # Confirm deletion
    if not args.force:
        display = item_title or f"ID {item_id}"
        print(f"About to delete question: {display}")
        try:
            confirm = input("Type 'yes' to confirm: ")
            if confirm.lower() != "yes":
                print("Cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return

    # Delete based on quiz type
    if is_new_quiz(quiz):
        result = delete_new_quiz_item(
            quiz.course, quiz.id, item_id, canvas._Canvas__requester
        )
    else:
        result = delete_classic_question(quiz, item_id)

    if result:
        print(f"Deleted question {item_id}")
    else:
        canvaslms.cli.err(1, "Failed to delete question")


def delete_new_quiz_item(course, assignment_id, item_id, requester):
    """Deletes an item from a New Quiz

    Args:
      course: Course object
      assignment_id: Quiz/assignment ID
      item_id: Item ID to delete
      requester: Canvas API requester

    Returns:
      True on success, False on failure
    """
    endpoint = f"courses/{course.id}/quizzes/{assignment_id}/items/{item_id}"

    try:
        requester.request(method="DELETE", endpoint=endpoint, _url="new_quizzes")
        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to delete New Quiz item: {e}")
        return False


def delete_classic_question(quiz, question_id):
    """Deletes a question from a Classic Quiz

    Args:
      quiz: Quiz object
      question_id: Question ID to delete

    Returns:
      True on success, False on failure
    """
    try:
        question = quiz.get_question(question_id)
        question.delete()
        return True
    except Exception as e:
        canvaslms.cli.warn(f"Failed to delete Classic Quiz question: {e}")
        return False


def items_export_command(config, canvas, args):
    """Exports all questions from a quiz to JSON"""
    # Find the quiz
    course_list = courses.process_course_option(canvas, args)
    quiz_list = list(filter_quizzes(course_list, args.assignment))

    if not quiz_list:
        canvaslms.cli.err(1, f"No quiz found matching: {args.assignment}")

    quiz = quiz_list[0]
    requester = canvas._Canvas__requester
    include_banks = args.include_banks and not args.no_banks

    # Export based on quiz type
    if is_new_quiz(quiz):
        export = export_new_quiz_items(quiz, requester, include_banks=include_banks)
        if getattr(args, "importable", False):
            export = clean_for_import(export, quiz_type="new_quiz")
    else:
        export = export_classic_questions(quiz)
        if getattr(args, "importable", False):
            export = clean_for_import(export, quiz_type="classic")

    # Output as JSON
    print(json.dumps(export, indent=2, ensure_ascii=False))


def clean_for_import(export, quiz_type="new_quiz"):
    """Cleans export data to produce import-ready JSON

    Removes metadata fields and UUIDs that should be regenerated on import.

    Args:
      export: Export dictionary from export_new_quiz_items or export_classic_questions
      quiz_type: Either 'new_quiz' or 'classic'

    Returns:
      Clean dictionary ready for use with items add command
    """
    if quiz_type == "new_quiz":
        return clean_new_quiz_for_import(export)
    else:
        return clean_classic_quiz_for_import(export)


def clean_new_quiz_for_import(export):
    """Cleans New Quiz export for import"""
    clean_items = []

    for item in export.get("items", []):
        # Skip bank references (can't import these directly)
        if "bank_reference" in item:
            continue

        entry = item.get("entry", {})
        if not entry:
            continue

        # Clean the entry
        clean_entry = {}
        # Keep essential fields
        for key in [
            "title",
            "item_body",
            "interaction_type_slug",
            "scoring_algorithm",
            "properties",
        ]:
            if key in entry:
                clean_entry[key] = entry[key]

        # Get original interaction_data before cleaning (need UUIDs for mapping)
        original_interaction_data = entry.get("interaction_data", {})

        # Clean interaction_data - remove UUIDs from choices
        if original_interaction_data:
            clean_entry["interaction_data"] = clean_interaction_data(
                original_interaction_data
            )

        # Update scoring_data to use position-based references
        # Pass original interaction_data to build UUID->position mapping
        if "scoring_data" in entry:
            clean_entry["scoring_data"] = clean_scoring_data(
                entry["scoring_data"],
                original_interaction_data,
                entry.get("interaction_type_slug", ""),
            )

        clean_items.append(
            {
                "position": item.get("position"),
                "points_possible": item.get("points_possible"),
                "entry": clean_entry,
            }
        )

    return {"items": clean_items}


def clean_interaction_data(interaction_data):
    """Removes UUIDs from interaction_data choices"""
    if not interaction_data:
        return interaction_data

    clean = dict(interaction_data)

    # Handle choices array (multiple choice, multi-answer)
    # Choices are dicts with id, position, item_body
    if "choices" in clean:
        clean_choices = []
        for i, choice in enumerate(clean["choices"]):
            # Skip if choice is not a dict (shouldn't happen, but be safe)
            if not isinstance(choice, dict):
                clean_choices.append(choice)
                continue
            clean_choice = {"position": choice.get("position", i + 1)}
            if "item_body" in choice:
                clean_choice["item_body"] = choice["item_body"]
            clean_choices.append(clean_choice)
        clean["choices"] = clean_choices

    # Handle questions array (matching questions)
    # Questions are dicts with id, item_body - we keep item_body, drop id
    if "questions" in clean:
        clean_questions = []
        for i, question in enumerate(clean["questions"]):
            if not isinstance(question, dict):
                clean_questions.append(question)
                continue
            clean_q = {}
            if "item_body" in question:
                clean_q["item_body"] = question["item_body"]
            clean_questions.append(clean_q)
        clean["questions"] = clean_questions

    # 'answers' is a list of strings (matching questions) - keep as-is

    return clean


def clean_scoring_data(scoring_data, original_interaction_data, interaction_type):
    """Cleans scoring_data - converts UUID references to position indices

    Since we remove UUIDs from choices during export, we need to convert
    scoring_data references from UUIDs to position indices. When importing,
    fresh UUIDs are generated and the position indices are mapped back.
    """
    if not scoring_data:
        return scoring_data

    # For types that use UUID references in scoring_data.value,
    # we convert to position indices
    if interaction_type in ("choice", "multi-answer"):
        value = scoring_data.get("value")
        if value is None:
            return scoring_data

        # Build UUID to position mapping from original choices
        uuid_to_position = {}
        choices = original_interaction_data.get("choices", [])
        for i, choice in enumerate(choices):
            choice_id = choice.get("id")
            if choice_id:
                uuid_to_position[choice_id] = choice.get("position", i + 1)

        # Convert value(s) from UUIDs to position indices
        if interaction_type == "choice":
            # Single correct answer
            if value in uuid_to_position:
                return {"value": uuid_to_position[value]}
            return scoring_data
        elif interaction_type == "multi-answer":
            # Multiple correct answers
            if isinstance(value, list):
                new_value = []
                for v in value:
                    if v in uuid_to_position:
                        new_value.append(uuid_to_position[v])
                    else:
                        new_value.append(v)
                return {"value": new_value}

    return scoring_data


def clean_classic_quiz_for_import(export):
    """Cleans Classic Quiz export for import"""
    clean_questions = []

    for q in export.get("questions", []):
        clean_q = {}
        # Keep essential fields, skip 'id'
        for key in [
            "question_name",
            "question_text",
            "question_type",
            "points_possible",
            "answers",
            "correct_comments",
            "incorrect_comments",
            "neutral_comments",
            "matching_answer_incorrect_matches",
            "formulas",
            "variables",
            "formula_decimal_places",
            "answer_tolerance",
        ]:
            if key in q:
                clean_q[key] = q[key]
        clean_questions.append(clean_q)

    return {"questions": clean_questions}


def get_cached_quiz_items(quiz):
    """Returns cached quiz items if available and fresh, else None"""
    if not hasattr(quiz, "_items_cache"):
        return None

    export_data, fetch_time = quiz._items_cache
    age = datetime.now() - fetch_time
    if age > timedelta(minutes=QUIZ_ITEMS_CACHE_TTL_MINUTES):
        logger.info(
            f"Quiz items cache expired for quiz {quiz.id} "
            f"(age: {age.total_seconds()/60:.1f} min, "
            f"TTL: {QUIZ_ITEMS_CACHE_TTL_MINUTES} min)"
        )
        quiz._items_cache = None
        return None

    logger.info(
        f"Quiz items cache hit for quiz {quiz.id} " f"(age: {age.total_seconds():.1f}s)"
    )
    return export_data


def cache_quiz_items(quiz, export_data):
    """Stores quiz items in the quiz's cache"""
    quiz._items_cache = (export_data, datetime.now())
    logger.debug(
        f"Cached quiz items for quiz {quiz.id} "
        f"({export_data.get('item_count', 0)} items)"
    )


def invalidate_quiz_items_cache(quiz):
    """Removes items from the quiz's cache"""
    if hasattr(quiz, "_items_cache"):
        quiz._items_cache = None
        logger.debug(f"Invalidated quiz items cache for quiz {quiz.id}")


def export_new_quiz_items(quiz, requester, include_banks=True):
    """Exports items from a New Quiz

    Args:
      quiz: Quiz object (must have .id and .course attributes)
      requester: Canvas API requester
      include_banks: If True, expand Bank/BankEntry items to include bank questions

    Returns:
      Dictionary with quiz metadata and items
    """
    # Check cache first (only for include_banks=True, the common case)
    if include_banks:
        cached = get_cached_quiz_items(quiz)
        if cached is not None:
            return cached

    import datetime

    course = quiz.course
    assignment_id = quiz.id
    endpoint = f"courses/{course.id}/quizzes/{assignment_id}/items"

    try:
        response = requester.request(
            method="GET", endpoint=endpoint, _url="new_quizzes"
        )
        raw_items = response.json()
    except Exception as e:
        canvaslms.cli.warn(f"Failed to fetch New Quiz items: {e}")
        raw_items = []

    items = []
    banks = {}  # bank_id -> bank data (to avoid duplicate fetches)

    for item in raw_items:
        entry_type = item.get("entry_type", "Item")
        entry = item.get("entry", {})

        # Handle both 'Bank' and 'BankEntry' types - they reference item banks
        if entry_type in ("Bank", "BankEntry") and include_banks:
            # Check if the entry itself contains a question (embedded bank item)
            nested_entry_type = entry.get("entry_type")
            if nested_entry_type == "Item" and entry.get("entry"):
                # This BankEntry has an embedded question - extract it
                nested_entry = entry.get("entry", {})
                items.append(
                    {
                        "position": item.get("position"),
                        "id": item.get("id"),
                        "entry_type": "BankEntry (embedded)",
                        "points_possible": item.get("points_possible"),
                        "entry": nested_entry,
                        "source": "embedded_bank_item",
                    }
                )
            else:
                # This is a bank reference - try to fetch the bank's questions
                bank_info = extract_bank_info(item)
                if bank_info:
                    bank_id = bank_info.get("bank_id")
                    if bank_id and bank_id not in banks:
                        # Try to fetch bank items (may fail due to API limitations)
                        bank_items = get_bank_items(requester, bank_id)
                        banks[bank_id] = {
                            "bank_id": bank_id,
                            "title": bank_info.get("title", ""),
                            "sample_num": bank_info.get("sample_num"),
                            "entry_count": bank_info.get("entry_count"),
                            "questions": bank_items,
                        }
                    # Include the bank reference with metadata
                    items.append(
                        {
                            "position": item.get("position"),
                            "id": item.get("id"),
                            "entry_type": entry_type,
                            "points_possible": item.get("points_possible"),
                            "bank_reference": bank_info,
                        }
                    )
                else:
                    # Could not extract bank info, include as-is
                    items.append(
                        {
                            "position": item.get("position"),
                            "id": item.get("id"),
                            "entry_type": entry_type,
                            "points_possible": item.get("points_possible"),
                            "entry": entry,
                        }
                    )
        else:
            # Regular question item or stimulus
            items.append(
                {
                    "position": item.get("position"),
                    "id": item.get("id"),
                    "entry_type": entry_type,
                    "points_possible": item.get("points_possible"),
                    "entry": entry,
                }
            )

    export_data = {
        "quiz_type": "new_quiz",
        "course_id": course.id,
        "assignment_id": assignment_id,
        "export_date": datetime.datetime.now().isoformat(),
        "item_count": len(items),
        "bank_count": len(banks),
        "items": items,
        "banks": banks,
    }

    # Cache the result (only for include_banks=True)
    if include_banks:
        cache_quiz_items(quiz, export_data)

    return export_data


def extract_bank_info(item):
    """Extracts bank information from a Bank or BankEntry item

    Args:
      item: Quiz item dictionary with entry_type 'Bank' or 'BankEntry'

    Returns:
      Dictionary with bank_id, title, and sample_num, or None
    """
    entry = item.get("entry", {})
    properties = item.get("properties", {})

    # The bank ID might be in different locations depending on API version/type
    # Try multiple possible locations
    bank_id = (
        entry.get("id")
        or entry.get("bank_id")
        or item.get("bank_id")
        or
        # For some Bank entries, the item ID might reference the bank
        (item.get("id") if item.get("entry_type") == "Bank" else None)
    )

    # Entry count information (how many questions to pull)
    sample_num = properties.get("sample_num") if properties else None

    if not bank_id and not entry.get("title"):
        return None

    return {
        "bank_id": bank_id,
        "title": entry.get("title", ""),
        "sample_num": sample_num,
        "entry_count": entry.get("entry_count"),
        "item_entry_count": entry.get("item_entry_count"),
        "archived": entry.get("archived", False),
    }


def export_classic_questions(quiz):
    """Exports questions from a Classic Quiz

    Args:
      quiz: Quiz object

    Returns:
      Dictionary with quiz metadata and questions
    """
    import datetime

    try:
        questions = list(quiz.get_questions())
    except Exception as e:
        canvaslms.cli.warn(f"Failed to fetch Classic Quiz questions: {e}")
        questions = []

    items = []
    for q in questions:
        # Convert canvasapi object to dictionary
        item = {
            "id": q.id,
            "position": getattr(q, "position", None),
            "question_name": getattr(q, "question_name", ""),
            "question_text": getattr(q, "question_text", ""),
            "question_type": getattr(q, "question_type", ""),
            "points_possible": getattr(q, "points_possible", 0),
            "answers": getattr(q, "answers", []),
        }
        # Include additional fields if present
        for field in [
            "correct_comments",
            "incorrect_comments",
            "neutral_comments",
            "matching_answer_incorrect_matches",
            "formulas",
            "variables",
        ]:
            if hasattr(q, field):
                item[field] = getattr(q, field)
        items.append(item)

    return {
        "quiz_type": "classic",
        "quiz_id": quiz.id,
        "course_id": quiz.course_id if hasattr(quiz, "course_id") else None,
        "export_date": datetime.datetime.now().isoformat(),
        "question_count": len(items),
        "questions": items,
    }


def add_banks_export_command(subp):
    """Registers the banks export subcommand"""
    parser = subp.add_parser(
        "export",
        help="Export item bank questions to JSON",
        description="""Export all questions from an item bank to JSON format.

The bank ID is required because Canvas does not provide an API to list banks.
You can find bank IDs by examining quiz items that reference banks or through
the Canvas web interface.""",
    )
    parser.set_defaults(func=banks_export_command)

    parser.add_argument(
        "--bank-id",
        required=True,
        help="Item bank ID (required; find via Canvas UI or quiz items)",
    )


def banks_export_command(config, canvas, args):
    """Exports item bank questions to JSON"""
    requester = canvas._Canvas__requester
    bank_id = args.bank_id

    # Get bank items
    items = get_bank_items(requester, bank_id)

    if not items:
        canvaslms.cli.err(
            1,
            f"No items found in bank {bank_id} "
            "(bank may not exist or be inaccessible)",
        )

    # Build export structure
    import datetime

    export = {
        "bank_id": bank_id,
        "export_date": datetime.datetime.now().isoformat(),
        "question_count": len(items),
        "questions": items,
    }

    # Output as JSON
    print(json.dumps(export, indent=2, ensure_ascii=False))


def get_bank_items(requester, bank_id):
    """Fetches items from an item bank

    Args:
      requester: Canvas API requester
      bank_id: Item bank ID

    Returns:
      List of item dictionaries, or empty list if bank is inaccessible
    """
    endpoint = f"item_banks/{bank_id}/items"

    try:
        response = requester.request(
            method="GET", endpoint=endpoint, _url="new_quizzes"
        )
        return response.json()
    except Exception:
        # Item Banks API often isn't accessible - this is expected
        return []


def add_command(subp):
    """Adds the quizzes command with subcommands to argparse parser subp"""
    quizzes_parser = subp.add_parser(
        "quizzes",
        help="Quiz-related commands",
        description="Quiz-related commands for Canvas LMS",
    )

    quizzes_subp = quizzes_parser.add_subparsers(
        title="quizzes subcommands", dest="quizzes_command", required=True
    )

    add_list_command(quizzes_subp)
    add_analyse_command(quizzes_subp)
    add_view_command(quizzes_subp)
    add_create_command(quizzes_subp)
    add_edit_command(quizzes_subp)
    add_delete_command(quizzes_subp)
    add_export_command(quizzes_subp)
    add_items_command(quizzes_subp)
    add_banks_command(quizzes_subp)


def add_list_command(subp):
    """Adds the quizzes list subcommand to argparse parser subp"""
    list_parser = subp.add_parser(
        "list",
        help="List all quizzes in a course",
        description="""Lists all quizzes (including Classic Quizzes, New Quizzes, and surveys)
  in a course. Output in CSV format with quiz ID, title, type, and whether it's published.""",
    )

    list_parser.set_defaults(func=list_command)

    try:
        courses.add_course_option(list_parser, required=True)
    except argparse.ArgumentError:
        pass


def add_analyse_command(subp):
    """Adds the quizzes analyse subcommand to argparse parser subp"""
    analyse_parser = subp.add_parser(
        "analyse",
        help="Summarize quiz/survey evaluation data",
        description="""Summarizes Canvas quiz or survey evaluation data.
      
  Can either fetch quiz data from Canvas or analyze a downloaded CSV file.
  Provides statistical summaries for quantitative data and AI-generated 
  summaries for qualitative (free text) responses.""",
    )

    analyse_parser.set_defaults(func=analyse_command)

    analyse_parser.add_argument(
        "--csv", "-f", help="Path to CSV file downloaded from Canvas", type=str
    )

    analyse_parser.add_argument(
        "--format",
        "-F",
        help="Output format: markdown (default) or latex",
        choices=["markdown", "latex"],
        default="markdown",
    )

    analyse_parser.add_argument(
        "--standalone",
        help="Generate standalone LaTeX document with preamble (latex format only)",
        action="store_true",
        default=False,
    )

    analyse_parser.add_argument(
        "--use-minted",
        help="Use minted package for syntax-highlighted code (requires pygments). "
        "Optionally specify language (default: python). Examples: --use-minted, --use-minted bash",
        nargs="?",
        const="python",
        default=False,
        metavar="LANG",
    )

    # Check if llm package is available
    try:
        import llm

        HAS_LLM = True
    except ImportError:
        HAS_LLM = False

    if HAS_LLM:
        analyse_parser.add_argument(
            "--ai",
            dest="ai",
            action="store_true",
            default=False,
            help="Enable AI-generated summaries. These use the `llm` package "
            "on PyPI and require configuration. Particularly you need to "
            "configure a default model and set up API keys. "
            "See https://pypi.org/project/llm/ for details.",
        )

    analyse_parser.add_argument(
        "--no-ai",
        dest="ai",
        action="store_false",
        default=True,
        help="Disable AI-generated summaries"
        + (
            ""
            if HAS_LLM
            else " (--ai option not available: install with "
            "'pipx install canvaslms[llm]' to enable AI summaries)"
        ),
    )

    try:
        courses.add_course_option(analyse_parser, required=False)
    except argparse.ArgumentError:
        pass

    try:
        assignments.add_assignment_option(
            analyse_parser, ungraded=False, required=False
        )
    except argparse.ArgumentError:
        pass


def add_create_command(subp):
    """Adds the quizzes create subcommand to argparse parser subp"""
    create_parser = subp.add_parser(
        "create",
        help="Create a new quiz",
        description="""Create a new quiz in a course from a JSON file.

  Use --example to see the full JSON format with all supported attributes.
  The JSON can include both quiz settings and questions, enabling a complete
  export/create workflow:

    canvaslms quizzes export -c "Source Course" -a "Quiz" -I > quiz.json
    canvaslms quizzes create -c "Target Course" -f quiz.json

  JSON STRUCTURE:
    {
      "quiz_type": "new" or "classic",
      "settings": { ... quiz settings ... },
      "items": [ ... ] (New Quizzes) or "questions": [ ... ] (Classic)
    }

  SETTINGS FOR NEW QUIZZES (time_limit in seconds):
    title, instructions, time_limit, allowed_attempts, shuffle_questions,
    shuffle_answers, points_possible, due_at, unlock_at, lock_at

  ADVANCED SETTINGS FOR NEW QUIZZES (in settings.quiz_settings):
    multiple_attempts: attempt_limit, score_to_keep, cooling_period_seconds
    result_view_settings: display_item_correct_answer, display_item_feedback, etc.

  SETTINGS FOR CLASSIC QUIZZES (time_limit in minutes):
    title, description, quiz_type (assignment/practice_quiz/graded_survey/survey),
    time_limit, allowed_attempts, shuffle_questions, shuffle_answers,
    points_possible, published, due_at, unlock_at, lock_at,
    show_correct_answers, one_question_at_a_time, cant_go_back, access_code

  For question format details, see: canvaslms quizzes items add --example""",
    )

    create_parser.set_defaults(func=create_command)

    try:
        courses.add_course_option(create_parser, required=False)
    except argparse.ArgumentError:
        pass

    create_parser.add_argument(
        "-f",
        "--file",
        help="JSON file containing quiz settings and optionally questions",
        type=str,
    )

    create_parser.add_argument(
        "--type",
        choices=["new", "classic"],
        default=None,
        help="Quiz type: 'new' (New Quizzes) or 'classic' (Classic Quizzes). "
        "Auto-detected from JSON if not specified. Default: new",
    )

    create_parser.add_argument(
        "--title", "-t", help="Quiz title (overrides title in JSON file)"
    )

    create_parser.add_argument(
        "--example",
        "-E",
        action="store_true",
        help="Print example JSON for creating quizzes and exit",
    )


def add_edit_command(subp):
    """Adds the quizzes edit subcommand to argparse parser subp"""
    edit_parser = subp.add_parser(
        "edit",
        help="Edit quiz settings and instructions",
        description="""Edit an existing quiz's settings and instructions.

  INTERACTIVE MODE (default):
    Opens your editor with YAML front matter (settings) and Markdown body
    (instructions). After editing, shows a preview and asks whether to
    accept, edit further, or discard the changes.

    Use --full-json to edit as full JSON (same format as 'quizzes export -I').
    This allows editing all quiz_settings including multiple_attempts and
    result_view_settings.

  FILE MODE (-f):
    Reads content from a file. Format is auto-detected from extension:
      .json      - Full JSON format (settings + optional items)
      .yaml/.yml - Full YAML format (same structure as JSON)
      .md        - YAML front matter + Markdown body

    The JSON/YAML format is the same as 'quizzes export' output, enabling
    a round-trip workflow: export, modify, edit.

  ITEM HANDLING:
    By default, items/questions in the file are ignored to protect student
    submissions. Use --replace-items to replace all questions (with confirmation
    if submissions exist).

  The quiz type (New or Classic) is auto-detected.""",
    )

    edit_parser.set_defaults(func=edit_command)

    try:
        courses.add_course_option(edit_parser, required=True)
    except argparse.ArgumentError:
        pass

    add_quiz_option(edit_parser, required=True)

    edit_parser.add_argument(
        "-f",
        "--file",
        help="Read content from file (format auto-detected: .json, .yaml, .yml, .md)",
        type=str,
        required=False,
    )

    edit_parser.add_argument(
        "--html",
        action="store_true",
        help="Edit raw HTML instead of converting to Markdown",
    )

    edit_parser.add_argument(
        "--full-json",
        action="store_true",
        help="Interactive mode: edit as full JSON instead of YAML+Markdown. "
        "Allows editing all quiz_settings including multiple_attempts.",
    )

    edit_parser.add_argument(
        "--replace-items",
        action="store_true",
        help="Replace existing questions with items from file. "
        "Default: ignore items to preserve student attempts. "
        "Will prompt for confirmation if quiz has submissions.",
    )


def add_delete_command(subp):
    """Adds the quizzes delete subcommand to argparse parser subp"""
    delete_parser = subp.add_parser(
        "delete",
        help="Delete a quiz",
        description="""Delete a quiz from a course. Requires confirmation
  unless --force is specified.""",
    )

    delete_parser.set_defaults(func=delete_command)

    try:
        courses.add_course_option(delete_parser, required=True)
    except argparse.ArgumentError:
        pass

    delete_parser.add_argument(
        "-a",
        "--assignment",
        required=True,
        help="Regex matching quiz title or Canvas ID",
    )

    delete_parser.add_argument(
        "--force", "-F", action="store_true", help="Skip confirmation prompt"
    )


def add_export_command(subp):
    """Adds the quizzes export subcommand to argparse parser subp"""
    export_parser = subp.add_parser(
        "export",
        help="Export a complete quiz to JSON",
        description="""Export a quiz (settings and questions) to JSON format.

  The output can be directly used with 'quizzes create' to duplicate a quiz
  in another course or create a backup.

  WORKFLOW EXAMPLE:
    # Export quiz from source course
    canvaslms quizzes export -c "Course A" -a "Quiz Name" -I > quiz.json

    # Create identical quiz in target course
    canvaslms quizzes create -c "Course B" -f quiz.json

  OUTPUT FORMAT:
    {
      "quiz_type": "new" or "classic",
      "settings": { ... quiz settings ... },
      "items": [ ... ] (New Quizzes) or "questions": [ ... ] (Classic)
    }

  Use --importable/-I for clean JSON ready for 'quizzes create'.
  Without -I, the output includes Canvas IDs and metadata for reference.""",
    )

    export_parser.set_defaults(func=export_command)

    try:
        courses.add_course_option(export_parser, required=True)
    except argparse.ArgumentError:
        pass

    export_parser.add_argument(
        "-a",
        "--assignment",
        required=True,
        help="Regex matching quiz title or Canvas ID",
    )

    export_parser.add_argument(
        "--importable",
        "-I",
        action="store_true",
        help="Output clean JSON directly usable with 'quizzes create' command",
    )

    export_parser.add_argument(
        "--include-banks",
        "-B",
        action="store_true",
        default=True,
        help="Include questions from referenced item banks (default: true)",
    )

    export_parser.add_argument(
        "--no-banks", action="store_true", help="Don't expand item bank references"
    )


def add_items_command(subp):
    """Adds the quizzes items subcommand group to argparse parser subp"""
    items_parser = subp.add_parser(
        "items",
        help="Manage quiz questions/items",
        description="Manage quiz questions (items) - list, add, edit, delete, or export",
    )

    items_subp = items_parser.add_subparsers(
        title="items subcommands", dest="items_command", required=True
    )

    add_items_list_command(items_subp)
    add_items_add_command(items_subp)
    add_items_edit_command(items_subp)
    add_items_delete_command(items_subp)
    add_items_export_command(items_subp)


def add_banks_command(subp):
    """Adds the quizzes banks subcommand group to argparse parser subp"""
    banks_parser = subp.add_parser(
        "banks",
        help="Export item banks (limited API support)",
        description="""Export item bank questions to JSON.

  IMPORTANT: Canvas does not provide an API to list item banks. You must
  provide the bank ID directly using --bank-id. Bank IDs can be found by:
  1. Examining quiz items that reference banks (entry_type: BankEntry)
  2. Using the Canvas web interface (in the URL when editing a bank)

  Creating and modifying banks must be done through the Canvas web interface.""",
    )

    banks_subp = banks_parser.add_subparsers(
        title="banks subcommands", dest="banks_command", required=True
    )

    add_banks_export_command(banks_subp)
