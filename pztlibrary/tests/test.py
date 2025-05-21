# tests/test_senddata.py

import unittest
from unittest.mock import MagicMock, patch

import serial
# 1) FakeSerial stub to avoid real COM ports
class FakeSerial:
    def __init__(self, *args, **kwargs):
        self.in_waiting = 0
        self._read_buf = b""
        self.written = b""
        self.closed = False

    def write(self, data):
        self.written += data
        return len(data)

    def read_all(self):
        data, self._read_buf = self._read_buf, b""
        return data

    def read(self, size=1):
        chunk, self._read_buf = self._read_buf[:size], self._read_buf[size:]
        return chunk

    def close(self):
        self.closed = True

    def isOpen(self):
        return not self.closed


# 2) Patch out real serial and delays before importing
serial.Serial = FakeSerial
import time as _t; _t.sleep = lambda *a, **k: None

# 3) Now import the module under test
import SendData


class TestDataAnla(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(SendData.DataAnla(0.0), b'\x00\x00\x00\x00')

    def test_positive_integer(self):
        self.assertEqual(tuple(SendData.DataAnla(2.0)), (0, 2, 0, 0))

    def test_positive_fraction(self):
        hi, lo, fh, fl = SendData.DataAnla(3.1415)
        self.assertEqual((hi, lo), (0, 3))
        self.assertEqual((fh << 8) | fl,
                         int((3.1415 - 3 + 1e-5) * 10000))

    def test_negative(self):
        hi, lo, fh, fl = SendData.DataAnla(-1.5)
        self.assertTrue(hi & 0x80)
        self.assertEqual((hi & 0x7F, lo), (0, 1))
        self.assertEqual((fh << 8) | fl, 5000)

    def test_rounding_edge(self):
        # tiny fraction drops to zero
        hi, lo, fh, fl = SendData.DataAnla(4.00001)
        self.assertEqual((hi, lo), (0, 4))
        self.assertEqual((fh << 8) | fl, 0)

    @patch('builtins.print')
    def test_close_failure(self, mock_print):
        # Arrange: force isOpen→True to simulate failure
        SendData.Usart.closed = False
        SendData.Usart.isOpen = lambda: True

        # Act
        SendData.port_close()

        # Assert: printed “closed failure”
        called = any(
            "Serial port closed failure" in call.args[0]
            for call in mock_print.call_args_list
        )
        self.assertTrue(called)


class TestSendVfChannels(unittest.TestCase):
    def setUp(self):
        self.fake = FakeSerial()
        SendData.Usart = self.fake

    def _xor(self, data, length):
        x = 0
        for b in data[:length]:
            x ^= b
        return x

    def test_channel_bytes_and_checksum(self):
        for ch, expected in [(0, 0x00), (1, 0x01), (2, 0x02)]:
            self.fake.written = b""
            SendData.sendVf(1.23, ch)
            pkt = self.fake.written
            # Verify channel byte
            self.assertEqual(pkt[5], expected)
            # Verify checksum
            self.assertEqual(self._xor(pkt, 10), pkt[10])


class TestSendMovefChannels(unittest.TestCase):
    def setUp(self):
        self.fake = FakeSerial()
        SendData.Usart = self.fake

    def test_channels(self):
        for ch in [0, 1, 2]:
            self.fake.written = b""
            SendData.sendMovef(5.5, ch)
            exp = 0x00 if ch == 0 else (0x01 if ch == 1 else 0x02)
            self.assertEqual(self.fake.written[5], exp)

    def test_checksum(self):
        SendData.sendMovef(5.5, 1)
        pkt = self.fake.written
        xor = 0
        for b in pkt[:10]:
            xor ^= b
        self.assertEqual(xor, pkt[10])


class TestSendLowSpeedDetail(unittest.TestCase):
    def setUp(self):
        self.fake = FakeSerial()
        SendData.Usart = self.fake

    def _xor(self, data, length):
        x = 0
        for b in data[:length]:
            x ^= b
        return x

    def test_length_and_checksum(self):
        SendData.sendLowSpeedVoltageFreq(1.0, 2.0, 'Z', 1)
        pkt = self.fake.written
        self.assertEqual(len(pkt), 20)
        # BCC at index 19
        self.assertEqual(self._xor(pkt, 19), pkt[19])

    def test_waveform_and_values(self):
        SendData.sendLowSpeedVoltageFreq(3.0, 4.0, 'F', 0)
        pkt = self.fake.written
        # waveform byte at 6
        self.assertEqual(pkt[6], ord('F'))
        # second float (4.0) at bytes 11–14: hi=0, lo=4, frac=0
        self.assertEqual((pkt[11], pkt[12]), (0, 4))
        self.assertEqual((pkt[13], pkt[14]), (0, 0))


class TestRecvAndUart(unittest.TestCase):
    def test_recv_empty(self):
        fake = FakeSerial(); fake._read_buf = b""
        self.assertEqual(SendData.recv(fake), b"")

    def test_recv_data(self):
        fake = FakeSerial(); fake._read_buf = b"XYZ"
        self.assertEqual(SendData.recv(fake), b"XYZ")

    def test_uart_send_data(self):
        fake = FakeSerial(); fake.write = MagicMock(return_value=7)
        self.assertEqual(SendData.uart_send_data(fake, "ping"), 7)

    def test_uart_receive_data(self):
        fake = FakeSerial(); fake.in_waiting = 3
        fake.read = MagicMock(return_value=b"hey")
        with patch('builtins.print') as mock_print:
            SendData.uart_receive_data(fake)
            mock_print.assert_called_with('hey')


class TestThreading(unittest.TestCase):
    def test_run_once(self):
        fake = FakeSerial(); fake.in_waiting = 1
        fake.read = MagicMock(return_value=b"?")
        calls = {'n': 0}
        def side(u):
            calls['n'] += 1
            raise KeyboardInterrupt
        SendData.uart_receive_data = side
        with self.assertRaises(KeyboardInterrupt):
            SendData.myThread(fake).run()
        self.assertEqual(calls['n'], 1)


class TestSendTestEnhanced(unittest.TestCase):
    def test_writes_encodings(self):
        fake = FakeSerial()
        SendData.sendTest(fake)
        data = fake.written
        self.assertIn(b"hello world", data)
        self.assertIn("你好".encode('utf-8'), data)
        self.assertIn("你好".encode('gbk'), data)

    def test_sendTest_idempotent(self):
        fake = FakeSerial()
        SendData.sendTest(fake)
        first = fake.written
        SendData.sendTest(fake)
        self.assertEqual(fake.written, first + first)


if __name__ == "__main__":
    unittest.main()
