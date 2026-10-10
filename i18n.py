"""Chinese (and English) texts for the user interface.

Every visible string in the app is written in English in the code and translated here,
so the code stays readable and a translation can never break it: `tr()` returns the
Chinese text when one is known and the English text otherwise.

The language is chosen once, when the module is first used:

  * the "language" setting in config.json ("zh" or "en");
  * otherwise the Windows display language - Chinese (any locale starting with "zh")
    gets Chinese, everything else English;
  * LANG can also be set by hand before the first call (tests, or a future menu).

Adding a translation: put the English string and its Chinese in ZH below.
Strings with a value in it (a device name, a percentage) are translated as a whole
before they are put together, so the %s / {} placeholders keep working.
"""
from __future__ import annotations

import ctypes
import locale
import os
from typing import Optional

EN = "en"
ZH_CN = "zh"

LANG: Optional[str] = None        # set by set_language(); None = not chosen yet
_LANGUAGE = LANG

# ------------------------------------------------------------------ translations
ZH = {
    # ---------------- tray menu: the top level
    "No devices found": "未发现设备",
    "Refresh now": "立即刷新",
    "Preferences": "设置",
    "Hidden devices": "已隐藏的设备",
    "Diagnostics…": "诊断信息…",
    "Rename…": "重命名…",
    "Reset name": "恢复默认名称",
    "Icon": "图标",
    "Low battery alert at": "低电量提醒阈值",
    "Hide this device": "隐藏此设备",
    # format(): "Default (20%)" / "Default (off)"
    "Default ({}%)": "默认（{}%）",
    "Default (off)": "默认（关闭）",
    "Show {}": "显示 {}",

    # ---------------- preferences
    "Poll interval": "轮询间隔",
    "Low battery alert": "低电量提醒",
    "Alert when fully charged": "充满时提醒",
    "Estimated time left": "显示剩余使用时间",
    "Quiet while gaming": "游戏全屏时静默",
    "Sound with the low battery alert": "低电量提醒时播放声音",
    "Windows Bluetooth devices": "Windows 蓝牙设备",
    "PlayStation full mode (Bluetooth)": "PlayStation 完整模式（蓝牙）",
    "Device types": "设备类型",
    "Device pictogram": "设备图形",
    "Percentage in the icon": "图标内显示百分比数字",
    "Charging animation": "充电动画",
    "Icon colour": "图标颜色",
    "Automatic": "自动",
    "White": "白色",
    "Black": "黑色",
    "Status file for other apps": "为其他应用输出状态文件",
    "Start with Windows": "开机自动启动",
    "Check for updates": "检查更新",
    "Mouse": "鼠标",
    "Keyboard": "键盘",
    "Language": "界面语言",
    "简体中文": "简体中文",
    "English": "English",

    # ---------------- intervals / thresholds
    "15 s": "15 秒",
    "30 s": "30 秒",
    "1 min": "1 分钟",
    "2 min": "2 分钟",
    "5 min": "5 分钟",
    "Off": "关闭",

    # ---------------- state, shown in the tooltip and under the name
    "no link (off or asleep)": "无连接（已关机或休眠）",
    "charging": "充电中",
    "(last known value, device asleep)": "（上次数值，设备已休眠）",

    # ---------------- notifications
    "Low battery": "电量不足",
    "Fully charged": "已充满",
    "{}: {}% left. Time to charge.": "{}：剩余 {}%，该充电了。",
    "{}: battery is low. Time to charge.": "{}：电量不足，该充电了。",
    "{} is fully charged.": "{} 已充满。",
    "Halo Battery is running from a temporary folder (straight from the ZIP). "
    "It cannot be added to autostart from there: unzip it to a folder first.": (
        "Halo Battery 正从临时文件夹运行（直接从压缩包解压的位置）。\r\n"
        "这种情况下无法设置开机自启：请先把整个文件夹解压出来再运行。"),

    # ---------------- 更新提示
    "Download v{}…": "下载 v{}…",
    "Download update…": "下载更新…",
    "Version {} is available. Right-click a battery icon "
    "and choose \"Download v{}…\".": (
        "有新版本 {} 可用。右键点击电量图标，选择“下载 v{}…”。"),

    # ---------------- rename dialog
    "Rename device": "重命名设备",
    "Name": "名称",
    "OK": "确定",
    "Cancel": "取消",

    # ---------------- device types (Preferences > Device types)
    "8BitDo controllers": "8BitDo 手柄",
    "AM Infinity 8K (Angry Miao)": "AM Infinity 8K（怒喵）",
    "Astro A50": "Astro A50 耳机",
    "ASUS ROG / TUF mice": "华硕 ROG / TUF 鼠标",
    "Audeze Maxwell": "Audeze Maxwell 耳机",
    "Razer Barracuda Pro": "雷蛇 Barracuda Pro 耳机",
    "Corsair headsets": "海盗船耳机",
    "G-Wolves mice": "G-Wolves 鼠标",
    "HyperX Cloud II Wireless": "HyperX Cloud II 无线版",
    "HyperX Cloud Alpha 2": "HyperX Cloud Alpha 2",
    "HyperX Cloud III Wireless": "HyperX Cloud III 无线版",
    "HyperX Cloud III S Wireless": "HyperX Cloud III S 无线版",
    "JBL Quantum": "JBL Quantum",
    "Keychron": "Keychron 键盘",
    "LAMZU mice": "LAMZU 鼠标",
    "Lofree keyboards": "洛斐键盘",
    "Logitech": "罗技设备",
    "Logitech G PRO X 2 LIGHTSPEED": "罗技 G PRO X 2 LIGHTSPEED",
    "MCHOSE mice": "MCHOSE 鼠标",
    "Nintendo Switch controllers": "任天堂 Switch 手柄",
    "PlayStation controllers": "PlayStation 手柄",
    "Pulsar / ATK VXE mice": "Pulsar / ATK VXE 鼠标",
    "Rapoo mice (2.4G receiver)": "雷柏鼠标（2.4G 接收器）",
    "Razer mice and headsets": "雷蛇鼠标与耳机",
    "SteelSeries": "赛睿设备",
    "SteelSeries Arctis Nova Elite": "赛睿 Arctis Nova Elite",
    "WLmouse": "WLmouse 鼠标",
    "Xbox-compatible controllers": "Xbox 兼容手柄",

    # ---------------- provider / device names
    "Rapoo mouse": "雷柏无线鼠标",

    # ---------------- 带变量的字符串（占位符 {} 保持原样）
    "Exit (v{})": "退出 (v{})",
    "No devices shown ({} hidden)": "未显示设备（{} 个已隐藏）",
    "battery is low": "电量不足",
    "{}% left": "剩余 {}%",
    "{}: {}. Time to charge.": "{}：{}，该充电了。",
    "New name for this device:": "设备的新名称：",
    "Halo Battery - Rename": "Halo Battery - 重命名",
    "less than 1 h of use left": "剩余使用时间不足 1 小时",
    "about {} h of use left": "大约还能用 {} 小时",
    "about {} days of use left": "大约还能用 {} 天",
    "Halo Battery is running from a temporary folder (straight from the ZIP). "
    "Extract the ZIP to a folder of its own, run HaloBattery.exe from there, "
    "then turn on Start with Windows.": (
        "Halo Battery 正从临时文件夹运行（直接从压缩包里打开）。\r\n"
        "请先把压缩包解压到一个文件夹，从那里运行 HaloBattery.exe，再开启开机自动启动。"),
}


def windows_language() -> str:
    """The Windows display language as a short code: "zh", "en", ... Empty when the
    system does not tell us."""
    try:
        lang = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage())
    except Exception:                    # not Windows, or the call failed
        lang = None
    if not lang:
        try:
            lang = locale.getdefaultlocale()[0] or ""
        except Exception:
            lang = ""
    return lang.split("_")[0].lower() if lang else ""


def set_language(lang: Optional[str]) -> None:
    """Choose the language: "zh", "en", or None (auto: the Windows language)."""
    global LANG, _LANGUAGE
    if lang in (None, "", "auto"):
        lang = ZH_CN if windows_language() == ZH_CN else EN
    LANG = _LANGUAGE = ZH_CN if str(lang).lower().startswith(ZH_CN) else EN


def tr(text: str) -> str:
    """The text in the current language; the English one when it is not translated."""
    if LANG is None:
        set_language(os.environ.get("HALO_LANG") or None)
    if LANG == EN:
        return text
    return ZH.get(text, text)


# the app starts in the Windows language unless the settings say otherwise
if LANG is None:
    set_language(None)
