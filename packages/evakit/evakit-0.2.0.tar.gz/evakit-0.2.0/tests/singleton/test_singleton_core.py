"""Singleton - Core
Verifies core functionality and behavior that must hold in every policy (legacy or strict).
# Core Functional Requirements
F: functional requirements
*After all, what defines a "Singleton"?*
- F1.1: At most 1 instance exists at any given moment for a Singleton class
- F1.2: Inheritance (sub-classes) are considered different classes
S: Safety property
- S1.1: No internal state of a parent class singletons is mutated by instantiation of a sub-class
  -  If Class B(A, Singleton), then B() should not create an instance of A or mutate attributes in \
      A.instance() implicitly.
- S1.2: No self-recursive instantiation (calling A() inside A()) or self-reference (calling \
    A.instance() inside A()). Violation raises exception immediately (no deadlock)
L: Liveness property
- L1.1: if Singleton() and Singleton.instance() happen in parallel, they eventually return the \
    same object regardless of concurrency (No deadlock)
  - Incorrect implementation of F3.1 might implicitly break this if a global state is used to \
      represent "the class is currently under construction"
- L1.2: if many different Singleton instantiation happens concurrently, they must overlap \
    regardless of inheritance. (No global sequential serialization)
# Extra Functional Requirements
- F2.1: Support @dataclass with inheritance
- F2.2: if an instance is not ready in timeout, a concurrent.futures.TimeoutError (not built-in \
    TimeoutError) is raised.
- L2.1: if some thread constructs successfully within timeout, all other threads calling \
    cls.instance(timeout) return the same object.
- L2.2: if the construction attempt fails, all waiting threads observe the same constructor \
    exception (no hang), and the class remain uninitialized (Exceptional behavior)
"""

import threading
import time
from concurrent import futures as ct
from dataclasses import dataclass

import pytest

from evakit.singleton import Singleton, reset_singleton


# F1.1: At most 1 instance exists at any given moment for a Singleton class
def test_f1_1_core_identity():
    class A(Singleton):
        def __init__(self):
            self.ready = True

    class B(Singleton): ...

    a = A()
    assert A.instance() is a
    assert getattr(A.instance(), "ready", False) is True
    assert A.instance() is not B()


# F1.2: Inheritance (sub-classes) are considered different classes
def test_f1_2_per_subclass_instance():
    class A(Singleton):
        pass

    class B(A, Singleton):
        pass

    a = A()
    b = B()
    assert A.instance() is a
    assert B.instance() is b
    assert a is not b


# S1.1: No internal state of a parent class singletons is mutated by instantiation of a sub-class
def test_s1_1_inheritance_isolation():
    class A(Singleton):
        def __init__(self):
            self.value = 42

    class B(A, Singleton):
        def __init__(self):
            super().__init__()
            self.value = 100

    class C(B, Singleton):
        def __init__(self):
            super().__init__()
            self.value = 200

    b = B()
    assert B.instance().value == 100
    assert not A.initialized()
    c = C()
    assert not A.initialized()
    assert c.value == 200
    assert b.value == 100
    reset_singleton(B)
    del b
    reset_singleton(C)
    del c
    a = A()
    c = C()
    assert a.value == 42
    assert not B.initialized()
    assert c.value == 200


# S1.2: No self-recursive instantiation (calling A() inside A()) or self-reference (calling
# A.instance() inside A()). Violation raises exception immediately (no deadlock)
def test_s1_2_no_self_recursion():
    class A(Singleton):
        tries = 0

        def __init__(self):
            self.value = 42
            if type(self).tries < 1:
                type(self).tries += 1
                A()

    with pytest.raises(Exception):
        A()


def test_s1_2_no_self_reference():
    class A(Singleton):
        def __init__(self):
            self.value = 42
            A.instance()

    with pytest.raises(Exception):
        A()


