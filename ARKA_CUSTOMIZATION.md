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
| Submodule `libs/hbb_common` | pinned at `7e1c392c62d39c364127307cd408421dd5f8cfb0` (matches tag 1.4.9) |
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

### Theme / colors (modern placeholder palette)
**File:** `flutter/lib/common.dart` — `class MyTheme` (single source of truth)

Modern professional **teal** palette (aligned with Arka's navy/teal identity),
replacing RustDesk's blue. To apply the final Arka palette later, edit **only**
this token block:

| Token | Original | New (placeholder) |
|-------|----------|-------------------|
| `accent` | `0xFF0071FF` | `0xFF0D9488` (teal-600) |
| `accent50` | `0x770071FF` | `0x770D9488` |
| `accent80` | `0xAA0071FF` | `0xAA0D9488` |
| `button` | `0xFF2C8CFF` | `0xFF14B8A6` (teal-500) |
| `idColor` | `0xFF00B6F0` | `0xFF0F766E` (teal-700) |
| `cmIdColor` | `0xFF21790B` | `0xFF0F766E` |
| `grayBg` | `0xFFEFEFF2` | `0xFFF4F5F7` |
| `border` | `0xFFCCCCCC` | `0xFFD9DCE1` |
| `canvasColor` | `0xFF212121` | `0xFF1C1D22` |
| `ColorScheme.light/dark primary` | `Colors.blue` | `accent` |

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
| 3 | **Color palette** | Replace the teal placeholder tokens in `MyTheme` with the final Arka palette. |
| 4 | **App display name → "Arka" (needs decision)** | See below. |

### Needs-decision: full display name switch to "Arka"

The in-app product name and window title come from the Rust global `APP_NAME`
(default `"RustDesk"`). It was **left unchanged on purpose** because changing it
cascades to things that will break if done half-way:
- config/data folder name (`%AppData%\RustDesk` → `%AppData%\Arka`) — migration,
- URI scheme (`rustdesk://` → `arka://`),
- **exe name assumptions**: `updater.rs` and `core_main.rs` derive the exe name
  from `APP_NAME.to_lowercase()` (they'd look for `arka.exe`), so the exe would
  also need renaming to `arka.exe`, plus installer/packaging updates.

**To do it fully later (recommended as one coordinated change):**
1. Set `APP_NAME` default to `"Arka"` in `libs/hbb_common/src/config.rs`.
2. Rename the built exe to `arka.exe` (update `build.py` `hbb_name`, the flutter
   Windows `BINARY_NAME`, and installer/portable/msi references).
3. Re-test updater, tray relaunch, and URI links.

Because it couldn't be verified here without breakage, it is flagged rather than
applied.

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
