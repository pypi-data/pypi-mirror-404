"""
Utility classes and functions for working with aiohttp.
"""
import asyncio
import sys
from contextlib import AbstractContextManager
from multiprocessing.connection import Connection
from io import BytesIO
from aiohttp.streams import StreamReader
from aiohttp.web import Request, HTTPError
from aiohttp.client import ClientSession
from typing import Any, Optional, Protocol, AsyncIterator, BinaryIO
if sys.version_info >= (3, 11):
    from typing import Unpack
else:
    from typing_extensions import Unpack
from collections.abc import Iterator, Iterable, Sequence
from heaobject.root import json_dumps, DesktopObjectDict, DesktopObjectDictValue
from heaobject.user import NONE_USER
from .oidcclaimhdrs import SUB
from .appproperty import HEA_COMPONENT
from contextlib import asynccontextmanager
import logging
import os
import time
from typing import ParamSpec, Callable, TypeVar, overload
from enum import Enum
from yarl import URL
from itertools import zip_longest


class SortOrder(Enum):
    """
    Sort order enumeration for use in parsing the sort query parameter in HEA REST API calls. The _missing_
    method is overridden to make the enum case insensitive when parsing from strings.

    The enum has methods to help with sorting desktop object dictionaries. The key functions return a key function for
    use in sorting, and the reverse method returns a boolean for use in the sorted function's reverse parameter. By
    default, the key functions return a tuple of (whether the sort attribute is None, the value of the sort attribute).
    You can override the default key functions. The sorted and sort methods use these key functions to perform the
    actual sorting. There are versions of the key and sort methods that work with tuples of objects in which the first
    object in the tuple is the desktop object dictionary to sort by, and the remaining objects are associated data such
    as overall object permissions and attribute permissions.
    """
    ASC = "asc"
    DESC = "desc"

    def reverse(self) -> bool:
        """
        Returns an argument for the sorted function's reverse parameter.

        :return: True if descending, False if ascending.
        """
        return True if self == SortOrder.DESC else False

    def key_fn(self, sort_attr: str | None = 'display_name',
               sort_key: Optional[Callable[[DesktopObjectDict], Any]] = None) -> Callable[[DesktopObjectDict], Any]:
        """
        Returns a key function for use in sorting. The sorting methods allow replacing the use of this method with a
        custom function.

        :param sort_attr: The attribute to sort by.
        :param sort_key: An optional custom sort key function.
        :return: The key function.
        """
        if not sort_attr:
            sort_attr = 'display_name'
        if not sort_key:
            def sort_key(obj: DesktopObjectDict) -> tuple[bool, DesktopObjectDictValue]:
                val = obj.get(sort_attr)
                return (val is None, val)
        return sort_key

    def key_fn_with_perms(self, sort_attr: str | None = 'display_name',
                          sort_key: Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]] = None) -> Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]:
        """
        Returns a key function for use in sorting that includes permissions. The sorting methods allow replacing the
        use of this method with a custom function.

        :param sort_attr: The attribute to sort by.
        :param sort_key: An optional custom sort key function.
        :return: The key function.
        """
        if not sort_attr:
            sort_attr = 'display_name'
        if not sort_key:
            def sort_key(t: tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]) -> tuple[bool, DesktopObjectDictValue]:
                val = t[0].get(sort_attr)
                return (val is None, val)
        return sort_key

    def sorted(self, objs: Iterable[DesktopObjectDict], sort_attr: str | None = 'display_name',
               sort_key: Optional[Callable[[DesktopObjectDict], Any]] = None,
               key_fn: Optional[Callable[[str | None, Optional[Callable[[DesktopObjectDict], Any]]], Callable[[DesktopObjectDict], Any]]] = None) -> list[DesktopObjectDict]:
        """
        Returns a sorted list of the provided objects.

        :param objs: The objects to sort.
        :param sort_attr: The attribute to sort by.
        :param sort_key: An optional custom sort key function, passed into the key_fn method.
        :param key_fn: An optional custom key function generator. If provided, it will be used to generate a sort key
        instead of the key_fn method.
        :return: The sorted list.
        """
        return sorted(objs,
                      key=key_fn(sort_attr, sort_key) if key_fn else self.key_fn(sort_attr, sort_key),
                      reverse=self.reverse())

    def sorted_with_permissions(self, t: Iterable[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]],
                                sort_attr: str | None = 'display_name',
                                sort_key: Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]] = None,
                                key_fn: Optional[Callable[[str | None, Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]], Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]] = None) -> list[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]]:
        """
        Returns a sorted list of the provided objects that include associated metadata such as permissions.

        :param t: A tuple of objects and associated metadata to sort.
        :param sort_attr: The attribute to sort by.
        :param sort_key: An optional custom sort key function, passed into the key_fn_with_perms method.
        :param key_fn: An optional custom key function generator. If provided, it will be used to generate a sort key
        instead of the key_fn_with_perms method.
        :return: The sorted list.
        """
        return sorted(t,
                      key=key_fn(sort_attr, sort_key) if key_fn else self.key_fn_with_perms(sort_attr, sort_key),
                      reverse=self.reverse())

    def sort(self, objs: list[DesktopObjectDict], sort_attr: str | None = 'display_name',
             sort_key: Optional[Callable[[DesktopObjectDict], Any]] = None,
             key_fn: Optional[Callable[[str | None, Optional[Callable[[DesktopObjectDict], Any]]], Callable[[DesktopObjectDict], Any]]] = None) -> None:
        """
        Sorts the provided objects in place.

        :param objs: The objects to sort.
        :param sort_attr: The attribute to sort by.
        :param sort_key: An optional custom sort key function, passed into the key_fn method.
        :param key_fn: An optional custom key function generator. If provided, it will be used to generate a sort key
        instead of the key_fn method.
        """
        objs.sort(key=key_fn(sort_attr, sort_key) if key_fn else self.key_fn(sort_attr, sort_key),
                  reverse=self.reverse())

    def sort_with_permissions(self, t: list[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]],
                              sort_attr: str | None = 'display_name',
                              sort_key: Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]] = None,
                              key_fn: Optional[Callable[[str | None, Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]], Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]] = None) -> None:
        """
        Sorts the provided objects that include permissions in place.

        :param t: A tuple of objects and associated metadata to sort.
        :param sort_attr: The attribute to sort by.
        :param sort_key: An optional custom sort key function, passed into the key_fn_with_perms method.
        :param key_fn: An optional custom key function generator. If provided, it will be used to generate a sort key
        instead of the key_fn_with_perms method.
        """
        t.sort(key=key_fn(sort_attr, sort_key) if key_fn else self.key_fn_with_perms(sort_attr, sort_key),
               reverse=self.reverse())

    @classmethod
    def from_request(cls, request: Request) -> Optional['SortOrder']:
        """
        Extracts the sort order from the request's first sort query parameter.

        :param request: The request object.
        :return: The SortOrder, or None if no sort information is present.
        """
        sort_value = request.query.get('sort')
        return SortOrder(sort_value) if sort_value is not None else None

    @classmethod
    def _missing_(cls, value: Any) -> Optional['SortOrder']:
        """
        Convert the input value to lowercase for comparison.

        :param value: The input value.
        :return: The matching enum member or None.
        """
        lower_value = str(value).casefold()
        return next((member for member in cls if member.value.casefold() == lower_value), None)


