# Phase 0 recording guide

Goal: about 70 short clips per speaker so we can test which speech service understands
isiZulu, Setswana, Xitsonga and mixed English best.

## Speakers
| ID | Who | Languages | Notes |
|---|---|---|---|
| s1 | You | en, zu, tn, ts | Also reviews the scripts first |
| s2 | ? | | |
| s3 | ? | | |
| s4 | ? | | |

A good mix (male and female, different ages and home regions) makes the results more trustworthy.
Each person records **only the languages they speak comfortably**, and English (`en01`–`en05`) too.

**Consent:** voices are personal information under POPIA. Before recording, tell each person the clips are only
used on your laptop to test speech software, aren't shared, and will be deleted when the
experiment ends. Get a clear "yes" from them, even just on WhatsApp.

## Before anyone records: review the scripts (s1)
The sentences in `phase0/prompts.csv` are drafts. **Correct anything that sounds unnatural**,
especially Setswana and Xitsonga, then regenerate the readable scripts:

```
uv run python -m phase0.prompts
```
Send speakers the matching file from `docs/phase0/` (`script-zu.md`, `script-tn.md`, `script-ts.md`, `script-en.md`).

## How to record

**Option A: iPhone Voice Memos (best)**
1. Record one clip per line and **rename each clip to its code** (`zu05`, `tn12`...).
2. Share the clips to the laptop (AirDrop isn't available on Windows, so use iCloud Drive, email or WhatsApp-as-document).

**Option B: WhatsApp voice notes (easiest for friends)**
1. Send one voice note per line, **in script order, without skipping any**. If you mess one up,
   re-record the whole language.
2. Export them and put them in a folder named after the language (see below). They're matched to the
   prompts by order, so the count must be exact.

**Tips:** quiet room, phone about 20 cm away, speak normally (not slowly or "radio voice"),
leave about 1 second of silence before and after.

If someone says something different from the script, or for the **free-speech** lines, write
what they actually said in `data/recordings/transcripts.csv`:
```
speaker,prompt_id,transcript
s2,zu21,"Eish Malume, today bekunzima emsebenzini, i-boss yami ibifuna i-report..."
```

## Where the files go
```
data/recordings/raw/
  s1/
    iph/            <- recorded on iPhone, files named zu05.m4a, tn12.m4a ...
    lap/            <- (optional) a few clips on the laptop mic
  s2/
    wa/             <- WhatsApp voice notes
      zu/           <- all isiZulu notes, in order
      en/
```
The `data/` folder is never committed to git.

## Run the benchmark
```
uv run python -m phase0.prepare                       # convert audio + build the clip list
uv sync --extra gemini --extra azure --extra mms      # install the engines (once)
uv run python -m phase0.benchmark --engines gemini --limit 5    # quick trial
uv run python -m phase0.benchmark --engines gemini azure mms    # everything
```
Put your API keys in `.env` first (copy `.env.example`). Results:
`data/results/summary.md` (scores) and `data/results/details.csv` (every transcript side by side).

## Also note
- In Setswana people may say **"Malome"** instead of "Malume". The wake word must accept both.
- Numbers: if a speaker says "fifteen" for "15", note it in transcripts.csv or it counts as an error.
