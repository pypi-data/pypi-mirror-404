#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#   and associated documentation files (the "Software"), to deal in the Software without
#   restriction, including without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import asyncio
import inspect
from typing import AsyncIterable, TypeVar, Callable, Awaitable

T = TypeVar("T")

def combine_iterators(input_iterators):

    queue = asyncio.Queue(1)

    async def read_from_iterator(aiter):
        try:
            while True:
                item = await anext(aiter)
                await queue.put((item,None))
        except Exception as exn:
            await queue.put((None,exn))

    tasks = [asyncio.create_task(read_from_iterator(input_iterator)) for input_iterator in input_iterators]

    async def combine():
        while not all(task.done() for task in tasks):
            (result,exn) = await queue.get()
            if exn is None:
                yield result
            else:
                if not isinstance(exn,StopAsyncIteration):
                    raise exn
        while not queue.empty():
            (result, exn) = await queue.get()
            if exn is None:
                yield result
            else:
                if not isinstance(exn,StopAsyncIteration):
                    raise exn

    return combine()

class ValueIteratorCombined:

    def __init__(self, parent_iterable, input_iterators, lockstep_threshold):
        self.parent_iterable = parent_iterable

        self.subscriber_locks = {}
        self.value = None
        self.value_available = False
        self.fetch_required = True
        self.lockstep_threshold = lockstep_threshold
        self.subscriber_count = 0
        self.fetched_count = 0
        self.input_exhausted = False
        self.exn = None

        if len(input_iterators) > 1:
            self.input_iterator = combine_iterators(input_iterators)
        else:
            self.input_iterator = input_iterators[0]

    async def subscribe(self):
        self.subscriber_count += 1
        subscriber_id = f"s{self.subscriber_count}"
        lock = asyncio.Lock()
        if not self.value_available:
            await lock.acquire()
            if self.value_available:
                lock.release()
        self.subscriber_locks[subscriber_id] = lock
        return subscriber_id

    def unsubscribe(self, subscriber_id):
        self.lockstep_threshold -= 1
        self.subscriber_locks[subscriber_id].release()
        del self.subscriber_locks[subscriber_id]
        if self.fetched_count == self.lockstep_threshold:
            self.fetch_required = True

    async def fetch(self, subscriber_id):
        if self.fetch_required:
            self.fetch_required = False
            try:
                self.value = await anext(self.input_iterator)
                self.value = await self.parent_iterable.transform(self.value)
                self.value_available = True
                self.fetched_count = 0
            except StopAsyncIteration:
                self.input_exhausted = True
            except Exception as exn:
                self.input_exhausted = True
                self.exn = exn
            for subscriber_lock in self.subscriber_locks.values():
                try:
                    subscriber_lock.release()
                except:
                    pass

        await self.subscriber_locks[subscriber_id].acquire()
        if self.input_exhausted:
            raise StopAsyncIteration()
        if self.exn:
            raise exn
        self.fetched_count += 1
        if self.fetched_count >= self.lockstep_threshold:
            self.fetch_required = True
        return self.value

class ValueIterator:

    def __init__(self):
        pass

class SyncValueIterator(ValueIterator):

    def __init__(self, combined_iterator):
        super().__init__()
        self.combined_iterator = combined_iterator
        self.subscriber_id = None

    async def __anext__(self):
        if self.subscriber_id is None:
            self.subscriber_id = await self.combined_iterator.subscribe()
        return await self.combined_iterator.fetch(self.subscriber_id)

    def close(self):
        self.combined_iterator.unsubscribe(self.subscriber_id)

class ValueIterable:

    def __init__(self, input_iterables:list[AsyncIterable[T]], transform_fn:Callable[[T],T]|Callable[[T],Awaitable[T]]|None, lockstep_threshold:int=0):
        self.input_iterables = input_iterables
        self.lockstep_threshold = lockstep_threshold
        self.combined_iterator = ValueIteratorCombined(self,
                                                       [aiter(input_iterable) for input_iterable in input_iterables],
                                                       self.lockstep_threshold)
        self.iterator_count = 0
        self.transform_fn = transform_fn
        self.transform_function_is_async = False
        if self.transform_fn is not None and inspect.iscoroutinefunction(self.transform_fn):
            self.transform_function_is_async = True

    async def transform(self, value):
        if self.transform_fn is None:
            return value
        if self.transform_function_is_async:
            return await self.transform_fn(value)
        else:
            return self.transform_fn(value)

    @staticmethod
    def create_from_iterables(input_iterables:list[AsyncIterable[T]], transform_fn:Callable[[T],T]|Callable[[T],Awaitable[T]]|None=None, lockstep_threshold:int=0):
        """
        Return an async iterable based on a set of input iterables.

        Args:
            input_iterables: a list of one or more async iterables that provide input values
            transform_fn: a function to transform values from the input iterables
            lockstep_threshold: Specify that this many iterators opened over this iterable will be optimised to share a
                              single set of iterators obtained from the input iterables.
                              Note that these iterators will yield values in lock-step.

        Returns:
            An async iterable
        """
        return ValueIterable(input_iterables, transform_fn, lockstep_threshold)

    def __aiter__(self) -> ValueIterator:
        self.iterator_count += 1
        return SyncValueIterator(self.combined_iterator)