CHUNK_SIZE = 16 * 1024


@asynccontextmanager
async def client_session(*args, **kwargs) -> AsyncIterator[ClientSession]:
    """
    Gets a new aiohttp ClientSession. The session's json_serialize parameter is set to heaobject.root.json_dumps,
    which unlike Python's native json serialization supports serializing timestamps. It supports any arguments that
    ClientSession's constructor supports.
    """
    session = ClientSession(json_serialize=json_dumps, *args, **kwargs)
    try:
        yield session
    finally:
        await session.close()


class ConnectionFileLikeObjectWrapper(AbstractContextManager):
    """
    Wraps a multiprocessing.connection.Connection object and provides file-like object methods.

    This class is a context manager, so it can be used in with statements.
    """

    def __init__(self, conn: Connection):
        """
        Creates a new ConnectionFileLikeObjectWrapper object, passing in the connection to wrap.

        :param conn: a multiprocessing.connection.Connection object (required).
        """
        if conn is None:
            raise ValueError('conn cannot be None')
        self.__conn = conn
        self.__buffer = BytesIO()

    def read(self, n=-1):
        """
        Reads up to n bytes. If n is not provided, or set to -1, reads until EOF and returns all read bytes.

        If the EOF was received and the internal buffer is empty, returns an empty bytes object.

        :param n: how many bytes to read, -1 for the whole stream.
        :return: the data.
        """
        if len(b := self.__buffer.read(n)) > 0:
            return b
        try:
            result = self.__conn.recv_bytes()
            if -1 < n < len(result):
                pos = self.__buffer.tell()
                self.__buffer.write(result[n:])
                self.__buffer.seek(pos)
                return result[:n]
            else:
                return result
        except EOFError:
            return b''

    def write(self, b):
        """
        Sends some bytes to the connection.

        :param b: some bytes (required).
        """
        self.__conn.send_bytes(b)

    def fileno(self) -> int:
        """
        Returns the integer file descriptor that is used by the connection.

        :return: the integer file descriptor.
        """
        return self.__conn.fileno()

    def close(self) -> None:
        """
        Closes the connection and any other resources associated with this object.
        """
        try:
            self.__buffer.close()
            self.__conn.close()
        finally:
            if not self.__conn.closed:
                try:
                    self.__conn.close()
                except OSError:
                    pass

    def __exit__(self, *exc_details):
        self.close()


