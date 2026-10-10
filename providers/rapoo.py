"""Rapoo (雷柏) wireless mice and keyboards on their 2.4 GHz receiver, and on the cable.

Two Rapoo families are out there and they speak different protocols.

Office family (this provider). The Telink-platform receivers of the MT760 / office
range expose a vendor collection 0xFFEF:0x0000 with one 64-byte report, id 0x05, that
answers a plain GET_REPORT(Feature) - no request has to be sent first, which makes this
channel passive and safe. The answer is the same eight-byte block repeated eight times:

    feature 0x05, 64 bytes:  04 55 91 01 00 00 00 00  (x8)

    [0]      0x04  block tag
    [1]      battery level, 0..100                    (0x55 = 85 %)
    [2..3]   battery voltage, u16 little endian, 10 mV (0x0191 = 401 = 4.01 V)
    [4..7]   00

Measured on a Rapoo 2.4G receiver 24AE:187B with a rechargeable mouse: 85 % and 4.01 V,
which agree with Rapoo's own voltage curve (>= 3950 mV -> 80 %, >= 4150 mV -> 100 %).
The reading survives the mouse being switched off: the receiver keeps the last telemetry
it got, so `online` stays True and the level is simply the last known one.

Rapoo's own Windows software (RapooDevice.dll) is the source of the layout above: it
polls a feature report of the same shape for MT760 Pro / Mini and their NearLink
variants, and reads the level as one byte with the charging state next to it. The report
id varies by model (0x05 here, 0x07 on the models they documented), so every report id
declared on the collection is tried and the first block that parses is used.

Gaming family (not implemented). The VT series (VT3 / VT7 / VT9) is a different chipset
and a different channel: output report 0xBA with command 0xAA on 0xFF00:0x000E, answered
by GET_REPORT(Input), plus an unsolicited 0xBB status report every three seconds. It
stops answering while the mouse sleeps, and about 40 % of the frames are dropped, so it
needs a retry loop and a handshake; see docs/protocols.md in the upstream project.

This provider only reads. Nothing is ever written to the device.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

try:
    import hid
except ImportError:              # pragma: no cover
    hid = None

from . import hidlist
from .base import DeviceStatus, Provider, hexdump, log

RAPOO_VID = 0x24AE

# the vendor collection that carries the telemetry (Rapoo office / Telink receivers)
TELEMETRY_USAGE_PAGE = 0xFFEF
TELEMETRY_USAGE = 0x0000

FEATURE_LENGTH = 64
# report ids to try, in order: the one measured here first, then the one Rapoo's
# software is documented to use, then the rest of the small ids as a safety net
REPORT_IDS = (0x05, 0x07, 0x04, 0x06, 0x08, 0x09, 0x0A, 0x02, 0x03, 0x01)

# a receiver that never answered keeps its last reading greyed out for this long
ASLEEP_KEEP = 600.0

# a plausible battery voltage in the report's own unit (10 mV): 2.00 V .. 5.00 V.
# Rejects blocks that are not telemetry.
VOLTAGE_MIN, VOLTAGE_MAX = 200, 500
VOLTAGE_UNIT_MV = 10

# the products that name themselves this way carry no model, so the icon says mouse
GENERIC_NAMES = ("rapoo 2.4g wireless device", "rapoo wireless device", "2.4g wireless device")
DEFAULT_NAME = "Rapoo mouse"

Reading = Tuple[int, bool]


def parse_block(data, offset: int = 0) -> Optional[Tuple[int, bool, Optional[int]]]:
    """One eight-byte block -> (level %, charging, voltage mV), or None.

    The level is the byte after the tag; the two after it are the voltage. A block is
    telemetry when the level is 0..100 and - when the voltage is present - it is a
    voltage a battery can have. Charging comes from the state byte: 2 is charging on
    Rapoo's own table, everything else means on battery.
    """
    d = list(data or [])
    if len(d) < offset + 4:
        return None
    tag, level, lo, hi = d[offset], d[offset + 1], d[offset + 2], d[offset + 3]
    if level > 100:
        return None
    voltage: Optional[int] = None
    raw = lo | (hi << 8)                 # u16 little endian, 10 mV per step
    if VOLTAGE_MIN <= raw <= VOLTAGE_MAX:
        voltage = raw * VOLTAGE_UNIT_MV
    elif raw != 0:
        return None                      # neither a voltage nor padding: not telemetry
    # the state byte: 2 = charging (Rapoo's table), 1 = on battery
    state = d[offset + 4] if len(d) > offset + 4 else 1
    charging = state == 2
    # a block of all zeros is padding, and a tag of 0 with no voltage is not a reply
    if tag == 0 and level == 0 and voltage is None:
        return None
    return level, charging, voltage


def parse_reply(resp) -> Optional[Tuple[int, bool, Optional[int]]]:
    """A feature report -> (level, charging, voltage) or None.

    hidapi on Windows hands back the report with the id in front; the block can start
    one byte in. Both are accepted, and the first block that looks like telemetry wins.
    """
    d = list(resp or [])
    if not d:
        return None
    for start in (0, 1):
        # one block every eight bytes; four bytes are needed for a block to parse
        for off in range(start, max(start, len(d) - 3), 8):
            got = parse_block(d, off)
            if got is not None:
                return got
    return None


class RapooProvider(Provider):
    name = "rapoo"

    def __init__(self):
        self._diag: List[str] = []
        self._report_id: Dict[bytes, int] = {}      # collection -> the report id that answered
        self._last: Dict[str, Tuple[int, bool, float]] = {}

    # ---------------- reading
    def _read(self, path: bytes) -> Optional[Tuple[int, bool, Optional[int]]]:
        """GET_REPORT(Feature) on one collection. Nothing is written."""
        dev = hid.device()
        try:
            dev.open_path(path)
        except (OSError, IOError) as e:
            self._diag.append(f"    open: {e}")
            return None
        try:
            ids = [self._report_id[path]] if path in self._report_id else list(REPORT_IDS)
            for rid in ids:
                try:
                    resp = dev.get_feature_report(rid, FEATURE_LENGTH)
                except (OSError, ValueError):
                    continue
                got = parse_reply(resp)
                if got is None:
                    continue
                self._report_id[path] = rid
                level, charging, voltage = got
                self._diag.append(f"    feature {rid:#04x}: {hexdump(resp, 8)}"
                                  f" -> {level}%{' charging' if charging else ''}"
                                  f"{f' {voltage/1000:.2f} V' if voltage else ''}")
                return got
            self._diag.append("    no telemetry block in any feature report")
            return None
        finally:
            try:
                dev.close()
            except Exception:
                pass

    @staticmethod
    def _telemetry_ifaces(infos: List[dict]) -> List[dict]:
        out = []
        for d in infos:
            if d.get("usage_page") == TELEMETRY_USAGE_PAGE:
                out.append(d)
        return out

    @staticmethod
    def _device_name(infos: List[dict]) -> str:
        for d in infos:
            name = (d.get("product_string") or "").strip()
            if not name:
                continue
            if name.lower() in GENERIC_NAMES:
                continue
            return name
        return DEFAULT_NAME

    def poll(self) -> List[DeviceStatus]:
        self._diag = []
        if hid is None:
            return []
        try:
            infos = hidlist.enumerate(RAPOO_VID)
        except Exception as e:              # pragma: no cover
            log.warning("hid.enumerate(rapoo): %s", e)
            return []
        if not infos:
            return []

        # one icon per receiver: group the collections by product id
        groups: Dict[int, List[dict]] = {}
        for d in infos:
            groups.setdefault(d.get("product_id", 0), []).append(d)

        out: List[DeviceStatus] = []
        for pid in sorted(groups):
            ifaces = groups[pid]
            name = self._device_name(ifaces)
            key = f"rapoo:{pid:04x}"
            self._diag.append(f"[Rapoo] pid={pid:04x} "
                              f"'{(ifaces[0].get('product_string') or '').strip()}' "
                              f"interfaces={len(ifaces)}")
            telemetry = self._telemetry_ifaces(ifaces)
            if not telemetry:
                # a Rapoo without the vendor collection: nothing to ask (e.g. the
                # gaming family, which this provider does not speak)
                self._diag.append("    no 0xFFEF collection: not an office-family receiver")
                continue
            got = None
            for d in telemetry:
                self._diag.append(f"    iface={d.get('interface_number')} "
                                  f"usage={d.get('usage_page', 0):04x}:{d.get('usage', 0):04x}")
                got = self._read(d["path"])
                if got is not None:
                    break
            if got is None:
                last = self._last.get(key)
                if last and time.time() - last[2] < ASLEEP_KEEP:
                    out.append(DeviceStatus(key, name, last[0], last[1], False, "rapoo",
                                            kind="mouse"))
                continue
            level, charging, _voltage = got
            self._last[key] = (level, charging, time.time())
            out.append(DeviceStatus(key, name, level, charging, True, "rapoo", kind="mouse"))
        return out

    def diagnostics(self) -> List[str]:
        return list(self._diag)
