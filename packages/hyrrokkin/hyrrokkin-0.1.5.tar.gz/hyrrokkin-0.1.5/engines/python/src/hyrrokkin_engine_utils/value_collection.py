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

import inspect
from abc import abstractmethod
from typing import Any, TypeVar, Callable, Awaitable

T = TypeVar("T")

class ValueCollectionIterator:

    def __init__(self, collection:"ValueCollection"):
        """
            Implement an iterator over a ValueCollection
        Args:
            iterable: a value collection instance
        """
        self.collection = collection
        self.position = 0

    async def __anext__(self) -> Any:
        """
        Get the next value

        Returns: next value in the collection

        Raises:
            StopAsyncException when the iterator is exhausted

        """
        if self.position < self.collection.size():
            value = await self.collection.get(self.position)
            self.position += 1
            return value
        else:
            raise StopAsyncIteration()

class ValueCollectionClosedError(Exception):

    def __init__(self):
        super().__init__("Attempting to access a value from a ValueCollection that has been closed")

class ValueCollectionIndexError(IndexError):

    def __init__(self, index, limit):
        super().__init__(f"Index {index} is out of range 0..{limit}")

class ValueStore:

    """Defines an interface for an object which can be used to store an ordered list of values and retrieve values based on an integer index"""

    @abstractmethod
    async def get(self, index:int) -> T:
        """
        Retrieve a value from the store at a particular index

        Args:
            index: an index into the store

        Returns:
            the stored value, if the index is within range

        Raises:
            IndexError if the index is out of range
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Gets the number of values held in this store

        Returns: number of values
        """
        pass

    @abstractmethod
    def close(self):
        """
        Close this store, freeing any resources
        """
        pass


class ValueCollection:

    def __init__(self):
        """
        Base class for a collection of values.

        Call create_from_collections or create_source static methods to create a subclass of this instance.
        """
        self.is_closed = False

    @staticmethod
    def create_from_collections(source_collections:list["ValueCollection"], transform_fn:Callable[[T],T]|Callable[[T],Awaitable[T]]|None=None) -> "ValueCollection":
        """
        Create a collection by concatenating one or more collections

        Args:
            source_collections: the collections to concatenate
            transform_fn: an optional function to transform values from the source collections into this collection

        Returns:
            A new ValueCollection instance
        """
        return TransformCollection(source_collections, transform_fn)

    @staticmethod
    def create_from_store(value_store:ValueStore=None) -> "ValueCollection":
        """
        Create a collection based on a value store

        Args:
            value_store: an object implementing the ValueStore interface which is used to store values held in the collection

        Returns:
            A new ValueCollection instance
        """
        return StoreCollection(value_store)

    def __aiter__(self) -> ValueCollectionIterator:
        """
        Open an async iterator over this collection

        Returns: an async iterator

        Raises: ValueCollectionClosedError if the collection has been closed

        """
        if self.is_closed:
            raise ValueCollectionClosedError()
        return ValueCollectionIterator(self)

    @abstractmethod
    def size(self) -> int:
        """
        Get the size of this collection

        Returns: number of values in this collection

        Raises: ValueCollectionClosedError if the collection has been closed
        """

    @abstractmethod
    async def get(self, index:int) -> T:
        """
        Attempt to retrieve a value from the collection

        Args:
            index: the index into the collection

        Returns:
            the value at that index

        Raises:
            IndexError if the index is out of range
            ValueCollectionClosedError if the collection has been closed
        """

    def close(self):
        """
        Close this collection, freeing up any resources held.  After calling this, the collection's values cannot be accessed.

        Raises:
            ValueCollectionClosedError if the collection has already been closed
        """
        if self.is_closed:
            raise ValueCollectionClosedError()
        self.is_closed = True


class TransformCollection(ValueCollection):

    def __init__(self, source_collections=[], transform_fn=None):
        super().__init__()
        self.source_collections = source_collections
        self.transform_fn = transform_fn

    def size(self):
        if self.is_closed:
            raise ValueCollectionClosedError()
        total_sz = 0
        for collection in self.source_collections:
            total_sz += collection.size()
        return total_sz

    async def get(self, pos):
        index = pos
        if self.is_closed:
            raise ValueCollectionClosedError()
        for collection in self.source_collections:
            sz = collection.size()
            if pos < sz:
                value = await collection.get(pos)
                if self.transform_fn:
                    if inspect.iscoroutinefunction(self.transform_fn):
                        value = await self.transform_fn(value)
                    else:
                        value = self.transform_fn(value)
                return value
            else:
                pos -= sz
        raise ValueCollectionIndexError(index,self.size())

class InMemoryValueStore(ValueStore):

    def __init__(self, values:list[T]):
        """
        A simple implementation of the ValueStore interface using an in-memory list of values
        """
        self.values = values

    async def get(self, index:int) -> T:
        if index < len(self.values):
            return self.values[index]
        else:
            raise ValueCollectionIndexError(index,len(self.values))

    def __len__(self) -> int:
        return len(self.values)

    def close(self):
        self.values = []

class StoreCollection(ValueCollection):

    def __init__(self, value_store:ValueStore=None):
        super().__init__()
        self.value_store = value_store

    def size(self):
        if self.is_closed:
            raise ValueCollectionClosedError()
        return len(self.value_store)

    async def get(self, pos):
        if self.is_closed:
            raise ValueCollectionClosedError()
        return await self.value_store.get(pos)

    def close(self):
        if self.is_closed:
            raise ValueCollectionClosedError()
        super(self,StoreCollection).close()
        self.value_store.close()
