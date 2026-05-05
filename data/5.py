# Apache License 2.0
# Copyright 2024 Google Inc.


class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def multiply(self, x):
        return x * self.factor

    @classmethod
    def create(cls):
        return cls(10)
