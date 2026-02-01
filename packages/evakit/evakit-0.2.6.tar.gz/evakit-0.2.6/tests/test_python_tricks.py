from dataclasses import dataclass

import pytest

from evakit.python_tricks import freeze_dataclass, get_public_methods


class Base:
    def foo(self): ...

    def _private(self): ...

    def __dunder__(self): ...


class Derived(Base):
    def bar(self): ...

    def baz(self): ...

    value = 123  # non-callable should not be listed


def test_get_public_methods_basic():
    methods = get_public_methods(Derived)
    # only callable, no _ or __
    assert "bar" in methods
    assert "baz" in methods
    assert "foo" in methods  # inherited
    assert "_private" not in methods
    assert "__dunder__" not in methods
    assert "value" not in methods


def test_works_on_instance():
    obj = Derived()
    methods = get_public_methods(obj.__class__)
    assert set(methods) == set(get_public_methods(Derived))


def test_handles_builtin_type():
    # Ensure it doesn't crash on types like str or dict
    methods = get_public_methods(str)
    assert "split" in methods
    assert "upper" in methods
    assert all(isinstance(m, str) for m in methods)


def test_empty_class():
    class Empty:
        pass

    assert get_public_methods(Empty) == []


@pytest.mark.parametrize(
    "operation, field_name",
    [
        (lambda obj: setattr(obj, "x", 10), "x"),  # assign existing
        (lambda obj: delattr(obj, "x"), "x"),  # delete existing
        (lambda obj: setattr(obj, "y", 20), "y"),  # add new
    ],
)
def test_freeze_dataclass_disallows_mutation(operation, field_name):
    @dataclass
    class Foo:
        x: int

        def __post_init__(self):
            freeze_dataclass(self.__class__)

    obj = Foo(1)

    with pytest.raises(TypeError) as exc:
        operation(obj)

    msg = str(exc.value)
    assert "Foo is frozen" in msg
    assert field_name in msg


def test_freeze_dataclass_allows_read():
    @dataclass
    class Foo:
        x: int

        def __post_init__(self):
            freeze_dataclass(self.__class__)

    obj = Foo(42)

    assert obj.x == 42


def test_freeze_dataclass_as_decorator():
    @freeze_dataclass
    @dataclass
    class Foo:
        x: int

    with pytest.raises(TypeError):
        Foo(1).x = 2
