import asyncio
from http.server import SimpleHTTPRequestHandler
from typing import Any, Callable, Optional
from aiohttp import StreamReader
from aiohttp.hdrs import CONTENT_DISPOSITION
from aiohttp.test_utils import make_mocked_request
from socketserver import TCPServer, ThreadingMixIn
from threading import Thread
from unittest import IsolatedAsyncioTestCase, TestCase
from heaserver.service.aiohttp import client_session, StreamReaderWrapper, RequestFileLikeWrapper, \
    ConnectionFileLikeObjectWrapper, desktop_object_dict_sorted, desktop_object_dict_sorted_with_permissions, extract_sort, extract_sort_attr, extract_sort_attrs, extract_sorts, SortOrder, sorted_response_data
from pathlib import Path
import inspect
import os
from abc import ABC
from unittest import mock
from contextlib import closing
from heaobject.root import Permission, DesktopObjectDict, DesktopObjectDictValue


class HTTPServer(ThreadingMixIn, TCPServer):
    pass


class AbstractMyAioHTTPTestCase(IsolatedAsyncioTestCase, ABC):
    def setUp(self) -> None:
        self.old_cwd = os.getcwd()
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        path = os.path.dirname(os.path.abspath(filename))
        os.chdir(path)
        self.data = 'aiohttpdata/requirements_dev.txt'

    def tearDown(self) -> None:
        os.chdir(self.old_cwd)


