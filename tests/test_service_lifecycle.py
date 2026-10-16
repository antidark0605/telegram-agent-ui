import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from telegram_ui.service_lifecycle import ServiceLifecycleView, render_service_lifecycle


class ServiceLifecycleTests(unittest.TestCase):
    def view(self, **overrides):
        values = dict(agent_label='Example Agent', state='ready',
                      started_at=datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
        values.update(overrides)
        return ServiceLifecycleView(**values)

    def test_unknown_reason_and_optional_release_exact_output(self):
        self.assertEqual(render_service_lifecycle(self.view()),
                         '🔔 **服務通知**\n**服務**：Example Agent\n**狀態**：服務已就緒\n'
                         '**啟動時間**：`2030-01-02T03:04:05+00:00`\n**原因**：原因未確認')

    def test_all_states_do_not_infer_a_cause(self):
        for state, label in [('ready', '服務已就緒'), ('restarted', '服務已重新啟動並就緒'),
                             ('recovered', '服務已恢復並就緒')]:
            text = render_service_lifecycle(self.view(state=state))
            self.assertIn('**狀態**：' + label, text)
            self.assertIn('原因未確認', text)
            self.assertNotIn('主機重新開機', text)
            self.assertNotIn('模型', text)

    def test_only_explicit_verified_reasons_are_shown(self):
        for reason, label in [('external_restart', '外部重新啟動服務'), ('host_reboot', '主機重新開機')]:
            self.assertIn('**原因**：' + label,
                          render_service_lifecycle(self.view(state='restarted', reason=reason)))

    def test_labels_and_release_are_escaped(self):
        text = render_service_lifecycle(self.view(agent_label='*Example* [A]', release='v1.2_test'))
        self.assertIn(r'\*Example\* \[A\]', text)
        self.assertIn(r'**版本**：v1\.2\_test', text)

    def test_invalid_labels_and_releases_rejected(self):
        for field in ['agent_label', 'release']:
            for value in ['', '   ', 1, 'x' * 301, 'a\nb', 'a\rb', 'a\tb',
                          'a\x00b', 'a\x7fb', 'a\u0085b', 'a\u2028b', 'a\u2029b']:
                with self.subTest(field=field, value=repr(value)), self.assertRaises(ValueError):
                    self.view(**{field: value})
        with self.assertRaises(ValueError):
            self.view(agent_label=None)
        self.assertIn('繁體😀', render_service_lifecycle(self.view(agent_label='繁體😀')))
        self.view(release='x' * 300)

    def test_naive_or_wrong_time_rejected(self):
        for value in [None, '2030-01-02', 0, datetime(2030, 1, 2)]:
            with self.assertRaises(ValueError):
                self.view(started_at=value)

    def test_original_timezone_retained(self):
        for offset, suffix in [(330, '+05:30'), (-210, '-03:30')]:
            at = datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(minutes=offset)))
            self.assertIn('2030-01-02T03:04:05' + suffix,
                          render_service_lifecycle(self.view(started_at=at)))

    def test_unknown_enums_and_unstructured_reason_rejected(self):
        for field in ['state', 'reason']:
            for value in ['', 'unknown', 'native_task_restart', True, [], {}, '/synthetic/path']:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.view(**{field: value})

    def test_immutable_deterministic_and_independent(self):
        view = self.view()
        with self.assertRaises(FrozenInstanceError):
            view.state = 'restarted'
        text = render_service_lifecycle(view)
        render_service_lifecycle(self.view(agent_label='Other', reason='host_reboot'))
        self.assertEqual(render_service_lifecycle(view), text)

    def test_renderer_requires_structured_view(self):
        for value in [None, {}, 'ready']:
            with self.assertRaises(ValueError):
                render_service_lifecycle(value)
