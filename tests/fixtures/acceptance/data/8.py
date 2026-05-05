# Mozilla Public License 2.0
# Copyright (c) 2024 Mozilla Foundation


def outer(x):
    def inner(y):
        return x + y

    return inner
