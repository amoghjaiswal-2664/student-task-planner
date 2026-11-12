from planner.models import Source
# from planner.sources.whatsapp import parse_whatsapp_export
from datetime import datetime
from planner.sources.whatsapp import IST, load_whatsapp_file, parse_whatsapp_export

GROUP = "CSE-3A"

CHAT = (
    "[11/3/26, 9:00:00 AM] Messages and calls are end-to-end encrypted. No one outside of this chat can read them.\n"
    "[11/4/26, 4:19:38 PM] +91 90000 00001: following students not submitted quiz\n"
    "[11/4/26, 4:21:56 PM] +91 90000 00001: <image omitted>\n"
    "[11/5/26, 8:55:03 AM] +91 90000 00002: Today is last date for assignment submission.\n"
    "You can upload assignment on Pod today till 9:00 pm.\n"
    "[11/5/26, 11:11:50 AM] +91 90000 00001: [Forwarded] <image omitted>\n"
    "[11/5/26, 11:37:26 AM] +91 90000 00001: Start Time\n"
    "2026-11-04 15:00\n"
    "End Time\n"
    "2026-11-06 23:00\n"
    "[11/5/26, 12:09:44 PM] +91 90000 00003: Test-2 on CodeTantra: attempt today\n"
)


def parse(text=CHAT, group=GROUP):
    return parse_whatsapp_export(text, group)


def test_skips_system_lines_and_media():
    assert len(parse()) == 4


def test_basic_fields():
    m = parse()[0]
    assert m.source == Source.WHATSAPP
    assert m.sender == "+91 90000 00001"
    assert m.text == "following students not submitted quiz"
    assert m.timestamp.isoformat() == "2026-11-04T16:19:38+05:30"
    assert m.source_ref == "CSE-3A:line-2"


def test_continuation_lines_join_the_previous_message():
    m = parse()[1]
    assert m.text == "Today is last date for assignment submission.\nYou can upload assignment on Pod today till 9:00 pm."
    assert m.source_ref == "CSE-3A:line-4"


def test_multiline_block_stays_one_message():
    m = parse()[2]
    assert m.text == "Start Time\n2026-11-04 15:00\nEnd Time\n2026-11-06 23:00"


def test_colon_inside_message_text_is_kept():
    m = parse()[3]
    assert m.sender == "+91 90000 00003"
    assert m.text == "Test-2 on CodeTantra: attempt today"


def test_twelve_hour_clock_edges():
    text = (
        "[11/5/26, 12:05:00 AM] A: just after midnight\n"
        "[11/5/26, 12:05:00 PM] A: just after noon\n"
    )
    msgs = parse(text)
    assert msgs[0].timestamp.isoformat() == "2026-11-05T00:05:00+05:30"
    assert msgs[1].timestamp.isoformat() == "2026-11-05T12:05:00+05:30"


def test_invisible_characters_are_cleaned():
    text = "\u200e[11/5/26, 4:05:00\u202fPM] A: hello there\n"
    msg = parse(text)[0]
    assert msg.timestamp.isoformat() == "2026-11-05T16:05:00+05:30"
    assert msg.text == "hello there"


def test_ids_are_stable_across_runs():
    assert [m.id for m in parse()] == [m.id for m in parse()]


def test_ids_are_unique_within_a_chat():
    ids = [m.id for m in parse()]
    assert len(set(ids)) == len(ids)


def test_same_message_in_different_groups_gets_different_ids():
    assert parse(group="CSE-3A")[0].id != parse(group="CSE-batch")[0].id


def test_ids_ignore_line_numbers():
    shifted = "[11/1/26, 9:00:00 AM] A: hi\n" + CHAT
    assert parse(shifted)[1].id == parse()[0].id


def test_empty_input():
    assert parse("") == []

def test_since_filters_older_messages(tmp_path):
    f = tmp_path / "chat.txt"
    f.write_text(CHAT, encoding="utf-8")
    since = datetime(2026, 11, 5, tzinfo=IST)
    msgs = load_whatsapp_file(str(f), GROUP, since=since)
    assert len(msgs) == 3
    assert all(m.timestamp >= since for m in msgs)