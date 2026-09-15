# Arka Custom RustDesk Client — Customization Log

Company: **Rayan Samaneh Arka (شرکت رایان سامانه آرکا)**
Goal: a Windows x64 RustDesk client, Arka-branded, that connects to the Arka
self-hosted server with **zero end-user configuration**.

> **Status: TEST / PREVIEW build.** Logo, icons and colors are temporary
> placeholders (see [Placeholders](#placeholders-to-finish-later)). The real
> server values still need to be provided. Nothing here is final except the
> mechanism.

---

## 1. Base source

| Item | Value |
|------|-------|
| Upstream repo | https://github.com/rustdesk/rustdesk |
| Base tag (stable) | **1.4.9** |
| `libs/hbb_common` | based on `7e1c392c…` (tag 1.4.9), now **embedded** as regular files (de-submodule) so the fork is self-contained and CI builds anywhere it is pushed |
| Work branch | `arka-custom` |

All Arka changes are marked in code with an `ARKA` comment so they are easy to
find (`grep -rn ARKA .`).

---

## 2. Server hardcoding (the important part)

RustDesk **1.4.9 does not use `option_env!`** for the server the way older
guides assume — the server/key live in plain constants, and there is a runtime
settings system (`OVERWRITE_SETTINGS`) used by the Pro "custom client". We use a
clean, low-risk, two-layer approach that gives **zero-config + locked fields**:

### Layer A — compile-time constants (deep fallback)

`option_env!` is read at build time; if the env var is unset **or empty**, a
placeholder fallback is used (empty-safe, because CI turns an unset secret into
an empty string).

**File:** `libs/hbb_common/src/config.rs`

| What | Original | New |
|------|----------|-----|
| `RENDEZVOUS_SERVERS` (line ~119) | `&["rs-ny.rustdesk.com"]` | `&[arka_env_or(option_env!("RENDEZVOUS_SERVER"), "id.arka.example")]` |
| `RS_PUB_KEY` (line ~120) | `"OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw="` | `arka_env_or(option_env!("RS_PUB_KEY"), "")` |
| helper `arka_env_or()` | *(new const fn)* | falls back when the env var is unset or empty |

**File:** `src/common.rs` — `get_api_server_()` final fallback

| Original | New |
|----------|-----|
| `"https://admin.rustdesk.com".to_owned()` | `match option_env!("API_SERVER") { Some(s) if !s.is_empty() => s.to_owned(), _ => "https://admin.rustdesk.com".to_owned() }` |

### Layer B — forced + locked runtime settings

A new function seeds `OVERWRITE_SETTINGS` from the same compile-time env vars.
Values placed in `OVERWRITE_SETTINGS` are both **applied** and **locked**: the
user cannot change them in the UI (enforced by `Config::is_option_can_save`, so
this is a genuine soft-lock with no UI hacking). Only non-empty values are
injected, so a build without env vars behaves exactly like stock RustDesk.

**File:** `src/common.rs`
- New `fn seed_arka_builtin_config()` — inserts, when non-empty:
  - `custom-rendezvous-server` ← `RENDEZVOUS_SERVER`
  - `relay-server` ← `RELAY_SERVER`
  - `api-server` ← `API_SERVER`
  - `key` ← `RS_PUB_KEY`
- Called at the top of `load_custom_client()` (runs on both the Flutter and the
  non-Flutter startup paths — verified they both call `load_custom_client()`).

### Why not the official signed `custom.txt`?

RustDesk's Pro "custom client" reads a **signed** base64 blob verified with
RustDesk's own public key (`read_custom_client()`), so it can't be produced
without RustDesk's private key. The two layers above are the correct path for an
open-source self-host build.

---

## 3. Branding

Only **display strings, resource metadata, theme color values, and image
assets** were changed. **No Rust crate names, package identifiers, or the exe
name were touched** (those break the build / updater / auto-update).

### Windows executable metadata
**File:** `flutter/windows/runner/Runner.rc`

| Field | Original | New |
|-------|----------|-----|
| CompanyName | `Purslane Tech Pte. Ltd.` | `Rayan Samaneh Arka` |
| FileDescription | `RustDesk Remote Desktop` | `Arka Remote Desktop` |
| LegalCopyright | `… Purslane Tech Pte. Ltd. …` | `… Rayan Samaneh Arka …` |
| ProductName | `RustDesk` | `Arka` |
| InternalName / OriginalFilename | `rustdesk` / `rustdesk.exe` | **unchanged** (technical — used by `get_license_from_exe_name`) |

### Design system — dark, mint-accented
**File:** `flutter/lib/common.dart` — `class MyTheme` (single source of truth)

Dark-first design system. **To apply the final Arka brand colour, change the one
`accent` line** — everything else derives from the tokens.

| Token | Value | Role |
|-------|-------|------|
| `arkaBg` | `#0C1311` | app background |
| `arkaSurface` | `#141D1A` | panels & cards (one step up) |
| `arkaBorder` | `rgba(255,255,255,.07)` | hairline separation |
| `arkaText` | `#E8EDEB` | primary text |
| `arkaTextDim` | `#8A9490` | secondary text |
| **`accent`** | **`#34E0A1`** | **the single accent — primary action, active item, key icons** |
| `accent50` / `accent80` | 47% / 67% of accent | derived |
| `button` / `idColor` / `cmIdColor` | `= accent` | derived |
| `radiusCard` | `16` | cards & panels |
| `radiusControl` | `12` | buttons & inputs |
| `radiusPill` | `999` | chips & badges |

Wired through the dark `ThemeData`: scaffold/dialog/card surfaces, filled
rounded-12 inputs with a hairline border and an accent focus ring, flat
(`elevation: 0`) accent buttons with **dark ink** (white on mint fails
contrast), and `colorScheme` primary/secondary/surface/onPrimary.

Surfaces are separated by **luminance + hairline**, never a heavy rule.

**Dark-first:** `MyTheme.getThemeModePreference()` returns `ThemeMode.dark` when
no preference is stored (fresh config). An explicit light/dark/system choice made
in Settings is still honoured.

### Layout changes (Flutter desktop)

| Area | File | Change |
|------|------|--------|
| Left pane | `desktop/pages/desktop_home_page.dart` | Arka logo + wordmark header with divider (replaced bare centered logo + "Powered by"); pane 200 → 240 px |
| ID / One-time password | same | thin 2 px accent bars → rounded surface **cards** (radius 16, hairline border, small tracked labels, heavier values) |
| Connect panel | `desktop/pages/connection_page.dart` | flat outline → elevated **card** (radius 16, hairline border, **soft green halo** behind this primary element); Connect button 28 → 36 px |
| Peer rows | `common/widgets/peer_card.dart` | list rows radius 5 → 12 (card-like); hover: hard 2 px accent border → accent wash (6%) + low-opacity edge (45%) |

**Still open (not implemented):** the narrow icon **navigation sidebar** and the
optional **third/details column**. The current shell is "identity pane + main
column" with navigation in the top tab bar. This is a genuine structural rebuild
and is best done with a local Flutter toolchain (live hot reload) rather than
blind edits validated by ~50-minute CI builds.

### Logo & icons (temporary placeholders)
A modern rounded-square **teal "A" monogram** was generated at the **exact
sizes/formats** of the originals (so no layout breaks). Generator kept at
`tools/gen_arka_icons.py` (copy) for regeneration.

| File | Format / sizes |
|------|----------------|
| `res/icon.ico` | ICO {16,32,48,64,128} |
| `res/tray-icon.ico` | ICO {32} |
| `flutter/windows/runner/resources/app_icon.ico` | ICO {48} |
| `res/icon.png` | 1024×1024 |
| `res/128x128@2x.png` | 256×256 |
| `res/128x128.png` / `res/64x64.png` / `res/32x32.png` | 128 / 64 / 32 |
| `flutter/assets/icon.svg`, `res/logo.svg` | SVG 26×26 (in-app logo) |
| `res/logo-header.svg` | SVG 1000×286.6 (wordmark) |

---

## 4. Placeholders to finish later

| # | Item | What's needed |
|---|------|---------------|
| 1 | **Server values** | Real `RENDEZVOUS_SERVER`, `RELAY_SERVER`, `API_SERVER`, `RS_PUB_KEY` (from the Arka hbbs/hbbr server). Put them in `arka-env.ps1`/`.sh` for local builds, or in GitHub Secrets for CI. |
| 2 | **Logo / icons** | Replace the placeholder "A" monogram with the official Arka logo (same file names & sizes; re-run `tools/gen_arka_icons.py` from the master, or drop in matched assets). |
| 3 | **Brand accent** | The design system is final in structure; only the brand colour is provisional. Change the single `accent` token in `MyTheme` (`#34E0A1`) to the official Arka colour — the derived tokens follow automatically. |
| 4 | **App display name → "Arka"** | ✅ Done — full identity switch (see below). |

### Full identity switch to "Arka" (DONE)

The app now ships as a **distinct product "Arka"**, not RustDesk-with-a-theme.
This was done with a small number of *central* edits so upstream updates stay
easy to re-apply:

| Change | File | Old → New |
|--------|------|-----------|
| App identity | `libs/hbb_common/src/config.rs` | `APP_NAME` `"RustDesk"` → `"Arka"` |
| Exe name | `flutter/windows/CMakeLists.txt` | `BINARY_NAME` `"rustdesk"` → `"arka"` (builds `arka.exe`) |
| Title fallback | `flutter/windows/runner/main.cpp` | `L"RustDesk"` → `L"Arka"` |
| Metadata | `flutter/windows/runner/Runner.rc` | `InternalName`/`OriginalFilename` → `arka`/`arka.exe` |
| UI strings | `src/lang/*.rs` (51 files) | product name `RustDesk` → `Arka` via **`tools/arka_rebrand.py`** |

Effects of the `APP_NAME` change (all intended):
- window title → **Arka**; config/data dir → `%AppData%\Arka` (separate from any
  installed RustDesk — no conflict / no shared config); URI scheme → `arka://`;
  tray relaunch + updater use `arka.exe` (matches `BINARY_NAME`); and
  `is_custom_client()` becomes true, so upstream hides RustDesk-specific promo.
- The window class is the generic `FLUTTER_RUNNER_WIN32_WINDOW`, and single-
  instance matches on class **+ title**, so Arka runs independently alongside a
  stock RustDesk install.

**Update-safety:** the code edits are 4 central lines (all marked `ARKA`); the
1300+ UI-string replacements are produced by the re-runnable
`tools/arka_rebrand.py`. After merging a newer RustDesk upstream, re-run that
script to re-apply the string rebrand — no hand-editing.

> **AGPL-3.0 note.** RustDesk is AGPL-licensed. Rebranding the client is allowed,
> but Arka must **keep this client's source available to its users** and preserve
> the `LICENSE` file and source copyright headers. The rebrand touches UI strings
> and identity only — not the license or copyright notices. Website/help links
> still point to `rustdesk.com` (no Arka URL provided yet); update those when a
> real Arka site exists.

---

## 5. How to build

### 5a. Local (Windows) — prerequisites
- Rust **1.75** with target `x86_64-pc-windows-msvc`
- Flutter **3.24.5** (desktop/windows enabled) + the rustdesk custom engine
- LLVM/Clang **15.0.6**
- vcpkg (commit `120deac3…`) with `libvpx libyuv opus aom` (`x64-windows-static`)
- Python 3 (for `build.py`)
- flutter_rust_bridge_codegen **1.80.1** (to generate the bridge once)

> Exact, pinned steps live in `.github/workflows/flutter-build.yml` (upstream)
> and `.github/workflows/arka-build.yml` (ours). Mirror those if building
> locally.

### 5b. Local build steps
```powershell
# 1) Fill in the 4 real server values:
notepad .\arka-env.ps1
# 2) Load them into THIS shell (compile-time injection):
. .\arka-env.ps1
# 3) Generate the bridge once (if not already present), then build:
python .\build.py --portable --flutter --skip-portable-pack --hwcodec
# Output: .\flutter\build\windows\x64\runner\Release\
```

### 5c. CI build (recommended — reproducible, no local toolchain)
Workflow: **`.github/workflows/arka-build.yml`** (manual trigger).
1. Push branch `arka-custom` to a GitHub repo.
2. Repo → **Settings → Secrets and variables → Actions** → add:
   `RENDEZVOUS_SERVER`, `RELAY_SERVER`, `API_SERVER`, `RS_PUB_KEY`.
   (If a secret is omitted, the build still succeeds using the placeholder.)
3. **Actions → "Arka Windows Build" → Run workflow.**
4. Download the `arka-windows-x64` artifact.

It reuses the repo's own `bridge.yml` to generate the bridge and mirrors the
upstream Windows x64 Flutter job (same pinned versions).

---

## 6. Reverting

Every change is on branch `arka-custom` and tagged with `ARKA` comments.
`git diff 1.4.9..arka-custom` shows the full delta; original values are recorded
in this file and in the code comments.
