"""Smoke test: build the tray menu without showing it, and read the Rapoo level.

    .venv\\Scripts\\python tools\\smoke_test.py

Prints the menu tree in the current language and the results of one poll.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import i18n  # noqa: E402
import halo_battery as h  # noqa: E402


def walk(menu, depth=0):
    """Print a pystray menu; texts can be callables."""
    for item in menu.items:
        if item is h.Menu.SEPARATOR:
            print("  " * depth + "---")
            continue
        text = item.text
        try:
            text = text(None) if callable(text) else text
        except Exception:
            pass
        print("  " * depth + str(text))
        if getattr(item, "submenu", None) is not None:
            walk(item.submenu, depth + 1)


def main():
    print(f"language: {i18n.LANG}")
    app = object.__new__(h.App)
    app.cfg = h.load_config()
    i18n.set_language(app.cfg.get("language"))
    print(f"language after config: {i18n.LANG}")
    app.cfg.setdefault("language", "auto")
    app._settings_map = lambda key: {}
    app.owner_status = None
    app.update = None
    app.disabled_providers = lambda: set()
    app.device_low = lambda key: None
    app.set_device_low = lambda *a: None
    app.set_pictogram = lambda *a: None
    app.hide = lambda *a: None
    app.unhide = lambda *a: None
    app.rename = lambda *a: None
    app.reset_name = lambda *a: None
    app.request_diag = lambda *a: None
    app.quit = lambda *a: None
    app.open_update = lambda *a: None
    app.toggle_provider = lambda *a: None
    app.refresh_menus = lambda *a: None
    app.wake = __import__("threading").Event()
    app.light_taskbar = True
    menu = h.App.build_menu(app, None)
    print("=== tray menu ===")
    walk(menu)

    print("=== poll ===")
    providers = h.make_providers()
    for p in providers:
        if p.name != "rapoo":
            continue
        for st in p.poll():
            print(f"  {st.name}: {st.level}% charging={st.charging} online={st.online}")
        for line in p.diagnostics():
            print("  " + line)


if __name__ == "__main__":
    main()
