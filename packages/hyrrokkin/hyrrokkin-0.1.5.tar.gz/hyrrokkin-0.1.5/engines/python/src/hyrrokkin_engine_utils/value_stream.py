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
from typing import Callable, Awaitable, TypeVar

T = TypeVar("T")

class ValueStream:

    def __init__(self, activation_threshold:int=None):
        """
        Create a value stream base class.  Do not call this directly, use the static methods create_from_streams
        or create_source to construct an appropriate subclass

        Args:
            activation_threshold: if supplied, block publishing onto this stream until this many subscribers are active
        """
        # map from subscriber_id to an async function that receives published values
        self.subscribers = {}
        # map from subscriber_id to an async function that is called when the stream closes
        self.close_fns = {}
        # count of subscriptions issued on this stream
        self.subscriber_count = 0

        # block publication on this stream until this many subscribers are attached
        self.activation_threshold = activation_threshold
        self.active = False

        self.is_closed = False
        self.was_cancelled = False

        self.publication_lock = asyncio.Lock()
        self.completion_lock = asyncio.Lock()

    async def prepare(self):
        """
        Prepare this stream for use.  Call this after construction.
        """
        if self.activation_threshold:
            await self.publication_lock.acquire()
        else:
            self.active = True
        await self.completion_lock.acquire()

    @staticmethod
    async def create_from_streams(input_streams:list["ValueStream"]=[],
                                  transform_function:Callable[[T],T]|Callable[[T],Awaitable[T]]|None=None,
                                  activation_threshold:int|None=None) -> "ValueStream":
        """
        Create a value stream based on 1 or more other value streams.  The resulting stream will publish events received on
        any of the input streams.

        Args:

            input_streams: a list of input streams
            transform_function: an optional function to transform values received on the input streams.  May be async or non-async.
            activation_threshold: if supplied, block publishing onto this stream until this many subscribers are active

        Returns:
            A ValueStream object
        """
        stream = TransformStream(activation_threshold, input_streams, transform_function)
        await stream.prepare()
        return stream

    @staticmethod
    async def create_source(activation_threshold:int=None):
        """
        Create a value source stream.  Call the publish method to publish values to this stream.

        Args:
            activation_threshold: if supplied, block publishing onto this stream until this many subscribers are active

        Returns:
            A ValueStream object
        """
        stream = SourceStream(activation_threshold)
        await stream.prepare()
        return stream

    def activate(self):
        """
        Activate this stream, unblocking the publish method.  This is not usually called directly, but automatically once enough subscribers are subscribed.
        """
        if not self.active:
            self.active = True
            self.publication_lock.release()

    def can_publish(self) -> bool:
        """
        Check that values can be published to this stream.

        Returns: True iff a caller can use the publish method without being blocked or raising an exception

        Raises: Exception if this kind of stream cannot be published to
        """
        return self.active and not self.is_closed

    def subscribe(self, subscriber: Callable[[T],Awaitable[None]], close_fn:Callable[[bool],Awaitable[None]]=None) -> str:
        """
        Subscribe to values in this stream, passing in two callback functions

        Args:
            subscriber: required - an async function that is invoked with a value published on the stream
            close_fn: optional - an async function that is invoked when the stream is closed.  The argument to this function is set to True if the stream was interrupted.

        Returns:
            a subscriber-id that is unique to this stream.  Pass this to the unsubscribe method to unsubscribe these functions from further values published on the stream
        """
        subscriber_id = f"s{self.subscriber_count}"
        self.subscriber_count += 1
        self.subscribers[subscriber_id] = subscriber
        if close_fn is not None:
            self.close_fns[subscriber_id] = close_fn
        if not self.active and self.activation_threshold is not None and len(self.subscribers) >= self.activation_threshold:
            self.activate()
        return subscriber_id

    def unsubscribe(self, subscriber_id:str) -> None:
        """
        Unsubscribe from further values published on this stream

        Args:
            subscriber_id: a subscriber id returned from a call to the subscribe method
        """
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
        if subscriber_id in self.close_fns:
            del self.close_fns[subscriber_id]

    async def publish(self, value:T) -> bool:
        """
        Publish a value onto the stream.  This call will block until the stream becomes active.

        Args:
            value: the value to be published

        Returns:
            True iff the value was published, False if the stream was closed
        """
        if self.is_closed:
            return False
        async with self.publication_lock:
            await asyncio.gather(*[subscriber(value) for subscriber in self.subscribers.values()])
        return True

    async def close(self, was_cancelled:bool) -> None:
        """
        Close this stream.  Closing will prevent further values from being published to subscribers.  Subscribers will be
        notified if they registered a callback for the close_fn parameter when they called the subscribe method

        Args:
            was_cancelled: True iff this stream is being closed abnormally (due to an error)
        """
        if not self.is_closed:
            self.is_closed = True
            self.was_cancelled = was_cancelled
            self.completion_lock.release()
            for close_fn in self.close_fns.values():
                await close_fn(was_cancelled)

    async def waitfor_close(self) -> bool:
        """
        Block until the stream has closed

        Return True if the stream was cancelled/interrupted, False if the stream was closed normally.
        """
        async with self.completion_lock:
            return self.was_cancelled

