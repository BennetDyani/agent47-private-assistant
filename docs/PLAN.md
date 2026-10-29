# Malume — Private AI Assistant: Plan

_Status: planning · Last updated: 2026-10-30_

## 1. Vision
**Malume** is a personal "virtual human" assistant with **eyes, ears, voice and hands**. It understands
**isiZulu, Setswana and (stretch) Xitsonga**, including natural **code-switching with English**.

This is an **experiment to test what's possible**, not a long-term product. We optimise for
learning fast and spending as close to **R0** as possible, with a **hard cap of R100/month**.

## 2. Decisions made
| Topic | Decision |
|---|---|
| Purpose | Prototype / exploration, not a long-term product |
| Budget | Free tiers first; **max R100/month** |
| Privacy | **Hybrid**: memory, files, logs and raw recordings stay local; only the needed snippets go to cloud APIs |
| Hands | **PC control** + **personal tools** (Gmail, Outlook, calendar, reminders, files) |
| Devices | Windows laptop (core + client) + **iPhone** (client) |
| Speech style | **Code-switching** (English mixed with isiZulu/Setswana) is the primary case |
| Persona | **Malume**: friendly, educated South African uncle (see §5) |
| Test data | The user (speaks all 3 languages + English) + 3 more speakers |
| Voice | Male |
| Code | Python 3.12 managed with uv |

## 3. Constraints
- Host machine: Intel i3-1115G4, ~20 GB RAM, integrated graphics, no GPU. Heavy models run in the
  cloud; light parts (wake word, voice detection, memory, tool execution, small TTS models) run locally.
- Budget means **free tiers**, and that comes with trade-offs:
  - Rate limits (requests per minute or per day). Fine for one person testing.
  - **Some free tiers (e.g. Gemini API free tier) may use your data to improve their products.**
    Don't send sensitive documents or screens while on free tiers.
  - Azure and Google Cloud sign-up asks for a card for identity checks, but the free tiers don't charge.
- iPhone: a native app needs a Mac and a paid Apple Developer account. **We'll use a web app (PWA)**
  in Safari instead. It's free, has microphone and camera access and can be added to the home screen.
  Limitation: **no "Hey Malume" wake word while the phone is locked**, so the phone uses push-to-talk.

## 4. Architecture

```
 iPhone (Safari PWA) ──┐   private tunnel (Tailscale, free)   ┌── Cloud (free tiers)
                       │                                       │   - Gemini API: brain + vision (+ audio?)
 Laptop client ────────┼──────►  CORE on laptop (Python)  ─────┼── - Azure Speech F0: isiZulu STT/TTS
                       │         - orchestrator + persona      │   - (others from Phase 0 benchmark)
                       │         - memory (SQLite)             │
                       │         - tools ("hands")             │
                       │         - permission gate + audit log │
                       │         - local TTS (MMS) for tn/ts   │
                       └─────────────────────────────────────  ┘
```

### Free / cheap component candidates
| Sense | Candidate | Cost | Notes |
|---|---|---|---|
| **Brain** | Google **Gemini API** (Flash models) | Free tier | Tool calling, vision and audio input. Decent isiZulu; Setswana/Xitsonga TBD in Phase 0 |
| | Groq (Llama/other open models) | Free tier | Backup brain; weaker on SA languages |
| **Ears (STT)** | **Gemini audio input** (transcribe + understand in one step) | Free tier | Might handle code-switching best. Must test |
| | **Azure Speech F0** (zu-ZA) | Free: ~5 audio hrs/month | isiZulu; check Setswana/Xitsonga support in Phase 0 |
| | **Meta MMS** (open model, covers zul/tsn/tso) | Free, local or Colab | Slow on this CPU; no code-switching training |
| | Lelapa AI Vulavula | Check free tier | SA-focused; check language list |
| **Voice (TTS)** | **Azure Neural TTS F0** (zu-ZA voices) | Free: ~0.5M chars/month | Natural isiZulu voice |
| | **Meta MMS-TTS** (zul/tsn/tso) | Free, runs on CPU | Robotic but works for Setswana/Xitsonga |
| | Edge/Windows built-in voices | Free | English fallback |
| **Wake word** | openWakeWord (custom "Malume") | Free | Laptop only |
| **Eyes** | Gemini vision (screenshots / camera frames) | Free tier | On demand only |
| **Hands: email** | Gmail API, Microsoft Graph (Outlook) | Free | OAuth, tokens stored locally |
| **Hands: PC** | Playwright (browser) + pywinauto (Windows apps), driven by LLM tool calls | Free | Computer-use models as a later option if free |
| **Memory** | SQLite (+ simple embeddings) | Free | Local |
| **Phone link** | Tailscale (personal plan) | Free | No public ports |

