import math
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from telegram_ui import (
    DisplayProfile, QuotaRow, QuotaWindow, ReplyIdentity, ReplyView,
    UsageView, render_reply, render_usage,
)


class ProfileTests(unittest.TestCase):
    def test_complete_identity_and_exact_body(self):
        profile = DisplayProfile.from_dict({
            'icons': {'writer': '🧠'}, 'account_mode': 'replace',
        })
        body = '  result\nTAGW_MEDIA: {"path":"synthetic.txt"}\n '
        view = ReplyView('writer', 'example-model', body, identity=ReplyIdentity(
            display_name='WRITER', effort='high', account='personal', speed='fast'))
        self.assertEqual(render_reply(view, profile=profile),
                         '🧠 **[personal]** · example\\-model · high · fast\n\n\u00a0\n\n' + body)

    def test_account_modes_and_field_order(self):
        view = ReplyView('writer', 'model', '', identity=ReplyIdentity(
            display_name='WRITER', effort='high', account='personal', speed='fast'))
        for mode, expected in [
            ('append', '⚡ **[WRITER]** · fast · personal · model'),
            ('replace', '⚡ **[personal]** · fast · model'),
            ('hide', '⚡ **[WRITER]** · fast · model'),
        ]:
            profile = DisplayProfile(account_mode=mode, fields=('speed', 'account', 'model'))
            self.assertEqual(render_reply(view, profile=profile).split('\n')[0], expected)

    def test_agent_rules_and_unknown_agent(self):
        profile = DisplayProfile.from_dict({
            'icons': {'builder': '🛠️'}, 'fallback_icon': '🤖',
            'hide_effort_for': ['builder'],
        })
        identity = ReplyIdentity(effort='high')
        self.assertEqual(render_reply(ReplyView('builder', None, '', identity=identity),
                                      profile=profile).split('\n')[0], '🛠️ **[builder]**')
        self.assertEqual(render_reply(ReplyView('unknown', None, '', identity=identity),
                                      profile=profile).split('\n')[0], '🤖 **[unknown]** · high')

    def test_missing_values_are_not_inferred_from_body(self):
        view = ReplyView('writer', None, 'model fast high personal', identity=ReplyIdentity())
        for mode in ('replace', 'append', 'hide'):
            self.assertEqual(render_reply(view, profile=DisplayProfile(account_mode=mode)).split('\n')[0],
                             '⚡ **[writer]**')

    def test_configuration_snapshot_and_profile_isolation(self):
        config = {'icons': {'writer': '🧠'}, 'fields': ['model'], 'hide_effort_for': ['writer']}
        profile = DisplayProfile.from_dict(config)
        config['icons']['writer'] = 'changed'
        config['fields'].append('speed')
        config['hide_effort_for'].clear()
        view = ReplyView('writer', 'model', '', identity=ReplyIdentity(speed='fast'))
        self.assertEqual(render_reply(view, profile=profile).split('\n')[0], '🧠 **[writer]** · model')
        self.assertEqual(render_reply(view).split('\n')[0], '⚡ **[writer]** · model · fast')
        with self.assertRaises(FrozenInstanceError):
            profile.account_mode = 'hide'

    def test_invalid_configuration(self):
        for config in [None, [], {'unknown': True}, {'icons': []}, {'fields': 'model'},
                       {'fields': ['model', 'model']}, {'fields': [[]]}, {'fields': ['body']},
                       {'account_mode': 'invalid'}, {'quota_precision': True},
                       {'quota_precision': -1}, {'quota_precision': 5},
                       {'show_reset_offset': 1}, {'hide_effort_for': 'writer'},
                       {'icons': {'writer': '\n'}}, {'fallback_icon': ''}]:
            with self.subTest(config=config), self.assertRaises(ValueError):
                DisplayProfile.from_dict(config)
        for kwargs in [{'icons': [('writer', '🤖')]}, {'fields': ['model']},
                       {'icons': (('writer', '🤖'), ('writer', '🧠'))},
                       {'icons': (('writer',),)}, {'hide_effort_for': []}]:
            with self.assertRaises(ValueError):
                DisplayProfile(**kwargs)

    def test_identity_labels_are_safe(self):
        for field in ('display_name', 'effort', 'account', 'speed'):
            for value in ('a\nb', 'a\u2028b', '', 1):
                with self.assertRaises(ValueError):
                    ReplyIdentity(**{field: value})
        view = ReplyView('writer', None, '', identity=ReplyIdentity(account='*alias*'))
        self.assertIn(r'\*alias\*', render_reply(view))
        with self.assertRaises(ValueError):
            ReplyView('writer', None, '', identity={})
        for renderer, view in [(render_reply, view), (render_usage, UsageView())]:
            with self.assertRaises(ValueError):
                renderer(view, profile={})

    def test_custom_quotas_keep_independent_values(self):
        view = UsageView(quota_rows=(
            QuotaRow('Daily', QuotaWindow(75.12, used_percent=20.34)),
            QuotaRow('*Monthly*'),
        ))
        text = render_usage(view, profile=DisplayProfile(quota_precision=2))
        self.assertIn('Daily: 20.34% used · 75.12% left', text)
        self.assertIn(r'\*Monthly\*: unavailable', text)
        self.assertNotIn('5h:', text)
        self.assertEqual(len(text.split('\n>\n')), 4)

    def test_absent_versus_unknown_quotas(self):
        self.assertEqual(len(render_usage(UsageView(quota_rows=())).split('\n>\n')), 2)
        self.assertIn('5h: unavailable', render_usage(UsageView()))
        for kwargs in [{'quota_rows': []}, {'quota_rows': ('bad',)},
                       {'quota_rows': (), 'five_hour': QuotaWindow(50)},
                       {'quota_rows': (QuotaRow('Daily'), QuotaRow('Daily'))}]:
            with self.assertRaises(ValueError):
                UsageView(**kwargs)
        with self.assertRaises(ValueError):
            QuotaRow('Daily', {})

    def test_percentage_bounds_and_zero(self):
        for value in (True, -1, 101, math.nan, math.inf, '10', 10**1000):
            with self.assertRaises(ValueError):
                QuotaWindow(50, used_percent=value)
        text = render_usage(UsageView(five_hour=QuotaWindow(50, used_percent=0)))
        self.assertIn('0.0% used · 50.0% left', text)

    def test_profile_applies_to_reply_usage(self):
        window = QuotaWindow(75, datetime(2030, 1, 2, tzinfo=timezone.utc))
        view = ReplyView('writer', None, '', UsageView(five_hour=window))
        text = render_reply(view, profile=DisplayProfile(quota_precision=2, show_reset_offset=False))
        self.assertIn('25.00% used · 75.00% left · resets 01/02 00:00', text)
        self.assertNotIn('+0000', text)
        self.assertIn('+0000', render_reply(view))
