from app.workers.download_worker import MAX_RETRIES, process_once, run_forever

__all__ = ["MAX_RETRIES", "process_once", "run_forever"]


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_forever())
