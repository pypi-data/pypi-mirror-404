# tests/c9m/unit/common/utils/test_args_base.py

import os
from argparse import ArgumentTypeError

import pytest

from evakit.args_base import (
    ArgsBase,
    arg_env_consistent_bool,
    env_to_bool,
    move_arg_from_to,
    str2bool,
)
from evakit.python_tricks import unfreeze_dataclass
from evakit.singleton import reset_singleton

# ------------------------------------------------------------------------------
# Test ArgsBase subclass
# ------------------------------------------------------------------------------


class DummyArgs(ArgsBase):
    flag: bool = False
    ints: list[int] = []
    floats: list[float] = []
    strs: list[str] = []
    bools: list[bool] = []
    int_set: set[int] = set()
    tup_fixed: tuple[int, str] = (0, "")
    tup_var: tuple[int, ...] = ()

    old: str = ""
    new: str = ""

    test: bool = False

    def _merge_args(self) -> None:
        move_arg_from_to(
            self,
            "old",
            "new",
            self.new,
            print_deprecated_msg=True,
        )

    def _process_args(self) -> None:
        arg_env_consistent_bool(self, "test", "TEST_ENV")


# ------------------------------------------------------------------------------
# Singleton reset fixture (CRITICAL)
# ------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_dummy_args():
    yield
    reset_singleton(DummyArgs)
    unfreeze_dataclass(DummyArgs)


# ------------------------------------------------------------------------------
# str2bool
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("y", True),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("n", False),
    ],
)
def test_str2bool_valid(value, expected):
    assert str2bool(value) is expected


def test_str2bool_invalid():
    with pytest.raises(ArgumentTypeError):
        str2bool("maybe")


# ------------------------------------------------------------------------------
# ArgsBase parsing – bool
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv,expected",
    [
        ([], False),
        (["--flag"], True),
        (["--flag", "true"], True),
        (["--flag", "false"], False),
    ],
)
def test_bool_flag(argv, expected):
    args = DummyArgs(argv)
    assert args.flag is expected


# ------------------------------------------------------------------------------
# CSV list / set parsing
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv,attr,expected",
    [
        (["--ints", "1,2,3"], "ints", [1, 2, 3]),
        (["--floats", "1.5,2.5"], "floats", [1.5, 2.5]),
        (["--strs", "a,b,c"], "strs", ["a", "b", "c"]),
        (["--bools", "true,false,1"], "bools", [True, False, True]),
        (["--int_set", "1,2,2"], "int_set", {1, 2}),
    ],
)
def test_csv_containers(argv, attr, expected):
    args = DummyArgs(argv)
    assert getattr(args, attr) == expected


def test_csv_invalid_int():
    with pytest.raises(SystemExit):
        DummyArgs(["--ints", "1,a"])


# ------------------------------------------------------------------------------
# Tuple parsing
# ------------------------------------------------------------------------------


def test_fixed_tuple():
    args = DummyArgs(["--tup_fixed", "42,hello"])
    assert args.tup_fixed == (42, "hello")


def test_fixed_tuple_wrong_len():
    with pytest.raises(SystemExit):
        DummyArgs(["--tup_fixed", "1"])


def test_var_tuple():
    args = DummyArgs(["--tup_var", "1,2,3"])
    assert args.tup_var == (1, 2, 3)


# ------------------------------------------------------------------------------
# Frozen behavior
# ------------------------------------------------------------------------------


def test_args_are_frozen():
    args = DummyArgs(["--flag"])
    with pytest.raises(TypeError):
        args.flag = False

    with pytest.raises(TypeError):
        del args.flag


# ------------------------------------------------------------------------------
# move_arg_from_to
# ------------------------------------------------------------------------------


def test_move_arg_from_to(caplog):
    args = DummyArgs(["--new", "value", "--old", "deprecated_value"])

    assert args.new == "value"
    assert args.old == "value"  # old arg updated for backward compatibility
    assert any("deprecated" in r.message for r in caplog.records)


# ------------------------------------------------------------------------------
# env_to_bool / arg_env_consistent_bool
# ------------------------------------------------------------------------------


def test_env_to_bool(monkeypatch):
    monkeypatch.setenv("TEST_ENV", "1")
    assert env_to_bool("TEST_ENV") is True

    monkeypatch.setenv("TEST_ENV", "false")
    assert env_to_bool("TEST_ENV") is False


@pytest.mark.parametrize(
    "arg_value,env_value,expected",
    [
        # both wins
        (True, "1", True),
        # env wins
        (False, "1", True),
        # arg wins
        (True, "0", True),
        # both false
        (False, "0", False),
    ],
)
def test_arg_env_consistent_bool(monkeypatch, arg_value, env_value, expected):
    monkeypatch.setenv("TEST_ENV", env_value)

    args = DummyArgs(["--test", str(arg_value)])

    assert args.test is expected
    assert os.environ["TEST_ENV"] == ("1" if expected else "0")
