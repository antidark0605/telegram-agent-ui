# telegram-agent-ui

Revision: 2 — 2026-10-16

Small, transport-independent Python presentation package for Telegram agent applications. Runtime dependencies: Python standard library only, Python 3.10+. Distribution name: `telegram-agent-ui`; import name: `telegram_ui`.

Initial 0.1.0 source candidate. No hosted package-index release or application migration is included. Install from a reviewed, fixed Git commit or a locally built wheel. This is a library, not a running Bot.

## Included

- Traditional Chinese task-progress view with elapsed time, optional activity and flow labels.
- A `🛑 中斷` button for active/waiting tasks; terminal views remove the button.
- Reply identity header, visible spacer paragraphs and Usage quote paragraphs. Each Usage row uses a separate quotation paragraph, avoiding folded Markdown soft line breaks. No “Selected model” or “Quota checked” label.
- Explicit unknown context/quota values; numeric bounds and timezone validation.
- Plain-text UTF-16 splitting that preserves all characters and complete Unicode code points.

```python
from telegram_ui import ReplyView, UsageView, render_progress, render_reply

progress = render_progress(
    state="running", elapsed_seconds=12, task_id="synthetic-task",
)
# Send progress.text and progress.reply_markup with your own Telegram client.

answer = render_reply(ReplyView(
    agent="Example", model="example-model", body="Task result",
    usage=UsageView(),
))
# Send answer as Rich Markdown using your application's existing transport.
```

`UsageView` optionally accepts `ContextUsage(used_tokens, window_tokens)` and `QuotaWindow(remaining_percent, resets_at)` for `five_hour`/`weekly`. Obtain these from a verified provider. A task's token totals do not establish live context occupancy. Reset times retain the caller-supplied timezone and show its UTC offset.

## Integration contract

This package only produces Markdown and button data. The application owns network calls, model catalogs, usage collection, sessions, scheduling, file permissions, recipient routing, delivery acknowledgement, retry policy and actual cancellation.

For cancellation, `callback_data` is `task:cancel:<task_id>` with a 1–48 character opaque ASCII identifier. The consumer must validate the authorized user/chat/topic, exact status message and current task before invoking its cancellation method. Rendering a button does not stop a task. Compute elapsed seconds from a monotonic clock; a flow line is a caller-provided checklist, not verified execution progress. Set `flow=None` if the default analysis/edit/test/done checklist is inappropriate.

Treat body Markdown as already prepared. Identity/activity labels are escaped and restricted to one line. `split_text` is for plain text, not arbitrary Markdown with formatting guarantees; Rich payload limits and safe fallback remain the transport's responsibility. Do not automatically remove a topic or resend after an ambiguous timeout.

Install a local checkout:

```sh
python -m pip install .
```

Applications should pin a reviewed full Git commit or verified wheel version rather than automatically fetching the default branch. No credentials or private application details belong in this repository.

## Verification

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
```

Tests cover active/terminal cancellation markup, callback byte limits, unknown/invalid usage, quote paragraphs, preserved reply markers, Unicode boundaries and deterministic randomized splitting. CI additionally installs a built wheel into a separate directory and imports it outside the checkout.

Real Telegram send/edit/client rendering and each application's authorization/cancellation integration still require separate acceptance testing. No existing service is changed by this package.

Manual acceptance for an integrating application: send a short task, verify progress and Stop while active, confirm only that task stops after an authorized click, confirm terminal buttons disappear, and verify Usage's four rows remain separate in the target client. Missing lines, retained terminal controls or cross-task cancellation fail acceptance.

## Sources

- [Telegram inline keyboard callbacks](https://core.telegram.org/bots/api#inlinekeyboardbutton)
- [Telegram Rich messages](https://core.telegram.org/bots/api#sendrichmessage)
- [Python packaging guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

License: MIT.

## Optional document contract package

The independent [`telegram-agent-transport`](packages/telegram-agent-transport/README.md) distribution provides synchronous/asynchronous document provider contracts and destination receipts. It is built and installed separately; `telegram_ui` retains its presentation-only contract. No application or live transport migration is included.
