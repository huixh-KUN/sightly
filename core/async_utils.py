"""
asyncio 工具函数与全局资源

提供：
- run_in_executor()：将同步阻塞函数放入线程池执行
- get_global_executor()：全局 ThreadPoolExecutor 单例
- cancel_all_tasks()：取消事件循环中所有任务
- create_async_thread()：创建运行事件循环的后台线程
"""
import asyncio
import functools
import threading
from concurrent.futures import ThreadPoolExecutor

_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def get_global_executor():
    """获取全局 ThreadPoolExecutor 单例（CPU 密集任务使用）"""
    return _EXECUTOR


async def run_in_executor(fn, *args, **kwargs):
    """
    在全局线程池中执行同步阻塞函数

    用法：
        result = await run_in_executor(blocking_fn, arg1, arg2)
        result = await run_in_executor(fn, arg1, kw=arg2)
    """
    loop = asyncio.get_event_loop()
    if kwargs:
        return await loop.run_in_executor(
            _EXECUTOR, functools.partial(fn, *args, **kwargs)
        )
    return await loop.run_in_executor(_EXECUTOR, fn, *args)


def cancel_all_tasks(loop=None):
    """取消指定事件循环中所有未完成的 asyncio.Task"""
    loop = loop or asyncio.get_event_loop()
    for task in asyncio.all_tasks(loop):
        if not task.done():
            task.cancel()


def create_async_thread(coro_factory, daemon=True):
    """
    创建后台线程运行 asyncio 事件循环

    Args:
        coro_factory: 返回协程或协程列表的可调用对象
        daemon: 是否为守护线程

    Returns:
        tuple: (thread, loop)
    """
    loop = asyncio.new_event_loop()

    def _run():
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro_factory())
        finally:
            loop.close()

    thread = threading.Thread(target=_run, daemon=daemon)
    thread.start()
    return thread, loop
