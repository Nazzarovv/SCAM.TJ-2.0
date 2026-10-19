# SCAM.TJ 3.0 — Product Requirements & Progress

## Original Problem Statement
Build SCAM.TJ 3.0, a polished, production-ready anti-scam mobile app (Expo + React Native + TypeScript) for Android & iOS. Helps ordinary users identify dangerous links, suspicious websites, scam messages, suspicious phone numbers, fraudulent offers and phishing. Clean modern LIGHT UI (Apple/Linear/Stripe quality). No login. Offline-resilient. Robust keyboard handling for the AI chat. Correct Android safe-area / navigation-bar handling. Tajik default language, plus Russian and English.

## Architecture
- **Frontend:** Expo Router (file-based), React Native, TypeScript. Bottom tabs (Home, Scan, AI Helper, History, Settings). react-native-keyboard-controller for keyboard UX. react-native-safe-area-context for insets. phosphor-react-native icons. @tanstack/react-query for the history cache. Centralized theme in `src/theme.ts`. Centralized i18n in `src/i18n` (tg/ru/en).
- **Backend:** FastAPI. Single AI endpoint `POST /api/ai/chat` (+ `GET /api/health`). Uses `emergentintegrations` LlmChat with Gemini `gemini-3-flash-preview`. Gemini key kept server-side (`GEMINI_API_KEY`) with `EMERGENT_LLM_KEY` fallback. Persists AI exchanges to Mongo `ai_messages`.
- **Local storage:** scan history, language, onboarding flag via `@/src/utils/storage` (AsyncStorage). No accounts.
- **Scanning:** fully offline heuristics — `linkScanner.ts`, `messageScanner.ts`, `phoneScanner.ts`. Only AI Helper needs network.

## User Personas
- Everyday Tajik phone user (non-technical) who receives suspicious SMS/links/calls.
- Russian/English-speaking residents needing quick scam checks.

## Core Requirements (static)
1. No login, works offline for scanning/history/settings.
2. 4 risk levels: SAFE / SUSPICIOUS / DANGEROUS / UNKNOWN.
3. Link, message, phone scanners with clear result screen.
4. AI Helper chat with persistent, keyboard-safe input; graceful error + retry; never asks for OTP/passwords.
5. Local scan history (view / delete / clear).
6. Tajik default, Russian & English switchable in Settings.
7. Onboarding, privacy & about info.
8. Correct safe-area handling; no overlap with Android system nav.

## Implemented (2026-06)
- [x] Onboarding (4 slides, skip/next, persisted) — 2026-06
- [x] Bottom tabs with active state; NativeTabs on iOS 26, classic Tabs elsewhere — 2026-06
- [x] Home dashboard (security status hero, quick actions, AI card, safety tip) — 2026-06
- [x] Scan screen (segmented Link/Message/Phone, keyboard-safe sticky CTA) — 2026-06
- [x] Offline heuristic scanners (link/message/phone) with weighted scoring — 2026-06
- [x] Result screen (tinted hero, indicators, recommended action, timestamp) — 2026-06
- [x] AI Helper chat (Gemini 3 Flash via backend, suggestion chips, typing indicator, error+retry, plain-text replies, multilingual) — 2026-06
- [x] History (list, single delete, clear-all confirm, empty state, pull-to-refresh) — 2026-06
- [x] Settings (language switch tg/ru/en, clear history, privacy & about modals, version) — 2026-06
- [x] Full i18n (Tajik default, Russian, English) — 2026-06
- [x] Backend AI endpoint + health, tested (8/8 backend + full frontend flow passing) — 2026-06
- [x] Rebranded to dark+red identity from user logo; logo set as icon/splash/adaptive/favicon — 2026-06
- [x] Redesigned Home into a security dashboard (status hero + live stats, scan tile grid, recent activity) — 2026-06
- [x] Light / Dark / System theme toggle in Settings (persisted, applies app-wide) — 2026-06
- [x] README with APK/EAS build instructions (`/app/README.md`) — 2026-06

## Backlog / Remaining
- P1: Optional Google Safe Browsing integration for live URL reputation (needs user API key).
- P1: Share a scan result (share sheet) so users can warn family.
- P2: Render markdown/rich formatting in AI replies.
- P2: Report/flag a scam number to build a local community blocklist.
- P2: Dark mode (theme already structured to add it).

## Notes
- No device permissions required (no camera/location), so no infoPlist entries needed.
- Keyboard behavior relies on native modules — validate final polish on a real device / EAS build (web preview can't fully exercise it).


## Update (Sep 2026) — Standalone AI + theme crash fix
- AI Helper now calls Gemini directly from the app (`src/services/aiService.ts`) using `EXPO_PUBLIC_GEMINI_API_KEY` from `frontend/.env`; works in exported APK without backend. Backend `/api/ai/chat` kept as optional fallback.
- Fixed Android crash on "System" theme: `Appearance.setColorScheme(null)` → now passes `"unspecified"` (`src/theme.ts`).
- README §5 documents how the offline scanners work (`linkScanner.ts`, `messageScanner.ts`, `phoneScanner.ts`).
