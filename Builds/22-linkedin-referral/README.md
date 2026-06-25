# Referral Outreach Assistant (n8n) — Human-in-the-Loop

A small n8n workflow that helps you run a **referral / networking campaign** without
turning into a spammer or risking your LinkedIn account.

## The hard rule baked into this design
**It never touches LinkedIn programmatically.** No auto-connect, no auto-DM, no scraping
of LinkedIn while logged in. LinkedIn aggressively bans automation, and a ban during a job
hunt is the worst possible time. So this workflow stops at *drafting*. The actual send is
done by you, by hand, from your own account. That is the whole point.

## What it does
1. **Reads a target list** from a Google Sheet (columns: `name, company, role, profileUrl, status, jobReqId`).
2. **Filters** to people you haven't contacted yet (`status` empty).
3. **Drafts** two messages per person with an LLM, in your voice:
   - a <280-char LinkedIn connection note
   - a follow-up message that makes the referral ask
4. **Sends the drafts to your own Slack** (or email/Telegram — swap the last node) for review.
5. You read, tweak if needed, and **send manually** from LinkedIn. Then mark `status = contacted` in the sheet.

```
Manual Trigger → Google Sheet (targets) → IF not-contacted → LLM draft → Slack (to you)
                                                                              ↓
                                                                  YOU send by hand
```

## Setup
1. Import `referral-workflow.n8n.json` into n8n (Workflows → Import from File).
2. Set environment variables / credentials:
   - `REFERRAL_SHEET_ID` — your Google Sheet ID
   - `SLACK_REVIEW_CHANNEL` — a private channel or your DM
   - OpenAI credential for the draft node (gpt-4o-mini is plenty)
3. Make a Google Sheet named tab **Targets** with the columns above.
4. Run manually whenever you add new targets.

## Why human-in-the-loop is the feature, not a limitation
- **Account safety:** zero automated LinkedIn calls = zero ToS exposure.
- **Quality:** every message gets a human glance before it represents you.
- **Honesty:** a referral ask should feel personal; the LLM gets you 80% there, you add the 20% that makes it real.

## Tweaks worth making
- Swap the Slack node for **Gmail** (draft into your Drafts folder) or **Telegram**.
- Add a column `notes` and feed it to the LLM for personalization ("we both did SoME", "saw your KubeCon talk").
- Add a second sheet of *companies* and have the LLM pick the best person to ask.

## Do NOT do this
- Do not add an HTTP node that hits LinkedIn endpoints.
- Do not use unofficial LinkedIn automation nodes/community packages.
- Do not bulk-send identical messages — the drafts are per-person on purpose.