class SupportsAsyncRead(Protocol):
    """
    Protocol with an async read() method and a close() method.
    """

    async def read(self, n=-1):
        """
        Reads up to n bytes. If n is not provided, or set to -1, reads until EOF and returns all read bytes.

        If the EOF was received and the internal buffer is empty, returns an empty bytes object.

        :param n: how many bytes to read, -1 for the whole stream.
        :return: the data.
        """
        pass

    def close(self):
        """
        Closes any resources associated with this object.
        """
        pass


class AsyncReader:
    """
    Wraps a bytes object in a simple reader with an asynchronous read method and a close method.
    """

    def __init__(self, b: bytes):
        """
        Creates a new AsyncReader, passing in a bytes object.

        :param b: bytes (required).
        """
        self.__b = BytesIO(b)

    async def read(self, n=-1):
        """
        Reads up to n bytes. If n is not provided, or set to -1, reads until EOF and returns all read bytes.

        If the EOF was received and the internal buffer is empty, returns an empty bytes object.

        :param n: how many bytes to read, -1 for the whole stream.
        :return: the data.
        """
        return self.__b.read(n)

    def close(self):
        """
        Closes any resources associated with this object.
        """
        self.__b.close()


class StreamReaderWrapper:
    """
    Wraps an aiohttp StreamReader in an asyncio StreamReader-like object with a read() method and a no-op close()
    method.
    """

    def __init__(self, reader: StreamReader):
        if reader is None:
            raise ValueError('reader cannot be None')
        self.__reader = reader

    async def read(self, n=-1):
        """
        Reads up to n bytes. If n is not provided, or set to -1, reads until EOF and returns all read bytes.

        If the EOF was received and the internal buffer is empty, returns an empty bytes object.

        :param n: how many bytes to read, -1 for the whole stream.
        :return: the data.
        """
        return await self.__reader.read(n)

    def close(self):
        pass


