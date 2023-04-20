from enum import Enum
from typing import Tuple, Union, Optional
import serial
from time import sleep


class RxActions(Enum):
    RESET = "RESET system -- also used as wake message"
    START_SHUFFLE_MCU = "(Incoming) Request to start shuffle with microcontroller's configurations"
    START_SHUFFLE_SBC = "ACK to shuffle with RasPi/web-server's configurations"
    CAPTURE_IMAGE = "ACK of previous card slot && permission to scan next card (w/ count sync data)"
    RX_STRING = "Running string-builder data (single char transferred)"


class TxActions(Enum):
    RESET = "RESET system -- also used as wake message"
    START_SHUFFLE_MCU = "ACK to shuffle with microcontroller's configurations"
    START_SHUFFLE_SBC = "(Outgoing) Request to start shuffle with RasPi/web-server's configurations"
    IDENTIFY_SLOT = "Location of slot to store card into (PI -> Micro)"
    REINDEX_SLOT = "Error correction and/or desync correction (see RxActions.CAPTURE_IMAGE)"


RxPacket = Tuple[RxActions, Union[str, int, None]]


def _translate_packet(packet: int) -> RxPacket:
    packet = 0xff & packet
    bits = [(packet & (0b1 << i)) != 0 for i in range(8)]  # 0: LSB, ..., 7: MSB
    # packet == { bits[7], bits[6], bits[5], bits[4], bits[3], bits[2], bits[1], bits[0] }
    if bits[7]:
        return RxActions.RX_STRING, chr(packet & 0x7f)
    elif bits[6]:
        return RxActions.CAPTURE_IMAGE, packet & 0x3f
    else:
        assert packet & 0x3c == 0, "Invalid packet received: 0x%02x" % packet
        if bits[1]:
            return RxActions.START_SHUFFLE_SBC if bits[0] else RxActions.START_SHUFFLE_MCU, None
        else:
            assert packet == 0, "Invalid packet received: 0x%02x" % packet
            return RxActions.RESET, None


def _build_packet(action: TxActions, arg: Optional[int] = None) -> int:
    if action == TxActions.RESET:
        return 0x00
    if action == TxActions.START_SHUFFLE_MCU:
        return 0x02
    if action == TxActions.START_SHUFFLE_SBC:
        return 0x03
    if action == TxActions.IDENTIFY_SLOT:
        assert arg is not None and 0 <= arg < 52, f"Invalid arg {arg} for action TxActions.IDENTIFY_SLOT"
        return 0x80 | arg
    if action == TxActions.REINDEX_SLOT:
        assert arg is not None and 0 <= arg < 52, f"Invalid arg {arg} for action TxActions.REINDEX_SLOT"
        return 0xc0 | arg
    assert False, f"Unrecognized TxAction: {action} = {action.value}"


class UART:
    verbose: bool = False

    def __init__(self, *, baud_rate: int):
        if UART.verbose:
            print(f"UART enabled @ baud={baud_rate}")
        self.ser = serial.Serial("/dev/ttyS0", baud_rate)

    def tx(self, action: TxActions, arg: Optional[int] = None) -> None:
        packet = _build_packet(action, arg).to_bytes(1, 'little')
        if UART.verbose:
            print(f"Sent packet(action={action.name}, arg={arg}) as packet(value={packet})")
        self.ser.write(packet)

    def _get_rx_packet(self) -> RxPacket:
        # @precondition: self.ser.in_waiting > 0
        assert self.ser.in_waiting > 0, "Cannot call UART._get_rx_packet() unless packet is actually available"
        packet = self.ser.read(1)
        action, arg = _translate_packet(packet)
        if UART.verbose:
            print(f"Received packet(value={packet}) as packet(action={action.name}, arg={arg})")
        return action, arg

    def rx(self) -> Optional[RxPacket]:
        return self._get_rx_packet() if self.ser.in_waiting > 0 else None

    def rx_blocking(self, ms_delay: Union[int, float] = 1) -> RxPacket:
        while self.ser.in_waiting == 0:
            sleep(ms_delay / 1000)
        else:
            # guaranteed: self.ser.in_waiting > 0
            return self._get_rx_packet()

    def rx_timeout(self, timeout_ms: int = 500) -> Optional[RxPacket]:
        for _ in range(timeout_ms):
            if self.ser.in_waiting > 0:
                return self._get_rx_packet()
            sleep(0.001)
        return None