class TransformStream(ValueStream):

    def __init__(self, activation_threshold:int=None, input_streams:list[ValueStream]=[],
                                  transform_fn:Callable[[T],T]|Callable[[T],Awaitable[T]]=None):
        """
        Do not call this directly, instead construct a stream using ValueStream.create_from_streams

        Args:
            activation_threshold: if supplied, block publishing onto this stream until this many subscribers are active
            input_streams: a list of input streams
            transform_fn: an optional function to transform values received on the input streams.  May be async or non-async.
        """
        super().__init__(activation_threshold)
        self.input_streams = []
        self.closed_count = 0
        self.cancelled_count = 0
        self.input_stream_count = 0
        self.subscriber_ids = []
        for input_stream in input_streams:
            self.attach_to(input_stream, transform_fn)

    def attach_to(self, input_stream:ValueStream, transform_fn:Callable[[T],T]|Callable[[T],Awaitable[T]]=None) -> str:
        """
        Attach an input stream and optionally, a transform function which will transform values received from that stream

        Args:
            input_stream: an input stream
            transform_fn: an optional function to transform values received on the input streams.  May be async or non-async.

        Returns:
            the subscriber id used to subscribe to the input stream
        """

        async def subscriber_fn(value):
            if transform_fn:
                if inspect.iscoroutinefunction(transform_fn):
                    value = await transform_fn(value)
                else:
                    value = transform_fn(value)
            await super(TransformStream,self).publish(value)

        async def close_fn(was_cancelled):
            self.closed_count += 1
            if was_cancelled:
                self.cancelled_count += 1
            if self.closed_count == self.input_stream_count:
                await self.close(was_cancelled=(self.cancelled_count>0))

        subscriber_id = input_stream.subscribe(subscriber_fn, close_fn)
        self.input_stream_count += 1
        self.input_streams.append(input_stream)
        self.subscriber_ids.append(subscriber_id)
        return subscriber_id

    def detach(self) -> None:
        """
        Detach from all input streams.
        """
        for idx in range(0,self.input_stream_count):
            self.input_streams[idx].unsubscribe(self.subscriber_ids[idx])
        self.input_streams = []
        self.subscriber_ids = []
        self.input_stream_count = 0

    def can_publish(self):
        """
        Check that values can be published to this stream.

        Raises:
            Always raises an exception - this kind of stream does not allow values to be published to it
        """
        raise Exception("Cannot publish directly to this kind of stream")

    async def publish(self, value:T):
        """
        Publish a value to this stream

        Args:
            value: value to be published

        Raises:
            Always raises an exception - this kind of stream does not allow values to be published to it
        """
        raise Exception("Cannot publish directly to this kind of stream")

class SourceStream(ValueStream):

    def __init__(self, activation_threshold:int|None=None):
        """
        Create a value stream which enables the caller to then publish values

        Args:
            activation_threshold: if supplied, block publishing onto this stream until this many subscribers are active
        """
        super().__init__(activation_threshold)










