#!/usr/bin/env python3
"""
NexusPulse Mod — automatic patcher for Telegram-FOSS
Run from the root of the Telegram-FOSS repository:
    python3 ../nexuspulse-mod-kit/scripts/apply_mod.py

What it does:
 1. Rebrand: AppName -> "NexusPulse" in ALL locales, applicationId -> com.nexuspulse.messenger,
    replace launcher icons with assets/logo.png (regular + adaptive icon).
 2. Ghost Mode: new toggle in Settings -> Privacy and Security.
    When ON, the client never sends an "online" status (TL_account_updateStatus offline=true),
    so contacts see "last seen recently" instead of "online".
"""
import os
import re
import shutil
import sys
from PIL import Image

APP_NAME = "NexusPulse"
NEW_APPLICATION_ID = "com.nexuspulse.messenger"

REPO = os.getcwd()
SRC = os.path.join(REPO, "TMessagesProj", "src", "main")
KIT = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.normpath(os.path.join(KIT, "..", "assets", "logo.png"))

changed = []

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

def patch(path, subs, required=True):
    """subs: list of (pattern, replacement, count) — regex replace."""
    p = os.path.join(REPO, path)
    s = read(p)
    for pat, rep, cnt in subs:
        new, n = re.subn(pat, rep, s, count=cnt)
        if n == 0:
            msg = f"[WARN] pattern not found in {path}:\n  {pat}"
            print(msg)
            if required:
                raise SystemExit("ABORT: " + msg)
        s = new
    write(p, s)
    changed.append(path)
    print(f"[OK] patched {path}")

# ---------------------------------------------------------------- 1. REBRAND
def rebrand_strings():
    res = os.path.join(SRC, "res")
    n = 0
    for root, _, files in os.walk(res):
        for fn in files:
            if fn == "strings.xml":
                p = os.path.join(root, fn)
                s = read(p)
                s2, c = re.subn(
                    r'(<string name="AppName">)[^<]*(</string>)',
                    rf"\g<1>{APP_NAME}\g<2>", s)
                if c:
                    write(p, s2)
                    n += c
    print(f"[OK] AppName -> {APP_NAME} in {n} strings.xml files")
    changed.append("res/values*/strings.xml")

def rebrand_gradle():
    # current Telegram-FOSS: package is set via APP_PACKAGE in gradle.properties
    p = os.path.join(REPO, "gradle.properties")
    s = read(p)
    s, c = re.subn(r'APP_PACKAGE\s*=\s*\S+', f'APP_PACKAGE={NEW_APPLICATION_ID}', s)
    if c == 0:
        # older layout: applicationId inside TMessagesProj/build.gradle
        p2 = os.path.join(REPO, "TMessagesProj", "build.gradle")
        s2 = read(p2)
        s2, c2 = re.subn(r'applicationId\s+"[^"]+"',
                         f'applicationId "{NEW_APPLICATION_ID}"', s2)
        if c2 == 0:
            print("[WARN] could not set applicationId (neither gradle.properties nor build.gradle)")
        else:
            write(p2, s2)
            print(f"[OK] applicationId -> {NEW_APPLICATION_ID} (build.gradle)")
            changed.append("TMessagesProj/build.gradle")
        return
    write(p, s)
    # strip obsolete JVM flags that break Gradle daemon on JDK 17
    s = read(p)
    s2, cfix = re.subn(r'^org\.gradle\.jvmargs=.*$',
                       'org.gradle.jvmargs=-Xmx4096M -Dfile.encoding=UTF-8',
                       s, flags=re.M)
    write(p, s2)
    print(f"[OK] gradle.properties jvmargs sanitized ({cfix} line) for JDK 17")
    print(f"[OK] APP_PACKAGE -> {NEW_APPLICATION_ID} (gradle.properties)")
    changed.append("gradle.properties")
    # remove debug suffix ".beta" so the final package is clean
    app_g = os.path.join(REPO, "TMessagesProj_App", "build.gradle")
    if os.path.exists(app_g):
        sa = read(app_g)
        sa, c3 = re.subn(r'applicationIdSuffix\s+"[^"]+"\n', '', sa, count=1)
        if c3:
            write(app_g, sa)
            print("[OK] removed applicationIdSuffix from debug build")

