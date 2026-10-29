"""Simulate independent menu availability lookups, preserving input order."""

import asyncio


async def check_availability(item, delay):
    # מדמה המתנה לבדיקת זמינות של פריט אחד.
    await asyncio.sleep(delay)
    return {"item_id": item.id, "available": item.available}


async def collect_sequential(jobs):
    # בודקת כל פריט רק אחרי שהקודם הסתיים.
    results = []
    for item, delay in jobs:
        results.append(await check_availability(item, delay))
    return results


async def collect_concurrent(jobs):
    # מפעילה את כל הבדיקות ואוספת לפי סדר הקלט.
    return await asyncio.gather(*(check_availability(item, delay) for item, delay in jobs))
