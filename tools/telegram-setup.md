# Telegram Setup

Telegram is the best fit for urgent alerts and lightweight mobile commands. It should be treated as a thin control surface, not as the source of truth. The source of truth stays in repo files and broker state.

## What Telegram is good for

- urgent trade alerts
- fill confirmations
- kill-switch warnings
- end-of-day summary delivery
- optional inbound commands like `status`, `halt`, `summary`

## What Telegram is bad for

- long-form journaling
- storing system state
- acting as the only audit trail

## BotFather setup

1. Open Telegram and search for `@BotFather`.
2. Run `/newbot`.
3. Choose a bot name and username.
4. Copy the bot token.
5. Add the bot to the chat where you want alerts delivered.

## Get your chat ID

Simplest path:

1. Send one message to the bot.
2. Use a Telegram API helper or a small script to inspect recent updates.
3. Copy the numeric `chat_id`.

Store the values in environment variables:

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## Suggested command set

Keep commands minimal and safe.

- `status` — return current mode, equity, open positions, last run times
- `summary` — return today’s short summary
- `halt` — create the halt flag and confirm it
- `resume` — remove halt only after manual confirmation

Avoid commands like `buy now` or `10x long BTC` unless the system is explicitly designed for that risk posture.

## Alert design

Recommended alerts:

- new trade placed
- stop updated materially
- position closed
- kill switch activated
- daily loss cap hit
- weekly review ready

Avoid:

- routine heartbeat spam
- every research note
- every price tick

## Security notes

- Treat the bot token like a password.
- Never commit the token.
- If the token leaks, revoke it in BotFather and rotate it.
- Keep withdrawals disabled on any broker connected to the workflow.
- Telegram should never be the only authorization boundary for moving money.
- Prefer alerts first. Add inbound commands only after the outbound path is stable.

## Repo integration

Telegram is a notification layer. The routine should still:

1. write state to files
2. update the journal/log
3. then send the Telegram message

If Telegram fails, the run should still preserve the file-based record.
