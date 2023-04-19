from uart import init_uart, write_string, tx, rx, RxActions, TxActions, translate_packet, build_packet
from time import sleep

if __name__ == '__main__':
    std_timeout = 0.5

    ser = init_uart(9600)

    # maybe wrap everything past here in a big ol' while loop?

    # Wake-up process
    wake_packet = build_packet(TxActions.RESET)
    while True:
        tx(ser, wake_packet)
        sleep(std_timeout)
        response = rx(ser)
        if response != None and translate_packet(response) == (RxActions.RESET, None):
            break

    # getting settings
    settings_buffer = ""
    while True:
        sleep(std_timeout)
        packet = rx(ser)
        if packet is None:
            continue
        (packet_type, char) = translate_packet(packet)
        if packet_type != RxActions.RX_STRING:
            # will we get non-string packets between the wake-up process and start shuffle?
            continue
        if char == "\0":
            break
        settings_buffer += char

    # TODO do stuff with the filled in settings buffer
    # (we'll have to nail down our format. personally, I'd love "field:value,field:value,field:value")

    # start process
    # right now, I'm assuming the pi sends the mode we want?
    # and we don't start until the micro sends back a ready-to-start with the same mode

    start_packet = build_packet(TxActions.START_SHUFFLE_MCU) # TODO add option for web server mode later
    # I know this is redundant, but separately defining for now in case we introduce disparities in SBC/MCU packets
    expected_type = RxActions.START_SHUFFLE_MCU
    while True:
        tx(ser, start_packet)
        sleep(std_timeout)
        packet = rx(ser)
        if packet is None:
            continue
        (packet_type, _) = translate_packet(packet)
        if packet_type != expected_type:
            # are we safe to just... drop every other type of packet here?
            continue
        # we should only hit this break if the MCU sends back the same start packet that we sent
        break

    # shuffle process
    # this should be the index of the NEXT expected. the count the mcu sends should be the number TO BE processed (ie sbc_count==mcu_count)
    sbc_count = 0
    while True:
        sleep(std_timeout)
        packet = rx(ser)
        if packet is None:
            continue
        (packet_type, mcu_count) = translate_packet(packet)
        if packet_type != RxActions.CAPTURE_IMAGE:
            # again, is there an issue with just dropping everything else?
            continue
        if mcu_count != sbc_count:
            correction_packet = build_packet(TxActions.REINDEX_SLOT, sbc_count)
            tx(ser, correction_packet)
            continue
        # this slot should be RELATIVE slots not ABSOLUTE slot. MCU is responsible for translating from R to A
        slot = 0 # TODO identifySlot()
        slot_packet = build_packet(TxActions.IDENTIFY_SLOT, slot)
        tx(ser, slot_packet)
