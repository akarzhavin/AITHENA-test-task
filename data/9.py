# MIT License
# Copyright (c) 2024 Modern Dev


def decorator(func):
    return func


@decorator
async def fetch_data(url: str, timeout: int = 10) -> dict:
    return {"url": url, "timeout": timeout}
