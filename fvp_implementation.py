# FVP — Funktionalno-Vektornoe Programmirovanie
# Functional list processing in Python, closure-based,
# without classes, built-in lists, or tuples.
# Based on patterns from student_client_task.py (OOP + argument styles).

"""
ЛАБОРАТОРНАЯ РАБОТА · ФВП · Функциональное программирование

Набор функций для обработки списков в функциональном стиле.
Все операции выполняются через замыкания (closures): pair(h,t) -> lambda s: s(h,t).
Пустой список обозначается None (маркер завершения).

Запуск:
    python fvp_implementation.py
    
Аргументы командной строки (унаследовано от студенческого клиента):
    --server       Адрес сервера blockchain (по умолчанию http://10.39.120.52:5000)
    --surname      Фамилия студента (по умолчанию Савицкий)
    --group        Группа студента (по умолчанию ОКБП-401итмп)
    --message      Сообщение в блоке (по умолчанию "Мой блок на ООП")
"""

import argparse
import sys


# === Basic list cell (cons) ===

def pair(head, tail):
    """Create a cons cell using a closure.
    Returns a function that delegates to a selector: selector(head, tail).
    """
    return lambda selector: selector(head, tail)


def head(lst):
    """Extract the first element from a non-empty list."""
    return lst(lambda h, t: h)


def tail(lst):
    """Extract the rest of the list from a non-empty list."""
    return lst(lambda h, t: t)


def is_null(lst):
    """Check if lst is the empty list (our sentinel None)."""
    return lst is None


# === Construction ===

def make_list(*args):
    """Create a list from variadic arguments.
    The last pair's tail is None (empty list sentinel).
    """
    if not args:
        return None
    return pair(args[0], make_list(*args[1:]))


def list_to_string(lst):
    """Convert list to string like [1,2,3]. """
    if is_null(lst):
        return "[]"
    return "[" + str(head(lst)) + "," + list_to_string(tail(lst)) + "]"


def list_range(low, high):
    """Return a list of integers from low to high inclusive.
    If low > high, returns empty list None.
    """
    if low > high:
        return None
    return pair(low, list_range(low + 1, high))


# === Folds ===

def foldl(func, lst, acc):
    """Left fold (reduce).
    f(f(...f(acc, x1), x2), ...), xn). Traverses left-to-right.
    """
    current = lst
    while not is_null(current):
        acc = func(acc, head(current))
        current = tail(current)
    return acc


def foldr(func, lst, acc):
    """Right fold.
    f(x1, f(x2, ... f(xn, acc)...)). Traverses right-to-left (recursive).
    """
    if is_null(lst):
        return acc
    return func(head(lst), foldr(func, tail(lst), acc))


# === Derived operations ===

def list_sum(lst):
    """Sum of all elements using foldl."""
    return foldl(lambda a, x: a + x, lst, 0)


def fact(n):
    """Factorial of n using foldl and list_range."""
    if n <= 0:
        return 1
    nums = list_range(1, n)
    return foldl(lambda a, x: a * x, nums, 1)


def list_map(func, lst):
    """Apply func to each element, returning a new list.
    Implemented using foldr: foldr (lambda x rest. pair(func(x), rest)) lst None
    """
    return foldr(lambda x, rest: pair(func(x), rest), lst, None)


def list_filter(pred, lst):
    """Filter elements satisfying predicate, returning a new list.
    Implemented using foldr.
    """
    return foldr(
        lambda x, rest: pair(x, rest) if pred(x) else rest,
        lst,
        None,
    )


def list_concat(lst1, lst2):
    """Concatenate two lists: lst1 ++ lst2.
    Uses foldr: prepend each element of lst1 to lst2.
    """
    return foldr(lambda x, rest: pair(x, rest), lst1, lst2)


def _copy_list(lst):
    """Helper: copy a list of cons cells (for use in list_replace)."""
    if is_null(lst):
        return None
    return pair(head(lst), _copy_list(tail(lst)))


