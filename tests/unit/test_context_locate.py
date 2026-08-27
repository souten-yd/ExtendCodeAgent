"""Finding where a described change goes, before anyone names a file."""

from __future__ import annotations

from extendcodeagent.context.locate import described_names, files_for


def search_for(index: dict[str, set[str]]):
    return lambda name: frozenset(index.get(name, set()))


def test_a_backticked_name_is_what_the_description_marks_out() -> None:
    assert described_names("`template_filter` can be used without parentheses") == (
        "template_filter",
    )


def test_a_config_key_counts_even_without_backticks() -> None:
    assert described_names("Added MAX_FORM_PARTS config") == ("MAX_FORM_PARTS",)


def test_a_qualifier_is_dropped_because_files_hold_the_bare_name() -> None:
    assert described_names("`Request.trusted_hosts` is checked") == ("trusted_hosts",)


def test_prose_is_not_a_name() -> None:
    assert described_names("Fix the session so it is marked as accessed") == ()


def test_short_names_are_left_out_as_too_common_to_locate_with() -> None:
    assert described_names("`app` and `g` are documented") == ()


def test_the_files_holding_the_named_things_are_returned() -> None:
    index = {"template_filter": {"src/app.py", "src/blueprints.py"}}
    found = files_for("`template_filter` without parentheses", search_for(index))
    assert found == ("src/app.py", "src/blueprints.py")


def test_a_name_the_project_does_not_have_yet_locates_nothing() -> None:
    # `TRUSTED_HOSTS` is what the change introduces; no search finds what is not there.
    assert files_for("Added `TRUSTED_HOSTS` config", search_for({})) == ()


def test_a_description_naming_nothing_locates_nothing() -> None:
    assert files_for("Fix a bug in the session", search_for({"x": {"a.py"}})) == ()


def test_matching_half_the_repository_is_not_a_location() -> None:
    index = {"handler": {f"src/m{n}.py" for n in range(20)}}
    assert files_for("`handler` is renamed", search_for(index)) == ()


def test_the_caller_sets_the_bound() -> None:
    index = {"handler": {"a.py", "b.py", "c.py"}}
    assert files_for("`handler` is renamed", search_for(index), max_files=2) == ()
    assert len(files_for("`handler` is renamed", search_for(index), max_files=3)) == 3


def test_a_new_name_is_looked_for_where_its_siblings_live() -> None:
    """`SESSION_COOKIE_PARTITIONED` does not exist yet; its family does."""

    index = {"SESSION_COOKIE": {"src/sessions.py", "src/app.py"}}
    found = files_for("Added `SESSION_COOKIE_PARTITIONED` config", search_for(index))
    assert found == ("src/app.py", "src/sessions.py")


def test_the_family_is_only_tried_when_the_name_itself_is_absent() -> None:
    # A stem matches far more, so an exact hit is never widened.
    index = {
        "SESSION_COOKIE_SECURE": {"src/sessions.py"},
        "SESSION_COOKIE": {"src/a.py", "src/b.py", "src/c.py"},
    }
    assert files_for("`SESSION_COOKIE_SECURE` is read", search_for(index)) == ("src/sessions.py",)


def test_a_stem_too_short_to_mean_anything_is_not_used() -> None:
    assert files_for("Added `X_THING` config", search_for({"X": {"a.py"}})) == ()
