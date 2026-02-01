import asyncio
import threading

import nest_asyncio


nest_asyncio.apply()


async def sleep():
    print("sleeping 1...")
    await asyncio.sleep(10)

    print("sleeping 2...")
    await asyncio.sleep(10)

    print("slept!")


def sync():
    print("sync")
    asyncio.get_running_loop().run_until_complete(sleep())
    print("done")


async def autograd():
    print("autograd started")
    await asyncio.sleep(10)
    print("autograd finished")
    return "DONE"


def backward(loop):
    print("backward started")
    future = asyncio.run_coroutine_threadsafe(autograd(), loop)
    print(future.result())
    print("backward finished")


async def task():
    while True:
        print("task")
        await asyncio.sleep(1)


async def main():
    asyncio.create_task(task())
    _thread = threading.Thread(target=backward, daemon=True, args=(asyncio.get_running_loop(),))
    _thread.start()
    sync()


if __name__ == '__main__':
    asyncio.run(main())