class RequestFileLikeWrapper:
    """
    Wraps an aiohttp request's content in a file-like object with read() and close() functions. Before doing any
    reading, call the initialize() method. The read() method must be called in a separate thread.
    """

    def __init__(self, request: Request, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """
        Creates the file-like object wrapper.

        :param request: the aiohttp request (required).
        :param loop: the current event loop. If None, it will use asyncio.get_running_loop().
        """
        if loop is not None:
            self.loop = loop
        else:
            self.loop = asyncio.get_running_loop()
        self.request = request
        self.__pump_task: asyncio.Task | None = None
        self.__reader: BinaryIO | None = None
        self.__writer: BinaryIO | None = None

    def initialize(self):
        """
        Creates resources needed for reading.
        """
        read_fd, write_fd = os.pipe()
        self.__reader = os.fdopen(read_fd, 'rb')
        self.__writer = os.fdopen(write_fd, 'wb')
        self.__pump_task = self.loop.create_task(self.__pump_bytes_into_fd())

    def read(self, n=-1, /) -> bytes:
        """
        Reads some bytes.

        :param n: the number of bytes to read (or -1 for everything).
        :return: the bytes that were read.
        """
        logger = logging.getLogger(__name__)
        logger.debug('Reading %s bytes', n)
        assert self.__reader is not None, 'Must call initialize() before calling read()'
        output = self.__reader.read(n)
        logger.debug('Read %s bytes', len(output))
        return output

    def close(self):
        """
        Cleans up all resources in this file-like object.
        """
        logger = logging.getLogger(__name__)
        logger.debug('Closing')
        try:
            if self.__writer is not None:
                self.__writer.close()
                self.__writer = None
            if self.__reader is not None:
                self.__reader.close()
                self.__reader = None
            while self.__pump_task is not None and not self.__pump_task.done():
                time.sleep(0.1)
            self.__pump_task = None
        except Exception as e:
            logger.exception('Failed to close pipe')
            if self.__reader is not None:
                try:
                    self.__reader.close()
                    self.__reader = None
                except:
                    pass
            try:
                while self.__pump_task is not None and not self.__pump_task.done():
                    time.sleep(0.1)
                self.__pump_task = None
            except:
                pass
            raise e

    async def __pump_bytes_into_fd(self):
        logger = logging.getLogger(__name__)
        writer_closed = False
        content_type = self.request.headers.get('Content-Type', '')
        try:
            if content_type.startswith('multipart/form-data'):
                logger.debug(f'Is multipart')
                mp_reader = await self.request.multipart()
                while True:
                    part = await mp_reader.next()
                    if part is None:
                        break
                    logger.debug("the part's headers %s" % part.headers)
                    while True:
                        chunk = await part.read_chunk(CHUNK_SIZE)
                        if not chunk or chunk == b'':
                            break
                        logger.debug('Read %d bytes from upload', len(chunk))
                        bytes_written = await self.loop.run_in_executor(None, self.__writer.write, chunk)
                        logger.debug('Wrote %d bytes to pipe', bytes_written)
            else:
                while not self.request.content.at_eof():
                    chunk = await self.request.content.read(CHUNK_SIZE)
                    logger.debug('Read %d bytes from upload', len(chunk))
                    bytes_written = await self.loop.run_in_executor(None, self.__writer.write, chunk)
                    logger.debug('Wrote %d bytes to pipe', bytes_written)
            self.__writer.close()
            writer_closed = True
            logger.debug('Done reading file')
        except Exception as e:
            logger.exception('Failed to read file')
            if not writer_closed:
                try:
                    self.__writer.close()
                except:
                    pass
                writer_closed = False
                raise e

def absolute_url_minus_base(request: Request, url: URL | str | None = None) -> str:
    """
    Removes the current service's base URL from the beginning of the provided URL. If no URL is provided, the request
    URL is used. If the provided URL is not prefixed with the service's base URL, the URL is returned unaltered.

    :param request: the HTTP request (required).
    :param url: optional URL.
    :return: the resulting URL.
    """
    if url is None:
        url_ = str(request.url)
    else:
        url_ = str(url)
    base_url = request.app[HEA_COMPONENT]
    if not url_.startswith(base_url):
        return url_
    else:
        return url_.removeprefix(base_url).lstrip('/')


P = ParamSpec('P')

def http_error_message(http_error: HTTPError, object_display_name: Callable[P, str], *args: P.args, **kwargs: P.kwargs) -> HTTPError:
    """
    If the HTTPError object has an empty body, it will try filling in the body with a message appropriate for the given
    status code for operations on desktop objects.

    :param http_error: the HTTPError (required). This object's body may be modified by this call if it is None or an
    empty byte array.
    :param object_display_name: a callable that generates a description of a desktop object for inclusion in an error
    message.
    :param args: positional arguments to pass to object_display_name.
    :param kwargs: keyword arguments to pass to object_display_name. The encoding keyword argument is reserved and will
    be used to set the encoding of the error message when encoded to bytes (the default is utf-8).
    :return: the updated HTTPError (the same object as the http_error argument).
    """
    encoding = kwargs.get('encoding')
    if encoding:
        encoding_ = str(encoding)
    else:
        encoding_ = 'utf-8'
    if not http_error.body:
        match http_error.status:
            case 403:
                http_error.body = f'Access to {object_display_name(*args, **kwargs)} is denied because you do not have sufficient permission for it'.encode(encoding=encoding_)
            case 404:
                http_error.body = f'{object_display_name(*args, **kwargs)} not found'.encode(encoding=encoding_)
    return http_error


def extract_sub(request: Request) -> str:
    """
    Extracts the current user (subject) from the request's OIDC_CLAIM_sub header.

    :param request: the HTTP request (required).
    :return: the user id, or system|none if the header has no value or is absent.
    """
    return request.headers.get(SUB, NONE_USER)


def extract_sort(request: Request) -> SortOrder | None:
    """
    Parse the sort query parameter from the request. Sort parameters are case insensitive.

    :param request: The request object.
    :return: the first sort parameter value, if present, or None.
    """
    return next(extract_sorts(request), None)


def extract_sorts(request: Request) -> Iterator[SortOrder]:
    """
    Parse the sort query parameter from the request. Sort parameters are case insensitive.

    :param request: The request object.
    :return: Iterator of sort parameter values, if present.
    """
    sorts = request.query.getall('sort') if 'sort' in request.query else []
    return (SortOrder(sort.strip()) for sort in sorts)


def extract_sort_attr(request: Request) -> str | None:
    """
    Parse the sort_attr query parameter from the request. Sort_attr parameters are case sensitive.

    :param request: The request object.
    :return: The first sort_attr parameter value, if present, or None
    """
    return next(extract_sort_attrs(request), None)


def extract_sort_attrs(request: Request) -> Iterator[str]:
    """
    Parse the sort_attr query parameter from the request. Sort_attr parameters are case sensitive.

    :param request: The request object.
    :return: Iterator of sort_attr parameter values, if present.
    """
    sort_attrs = request.query.getall('sort_attr') if 'sort_attr' in request.query else []
    return (sort_attr.strip() for sort_attr in sort_attrs)


def desktop_object_dict_sorted(request: Request, objs: Iterable[DesktopObjectDict],
                               default_sort_attr: str = 'display_name',
                               sort_key: Optional[Callable[[DesktopObjectDict], Any]] = None,
                               key_fn: Optional[Callable[[str | None, Optional[Callable[[DesktopObjectDict], Any]]], Callable[[DesktopObjectDict], Any]]] = None) -> list[DesktopObjectDict]:
    """
    Sorts the provided objects according to the sort and sort_attr query parameters in the request. Missing sort_attr
    parameters are defaulted to the provided default_sort_attr from left to right. Any sort_attr parameters more than
    the number of sort parameters are ignored. If no sort parameters are present, the objects are returned as a list
    without sorting. If there are duplicate sort parameters for the same sort attribute, the first one takes
    precedence. Sort parameters are case insensitive, and sort_attr parameters are case sensitive.

    :param request: The request object.
    :param objs: The objects to sort.
    :param default_sort_attr: The default sort attribute to use if no sort_attr parameter is present.
    :param sort_key: An optional custom sort key function.
    :param key_fn: An optional key function generator.
    :return: A sorted list of the provided objects.
    """
    if not default_sort_attr:
        default_sort_attr = 'display_name'
    sorts = extract_sorts(request)
    sort_attrs = extract_sort_attrs(request)
    all_sort_info = reversed(list(((sort, sort_attr or default_sort_attr) for sort, sort_attr in
                                   zip_longest(sorts, sort_attrs))))
    if first_sort := next(all_sort_info, None):
        objs_sorted = first_sort[0].sorted(objs, sort_attr=first_sort[1], sort_key=sort_key, key_fn=key_fn)
        for sort_order, sort_attr in all_sort_info:
            if not sort_order:
                break
            sort_order.sort(objs_sorted, sort_attr=sort_attr, sort_key=sort_key, key_fn=key_fn)
    else:
        objs_sorted = list(objs)
    return objs_sorted


def desktop_object_dict_sorted_with_permissions(request: Request, objs: Iterable[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]],
                                                default_sort_attr: str = 'display_name',
                                                sort_key: Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]] = None,
                                                key_fn: Optional[Callable[[str | None, Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]], Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]] = None) -> list[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]]:
    """
    Sorts the provided objects according to the sort and sort_attr query parameters in the request. Missing sort_attr
    parameters are defaulted to the provided default_sort_attr from left to right. Any sort_attr parameters more than
    the number of sort parameters are ignored. If no sort parameters are present, the objects are returned as a list
    without sorting. If there are duplicate sort parameters for the same sort attribute, the first one takes
    precedence. Sort parameters are case insensitive, and sort_attr parameters are case sensitive.

    :param request: The request object.
    :param objs: The objects to sort.
    :param default_sort_attr: The default sort attribute to use if no sort_attr parameter is present.
    :param sort_key: An optional custom sort key function. If provided, it will be passed into the key_fn generator.
    :param key_fn: An optional key function generator. If provided, it will be used to generate a sort key instead of
    the default generator (SortOrder.key_fn_with_perms).
    :return: A sorted list of the provided objects.
    """
    if not default_sort_attr:
        default_sort_attr = 'display_name'
    sorts = extract_sorts(request)
    sort_attrs = extract_sort_attrs(request)
    all_sort_info = reversed(list(((sort, sort_attr or default_sort_attr) for sort, sort_attr in \
                                   zip_longest(sorts, sort_attrs))))
    if first_sort := next(all_sort_info, None):
        objs_sorted = first_sort[0].sorted_with_permissions(objs, sort_attr=first_sort[1],
                                                            sort_key=sort_key, key_fn=key_fn)
        for sort_order, sort_attr in all_sort_info:
            if not sort_order:
                break
            sort_order.sort_with_permissions(objs_sorted, sort_attr=sort_attr,
                                             sort_key=sort_key, key_fn=key_fn)
    else:
        objs_sorted = list(objs)
    return objs_sorted


