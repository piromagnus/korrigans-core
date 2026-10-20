# Module mail

Adds the Chamberlain, who guards the user's attention at the door of their mailbox. Every morning
(`korrigans daily`), `korrigans mail` extracts the mail received since the last run from local mailboxes,
read only, into `state/mail/` (never versioned). The Chamberlain sorts it (skill `sort-mail`) and writes
`mail/YYYY-MM-DD.md`: what is for you, what is for information, how much was ignored. The Seneschal puts it
in the Morning Chronicle.

Enable it with `modules = ["mail"]` in `korrigans.toml`. By default it reads Thunderbird's inboxes
(`~/.thunderbird/*/ImapMail/*/INBOX`, `~/.thunderbird/*/Mail/*/Inbox`). For other mbox files:

```toml
[mail]
mailboxes = ["~/Mail/*/INBOX"]
```

The Chamberlain never sends and never deletes. It may move mail into agreed folders only once you have set up
that access and written it in `memory/global/registry.md`. Replies are drafts in `mail/drafts/`.
