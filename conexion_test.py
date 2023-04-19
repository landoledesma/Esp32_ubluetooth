import ubluetooth
import random
import time
from ubluetooth import BLE, UUID, FLAG_READ, FLAG_NOTIFY, FLAG_WRITE, BLE_IRQ_GATTS_WRITE
from micropython import const

_DEVICE_NAME = 'Exoesqueleto'
_SERVICE_UUID = UUID('12345678-1234-5678-1234-56789ABCDEF0')
_CHAR_UUID = UUID('12345678-1234-5678-1234-56789ABCDEF1')
_CONTROL_CHAR_UUID = UUID('12345678-1234-5678-1234-56789ABCDEF2')
_BLE_IRQ_CENTRAL_CONNECT = const(1)
_BLE_IRQ_CENTRAL_DISCONNECT = const(2)

class BLEServer:
    def __init__(self, ble, name):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._connections = set()
        self._transmitting = False

        self._payload = b''

        self._services = (
            (_SERVICE_UUID, (
                (_CHAR_UUID, FLAG_READ | FLAG_NOTIFY),
                (_CONTROL_CHAR_UUID, FLAG_WRITE),
            )),
        )
        self._handles = self._ble.gatts_register_services(self._services)

        name_bytes = bytes(name, "utf-8")
        adv_payload = bytearray(
            b'\x02\x01\x06'  # Tipo de publicidad: General Discoverable Mode y BR/EDR Not Supported
            b'\x03\x03\x9E\xFE'  # Tipo de publicidad: Complete List of 16-bit Service Class UUIDs
            + bytes([1 + len(name_bytes)]) + b'\x09' + name_bytes  # Tipo de publicidad: Complete Local Name
        )
        self._ble.gap_advertise(100, adv_data=adv_payload)

    def _irq(self, event, data):
        if event == _BLE_IRQ_CENTRAL_CONNECT:
            conn_handle, _, _, = data
            self._connections.add(conn_handle)
            print("Conexión exitosa")
        elif event == _BLE_IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _, = data
            self._connections.remove(conn_handle)
            self._ble.gap_advertise(100, adv_data=self._adv_data)
        elif event == BLE_IRQ_GATTS_WRITE:
            conn_handle, attr_handle, buf, offset = data
            if attr_handle == self._handles[0][1][1] and buf[0] in (0x00, 0x01):
                self._transmitting = buf[0] == 0x01

    def set_payload(self, value):
        self._payload = "El número aleatorio generado es: {}.".format(value).encode()

    def send_payload(self):
        if not self._transmitting:
            return
        
        for conn_handle in self._connections:
            self._ble.gatts_write(self._handles[0][0], self._payload)
            self._ble.gatts_notify(conn_handle, self._handles[0][0])

def main():
    ble = BLE()
    ble_server = BLEServer(ble, _DEVICE_NAME)
    while True:
        if not ble_server._connections:
            print("Esperando...")
            time.sleep(1)
        else:
            random_value = random.randrange(20, 51)
            ble_server.set_payload(random_value)
            ble_server.send_payload()
            time.sleep(0.5)

if __name__ ==

