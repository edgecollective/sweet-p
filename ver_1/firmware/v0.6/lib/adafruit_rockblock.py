# SPDX-FileCopyrightText: 2020 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rockblock`
================================================================================

CircuitPython driver for Rock Seven RockBLOCK Iridium satellite modem

* Author(s): Carter Nelson
* Modified: Fixed epoch calculation for CircuitPython compatibility
*           Updated to ERA3 epoch (Feb 14, 2025) for post-Jan 14, 2026 compatibility

Implementation Notes
--------------------

**Hardware:**

* `RockBLOCK 9603 Iridium Satellite Modem <https://www.adafruit.com/product/4521>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

**Iridium Epoch Notes:**

* ERA2: May 11, 2014, 14:23:55 UTC (expired Jan 14, 2026)
* ERA3: February 14, 2025, 18:14:17 UTC (current, effective Jan 14, 2026)

"""
from __future__ import annotations

try:
    from typing import Tuple, Union, Optional
    from busio import UART
    from serial import Serial
except ImportError:
    pass

import time
import struct

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RockBlock.git"


def _is_leap_year(year):
    """Check if a year is a leap year."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _days_in_month(year, month):
    """Return the number of days in a given month."""
    days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month == 2 and _is_leap_year(year):
        return 29
    return days[month]


def _add_seconds_to_datetime(year, month, day, hour, minute, second, secs_to_add):
    """
    Add seconds to a datetime and return the new datetime components.
    This avoids using mktime/localtime which have epoch issues in CircuitPython.
    """
    # Add seconds
    second += secs_to_add

    # Normalize seconds -> minutes
    extra_minutes = second // 60
    second = second % 60
    minute += extra_minutes

    # Normalize minutes -> hours
    extra_hours = minute // 60
    minute = minute % 60
    hour += extra_hours

    # Normalize hours -> days
    extra_days = hour // 24
    hour = hour % 24
    day += extra_days

    # Normalize days -> months -> years
    while True:
        dim = _days_in_month(year, month)
        if day <= dim:
            break
        day -= dim
        month += 1
        if month > 12:
            month = 1
            year += 1

    # Calculate day of week (Zeller's congruence, adjusted for struct_time)
    # struct_time uses 0=Monday, 6=Sunday
    q = day
    m = month
    y = year
    if m < 3:
        m += 12
        y -= 1
    k = y % 100
    j = y // 100
    h = (q + (13 * (m + 1)) // 5 + k + k // 4 + j // 4 - 2 * j) % 7
    # Convert from Zeller (0=Sat, 1=Sun, ...) to struct_time (0=Mon, 6=Sun)
    wday = (h + 5) % 7

    # Calculate day of year
    yday = day
    for m in range(1, month):
        yday += _days_in_month(year, m)

    return time.struct_time((year, month, day, hour, minute, second, wday, yday, -1))


class RockBlock:
    """Driver for RockBLOCK Iridium satellite modem."""

    def __init__(self, uart: Union[UART, Serial], baudrate: int = 19200) -> None:
        self._uart = uart
        self._uart.baudrate = baudrate
        self._buf_out = None
        self.reset()

    def _uart_xfer(self, cmd: str) -> Tuple[bytes, ...]:
        """Send AT command and return response as tuple of lines read."""
        self._uart.reset_input_buffer()
        self._uart.write(str.encode("AT" + cmd + "\r"))

        if cmd == "+SBDIX":
            print("giving SBDIX time to respond ...")
            time.sleep(20)

        resp = []
        line = self._uart.readline()
        resp.append(line)
        while not any(EOM in line for EOM in (b"OK\r\n", b"ERROR\r\n")):
            line = self._uart.readline()
            resp.append(line)

        self._uart.reset_input_buffer()

        return tuple(resp)

    def reset(self) -> None:
        """Perform a software reset."""
        self._uart_xfer("&F0")  # factory defaults
        self._uart_xfer("&K0")  # flow control off

    def _transfer_buffer(self) -> None:
        """Copy out buffer to in buffer to simulate receiving a message."""
        self._uart_xfer("+SBDTC")

    @property
    def data_out(self) -> Optional[bytes]:
        """The binary data in the outbound buffer."""
        return self._buf_out

    @data_out.setter
    def data_out(self, buf: bytes) -> None:
        if buf is None:
            # clear the buffer
            resp = self._uart_xfer("+SBDD0")
            resp = int(resp[1].strip().decode())
            if resp == 1:
                raise RuntimeError("Error clearing buffer.")
        else:
            # set the buffer
            if len(buf) > 340:
                raise RuntimeError("Maximum length of 340 bytes.")
            self._uart.write(str.encode("AT+SBDWB={}\r".format(len(buf))))
            line = self._uart.readline()
            while line != b"READY\r\n":
                line = self._uart.readline()
            # binary data plus checksum
            self._uart.write(buf + struct.pack(">H", sum(buf)))
            line = self._uart.readline()  # blank line
            line = self._uart.readline()  # status response
            resp = int(line)
            if resp != 0:
                raise RuntimeError("Write error", resp)
            # seems to want some time to digest
            time.sleep(0.1)
        self._buf_out = buf

    @property
    def text_out(self) -> Optional[str]:
        """The text in the outbound buffer."""
        text = None
        try:
            text = self._buf_out.decode()
        except Exception:
            pass
        return text

    @text_out.setter
    def text_out(self, text: str) -> None:
        if not isinstance(text, str):
            raise ValueError("Only strings allowed.")
        if len(text) > 120:
            raise ValueError("Text size limited to 120 bytes.")
        self.data_out = str.encode(text)

    @property
    def data_in(self) -> Optional[bytes]:
        """The binary data in the inbound buffer."""
        data = None
        if self.status[2] == 1:
            resp = self._uart_xfer("+SBDRB")
            data = resp[0].splitlines()[1]
            data = data[2:-2]
        return data

    @data_in.setter
    def data_in(self, buf: bytes) -> None:
        if buf is not None:
            raise ValueError("Can only set in buffer to None to clear.")
        resp = self._uart_xfer("+SBDD1")
        resp = int(resp[1].strip().decode())
        if resp == 1:
            raise RuntimeError("Error clearing buffer.")

    @property
    def text_in(self) -> Optional[str]:
        """The text in the inbound buffer."""
        text = None
        if self.status[2] == 1:
            resp = self._uart_xfer("+SBDRT")
            try:
                text = resp[2].strip().decode()
            except UnicodeDecodeError:
                pass
        return text

    @text_in.setter
    def text_in(self, text: bytes) -> None:
        self.data_in = text

    def satellite_transfer(self, location: str = None) -> Tuple[Optional[int], ...]:
        """Initiate a Short Burst Data transfer with satellites."""
        status = (None,) * 6
        if location:
            resp = self._uart_xfer("+SBDIX=" + location)
        else:
            resp = self._uart_xfer("+SBDIX")
        if resp[-1].strip().decode() == "OK":
            status = resp[-3].strip().decode().split(":")[1]
            status = [int(s) for s in status.split(",")]
            if status[0] <= 5:
                # outgoing message sent successfully
                self.data_out = None
        return tuple(status)

    @property
    def status(self) -> Tuple[Optional[int], ...]:
        """Return tuple of Short Burst Data status."""
        resp = self._uart_xfer("+SBDSX")
        if resp[-1].strip().decode() == "OK":
            status = resp[1].strip().decode().split(":")[1]
            return tuple(int(a) for a in status.split(","))
        return (None,) * 6

    @property
    def model(self) -> Optional[str]:
        """Return modem model."""
        resp = self._uart_xfer("+GMM")
        if resp[-1].strip().decode() == "OK":
            return resp[1].strip().decode()
        return None

    @property
    def serial_number(self) -> Optional[str]:
        """Modem's serial number, also known as the modem's IMEI."""
        resp = self._uart_xfer("+CGSN")
        if resp[-1].strip().decode() == "OK":
            return resp[1].strip().decode()
        return None

    @property
    def signal_quality(self) -> Optional[int]:
        """Signal Quality (RSSI). Values 0-5, where 0 is no signal and 5 is strong."""
        resp = self._uart_xfer("+CSQ")
        if resp[-1].strip().decode() == "OK":
            return int(resp[1].strip().decode().split(":")[1])
        return None

    @property
    def revision(self) -> Tuple[Optional[str], ...]:
        """Modem's internal component firmware revisions."""
        resp = self._uart_xfer("+CGMR")
        if resp[-1].strip().decode() == "OK":
            lines = []
            for x in range(1, len(resp) - 2):
                line = resp[x]
                if line != b"\r\n":
                    lines.append(line.decode().strip())
            return tuple(lines)
        return (None,) * 7

    @property
    def ring_alert(self) -> Optional[bool]:
        """The current ring indication mode."""
        resp = self._uart_xfer("+SBDMTA?")
        if resp[-1].strip().decode() == "OK":
            return bool(int(resp[1].strip().decode().split(":")[1]))
        return None

    @ring_alert.setter
    def ring_alert(self, value: Union[int, bool]) -> Optional[bool]:
        if value in (True, False):
            resp = self._uart_xfer("+SBDMTA=" + str(int(value)))
            if resp[-1].strip().decode() == "OK":
                return True
            raise RuntimeError("Error setting Ring Alert.")
        raise ValueError(
            "Use 0 or False to disable Ring Alert or use 1 or True to enable Ring Alert."
        )

    @property
    def ring_indication(self) -> Tuple[Optional[str], ...]:
        """The ring indication status."""
        resp = self._uart_xfer("+CRIS")
        if resp[-1].strip().decode() == "OK":
            return tuple(resp[1].strip().decode().split(":")[1].split(","))
        return (None,) * 2

    @property
    def geolocation(
        self,
    ) -> Union[Tuple[int, int, int, time.struct_time], Tuple[None, None, None, None]]:
        """Most recent geolocation of the modem as measured by the Iridium constellation."""
        resp = self._uart_xfer("-MSGEO")
        if resp[-1].strip().decode() == "OK":
            temp = resp[1].strip().decode().split(":")[1].split(",")
            ticks_since_epoch = int(temp[3], 16)

            # Convert ticks to seconds (each tick = 90ms)
            secs_since_epoch = (ticks_since_epoch * 90) // 1000

            # Iridium ERA3 epoch: February 14, 2025, 18:14:17 UTC
            result_time = _add_seconds_to_datetime(2025, 2, 14, 18, 14, 17, secs_since_epoch)

            return (
                int(temp[0]),
                int(temp[1]),
                int(temp[2]),
                result_time,
            )
        return (None,) * 4

    @property
    def system_time(self) -> Optional[time.struct_time]:
        """Current date and time as given by the Iridium network.

        The system time is available and valid only after the ISU has registered with
        the network and has received the Iridium system time from the network.

        The timestamp used by the modem is Iridium system time, which is a running count of
        90 millisecond intervals since the Iridium epoch.

        As of January 14, 2026, the Iridium network uses ERA3 with epoch:
        February 14, 2025, 18:14:17 UTC

        The system time value is always expressed in UTC time.

        Returns:
        time.struct_time
        """
        resp = self._uart_xfer("-MSSTM")
        if resp[-1].strip().decode() == "OK":
            temp = resp[1].strip().decode().split(":")[1]
            if temp == " no network service":
                return None

            ticks_since_epoch = int(temp, 16)

            # Convert ticks to seconds (each tick = 90ms)
            secs_since_epoch = (ticks_since_epoch * 90) // 1000

            # Iridium ERA3 epoch: February 14, 2025, 18:14:17 UTC
            # ERA3 became active on January 14, 2026
            # (ERA2 was May 11, 2014, 14:23:55 UTC - no longer valid)
            result_time = _add_seconds_to_datetime(2025, 2, 14, 18, 14, 17, secs_since_epoch)

            return result_time
        return None

    @property
    def energy_monitor(self) -> Optional[int]:
        """The current accumulated energy usage estimate in microamp hours."""
        resp = self._uart_xfer("+GEMON")
        if resp[-1].strip().decode() == "OK":
            return int(resp[1].strip().decode().split(":")[1])
        return None

    @energy_monitor.setter
    def energy_monitor(self, value: int) -> Optional[int]:
        if 0 <= value <= 67108863:  # 0 to 2^26 - 1
            resp = self._uart_xfer("+GEMON=" + str(value))
            if resp[-1].strip().decode() == "OK":
                return True
            raise RuntimeError("Error setting energy monitor accumulator.")
        raise ValueError("Value must be between 0 and 67108863 (2^26 - 1).")
