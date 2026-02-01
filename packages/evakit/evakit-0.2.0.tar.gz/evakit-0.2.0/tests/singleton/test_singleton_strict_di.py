"""Singleton - Strict DI Mode
- F3.1: Referring to other existing singleton instances raises exceptions while instantiating a \
    singleton instance.
  - DI requires other dependent singleton instances to be passed into the __init__() as parameters
- F3.2: a constructor(__new__) or initializer(__init__) is allowed to be called once and only once
  - Prevents implicitly violating DI when calling A() in B.__init__() implicitly referring to A \
      instance rather than creating an A instance.
- F3.3: Strict Pure Dependency Injection in Singleton method calls
    - prevent calling A.instance() inside B.do_something() if A is not explicitly passed into \
        B.__init__()
- S2.1: Non-leaf singleton class ensure once-and-only-once construction across all its subclasses
    - Prevents implicitly violating S1.1 when instantiating a singleton within constructor of \
        another singleton subclass.
# Extra Functional Requirements
- F4.1: Warning messages are logged if .instance() timeout without other threads constructing the \
    singleton.
"""

from concurrent import futures as ct

import pytest

from evakit.singleton import (
    ManyConstructionError,
    Singleton,
    reset_singleton,
)


# F3.1: Referring to other existing singleton instances raises exceptions while instantiating a
# singleton instance.
def test_f3_1_violating_dependency_injection_raises_exception():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    class B(Singleton):
        def __init__(self):
            super().__init__()
            A.instance()

    a = A()
    assert a.value == 42
    with pytest.raises(Exception):
        B()


# F3.2: a constructor(__new__) or initializer(__init__) is allowed to be called once and only once
def test_f3_2_constructor_or_initializer_called_only_once():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    a = A()
    assert a.value == 42
    with pytest.raises(ManyConstructionError):
        A()


def test_f3_2_constructor_or_initializer_called_only_once_nested():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    class B(Singleton):
        def __init__(self):
            super().__init__()

    class C(B):
        def __init__(self):
            super().__init__()
            self.a = A()

    c = C()
    assert A.initialized()
    assert not B.initialized()
    assert C.initialized()

    assert c.a.value == 42
    with pytest.raises(ManyConstructionError):
        A()


def test_f3_3_strict_dependency_injection_in_method_calls():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    class B(Singleton):
        def __init__(self):
            super().__init__()

        def do_something(self):
            A.instance()

        @classmethod
        def do_something_classmethod(cls):
            # this is allowed
            A.instance()

        @staticmethod
        def do_something_staticmethod():
            # this is allowed
            A.instance()

    a = A()
    assert a.value == 42
    b = B()
    with pytest.raises(Exception):
        b.do_something()

    # classmethod call is allowed
    B.do_something_classmethod()

    # staticmethod call is allowed
    B.do_something_staticmethod()


def test_f3_3_strict_dependency_injection_in_method_calls_nested():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    class B(Singleton):
        def __init__(self):
            super().__init__()
            self.a = A()

    class C(Singleton):
        def __init__(self):
            super().__init__()
            self.b = B()

        def do_something(self):
            return A.instance().value

    # nested references are allowed method calls
    c = C()
    assert A.initialized()
    assert B.initialized()
    assert C.initialized()

    assert c.do_something() == 42


def test_s2_1_non_leaf_singleton_once_and_only_once_construction():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    class B(A):
        def __init__(self):
            super().__init__()
            self.a = A()

    a = A()
    assert a.value == 42

    with pytest.raises(ManyConstructionError):
        B()


def test_reset_clean_up_owned_singletons():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    class C(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 100
            self.a = A()

    class B(A):
        def __init__(self):
            super().__init__()
            self.c = C()

    B()

    assert A.initialized()
    assert B.initialized()
    assert C.initialized()

    reset_singleton(B)
    assert not A.initialized()
    assert not B.initialized()
    assert not C.initialized()


# F4.1: Warning messages are logged if .instance() timeout without other threads constructing the
# singleton.
def test_f4_1_instance_timeout_logs_warning(caplog):
    class A(Singleton):
        def __init__(self, *args, **kwargs):
            # We intentionally do NOT call super().__init__() here because
            # we will never actually construct the instance — we only test timeout.
            pass

    caplog.set_level("WARNING")

    # Force a timeout immediately. No other thread is constructing A.
    with pytest.raises(ct.TimeoutError):
        A.instance(timeout=0.01)

    # The result may be None or anything else — not specified — we do NOT assert on it.
    # We only assert that a WARNING log is emitted.
    warnings = [rec.message for rec in caplog.records if rec.levelname == "WARNING"]
    assert warnings, "Expected a warning when A.instance() times out"

    # Optionally: enforce loose matching of the log text
    assert any(
        "waiting" in msg.lower() for msg in warnings
    ), f"Expected timeout message in warnings, got: {warnings}"


def test_f4_2_failed_construction_is_recoverable():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    class B(Singleton):
        value = 100

        def __init__(self):
            super().__init__()

            print(f"B constructing with value={B.value}")

            if B.value == 100:
                B.value += 1
                raise RuntimeError("Intentional failure during B construction")

    class C(Singleton):
        def __init__(self):
            super().__init__()
            self.a = A()
            self.b = B()

    with pytest.raises(RuntimeError):
        B()

    assert not B.initialized()

    b = B()

    assert B.initialized()
    assert b is B.instance()


def test_f4_2_failed_construction_is_not_recoverable_with_ownership():
    class A(Singleton):
        def __init__(self):
            super().__init__()
            self.value = 42

    class B(Singleton):
        value = 100

        def __init__(self):
            super().__init__()

            print(f"B constructing with value={B.value}")

            if B.value == 100:
                B.value += 1
                raise RuntimeError("Intentional failure during B construction")

    class C(Singleton):
        def __init__(self):
            super().__init__()
            self.a = A()
            self.b = B()

    with pytest.raises(RuntimeError):
        C()

    assert not B.initialized()
    assert not C.initialized()
    assert A.initialized()

    with pytest.raises(ManyConstructionError):
        C()

    assert A.initialized()
    assert not B.initialized()
    assert not C.initialized()


def test_partial_initialization_is_not_allowed():
    class A(Singleton):
        def __init__(self, b: "B"):
            super().__init__()
            self.value = 42
            self.b = b

    class B(Singleton):
        def __init__(self):
            super().__init__()
            A(self)

    with pytest.raises(Exception):
        B()