def make_icons():
    """Generate launcher mipmaps + adaptive icon from assets/logo.png."""
    res = os.path.join(SRC, "res")
    logo = Image.open(LOGO).convert("RGBA")

    sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    for dpi, size in sizes.items():
        d = os.path.join(res, f"mipmap-{dpi}")
        os.makedirs(d, exist_ok=True)
        img = logo.resize((size, size), Image.LANCZOS)
        img.save(os.path.join(d, "ic_launcher.png"))
        img.save(os.path.join(d, "ic_launcher_round.png"))

    # adaptive icon: foreground = logo with 25% safe-zone inset, background = black
    fg_size = 432
    fg = logo.resize((int(fg_size * 0.62),) * 2, Image.LANCZOS)
    canvas = Image.new("RGBA", (fg_size, fg_size), (0, 0, 0, 0))
    off = (fg_size - fg.width) // 2
    canvas.paste(fg, (off, off), fg)
    for dpi, size in {"mdpi": 108, "hdpi": 162, "xhdpi": 216,
                      "xxhdpi": 324, "xxxhdpi": 432}.items():
        d = os.path.join(res, f"mipmap-{dpi}")
        canvas.resize((size, size), Image.LANCZOS).save(os.path.join(d, "ic_launcher_foreground.png"))

    write(os.path.join(res, "mipmap-anydpi-v26", "ic_launcher.xml"),
          '<?xml version="1.0" encoding="utf-8"?>\n'
          '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
          '    <background android:drawable="@color/np_icon_bg"/>\n'
          '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
          '</adaptive-icon>\n')
    write(os.path.join(res, "mipmap-anydpi-v26", "ic_launcher_round.xml"),
          '<?xml version="1.0" encoding="utf-8"?>\n'
          '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
          '    <background android:drawable="@color/np_icon_bg"/>\n'
          '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
          '</adaptive-icon>\n')
    vals = os.path.join(res, "values")
    os.makedirs(vals, exist_ok=True)
    write(os.path.join(vals, "np_colors.xml"),
          '<?xml version="1.0" encoding="utf-8"?>\n'
          '<resources>\n    <color name="np_icon_bg">#000000</color>\n</resources>\n')
    print("[OK] launcher icons replaced from assets/logo.png")
    changed.append("res/mipmap-*/ic_launcher*")

# -------------------------------------------------------------- 2. GHOST MODE
GHOST_CONFIG_JAVA = '''package org.telegram.messenger;

import android.content.Context;
import android.content.SharedPreferences;

/* NexusPulse mod: Ghost Mode (never report "online" presence) */
public class GhostConfig {
    public static boolean enabled;

    private static SharedPreferences prefs() {
        return ApplicationLoader.applicationContext.getSharedPreferences("nexuspulse", Context.MODE_PRIVATE);
    }

    public static void load() {
        enabled = prefs().getBoolean("ghostMode", true);
    }

    public static void setEnabled(boolean value) {
        enabled = value;
        prefs().edit().putBoolean("ghostMode", value).apply();
    }
}
'''

def add_ghost_config():
    p = os.path.join(SRC, "java", "org", "telegram", "messenger", "GhostConfig.java")
    write(p, GHOST_CONFIG_JAVA)
    print("[OK] created org/telegram/messenger/GhostConfig.java")
    changed.append("GhostConfig.java (new)")

def patch_messages_controller():
    # In updateTimerProc(): block the branch that reports "online" when ghost is on.
    patch("TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java", [(
        r'if \(!ignoreSetOnline && getConnectionsManager\(\)\.getPauseTime\(\) == 0',
        'if (!ignoreSetOnline && !GhostConfig.enabled && getConnectionsManager().getPauseTime() == 0',
        1)])