class MyAioHTTPTestCase(AbstractMyAioHTTPTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.server = HTTPServer(('localhost', 0), SimpleHTTPRequestHandler)
        self.port = self.server.server_address[1]
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.start()

    async def test_client_session(self):
        async with client_session() as session:
            async with session.get(f'http://localhost:{self.port}') as response:
                self.assertEqual(200, response.status)

    async def test_stream_reader_wrapper(self):

        async with client_session() as session:
            async with session.get(f'http://localhost:{self.port}/{self.data}') as response:
                wrapper = StreamReaderWrapper(response.content)
                try:
                    self.assertEqual(Path(self.data).read_bytes(), await wrapper.read())
                finally:
                    wrapper.close()
                self.assertEqual(200, response.status)

    def tearDown(self) -> None:
        super().tearDown()
        self.server.shutdown()
        self.server.server_close()


class MyAioHTTPTestCase2(AbstractMyAioHTTPTestCase):

    async def test_request_file_like_wrapper(self):
        loop = asyncio.get_event_loop()
        protocol = mock.Mock(_reading_paused=False)
        filename = Path(self.data).name
        payload = StreamReader(protocol, 2**16, loop=loop)
        payload.feed_data(Path(self.data).read_bytes())
        payload.feed_eof()
        request = make_mocked_request(method='GET', path=f'/{filename}', payload=payload)
        with closing(RequestFileLikeWrapper(request, loop=loop)) as wrapper:
            wrapper.initialize()
            self.assertEqual(Path(self.data).read_bytes(), await loop.run_in_executor(None, wrapper.read))

    async def test_connection_file_like_object_wrapper(self):
        from multiprocessing import Pipe
        a, b = Pipe()
        the_bytes = Path(self.data).read_bytes()
        with closing(ConnectionFileLikeObjectWrapper(a)) as wrapper, closing(b) as b:
            b.send_bytes(the_bytes)
            self.assertEqual(the_bytes, wrapper.read())

class SimpleAioHTTPTestCase(IsolatedAsyncioTestCase):

    async def test_parse_sort_asc(self):
        request = make_mocked_request('GET', '/test?sort=asc')
        self.assertEqual(SortOrder.ASC, next(extract_sorts(request)), None)

    async def test_parse_sort_asc_with_space(self):
        request = make_mocked_request('GET', '/test?sort=asc ')
        self.assertEqual(SortOrder.ASC, next(extract_sorts(request)), None)

    async def test_parse_sort_desc(self):
        request = make_mocked_request('GET', '/test?sort=desc')
        self.assertEqual(SortOrder.DESC, next(extract_sorts(request)), None)

    async def test_parse_sort_ASC(self):
        request = make_mocked_request('GET', '/test?sort=ASC')
        self.assertEqual(SortOrder.ASC, next(extract_sorts(request)), None)

    async def test_parse_sort_DESC(self):
        request = make_mocked_request('GET', '/test?sort=DESC')
        self.assertEqual(SortOrder.DESC, next(extract_sorts(request)))


class SortOrderTestCase(TestCase):

    def test_missing(self):
        self.assertIsNone(SortOrder._missing_('invalid'))
        self.assertIsNone(SortOrder._missing_(''))

    def test_from_request_none(self):
        request = make_mocked_request('GET', '/test')
        self.assertIsNone(SortOrder.from_request(request))

    def test_from_request_asc(self):
        request = make_mocked_request('GET', '/test?sort=asc')
        self.assertEqual(SortOrder.ASC, SortOrder.from_request(request))

    def test_from_request_desc(self):
        request = make_mocked_request('GET', '/test?sort=desc')
        self.assertEqual(SortOrder.DESC, SortOrder.from_request(request))

    def test_from_request_asc_uppercase(self):
        request = make_mocked_request('GET', '/test?sort=ASC')
        self.assertEqual(SortOrder.ASC, SortOrder.from_request(request))

    def test_from_request_asc_mixed_case(self):
        request = make_mocked_request('GET', '/test?sort=AsC')
        self.assertEqual(SortOrder.ASC, SortOrder.from_request(request))

    def test_sorted_asc(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        sorted_objs = SortOrder.ASC.sorted(objs, 'display_name')
        self.assertEqual(['Alice', 'Bob', 'Charlie'], [obj['display_name'] for obj in sorted_objs])

    def test_sorted_desc(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        sorted_objs = SortOrder.DESC.sorted(objs, 'display_name')
        self.assertEqual(['Charlie', 'Bob', 'Alice'], [obj['display_name'] for obj in sorted_objs])

    def test_sort_asc(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        SortOrder.ASC.sort(objs, 'display_name')
        self.assertEqual(['Alice', 'Bob', 'Charlie'], [obj['display_name'] for obj in objs])

    def test_sort_desc(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        SortOrder.DESC.sort(objs, 'display_name')
        self.assertEqual(['Charlie', 'Bob', 'Alice'], [obj['display_name'] for obj in objs])

class ExtractSortsTestCase(TestCase):

    def test_extract_sorts_none(self):
        request = make_mocked_request('GET', '/test')
        sorts = list(extract_sorts(request))
        self.assertEqual(0, len(sorts))

    def test_extract_sorts_single(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorts = list(extract_sorts(request))
        self.assertEqual([SortOrder.ASC], sorts)

    def test_extract_sorts_multiple(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=display_name&sort_attr=created_at')
        sorts = list(extract_sorts(request))
        self.assertEqual([SortOrder.ASC, SortOrder.DESC], sorts)

    def test_extract_sorts_extra_sort_attrs(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name&sort_attr=created_at')
        sorts = list(extract_sorts(request))
        self.assertEqual([SortOrder.ASC], sorts)

    def test_extract_sorts_missing_sort_attrs(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=display_name')
        sorts = list(extract_sorts(request))
        self.assertEqual([SortOrder.ASC, SortOrder.DESC], sorts)

    def test_extract_sorts_no_sort_attrs(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc')
        sorts = list(extract_sorts(request))
        self.assertEqual([SortOrder.ASC, SortOrder.DESC], sorts)

class DesktopObjectDictSortedTestCase(TestCase):
    def test_sorted_none(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        request = make_mocked_request('GET', '/test')
        sorted_objs = desktop_object_dict_sorted(request, objs)
        self.assertEqual(['Charlie', 'Alice', 'Bob'], [obj['display_name'] for obj in sorted_objs])

    def test_sorted_single_default_attr_asc(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        request = make_mocked_request('GET', '/test?sort=asc')
        sorted_objs = desktop_object_dict_sorted(request, objs)
        self.assertEqual(['Alice', 'Bob', 'Charlie'], [obj['display_name'] for obj in sorted_objs])

    def test_sorted_single_asc(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorted_objs = desktop_object_dict_sorted(request, objs)
        self.assertEqual(['Alice', 'Bob', 'Charlie'], [obj['display_name'] for obj in sorted_objs])

    def test_sorted_single_desc(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        request = make_mocked_request('GET', '/test?sort=desc&sort_attr=display_name')
        sorted_objs = desktop_object_dict_sorted(request, objs)
        self.assertEqual(['Charlie', 'Bob', 'Alice'], [obj['display_name'] for obj in sorted_objs])

    def test_sorted_multiple(self):
        objs = [
            {'display_name': 'Charlie', 'created_at': '2023-01-02'},
            {'display_name': 'Alice', 'created_at': '2023-01-03'},
            {'display_name': 'Bob', 'created_at': '2023-01-01'},
            {'display_name': 'Bob', 'created_at': '2023-01-02'}
        ]
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=display_name&sort_attr=created_at')
        sorted_objs = desktop_object_dict_sorted(request, objs)
        self.assertEqual(
            [('Alice', '2023-01-03'), ('Bob', '2023-01-02'), ('Bob', '2023-01-01'), ('Charlie', '2023-01-02')],
            [(obj['display_name'], obj['created_at']) for obj in sorted_objs]
        )

    def test_sorted_missing_sort_attr(self):
        objs = [
            {'display_name': 'Charlie', 'created_at': '2023-01-02'},
            {'display_name': 'Alice', 'created_at': '2023-01-03'},
            {'display_name': 'Bob', 'created_at': '2023-01-01'},
            {'display_name': 'Bob', 'created_at': '2023-01-02'}
        ]
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=created_at')
        sorted_objs = desktop_object_dict_sorted(request, objs)
        self.assertEqual(
            [('Bob', '2023-01-01'), ('Charlie', '2023-01-02'), ('Bob', '2023-01-02'), ('Alice', '2023-01-03')],
            [(obj['display_name'], obj['created_at']) for obj in sorted_objs]
        )

    def test_sorted_duplicate_asc(self):
        objs = [
            {'display_name': 'Alice'},
            {'display_name': 'Bob'},
            {'display_name': 'Alice'}
        ]
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc')
        sorted_objs = desktop_object_dict_sorted(request, objs)
        self.assertEqual(['Alice', 'Alice', 'Bob'], [obj['display_name'] for obj in sorted_objs])

    def test_sorted_duplicate_desc(self):
        objs = [
            {'display_name': 'Alice'},
            {'display_name': 'Bob'},
            {'display_name': 'Alice'}
        ]
        request = make_mocked_request('GET', '/test?sort=desc&sort=asc')
        sorted_objs = desktop_object_dict_sorted(request, objs)
        self.assertEqual(['Bob', 'Alice', 'Alice'], [obj['display_name'] for obj in sorted_objs])

    def test_sorted_with_custom_sort_key(self):
        objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'alice'},
            {'display_name': 'bob'}
        ]
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorted_objs = desktop_object_dict_sorted(request, objs, sort_key=lambda obj: obj['display_name'].lower())
        # Would be Charlie, alice, bob without the custom sort key.
        self.assertEqual(['alice', 'bob', 'Charlie'], [obj['display_name'] for obj in sorted_objs])

class DesktopObjectDictSortedWithPermissionsTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self) -> None:
        self.objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        self.perms = [Permission.VIEWER, Permission.EDITOR, Permission.COOWNER]
        self.attr_perms = [Permission.VIEWER, Permission.EDITOR, Permission.VIEWER]
        self.zipped_objs = zip(self.objs, self.perms, self.attr_perms)


    def test_sorted_none(self):
        request = make_mocked_request('GET', '/test')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(request, self.zipped_objs)))
        self.assertEqual([({'display_name': 'Charlie'}, {'display_name': 'Alice'}, {'display_name': 'Bob'}),
                         (Permission.VIEWER, Permission.EDITOR, Permission.COOWNER),
                         (Permission.VIEWER, Permission.EDITOR, Permission.VIEWER)],
                         sorted_objs)

    def test_sorted_single_default_attr_asc(self):
        request = make_mocked_request('GET', '/test?sort=asc')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(request, self.zipped_objs)))
        self.assertEqual([({'display_name': 'Alice'}, {'display_name': 'Bob'}, {'display_name': 'Charlie'}),
                         (Permission.EDITOR, Permission.COOWNER, Permission.VIEWER),
                         (Permission.EDITOR, Permission.VIEWER, Permission.VIEWER)],
                         sorted_objs)

    def test_sorted_single_asc(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(request, self.zipped_objs)))
        self.assertEqual([({'display_name': 'Alice'}, {'display_name': 'Bob'}, {'display_name': 'Charlie'}),
                         (Permission.EDITOR, Permission.COOWNER, Permission.VIEWER),
                         (Permission.EDITOR, Permission.VIEWER, Permission.VIEWER)],
                         sorted_objs)

    def test_sorted_single_default_attr_desc(self):
        request = make_mocked_request('GET', '/test?sort=desc')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(request, self.zipped_objs)))
        self.assertEqual([({'display_name': 'Charlie'}, {'display_name': 'Bob'}, {'display_name': 'Alice'}),
                         (Permission.VIEWER, Permission.COOWNER, Permission.EDITOR),
                         (Permission.VIEWER, Permission.VIEWER, Permission.EDITOR)],
                         sorted_objs)

    def test_sorted_single_desc(self):
        request = make_mocked_request('GET', '/test?sort=desc&sort_attr=display_name')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(request, self.zipped_objs)))
        self.assertEqual([({'display_name': 'Charlie'}, {'display_name': 'Bob'}, {'display_name': 'Alice'}),
                         (Permission.VIEWER, Permission.COOWNER, Permission.EDITOR),
                         (Permission.VIEWER, Permission.VIEWER, Permission.EDITOR)],
                         sorted_objs)

class DesktopObjectDictSortedWithPermissionsAndCustomSortKeyTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self) -> None:
        self.objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'alice'},
            {'display_name': 'bob'}
        ]
        self.perms = [Permission.VIEWER, Permission.EDITOR, Permission.COOWNER]
        self.attr_perms = [Permission.VIEWER, Permission.EDITOR, Permission.VIEWER]
        self.zipped_objs = zip(self.objs, self.perms, self.attr_perms)
        self.sort_key = lambda obj: obj[0]['display_name'].lower()


    def test_sorted_single_asc_with_custom_sort_key(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(
            request,
            self.zipped_objs,
            sort_key=self.sort_key
        )))
        self.assertEqual([({'display_name': 'alice'}, {'display_name': 'bob'}, {'display_name': 'Charlie'}),
                         (Permission.EDITOR, Permission.COOWNER, Permission.VIEWER),
                         (Permission.EDITOR, Permission.VIEWER, Permission.VIEWER)],
                         sorted_objs)

