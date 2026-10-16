import asyncio
from io import BytesIO
import unittest
from telegram_transport import Destination, Document, Receipt, send_document, send_document_async


class DocumentTests(unittest.TestCase):
    def test_html_md_txt_exact_bytes_topic_and_lifetime(self):
        target = Destination(12345, 77)
        for ext in ['html', 'md', 'txt']:
            content = ('標題\n**raw**\r\n<tag>.' + ext).encode()
            stream = BytesIO(content)
            calls = []
            def sender(**kwargs):
                calls.append(kwargs)
                self.assertEqual(kwargs['document'].read(), content)
                self.assertEqual(kwargs['filename'], '報告.' + ext)
                self.assertEqual(kwargs['message_thread_id'], 77)
                self.assertEqual(kwargs['caption'], '範例')
                self.assertNotIn('parse_mode', kwargs)
                return Receipt(target, 1)
            receipt = send_document(sender, target, Document('報告.' + ext, stream, len(content), '範例'))
            self.assertEqual(receipt.destination, target)
            self.assertEqual(len(calls), 1)
            self.assertFalse(stream.closed)

    def test_over_limit_does_not_call_sender(self):
        def unexpected(**kwargs):
            self.fail('sender called')
        with self.assertRaises(ValueError):
            send_document(unexpected, Destination(1), Document('a.txt', BytesIO(b'abc'), 3), max_bytes=2)

    def test_exact_limit_and_omitted_optional_fields(self):
        def sender(**kwargs):
            self.assertNotIn('caption', kwargs)
            self.assertNotIn('message_thread_id', kwargs)
            return Receipt(Destination(1), 2)
        send_document(sender, Destination(1), Document('a', BytesIO(b'a'), 1), max_bytes=1)

    def test_error_never_retries_or_removes_topic(self):
        calls = []
        def sender(**kwargs):
            calls.append(kwargs)
            raise TimeoutError('ambiguous')
        with self.assertRaises(TimeoutError):
            send_document(sender, Destination(1, 2), Document('a', BytesIO(b'a'), 1))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['message_thread_id'], 2)

    def test_validation(self):
        for filename in ['', '.', '..', '../a', 'a/b', 'a\\b', 'a\n', 'a\x00']:
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                Document(filename, BytesIO(), 1)
        for size in [0, -1, True, 1.5]:
            with self.assertRaises(ValueError):
                Document('a', BytesIO(), size)
        with self.assertRaises(ValueError):
            Document('a', BytesIO(), 1, '😀' * 513)
        for topic in [0, -1, True, '1']:
            with self.assertRaises(ValueError):
                Destination(1, topic)

    def test_wrong_receipt_is_error_without_second_call(self):
        calls = []
        def sender(**kwargs):
            calls.append(kwargs)
            return Receipt(Destination(1, 3), 2)
        with self.assertRaises(ValueError):
            send_document(sender, Destination(1, 2), Document('a', BytesIO(b'a'), 1))
        self.assertEqual(len(calls), 1)


class AsyncDocumentTests(unittest.IsolatedAsyncioTestCase):
    async def test_await_keeps_stream_and_topic(self):
        stream = BytesIO(b'exact')
        async def sender(**kwargs):
            await asyncio.sleep(0)
            self.assertEqual(kwargs['document'].read(), b'exact')
            self.assertEqual(kwargs['message_thread_id'], 5)
            return Receipt(Destination(1, 5), 9)
        result = await send_document_async(sender, Destination(1, 5), Document('a.txt', stream, 5))
        self.assertEqual(result.message_id, 9)
        self.assertFalse(stream.closed)

    async def test_cancel_propagates_without_retry_or_closing_owned_stream(self):
        calls = []
        stream = BytesIO(b'a')
        async def sender(**kwargs):
            calls.append(kwargs)
            raise asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await send_document_async(sender, Destination(1), Document('a', stream, 1))
        self.assertEqual(len(calls), 1)
        self.assertFalse(stream.closed)