def patch_privacy_settings():
    path = "TMessagesProj/src/main/java/org/telegram/ui/PrivacySettingsActivity.java"
    subs = [
        # row field
        (r'(private int lastSeenRow;)',
         r'\1\n    private int nexusGhostRow;   // NexusPulse ghost mode', 1),
        # row registration (right after lastSeenRow)
        (r'(        lastSeenRow = rowCount\+\+;)',
         r'\1\n        nexusGhostRow = rowCount++;   // NexusPulse ghost mode', 1),
        # enabled row
        (r'(                    position == lastSeenRow && !getContactsController\(\)\.getLoadingPrivacyInfo\(ContactsController\.PRIVACY_RULES_TYPE_LASTSEEN\) \|\|)',
         r'                    position == nexusGhostRow || // NexusPulse ghost mode\n\1', 1),
        # view type 3 (TextCheckCell)
        (r'(} else if \(position == secretWebpageRow \|\| position == contactsSyncRow \|\| position == contactsSuggestRow \|\| position == newChatsRow\) \{)',
         r'} else if (position == nexusGhostRow) { // NexusPulse ghost mode\n                return 3;\n\1', 1),
        # bind: check state
        (r'(                    textCheckCell\.setTextAndCheck\(LocaleController\.getString\("ArchiveAndMute", R\.string\.ArchiveAndMute\), archiveChats, false\);\n                    \})',
         r'\1 else if (position == nexusGhostRow) { // NexusPulse ghost mode\n'
         r'                        textCheckCell.setTextAndCheck(LocaleController.getString("NPGhostMode", R.string.NPGhostMode), GhostConfig.enabled, false);\n'
         r'                        textCheckCell.setChecked(GhostConfig.enabled);\n                    }', 1),
        # click handler: toggle + push offline status immediately when enabled
        (r'(            \} else if \(position == newChatsRow\) \{)',
         '            } else if (position == nexusGhostRow) { // NexusPulse ghost mode\n'
         '                GhostConfig.setEnabled(!GhostConfig.enabled);\n'
         '                if (view instanceof TextCheckCell) {\n'
         '                    ((TextCheckCell) view).setChecked(GhostConfig.enabled);\n'
         '                }\n'
         '                if (GhostConfig.enabled) {\n'
         '                    org.telegram.tgnet.TLRPC.TL_account_updateStatus req = new org.telegram.tgnet.TLRPC.TL_account_updateStatus();\n'
         '                    req.offline = true;\n'
         '                    getConnectionsManager().sendRequest(req, (response, error) -> { });\n'
         '                }\n'
         r'\1', 1),
    ]
    patch(path, subs)

def add_strings():
    p = os.path.join(SRC, "res", "values", "strings.xml")
    s = read(p)
    add_ru = ""
    ru = os.path.join(SRC, "res", "values-ru", "strings.xml")
    if os.path.exists(ru):
        add_ru = '\n    <string name="NPGhostMode">Режим невидимки (NexusPulse)</string>\n</resources>'
        s_ru = read(ru)
        s_ru, c = re.subn(r'</resources>',
            '\n    <string name="NPGhostMode">Режим невидимки (NexusPulse)</string>\n</resources>',
            s_ru, count=1)
        if c == 0:
            print("[WARN] could not add RU string")
        else:
            write(ru, s_ru)
            print("[OK] RU string added")
    if 'name="NPGhostMode"' in s:
        print("[SKIP] ghost string already present")
        return
    s, c = re.subn(r'</resources>',
        '\n    <string name="NPGhostMode">Ghost mode (NexusPulse)</string>\n'
        '    <string name="NPGhostModeInfo">Do not show “online” status to other users</string>\n</resources>'
        + add_ru.replace('</resources>', '').rstrip('\n') + ('\n</resources>' if add_ru else ''),
        s, count=1)
    if c == 0:
        raise SystemExit("[WARN] </resources> not found in values/strings.xml")
    write(p, s)
    print("[OK] ghost strings added")
    changed.append("res/values*/strings.xml (NPGhostMode)")

def load_ghost_config():
    """Initialize GhostConfig at app start (ApplicationLoader.onCreate)."""
    p = "TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java"
    s = read(os.path.join(REPO, p))
    if "GhostConfig.load()" in s:
        print("[SKIP] GhostConfig.load() already present")
        return
    if "super.onCreate();" not in s:
        raise SystemExit("[WARN] super.onCreate() not found in ApplicationLoader")
    s = s.replace("super.onCreate();", "super.onCreate();\n        GhostConfig.load(); // NexusPulse", 1)
    write(os.path.join(REPO, p), s)
    print("[OK] GhostConfig.load() injected into ApplicationLoader")
    changed.append(p)

# --------------------------------------------------------------------- main
if __name__ == "__main__":
    if not os.path.isdir(os.path.join(REPO, "TMessagesProj")):
        raise SystemExit("Run this script from the ROOT of the Telegram-FOSS repository!")
    if not os.path.exists(LOGO):
        raise SystemExit(f"Logo not found: {LOGO}")
    print("=== NexusPulse mod: applying patches ===\n[1/6] strings")
    rebrand_strings()
    print("[2/6] applicationId")
    rebrand_gradle()
    print("[3/6] icons")
    make_icons()
    print("[4/6] ghost config")
    add_ghost_config()
    load_ghost_config()
    print("[5/6] presence blocking")
    patch_messages_controller()
    print("[6/6] settings toggle")
    patch_privacy_settings()
    add_strings()
    print("\n=== DONE. NexusPulse mod applied to:", len(set(changed)), "locations ===")
