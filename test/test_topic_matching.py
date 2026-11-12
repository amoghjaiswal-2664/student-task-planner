from planner.models import Task, TaskEvent, DecisionAction
from planner.intelligence.matching import topic_words, find_candidates, decide, expand_aliases


def task(id, title, task_type="other", subject=None):
    return Task(id=id, title=title, task_type=task_type, subject=subject)


def event(title, task_type="other", subject=None):
    return TaskEvent(
        action="create", title=title, task_type=task_type, subject=subject,
        source_message_id="s", evidence="x",
    )


def test_topic_words_drop_numbers_and_generic_words():
    assert topic_words("DBMS Assignment 2") == {"dbms"}
    assert topic_words("Digital Electronics Experiment 1") == {"digital", "electronics"}


def test_topic_words_empty_when_title_is_generic():
    assert topic_words("Assignment 2") == set()
    assert topic_words("quiz") == set()


def test_unrelated_titles_of_the_same_type_do_not_match():
    tasks = [task(1, "Soft Skills Faculty Feedback Form")]
    assert find_candidates(event("Digital Electronics Experiment 1"), tasks) == []


def test_unrelated_quizzes_do_not_match():
    tasks = [task(1, "DE Quiz 1", "quiz")]
    assert find_candidates(event("Data structure quiz", "quiz"), tasks) == []


def test_new_unrelated_task_is_created_not_merged():
    tasks = [task(1, "Soft Skills Faculty Feedback Form")]
    assert decide(event("Course Registration Slip"), tasks).action == DecisionAction.CREATE


def test_shared_topic_word_still_matches():
    tasks = [task(1, "Digital Electronics Quiz", "quiz")]
    found = find_candidates(event("Digital Electronics Quiz 1", "quiz"), tasks)
    assert [t.id for t in found] == [1]


def test_generic_event_title_still_matches_any_topic():
    tasks = [task(1, "DBMS Assignment 2", "assignment", "DBMS")]
    found = find_candidates(event("Assignment 2", "assignment"), tasks)
    assert [t.id for t in found] == [1]

def test_expand_aliases():
    assert expand_aliases("DE Quiz 1") == "digital electronics quiz 1"
    assert expand_aliases("DBMS Assignment") == "dbms assignment"


def test_de_and_digital_electronics_are_the_same_topic():
    assert topic_words("DE Quiz 1") == topic_words("Digital Electronics Quiz")


def test_different_feedback_forms_do_not_match():
    tasks = [task(1, "Soft Skills Faculty Feedback Form")]
    assert find_candidates(event("CodeTantra Feedback Form"), tasks) == []


def test_shared_faculty_word_still_matches():
    tasks = [task(1, "Soft Skills Faculty Feedback Form")]
    assert [t.id for t in find_candidates(event("Faculty Feedback Form"), tasks)] == [1]


def test_abbreviated_subject_does_not_conflict():
    tasks = [task(1, "Digital Electronics Quiz 1", "quiz", "Digital Electronics")]
    found = find_candidates(event("DE Quiz 1", "quiz", "DE"), tasks)
    assert [t.id for t in found] == [1]