class DesktopObjectDictSortedWithPermissionsAndCustomKeyFnTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self) -> None:
        self.objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'alice'},
            {'display_name': 'bob'}
        ]
        self.perms = [Permission.VIEWER, Permission.EDITOR, Permission.COOWNER]
        self.attr_perms = [Permission.VIEWER, Permission.EDITOR, Permission.VIEWER]
        self.zipped_objs = zip(self.objs, self.perms, self.attr_perms)
        def key_fn(sort_attr: str | None = 'display_name',
                   sort_key: Optional[Callable[[tuple[DesktopObjectDict, ...]], Any]] = None):
            if not sort_attr:
                sort_attr = 'display_name'
            if not sort_key:
                def sort_key(obj: tuple[DesktopObjectDict, ...]) -> tuple[bool, DesktopObjectDictValue]:
                    val = obj[0].get(sort_attr)
                    return (val is None, val.lower() if val else None)
            return sort_key
        self.key_fn = key_fn


    def test_sorted_single_asc_with_custom_sort_key(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(
            request,
            self.zipped_objs,
            key_fn=self.key_fn
        )))
        self.assertEqual([({'display_name': 'alice'}, {'display_name': 'bob'}, {'display_name': 'Charlie'}),
                         (Permission.EDITOR, Permission.COOWNER, Permission.VIEWER),
                         (Permission.EDITOR, Permission.VIEWER, Permission.VIEWER)],
                         sorted_objs)

class DesktopObjectDictSortedResponseDataTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self) -> None:
        self.objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'Alice'},
            {'display_name': 'Bob'}
        ]
        self.perms = [Permission.VIEWER, Permission.EDITOR, Permission.COOWNER]
        self.attr_perms = [Permission.VIEWER, Permission.EDITOR, Permission.VIEWER]


    def test_sorted_none(self):
        request = make_mocked_request('GET', '/test')
        sorted_objs = sorted_response_data(request, self.objs, self.perms, self.attr_perms)
        self.assertEqual((({'display_name': 'Charlie'}, {'display_name': 'Alice'}, {'display_name': 'Bob'}),
                         (Permission.VIEWER, Permission.EDITOR, Permission.COOWNER),
                         (Permission.VIEWER, Permission.EDITOR, Permission.VIEWER)),
                         sorted_objs)

    def test_sorted_single_default_attr_asc(self):
        request = make_mocked_request('GET', '/test?sort=asc')
        sorted_objs = sorted_response_data(request, self.objs, self.perms, self.attr_perms)
        self.assertEqual((({'display_name': 'Alice'}, {'display_name': 'Bob'}, {'display_name': 'Charlie'}),
                         (Permission.EDITOR, Permission.COOWNER, Permission.VIEWER),
                         (Permission.EDITOR, Permission.VIEWER, Permission.VIEWER)),
                         sorted_objs)

    def test_sorted_single_asc(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorted_objs = sorted_response_data(request, self.objs, self.perms, self.attr_perms)
        self.assertEqual((({'display_name': 'Alice'}, {'display_name': 'Bob'}, {'display_name': 'Charlie'}),
                         (Permission.EDITOR, Permission.COOWNER, Permission.VIEWER),
                         (Permission.EDITOR, Permission.VIEWER, Permission.VIEWER)),
                         sorted_objs)

    def test_sorted_single_default_attr_desc(self):
        request = make_mocked_request('GET', '/test?sort=desc')
        sorted_objs = sorted_response_data(request, self.objs, self.perms, self.attr_perms)
        self.assertEqual((({'display_name': 'Charlie'}, {'display_name': 'Bob'}, {'display_name': 'Alice'}),
                         (Permission.VIEWER, Permission.COOWNER, Permission.EDITOR),
                         (Permission.VIEWER, Permission.VIEWER, Permission.EDITOR)),
                         sorted_objs)

    def test_sorted_single_desc(self):
        request = make_mocked_request('GET', '/test?sort=desc&sort_attr=display_name')
        sorted_objs = sorted_response_data(request, self.objs, self.perms, self.attr_perms)
        self.assertEqual((({'display_name': 'Charlie'}, {'display_name': 'Bob'}, {'display_name': 'Alice'}),
                         (Permission.VIEWER, Permission.COOWNER, Permission.EDITOR),
                         (Permission.VIEWER, Permission.VIEWER, Permission.EDITOR)),
                         sorted_objs)

class DesktopObjectDictSortedResponseAndCustomSortKeyDataTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self) -> None:
        self.objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'alice'},
            {'display_name': 'bob'}
        ]
        self.perms = [Permission.VIEWER, Permission.EDITOR, Permission.COOWNER]
        self.attr_perms = [Permission.VIEWER, Permission.EDITOR, Permission.VIEWER]
        self.sort_key = lambda obj: obj[0]['display_name'].lower()


    def test_sorted_single_asc_with_custom_sort_key(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorted_objs = sorted_response_data(
            request,
            self.objs,
            self.perms,
            self.attr_perms,
            sort_key=self.sort_key
        )
        self.assertEqual((({'display_name': 'alice'}, {'display_name': 'bob'}, {'display_name': 'Charlie'}),
                         (Permission.EDITOR, Permission.COOWNER, Permission.VIEWER),
                         (Permission.EDITOR, Permission.VIEWER, Permission.VIEWER)),
                         sorted_objs)


class DesktopObjectDictSortedResponseAndCustomKeyFnDataTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self) -> None:
        self.objs = [
            {'display_name': 'Charlie'},
            {'display_name': 'alice'},
            {'display_name': 'bob'}
        ]
        self.perms = [Permission.VIEWER, Permission.EDITOR, Permission.COOWNER]
        self.attr_perms = [Permission.VIEWER, Permission.EDITOR, Permission.VIEWER]
        def key_fn(sort_attr: str | None = 'display_name',
                   sort_key: Optional[Callable[[tuple[DesktopObjectDict, ...]], Any]] = None):
            if not sort_attr:
                sort_attr = 'display_name'
            if not sort_key:
                def sort_key(obj: tuple[DesktopObjectDict, ...]) -> tuple[bool, DesktopObjectDictValue]:
                    val = obj[0].get(sort_attr)
                    return (val is None, val.lower() if val else None)
            return sort_key
        self.key_fn = key_fn


    def test_sorted_single_asc_with_custom_sort_key(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort_attr=display_name')
        sorted_objs = sorted_response_data(
            request,
            self.objs,
            self.perms,
            self.attr_perms,
            key_fn=self.key_fn
        )
        self.assertEqual((({'display_name': 'alice'}, {'display_name': 'bob'}, {'display_name': 'Charlie'}),
                         (Permission.EDITOR, Permission.COOWNER, Permission.VIEWER),
                         (Permission.EDITOR, Permission.VIEWER, Permission.VIEWER)),
                         sorted_objs)

class DesktopObjectDictSortedMultipleWithPermissionsTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self) -> None:
        self.objs = [
            {'display_name': 'Charlie', 'created_at': '2023-01-02'},
            {'display_name': 'Alice', 'created_at': '2023-01-03'},
            {'display_name': 'Bob', 'created_at': '2023-01-01'},
            {'display_name': 'Bob', 'created_at': '2023-01-02'}
        ]
        self.perms = [Permission.VIEWER, Permission.EDITOR, Permission.COOWNER, Permission.DELETER]
        self.attr_perms = [Permission.VIEWER, Permission.EDITOR, Permission.VIEWER, Permission.EDITOR]
        self.zipped_objs = list(zip(self.objs, self.perms, self.attr_perms))

    def test_sorted_multiple(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=display_name&sort_attr=created_at')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(request, self.zipped_objs)))
        self.assertEqual(
            [('Alice', '2023-01-03'), ('Bob', '2023-01-02'), ('Bob', '2023-01-01'), ('Charlie', '2023-01-02')],
            [(obj['display_name'], obj['created_at']) for obj in sorted_objs[0]]
        )

    def test_sorted_missing_sort_attr(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc&sort_attr=created_at')
        sorted_objs = list(zip(*desktop_object_dict_sorted_with_permissions(request, self.zipped_objs)))
        self.assertEqual(
            [('Bob', '2023-01-01'), ('Charlie', '2023-01-02'), ('Bob', '2023-01-02'), ('Alice', '2023-01-03')],
            [(obj['display_name'], obj['created_at']) for obj in sorted_objs[0]]
        )

class ExtractSortAttrsTestCase(TestCase):
    def test_extract_sort_attrs_none(self):
        request = make_mocked_request('GET', '/test')
        sort_attrs = list(extract_sort_attrs(request))
        self.assertEqual(0, len(sort_attrs))

    def test_extract_sort_attrs_single(self):
        request = make_mocked_request('GET', '/test?sort_attr=display_name')
        sort_attrs = list(extract_sort_attrs(request))
        self.assertEqual(['display_name'], sort_attrs)

    def test_extract_sort_attrs_multiple(self):
        request = make_mocked_request('GET', '/test?sort_attr=display_name&sort_attr=created_at')
        sort_attrs = list(extract_sort_attrs(request))
        self.assertEqual(['display_name', 'created_at'], sort_attrs)

    def test_extract_sort_attrs_with_spaces(self):
        request = make_mocked_request('GET', '/test?sort_attr= display_name &sort_attr= created_at ')
        sort_attrs = list(extract_sort_attrs(request))
        self.assertEqual(['display_name', 'created_at'], sort_attrs)


class ExtractSortAttrTestCase(TestCase):
    def test_extract_sort_attr_none(self):
        request = make_mocked_request('GET', '/test')
        self.assertEqual(None, extract_sort_attr(request))

    def test_extract_sort_attr_single(self):
        request = make_mocked_request('GET', '/test?sort_attr=display_name')
        sort_attr = extract_sort_attr(request)
        self.assertEqual('display_name', sort_attr)

    def test_extract_sort_attr_multiple(self):
        request = make_mocked_request('GET', '/test?sort_attr=display_name&sort_attr=created_at')
        sort_attr = extract_sort_attr(request)
        self.assertEqual('display_name', sort_attr)


class ExtractSortTestCase(TestCase):
    def test_extract_sort_none(self):
        request = make_mocked_request('GET', '/test')
        self.assertIsNone(extract_sort(request), None)

    def test_extract_sort_single(self):
        request = make_mocked_request('GET', '/test?sort=asc')
        sort = extract_sort(request)
        self.assertEqual(SortOrder.ASC, sort)

    def test_extract_sort_multiple(self):
        request = make_mocked_request('GET', '/test?sort=asc&sort=desc')
        sort = extract_sort(request)
        self.assertEqual(SortOrder.ASC, sort)


class SortOrderFromRequestTestCase(TestCase):

    def test_from_request_invalid(self):
        request = make_mocked_request('GET', '/test?sort=invalid')
        self.assertRaises(ValueError, SortOrder.from_request, request)

    def test_from_request_empty(self):
        request = make_mocked_request('GET', '/test?sort=')
        self.assertRaises(ValueError, SortOrder.from_request, request)

    def test_from_request_whitespace(self):
        request = make_mocked_request('GET', '/test?sort=   ')
        self.assertRaises(ValueError, SortOrder.from_request, request)
