# SCAM.TJ 3.0

A production-ready anti-scam mobile app (Expo + React Native + TypeScript).
Check suspicious **links, messages and phone numbers**, and ask an **AI Helper**
about anything that looks like a scam. Tajik / Russian / English. No login.

- **Frontend:** Expo Router app in `frontend/`
- **Backend:** FastAPI service in `backend/` (only the AI Helper needs it — all
  link/message/phone scanning and history work **fully offline** on the device)

---

## 1. Does the exported project build into an APK?

**Yes.** The project is a standard Expo (SDK 57) app and builds to APK/AAB with EAS.

What works where:

| Feature | Needs internet / backend? |
|---|---|
| Onboarding, navigation, Settings, language | No |
| Link / Message / Phone scanning | No (offline heuristics) |
| Scan history (save / delete / clear) | No (stored on device) |
| **AI Helper chat** | **No backend needed** — the app calls Gemini directly using `EXPO_PUBLIC_GEMINI_API_KEY` |

So the APK installs and runs immediately. The AI Helper needs only internet
access and a Gemini key in `frontend/.env` (see §3.3). The FastAPI backend is
now **optional** (used only as a fallback when no key is set).

---

## 2. Easiest way to build (recommended)

Use the **Publish** button (top-right of the Emergent editor):

1. **Publish → Deploy your app** — this deploys the backend and wires
   `EXPO_PUBLIC_BACKEND_URL` for you.
2. **Generate iOS and Android builds** — provide the requested credentials and
   Emergent produces the installable builds. No local setup, no Expo account
   needed.

> Emergent manages `eas.json` and your Expo account in this flow, so you don't
> have to configure anything.

---

## 3. Building the APK yourself with EAS (after exporting the project)

If you export the code and want to build locally with your own Expo account:

### 3.1 Prerequisites
```bash
npm install -g eas-cli
eas login            # log in to your Expo account
```

### 3.2 Add an `eas.json` in `frontend/`
Create `frontend/eas.json` with an APK profile:

```json
{
  "cli": { "version": ">= 12.0.0" },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "android": { "buildType": "apk" }
    },
    "production": {
      "android": { "buildType": "app-bundle" }
    }
  },
  "submit": { "production": {} }
}
```
- `preview` → produces a directly-installable **APK**.
- `production` → produces an **AAB** for the Play Store.

### 3.3 Add your Gemini key (AI Helper works without a backend)
In `frontend/.env` (values starting with `EXPO_PUBLIC_` are bundled into the APK):
```
EXPO_PUBLIC_GEMINI_API_KEY=AIza...            # from https://aistudio.google.com/apikey
EXPO_PUBLIC_GEMINI_MODEL=gemini-3-flash-preview
```
The AI Helper (`frontend/src/services/aiService.ts`) calls
`https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`
directly from the phone. `EXPO_PUBLIC_BACKEND_URL` is optional — it is only
used as a fallback if the key is missing.

> ⚠️ Anything in `EXPO_PUBLIC_*` ships inside the APK, so someone could extract
> the key. In Google AI Studio, set a usage quota / restrict the key so abuse
> costs you nothing. Rotate it if needed.

**Rebuild the APK after changing `.env`** — env values are baked in at build time.

### 3.4 Build
```bash
cd frontend

# one-time native project configuration (creates credentials, keystore, etc.)
eas build:configure

# installable APK (internal / sideload)
eas build -p android --profile preview

# Play Store bundle
eas build -p android --profile production
```
When the build finishes, EAS gives you a download link for the `.apk` / `.aab`.

### 3.5 App identifiers
Set in `frontend/app.json` (keep them stable across builds):
- `expo.android.package` = `com.emergent.frauddetector.qz57wu`
- `expo.ios.bundleIdentifier` = `com.emergent.frauddetector.qz57wu`

---

## 4. Backend (optional fallback for the AI Helper)

FastAPI service in `backend/` exposing:
- `POST /api/ai/chat` — Gemini (`gemini-3-flash-preview`) security assistant
- `GET /api/health`