# L1.1: if Singleton() and Singleton.instance() happen in parallel, they eventually return the
# same object regardless of concurrency (No deadlock)
def test_l1_1_concurrent_instantiation_and_reference(thread_runner):
    class A(Singleton):
        def __init__(self):
            time.sleep(0.03)
            self.value = 42

    outcomes, has_exc = thread_runner(
        32,
        lambda tid_: A() if tid_ == 16 else A.instance(),
        random_sleep_before_start=0.03,
    )
    assert not has_exc, [e.exc for e in outcomes]
    assert len({id(outcome.result) for outcome in outcomes}) == 1


# L1.2: if many different Singleton instantiation happens concurrently, they must overlap regardless
# of inheritance. (No global sequential serialization)
def test_l1_2_concurrent_instantiation_many_classes(thread_runner):
    n_classes = 16

    def make_singleton(name, bases=None):
        def __init__(self):
            time.sleep(0.5)

        if bases is None:
            bases = (Singleton,)
        return type(name, bases, {"__init__": __init__})

    classes = [make_singleton(f"Singleton_{idx}") for idx in range(n_classes)]
    base_cls = make_singleton("BaseSingleton")
    classes = [make_singleton(f"SubSingleton_{idx}", bases=(base_cls,)) for idx in range(n_classes)]
    classes.append(base_cls)

    def worker(tid_: int):
        if tid_ < len(classes):
            return classes[tid_]()
        else:
            return classes[tid_ % len(classes)].instance()

    outcomes, has_exc = thread_runner(
        3 * len(classes),
        worker,
        timeout=0.8,
        random_sleep_before_start=0.1,
    )
    assert not has_exc, [e.exc for e in outcomes]
    assert len({id(outcome.result) for outcome in outcomes}) == len(classes)
    for cls in classes:
        assert cls.initialized()


# F2.1: Support @dataclass with inheritance
def test_f2_1_support_dataclass_with_inheritance():
    @dataclass
    class A(Singleton):
        value: int = 42

        def __post_init__(self):
            self.value += 1

    @dataclass
    class B(A):
        value: int = 100

        def __post_init__(self):
            super().__post_init__()
            self.value += 100

    b = B()
    assert b is B.instance()
    assert b.value == 201
    a = A()
    assert a is A.instance()
    assert a.value == 43
    reset_singleton(A)
    reset_singleton(B)
    a = A()
    assert a.value == 43
    b = B()
    assert b is B.instance()
    assert b.value == 201


# F2.2: if an instance is not ready in timeout, a concurrent.futures.TimeoutError (not built-in
# TimeoutError) is raised.
def test_f2_2_instance_timeout():
    started = threading.Event()

    class A(Singleton):
        def __init__(self):
            super().__init__()
            started.set()
            time.sleep(0.5)

    t = threading.Thread(target=A, daemon=True)
    t.start()
    time.sleep(0.03)
    assert started.wait(timeout=0.03)
    with pytest.raises(ct.TimeoutError):
        A.instance(timeout=0.03)
    t.join()


# L2.1: if some thread constructs successfully within timeout, all other threads calling
# cls.instance(timeout) return the same object.
def test_l2_1_concurrent_instantiation_with_timeout(thread_runner):
    class A(Singleton):
        def __init__(self):
            time.sleep(0.05)
            self.value = 42

    outcomes, has_exc = thread_runner(
        32,
        lambda tid_: A() if tid_ == 16 else A.instance(timeout=0.1),
        random_sleep_before_start=0.03,
    )
    assert not has_exc, [e.exc for e in outcomes]
    assert len({id(outcome.result) for outcome in outcomes}) == 1


# L2.2: if the construction attempt fails, all waiting threads observe the same constructor
# exception (no hang), and the class remain uninitialized (Exceptional behavior)
def test_l2_2_concurrent_instantiation_failed_with_timeout(thread_runner):
    class A(Singleton):
        def __init__(self):
            time.sleep(0.03)
            raise RuntimeError("boom")

    outcomes, has_exc = thread_runner(
        32,
        lambda tid_: A() if tid_ == 16 else A.instance(),
        random_sleep_before_start=0.03,
        cancel_on_first_exception=False,
    )
    assert has_exc, [e.exc for e in outcomes]
    assert ["boom" in str(e.exc) for e in outcomes].count(True) == 32
