import sys
from time import sleep

from uart import UART, TxActions, RxActions
import identify_card as cv
from orderer import OrderGenerator


def noop(*args):
    pass


_dbprint = noop

_string_buffer: str = ""


def _build_string(char: str) -> None:
    global _string_buffer
    if char != '\0':
        _string_buffer += char
    else:
        _dbprint(f"Built config string \"{_string_buffer}\"")
        # format for each string is "<field>:<value>", where <field>
        # and <value> are only `[^:]*`, and the delimiter is ':'
        key, value = _string_buffer.split(":")
        OrderGenerator.reconfigure(key, value)
        _string_buffer = ""  # clear buffer


class _SystemReset(Exception):
    pass


# noinspection PyShadowingNames
def _exec_logic(uart: UART, verbose_cv: bool) -> None:
    _dbprint("Starting execution loop")

    # wake/reset handshake
    _dbprint("Starting Wake/RESET handshake")
    while True:
        uart.tx(TxActions.RESET)
        response = uart.rx_timeout()
        if response is not None:
            action, _ = response
            if action == RxActions.RESET:
                break
    sleep(0.5)
    while uart.rx() is not None:
        continue  # clear all pending RESET transmissions -- prevents "boot-loop"
    _dbprint("Handshake completed")

    # get user settings
    _dbprint("Waiting for MCU start and/or settings")
    while True:
        action, char = uart.rx_blocking()
        if action == RxActions.RX_STRING:
            _build_string(char)
        elif action == RxActions.START_SHUFFLE_MCU:
            break
        elif action == RxActions.RESET:
            raise _SystemReset("@ loop for settings/start wait")
    _dbprint("Starting card processing with µC settings")

    # send start ack
    uart.tx(TxActions.START_SHUFFLE_MCU)
    # NTS webserver/START_SHUFFLE_SBC would go here as well (stretch goal #1)

    # shuffle process
    target_order = OrderGenerator.generate_order()
    # this should be the index of the NEXT expected.
    # the count the mcu sends should be the number TO BE processed (ie sbc_count==mcu_count)
    _dbprint("Starting card processing")
    for i in range(52):
        while True:
            action, data = uart.rx_blocking()
            while action != RxActions.CAPTURE_IMAGE:
                if action == RxActions.RESET:
                    raise _SystemReset("@ loop for card recognition/processing")
                if action == RxActions.RX_STRING:
                    _build_string(data)
                action, data = uart.rx_blocking()
            if data != i:
                _dbprint("Received image capture clearance, but index/key is out of sync... Retrying handshake...")
                uart.tx(TxActions.REINDEX_SLOT, i)
            else:
                _dbprint("Received image capture clearance")
                break

        # this slot should be RELATIVE slots not ABSOLUTE slot. MCU is responsible for translating from R to A
        img = None  # TODO capture image from camera
        edges, bboxes = cv.preprocess_image(img, verbose=verbose_cv)
        card, score_map = cv.identify_card(edges, bboxes, verbose=verbose_cv)  # TODO use score_map for card corrections
        slot = target_order[card]
        _dbprint(f"Identified current (index={i}) card as (card={card[0]}{card[1]}) to be placed into (slot={slot})")
        uart.tx(TxActions.IDENTIFY_SLOT, slot)
        # NTS store card location corrections here (stretch goal #2)
    _dbprint("Card processing complete")

    # NTS send all card location corrections here (stretch goal #2) via
    #  uart.tx(TxActions.REINDEX_SLOT, ...) & uart.tx(TxActions.IDENTIFY_SLOT, ...) packets
    _dbprint("Finishing execution loop")


if __name__ == '__main__':
    verbose_cv: bool = False

    if len(sys.argv) == 3:
        if sys.argv[1] != '-v':
            print("Second argument must be exactly `-v`")
            sys.exit(1)
        flags = sys.argv[2]
        if 'L' in flags or 'l' in flags:
            _dbprint = print
        if 'U' in flags or 'u' in flags:
            UART.verbose = True
        if 'C' in flags or 'c' in flags:
            verbose_cv = True
    elif len(sys.argv) != 1:
        print(f"{sys.argv[0]} takes either 0 or 2 arguments only")
        print("0 args: Normal operation")
        print("2 args: -v ???")
        print("  - enables verbose mode, and subsequent flags (`L`, `U`, `C`) enables verbosity"
              " for core logic, UART, and card recognition, respectively...")
        sys.exit(1)

    uart = UART(baud_rate=9600)

    while True:
        try:
            _exec_logic(uart, verbose_cv)
        except _SystemReset as e:
            _dbprint(e)
            pass