T1 = TypeVar('T1')
T2 = TypeVar('T2')


@overload
def sorted_response_data(
    request: Request,
    data: Iterable[DesktopObjectDict],
    *,
    default_sort_attr: str = ...,
    sort_key: Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]] = ...,
    key_fn: Optional[Callable[[str | None, Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]], Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]] = ...
) -> tuple[tuple[DesktopObjectDict, ...]]: ...


@overload
def sorted_response_data(
    request: Request,
    data: Iterable[DesktopObjectDict],
    __arg1: Iterable[T1],
    *,
    default_sort_attr: str = ...,
    sort_key: Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]] = ...,
    key_fn: Optional[Callable[[str | None, Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]], Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]] = ...
) -> tuple[tuple[DesktopObjectDict, ...], tuple[T1, ...]]: ...


@overload
def sorted_response_data(
    request: Request,
    data: Iterable[DesktopObjectDict],
    __arg1: Iterable[T1],
    __arg2: Iterable[T2],
    *,
    default_sort_attr: str = ...,
    sort_key: Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]] = ...,
    key_fn: Optional[Callable[[str | None, Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]], Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]] = ...
) -> tuple[tuple[DesktopObjectDict, ...], tuple[T1, ...], tuple[T2, ...]]: ...


def sorted_response_data(request: Request, data: Iterable[DesktopObjectDict], *args: Iterable[Any],
                         default_sort_attr: str = 'display_name',
                         sort_key: Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]] = None,
                         key_fn: Optional[Callable[[str | None, Optional[Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]], Callable[[tuple[DesktopObjectDict, Unpack[tuple[Any, ...]]]], Any]]] = None) -> tuple[tuple[Any, ...], ...]:
    """
    Returns a sorted list of all response data, including additional metadata like permissions. The additional metadata
    must be provided as additional sequences in the same order as the data sequence. None is not allowed.

    :param request: The HTTP request (required).
    :param data: The main response data to sort (required).
    :param args: Additional sequences of metadata to sort along with the main data.
    :param default_sort_attr: The default sort attribute to use if no sort_attr parameter is present.
    :param sort_key: An optional custom sort key function. If provided, it will be passed into the key_fn generator.
    :param key_fn: An optional key function generator. If provided, it will be used to generate a sort key instead of
    the default generator (SortOrder.key_fn_with_perms).
    :return: A tuple of sorted sequences, with the first sequence being the main data, and the rest being the additional
    metadata.
    """
    if not data:
        return tuple(() for _ in range(len(args) + 1))
    return tuple(zip(*desktop_object_dict_sorted_with_permissions(request, zip(data, *args), default_sort_attr=default_sort_attr, sort_key=sort_key, key_fn=key_fn)))  # type: ignore[return-value, call-overload]


def is_sorting_requested(request: Request) -> bool:
    """
    Determines if sorting is requested in the request via the presence of sort query parameters.

    :param request: The HTTP request (required).
    :return: True if sorting is requested, False otherwise.
    """
    return 'sort' in request.query