Environment (`backend/.env`):
```
MONGO_URL=...
DB_NAME=...
GEMINI_API_KEY=...        # your Google Gemini key
EMERGENT_LLM_KEY=...      # fallback key
```
Run locally:
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001
```

You only need this if you prefer NOT to ship the Gemini key inside the APK.
In that case remove `EXPO_PUBLIC_GEMINI_API_KEY` and set
`EXPO_PUBLIC_BACKEND_URL` to your deployed backend.

---

## 5. How the scanning system works (100% offline)

All scanners are plain TypeScript functions — no network, no API keys.
They live in `frontend/src/services/` and return `{ level, indicators }` where
`level` is `safe | suspicious | dangerous | unknown` and `indicators` are
translation keys shown on the result screen (`frontend/src/i18n/*.ts`).

| Scanner | File | Function |
|---|---|---|
| Link / URL | `src/services/linkScanner.ts` | `analyzeLink(url)` |
| Message / SMS | `src/services/messageScanner.ts` | `analyzeMessage(text)` |
| Phone number | `src/services/phoneScanner.ts` | `analyzePhone(number)` |

Flow: `app/(tabs)/scan.tsx` (input) → scanner function → saved via
`src/services/historyStore.ts` → shown in `app/result.tsx`.

### Link scanner — point-based scoring
Each red flag adds points; `0 = safe`, `1–2 = suspicious`, `3+ = dangerous`.

| Check | Points | Example |
|---|---|---|
| Raw IP as host | 3 | `http://185.12.3.4/login` |
| `@` in the address (user-info trick) | 3 | `https://alif.tj@evil.xyz` |
| Punycode / look-alike letters (`xn--`) | 3 | `xn--pple-43d.com` |
| Brand name inside a non-brand domain | 3 | `alif-verify.top` (brands list: paypal, alif, humo, eskhata, spitamen, korti, amonatbonk…) |
| Suspicious TLD | 2 | `.xyz .top .tk .ml .click .zip …` |
| URL shortener | 2 | `bit.ly`, `tinyurl.com`, `t.co` … |
| Sensitive words (login, verify, otp, card, pay…) | 2 | `/secure-login` |
| Too many subdomains (>4 parts) | 1 | `a.b.c.d.site.com` |
| `http://` instead of `https://` | 1 | |
| Very long URL (>90 chars or path >60) | 1 | |
| Digit-heavy domain (≥5 digits) | 1 | `bank12345.com` |

Edit the lists at the top of `linkScanner.ts` (`SUSPICIOUS_TLDS`, `SHORTENERS`,
`SENSITIVE_WORDS`, `BRANDS`) to tune it.

### Message scanner — keyword rules (Tajik / Russian / English)
`RULES` in `messageScanner.ts` is a list of `{ key, weight, patterns }`.
Text is lower-cased and each rule fires if any pattern is a substring.
Same thresholds (`0 / 1–2 / 3+`).

| Rule | Weight | Sample patterns |
|---|---|---|
| OTP / code request | 3 | `otp`, `код из смс`, `рамзи тасдиқ` |
| Threat / blocking | 2 | `blocked`, `заблокир`, `ҳабс` |
| Prize / lottery | 2 | `you won`, `приз`, `ҷоиза` |
| Money request | 2 | `send money`, `на карту`, `пул фиристед` |
| Government impersonation | 2 | `tax`, `налог`, `андоз` |
| Account takeover | 2 | `verify your account`, `аккаунт` |
| Personal-info request | 2 | `passport`, `cvv`, `шиноснома` |
| Crypto / investment | 2 | `usdt`, `инвест`, `сармоягузор` |
| Urgency | 1 | `urgent`, `срочно`, `фавран` |
| Contains a link | 1 | regex `URL_RE` |

Add a new rule = add one object to `RULES` + its translation key in
`src/i18n/{tg,ru,en}.ts`.

### Phone scanner — format heuristics
`phoneScanner.ts` strips everything except digits/`+` and then:
- 3–5 digit short code → **suspicious** (premium / SMS short codes)
- `+992…` / `992…` / 9-digit starting with 9 → Tajik; valid 9-digit national
  number → **safe** ("no red flags", we cannot verify the owner)
- Other `+country` numbers → **suspicious** (foreign caller — caution, not certainty)
- >15 digits → suspicious; <7 digits → unknown; everything else → unknown

It deliberately never says "this IS a scam" from format alone — that is what
the AI Helper and the user's judgement are for.

---

## 6. Project structure
```
frontend/
  app/                 # screens (expo-router)
    (tabs)/            # Home, Scan, AI, History, Settings
    onboarding.tsx
    result.tsx
  src/
    components/        # Button, Segmented, RiskBadge, RiskIcon, ConfirmModal
    services/          # linkScanner, messageScanner, phoneScanner, aiService, historyStore
    i18n/              # tg / ru / en
    theme.ts           # dark + red design tokens
    utils/
  assets/images/       # icon / splash / adaptive-icon (SCAM.TJ logo)
backend/
  server.py            # FastAPI + AI endpoint
```
