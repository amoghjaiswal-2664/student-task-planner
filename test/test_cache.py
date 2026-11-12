import sqlite3
from planner.intelligence.cache import make_cached_llm

GOOD = '{"events": []}'


def make_llm(*replies):
    calls = []

    def fake(prompt, system=None):
        calls.append(prompt)
        return replies[min(len(calls) - 1, len(replies) - 1)]

    fake.calls = calls
    return fake


def make_cache(llm):
    return make_cached_llm(sqlite3.connect(":memory:"), llm=llm)


def test_second_identical_call_is_served_from_cache():
    llm = make_llm(GOOD)
    cached = make_cache(llm)
    assert cached("a", "sys") == GOOD
    assert cached("a", "sys") == GOOD
    assert len(llm.calls) == 1


def test_different_prompt_calls_the_llm_again():
    llm = make_llm(GOOD)
    cached = make_cache(llm)
    cached("a", "sys")
    cached("b", "sys")
    assert len(llm.calls) == 2


def test_changed_system_prompt_does_not_reuse_old_reply():
    llm = make_llm(GOOD)
    cached = make_cache(llm)
    cached("a", "sys v1")
    cached("a", "sys v2")
    assert len(llm.calls) == 2


def test_garbage_replies_are_not_cached():
    llm = make_llm("sorry, no", GOOD)
    cached = make_cache(llm)
    assert cached("a", "sys") == "sorry, no"
    assert cached("a", "sys") == GOOD
    assert len(llm.calls) == 2