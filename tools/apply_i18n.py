"""One-off patch: put the English UI strings of the app behind i18n.tr().

Run from the HaloBattery-CN folder:  python tools/apply_i18n.py
Every replacement is anchored on the exact original text and asserted to be unique,
so the script fails loudly instead of silently mangling the app.
"""
import io
import sys


def patch(path, pairs):
    # the files mix LF and CRLF; work on LF only and write LF back
    s = io.open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    for old, new in pairs:
        old = old.replace("\r\n", "\n")
        new = new.replace("\r\n", "\n")
        n = s.count(old)
        if n != 1:
            raise SystemExit(f"anchor not unique ({n}x) in {path}:\n{old!r}")
        s = s.replace(old, new, 1)
    io.open(path, "w", encoding="utf-8", newline="").write(s)
    print(f"patched {path}: {len(pairs)} edits")


NL = "\r\n"
T = "tr("


main_pairs = [
    # ---------------- imports
    ("import history  # noqa: E402",
     "import history  # noqa: E402" + NL + "import i18n  # noqa: E402" + NL
     + "from i18n import tr  # noqa: E402"),

    # ---------------- defaults: numbers in the icon by default (this build), language auto
    ('    "percent_in_icon": False,  # the level as a number in the ring, instead of the pictogram',
     '    "percent_in_icon": True,   # the level as a number in the ring, instead of the pictogram'),
    ('    "quiet_fullscreen": True,  # while a game is full screen: hold alerts, poll every 5 min',
     '    "quiet_fullscreen": True,  # while a game is full screen: hold alerts, poll every 5 min' + NL
     + '    "language": "auto",       # "zh" / "en" / "auto" (the Windows display language)'),

    # ---------------- notifications (three small anchors: one per function)
    ('''    left = "battery is low" if approx else f"{level}% left"
    return f"{name}: {left}. Time to charge."''',
     '''    left = tr("battery is low") if approx else tr("{}% left").format(level)
    return tr("{}: {}. Time to charge.").format(name, left)'''),

    ('''    return f"{name} is fully charged."''',
     '''    return tr("{} is fully charged.").format(name)'''),

    ('''    return (f"Version {latest} is available. Right-click a battery icon "
            f"and choose \\"Download v{latest}…\\".")''',
     '''    return tr("Version {} is available. Right-click a battery icon "
              "and choose \\"Download v{}…\\".").format(latest, latest)'''),

    # ---------------- the state line of the tooltip
    ('''    if st.approx:
        state = st.approx          # XInput: coarse levels or "not reported yet", never a fake "NN%"
    elif st.level is None:
        state = "no link (off or asleep)"
    else:
        state = f"{st.level}%"
        if st.charging:
            state += ", charging"
        if not st.online:
            state += " (last known value, device asleep)"''',
     '''    if st.approx:
        state = tr(st.approx)      # XInput: coarse levels or "not reported yet", never a fake "NN%"
    elif st.level is None:
        state = tr("no link (off or asleep)")
    else:
        state = f"{st.level}%"
        if st.charging:
            state += ", " + tr("charging")
        if not st.online:
            state += " " + tr("(last known value, device asleep)")'''),

    # ---------------- the rename box
    ('''"'New name for this device:', 'Halo Battery - Rename', $env:HALO_BATTERY_NAME)"''',
     '''"'" + tr("New name for this device:") + "', '" + tr("Halo Battery - Rename")
              + "', $env:HALO_BATTERY_NAME)"'''),

    # ---------------- menu: the header
    ('''            return f"No devices shown ({hidden} hidden)" if hidden else "No devices found"''',
     '''            return (tr("No devices shown ({} hidden)").format(hidden) if hidden
                    else tr("No devices found"))'''),

    # ---------------- menu: the lists behind the submenus
    ('''        intervals = [(15, "15 s"), (30, "30 s"), (60, "1 min"), (120, "2 min"), (300, "5 min")]
        themes = [("auto", "Automatic"), ("white", "White"), ("black", "Black")]
        lows = [(0, "Off"), (10, "10%"), (15, "15%"), (20, "20%"), (25, "25%"), (30, "30%")]''',
     '''        intervals = [(15, tr("15 s")), (30, tr("30 s")), (60, tr("1 min")),
                     (120, tr("2 min")), (300, tr("5 min"))]
        themes = [("auto", tr("Automatic")), ("white", tr("White")), ("black", tr("Black"))]
        lows = [(0, tr("Off")), (10, "10%"), (15, "15%"), (20, "20%"), (25, "25%"), (30, "30%")]
        languages = [("auto", tr("Automatic")), ("zh", tr("简体中文")), ("en", tr("English"))]'''),

    ('''            return f"Download v{self.update[0]}…" if self.update else "Download update…"''',
     '''            return (tr("Download v{}…").format(self.update[0]) if self.update
                    else tr("Download update…"))'''),

    ('''            return f"Default ({low}%)" if low else "Default (off)"''',
     '''                return tr("Default ({}%)").format(low) if low else tr("Default (off)")'''),

    # ---------------- menu: the language switch
    ('''        def set_theme(mode):''',
     '''        def pick_language(value):
            def _f(icon, item):
                self.cfg["language"] = value
                save_config(self.cfg)
                i18n.set_language(value)
                self.refresh_menus()
            return _f

        def set_theme(mode):'''),

    # ---------------- menu: the items themselves
    ('''            flyout.classic_only(Item("Rename…", lambda i, it: self.rename(owner))),
            Item("Reset name", lambda i, it: self.reset_name(owner), visible=renamed),
            Item("Icon", Menu(*[Item(label, pick(value), checked=picked(value), radio=True)
                                for value, label in PICTOGRAM_CHOICES])),
            Item("Low battery alert at", Menu(''',
     '''            flyout.classic_only(Item(tr("Rename…"), lambda i, it: self.rename(owner))),
            Item(tr("Reset name"), lambda i, it: self.reset_name(owner), visible=renamed),
            Item(tr("Icon"), Menu(*[Item(tr(label), pick(value), checked=picked(value), radio=True)
                                    for value, label in PICTOGRAM_CHOICES])),
            Item(tr("Low battery alert at"), Menu('''),

    ('''            Item("Hide this device", lambda i, it: self.hide(owner)),''',
     '''            Item(tr("Hide this device"), lambda i, it: self.hide(owner)),'''),

    ('''            flyout.CounterItem("Poll interval", intervals, lambda: self.cfg["interval"], set_interval),
            flyout.CounterItem("Low battery alert", lows, lambda: self.cfg["low"], set_low),
            Item("Alert when fully charged", toggle("full_alert"),''',
     '''            flyout.CounterItem(tr("Poll interval"), intervals,
                                lambda: self.cfg["interval"], set_interval),
            flyout.CounterItem(tr("Low battery alert"), lows, lambda: self.cfg["low"], set_low),
            Item(tr("Alert when fully charged"), toggle("full_alert"),'''),

    ('''            Item("Estimated time left", toggle("time_left"),''',
     '''            Item(tr("Estimated time left"), toggle("time_left"),'''),
    ('''            Item("Quiet while gaming", toggle("quiet_fullscreen"),''',
     '''            Item(tr("Quiet while gaming"), toggle("quiet_fullscreen"),'''),
    ('''            Item("Sound with the low battery alert", toggle("low_sound"),''',
     '''            Item(tr("Sound with the low battery alert"), toggle("low_sound"),'''),
    ('''            Item("Windows Bluetooth devices", toggle("bluetooth"),''',
     '''            Item(tr("Windows Bluetooth devices"), toggle("bluetooth"),'''),
    ('''            Item("PlayStation full mode (Bluetooth)", toggle("playstation_full_mode"),''',
     '''            Item(tr("PlayStation full mode (Bluetooth)"), toggle("playstation_full_mode"),'''),
    ('''            Item("Device types", Menu(provider_items)),
            Item("Device pictogram", toggle("badges"),''',
     '''            Item(tr("Device types"), Menu(provider_items)),
            Item(tr("Device pictogram"), toggle("badges"),'''),
    ('''            Item("Percentage in the icon", toggle("percent_in_icon"),''',
     '''            Item(tr("Percentage in the icon"), toggle("percent_in_icon"),'''),
    ('''            Item("Charging animation", toggle("animation"),''',
     '''            Item(tr("Charging animation"), toggle("animation"),'''),
    ('''            Item("Icon colour", Menu(*[''',
     '''            Item(tr("Icon colour"), Menu(*['''),
    ('''            Item("Status file for other apps", toggle("status_file"),''',
     '''            Item(tr("Status file for other apps"), toggle("status_file"),'''),
    ('''            Item("Start with Windows", toggle_autostart,''',
     '''            Item(tr("Start with Windows"), toggle_autostart,'''),
    ('''            Item("Check for updates", toggle("update_check"),''',
     '''            Item(tr("Check for updates"), toggle("update_check"),'''),
    ('''            Item("Refresh now", lambda i, it: self.wake.set(), default=True),
            Item("Preferences", preferences),
            Item("Hidden devices", Menu(hidden_items),''',
     '''            Item(tr("Language"), Menu(*[
                Item(t, pick_language(v),
                     checked=lambda it, v=v: self.cfg.get("language", "auto") == v, radio=True)
                for v, t in languages])),
            Menu.SEPARATOR,
            Item(tr("Refresh now"), lambda i, it: self.wake.set(), default=True),
            Item(tr("Preferences"), preferences),
            Item(tr("Hidden devices"), Menu(hidden_items),'''),
    ('''            Item("Diagnostics…", lambda i, it: self.request_diag()),
            Item(f"Exit (v{VERSION})", lambda i, it: self.quit()),''',
     '''            Item(tr("Diagnostics…"), lambda i, it: self.request_diag()),
            Item(tr("Exit (v{})").format(VERSION), lambda i, it: self.quit()),'''),

    # ---------------- menu: names that come from data
    ('''                yield Item(label, flip_provider(name), checked=provider_on(name))''',
     '''                yield Item(tr(label), flip_provider(name), checked=provider_on(name))'''),
    ('''                yield Item(f"Show {name}", show_again(key))''',
     '''                yield Item(tr("Show {}").format(name), show_again(key))'''),

    # ---------------- the autostart warning
    ('''                    icon.notify(TEMP_AUTOSTART_TEXT, "Start with Windows")''',
     '''                    icon.notify(tr(TEMP_AUTOSTART_TEXT), tr("Start with Windows"))'''),
]


history_pairs = [
    ('''from __future__ import annotations''',
     '''from __future__ import annotations'''),
    ('''    if hours < 1:
        return "less than 1 h of use left"
    if hours < 48:
        return f"about {round(hours)} h of use left"
    return f"about {round(hours / 24)} days of use left"''',
     '''    if hours < 1:
        return tr("less than 1 h of use left")
    if hours < 48:
        return tr("about {} h of use left").format(round(hours))
    return tr("about {} days of use left").format(round(hours / 24))'''),
]


if __name__ == "__main__":
    if "--history" in sys.argv:
        patch("history.py", history_pairs)
    else:
        patch("halo_battery.pyw", main_pairs)
