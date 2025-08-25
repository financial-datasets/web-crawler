import asyncio

async def spinner(message: str = "Searching...", interval: float = 0.1):
    symbols = "|/-\\"
    idx = 0
    try:
        while True:
            print(f"{message} {symbols[idx % len(symbols)]}", end="\r", flush=True)
            idx += 1
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        print(" " * (len(message) + 2), end="\r", flush=True)
        raise 