# Turning the helpful/not-helpful votes into real numbers

Right now a vote is stored in the reader's own browser and nowhere else. The UI
responds and they are not asked twice, but **no total exists** — a static site has
no server to count on.

The report path (thumbs down → reason → GitHub issue or email) already works and
is the part with real value, because it reaches you.

If you want aggregate counts, the cheapest way is a Google Form. Free, unlimited,
and responses land in a spreadsheet.

## Setup, about ten minutes

1. Create a Google Form with three **short answer** questions, in this order:
   `page`, `vote`, `reason`.
2. Click **Send → link**, and note the form ID from the URL:
   `https://docs.google.com/forms/d/e/FORM_ID/viewform`
3. Open the live form, right-click → View Source, and search for `entry.` — you
   will find three ids like `entry.123456789`. Note which belongs to which
   question (they appear in the same order as your questions).
4. In `build.py`, set:

   ```python
   FEEDBACK_ENDPOINT = "https://docs.google.com/forms/d/e/FORM_ID/formResponse"
   FEEDBACK_FIELDS = {
       "page":   "entry.111111111",
       "vote":   "entry.222222222",
       "reason": "entry.333333333",
   }
   ```

5. Rebuild and push.

`templates/search.js` currently posts plain `page` / `vote` / `reason` field
names. When you fill in `FEEDBACK_FIELDS`, the field names need to be swapped to
the `entry.*` ids — that is a small change in the `record()` function, and worth
doing at the same time.

## Why `mode: "no-cors"`

Google Forms does not send CORS headers, so the browser will not let JavaScript
read the response. `no-cors` submits the data anyway and ignores the reply, which
is fine here: nothing depends on the answer. The trade is that a failed submission
is silent, so treat the counts as indicative rather than exact.

## Privacy

If you switch this on, votes leave the reader's browser and you are collecting
data. `content/privacy.md` currently says the site collects nothing directly —
**that would stop being true**, and the privacy page must be updated to say what
is collected (page URL, a vote, an optional reason category — no personal data)
before you enable it.
