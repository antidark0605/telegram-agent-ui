import math
import random
import unittest
from datetime import datetime, timezone

from telegram_ui import (
    ContextUsage, QuotaWindow, ReplyView, UsageView,
    render_progress, render_reply, render_usage, split_text, utf16_length,
)


class RenderingTests(unittest.TestCase):
    def test_running_progress_and_cancel_contract(self):
        view = render_progress(state='running', elapsed_seconds=12, task_id='synthetic-task')
        self.assertEqual(view.text, '**任務進度**\n—————\n**流程**：分析 → 修改 → 測試 → 完成\n**目前**：執行中\n**已執行**：12 秒')
        self.assertEqual(view.reply_markup['inline_keyboard'][0][0]['callback_data'], 'task:cancel:synthetic-task')

    def test_terminal_states_remove_cancel_and_activity(self):
        for state in ['completed', 'cancelled', 'failed']:
            view = render_progress(state=state, elapsed_seconds=0, task_id='synthetic', activity='old')
            self.assertEqual(view.reply_markup, {'inline_keyboard': []})
            self.assertNotIn('old', view.text)

    def test_waiting_can_be_stopped(self):
        view = render_progress(state='waiting', elapsed_seconds=30, task_id='synthetic', activity='等待選擇')
        self.assertIn('等待回覆', view.text)
        self.assertIn('等待選擇', view.text)
        self.assertTrue(view.reply_markup['inline_keyboard'])

    def test_callback_byte_limit(self):
        view = render_progress(state='running', elapsed_seconds=0, task_id='x' * 48)
        callback = view.reply_markup['inline_keyboard'][0][0]['callback_data']
        self.assertLessEqual(len(callback.encode()), 64)
        for task in ['', 'x' * 49, 'bad:task', '../path', '中文']:
            with self.assertRaises(ValueError):
                render_progress(state='running', elapsed_seconds=0, task_id=task)

    def test_invalid_progress_is_not_silently_successful(self):
        for values in [{'state': 'unknown'}, {'elapsed_seconds': True}, {'elapsed_seconds': -1}, {'flow': ()}]:
            args = dict(state='running', elapsed_seconds=0, task_id='synthetic')
            args.update(values)
            with self.assertRaises(ValueError):
                render_progress(**args)

    def test_optional_flow_and_escaped_labels(self):
        view = render_progress(state='running', elapsed_seconds=0, task_id='synthetic', flow=None, activity='**not bold**')
        self.assertNotIn('流程', view.text)
        self.assertIn(r'\*\*not bold\*\*', view.text)
        with self.assertRaises(ValueError):
            render_progress(state='running', elapsed_seconds=0, task_id='synthetic', activity='a\nb')

    def test_usage_quote_rows_and_unknown(self):
        text = render_usage(UsageView())
        self.assertEqual(len(text.split('\n>\n')), 4)
        for value in ['Context: unavailable', '5h: unavailable', 'Weekly: unavailable']:
            self.assertIn(value, text)
        self.assertNotIn('Quota checked', text)

    def test_verified_context_and_quota(self):
        data = UsageView(ContextUsage(250, 1000), QuotaWindow(75, datetime(2030, 1, 2, tzinfo=timezone.utc)), QuotaWindow(0), True)
        text = render_usage(data)
        self.assertIn('250 / 1,000 tokens (25.00%)', text)
        self.assertIn('25.0% used · 75.0% left', text)
        self.assertIn('100.0% used · 0.0% left', text)
        self.assertIn('+0000', text)
        self.assertIn('cached', text)

    def test_invalid_context_is_rejected(self):
        for used, window in [(True, 100), (0, 0), (-1, 100), (101, 100), (1, 2.0)]:
            with self.assertRaises(ValueError):
                ContextUsage(used, window)

    def test_invalid_quota_is_rejected(self):
        for value in [True, -1, 101, math.nan, math.inf, '75', 10**1000]:
            with self.assertRaises(ValueError):
                QuotaWindow(value)
        with self.assertRaises(ValueError):
            QuotaWindow(50, datetime(2030, 1, 1))

    def test_usage_schema_rejects_wrong_types(self):
        for values in [{'context': {}}, {'five_hour': 'unknown'}, {'cached': 1}]:
            with self.assertRaises(ValueError):
                UsageView(**values)

    def test_reply_preserves_body_and_spacers(self):
        body = 'Answer\nTAGW_MEDIA: {"path":"artifacts/synthetic.txt"}'
        text = render_reply(ReplyView('Example', 'example-model', body, UsageView()))
        self.assertEqual(text.count('\n\n\u00a0\n\n'), 2)
        self.assertIn(body, text)
        self.assertNotIn('Selected model', text)
        self.assertNotIn('Quota checked', text)

    def test_optional_model_and_usage(self):
        text = render_reply(ReplyView('Example', None, 'Answer'))
        self.assertEqual(text, '⚡ **[Example]**\n\n\u00a0\n\nAnswer')

    def test_untrusted_identity_cannot_add_lines(self):
        with self.assertRaises(ValueError):
            ReplyView('a\nb', 'model', 'answer')
        text = render_reply(ReplyView('Example', '*model*', 'answer'))
        self.assertIn(r'\*model\*', text)

    def test_unicode_and_newline_splitting(self):
        for text in ['x' * 9000, '中' * 9000, '😀' * 3800, '\n' * 5000, 'a\n' + '😀' * 5000]:
            parts = split_text(text)
            self.assertEqual(''.join(parts), text)
            self.assertTrue(all(0 < utf16_length(p) <= 4096 for p in parts))
        self.assertEqual(split_text(''), [])

    def test_seeded_split_boundary_cases(self):
        rng = random.Random(7)
        for _ in range(300):
            text = ''.join(rng.choice('ab中😀\n ') for _ in range(rng.randrange(200)))
            limit = rng.randrange(2, 30)
            chunks = split_text(text, limit)
            self.assertEqual(''.join(chunks), text)
            self.assertTrue(all(0 < utf16_length(c) <= limit for c in chunks))

    def test_invalid_split_limits(self):
        for value in [0, 1, -1, True, 4.5]:
            with self.assertRaises(ValueError):
                split_text('x', value)