def _length(lst):
    """Return the length of the list using foldl."""
    return foldl(lambda n, _: n + 1, lst, 0)


def list_replace(lst, index, value):
    """Replace element at given index with value.
    Returns a new list. If index is out of range, returns lst unchanged.
    """
    if is_null(lst):
        return None

    length = _length(lst)
    if index < 0 or index >= length:
        return lst  # index out of range — return original

    def replace_helper(lst, idx, val, pos):
        """Recursively build new list with element at pos replaced by val."""
        if is_null(lst):
            return None
        if pos == idx:
            # Replace this element; copy the original tail starting from here
            original_tail = tail(lst)
            copied_tail = _copy_list(original_tail)
            return pair(val, copied_tail)
        # Keep current element, recurse on tail
        new_tail = replace_helper(tail(lst), idx, val, pos + 1)
        return pair(head(lst), new_tail)

    return replace_helper(lst, index, value, 0)


# === 2.15 sum of odd squares ===

def sum_odd_squares(lst):
    """Sum of squares of odd elements in the list.
    Uses list_filter, list_map, list_sum as per task requirements.
    """
    odd = list_filter(lambda x: x % 2 != 0, lst)
    squared = list_map(lambda x: x ** 2, odd)
    return list_sum(squared)


# === CLI entry point (structure borrowed from student_client_task.py) ===

def parse_args(args=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="FVP — Funktionalno-Vektornoe Programmirovanie."
    )
    parser.add_argument(
        "--server",
        default="http://10.39.120.52:5000",
        help="адрес сервера blockchain (по умолчанию http://10.39.120.52:5000)",
    )
    parser.add_argument(
        "--surname",
        default="Савицкий",
        help="фамилия студента",
    )
    parser.add_argument(
        "--group",
        default="ОКБП-401итмп",
        help="группа студента",
    )
    parser.add_argument(
        "--message",
        default="Мой блок на ООП",
        help="сообщение внутри блока",
    )
    return parser.parse_args(args)


# === Test block (borrowed structure from student_client_task.py) ===

if __name__ == "__main__":
    args = parse_args()

    # Basic list
    lst = make_list(1, 2, 3, 4, 5)
    print("make_list(1,2,3,4,5):", list_to_string(lst))
    print("head:", head(lst))
    print("tail head:", head(tail(lst)))
    print("tail tail head:", head(tail(tail(lst))))
    print("is_null None:", is_null(None))
    print("is_null list:", is_null(lst))

    # list_range
    print("list_range(3,7):", list_to_string(list_range(3, 7)))
    print("list_range(5,3):", list_to_string(list_range(5, 3)))

    # foldl and list_sum
    print("list_sum:", list_sum(lst))
    print("fact(5):", fact(5))

    # foldr and list_map
    print("list_map(lambda x: x*2, lst):", list_to_string(list_map(lambda x: x * 2, lst)))

    # list_filter
    print("list_filter(lambda x: x%2==0, lst):", list_to_string(list_filter(lambda x: x % 2 == 0, lst)))

    # list_concat
    lst2 = make_list(6, 7, 8)
    print("list_concat:", list_to_string(list_concat(lst, lst2)))

    # list_replace
    lst_replaced = list_replace(lst, 2, 99)  # replace element at index 2 (value 3) with 99
    print("list_replace(2, 99):", list_to_string(lst_replaced))
    lst_out = list_replace(lst, 5, 99)  # out of range
    print("list_replace(5, 99) [out of range]:", list_to_string(lst_out))

    # sum_odd_squares (2.15)
    print("sum_odd_squares:", sum_odd_squares(lst))

    # Empty list
    empty = None
    print("list_to_string(None):", list_to_string(empty))
    print("is_null(None):", is_null(empty))
    print("fact(0):", fact(0))
    print("fact(1):", fact(1))