**Expected spend: R0.** The R100 cap is a buffer for going over a free tier.

## 5. Persona: Malume
- **Who:** a warm, educated South African uncle. Wise, patient, encouraging, a bit of humour. He gives
  advice the way a respected malume would: honest, never condescending.
- **Language behaviour:** answers in the language the user uses, and code-switches naturally the
  way the user does. Defaults to English if unsure.
- **Address forms:** calls the user something like *mshana* (isiZulu) / *motlogolo* (Setswana)
  when it fits, but not in every sentence. Uses greetings like *Sawubona*, *Dumela*, *Avuxeni*.
- **Style:** short spoken answers (it's a voice assistant), occasional proverb or idiom when it
  fits, local references (rands, load-shedding, taxis, etc.).
- **Guardrails:** respectful, no exaggerated stereotypes, admits when unsure ("Eish, mshana,
  I'm not sure about that one, let me check").
- **Native speakers check the tone** in Phase 1 so Malume sounds natural, not like a caricature.

## 6. Safety model for "hands"
1. Risk levels: **read** (automatic), **write/draft** (confirm), **send/delete/pay** (always confirm).
2. PC-control sessions are visible, interruptible ("Malume, stop!") and time-limited.
3. Every action goes into a local audit log.
4. API keys and OAuth tokens live in Windows Credential Manager or a local `.env`, never in git.

## 7. Phases (slimmed for a prototype)
| Phase | Goal | Exit criteria |
|---|---|---|
| **0. Language spike** | Choose STT/TTS/brain per language | ~20–30 clips per language (pure + code-switched), scored for accuracy and naturalness; vendors chosen |
| **1. Text Malume** | Core + text chat + persona + memory | Natural chat in isiZulu/Setswana; remembers facts; native speakers approve the tone |
| **2. Voice Malume** | Voice loop on laptop | Wake word or push-to-talk, then a spoken reply in about 3–5 s |
| **3. Hands** | Gmail + Outlook + calendar + files, then browser/PC control | Reads, drafts and sends with confirmation; does a simple multi-step PC task |
| **4. Eyes** | Screen + camera | "Malume, what's on my screen?" / "read this letter" |
| **5. iPhone** | PWA over Tailscale | Push-to-talk voice chat from the phone |
| _Stretch_ | Animated face/avatar, custom Malume voice, Xitsonga polish | — |

## 8. Phase 0 detail (next up)
1. **Recording script** (~25 prompts per language): greetings, questions, commands to Malume
   ("Malume, ngicela ufunde ama-email ami"), numbers/dates/times, names, and **code-switched** sentences.
2. Speakers record on the **iPhone and the laptop mic** (16 kHz WAV/M4A), and write the correct
   transcript for each clip.
3. Benchmark script runs each clip through every STT candidate and reports **word error rate** per language.
4. TTS check: listeners rate each voice 1–5 for clarity and naturalness.
5. Brain check: does the reply sound right in each language? Native speakers rate it.
6. Output: `docs/phase0-results.md` with the chosen setup.

## 9. Open questions
- [x] Voice: **male**
- [x] Programming language: **Python** core (uv, Python 3.12) + plain web (HTML/JS) PWA
- [x] Speakers: the user (speaks en/zu/tn/ts) + 3 more people
- [ ] Does Azure offer Setswana/Xitsonga STT/TTS? Verify in Phase 0
- [ ] Wake word must accept "Malume" and "Malome" (Setswana)

## 10. Risks
| Risk | Mitigation |
|---|---|
| Poor STT on code-switched speech | Benchmark Gemini audio vs Azure vs MMS; text fallback |
| Free tier limits/terms change | Keep each vendor behind a small adapter so it can be swapped |
| Free tier data used for training | No sensitive screens/docs while testing |
| Setswana/Xitsonga voice quality | MMS-TTS fallback; custom voice is a stretch goal |
| Agent does wrong thing on PC | Permission gate, confirmations, audit log, kill phrase |
| Laptop must be on for iPhone use | Acceptable for a prototype |
