from socket import *
import socket
import threading
import logging
import time
import sys

from file_protocol import FileProtocol
fp = FileProtocol()

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        threading.Thread.__init__(self)
        self.connection = connection
        self.address = address

    def run(self):
        while True:
            try:
                data = self.connection.recv(32)
                if data:
                    d = data.decode()
                    hasil = fp.proses_string(d)
                    hasil = hasil + "\r\n\r\n"
                    self.connection.sendall(hasil.encode())
                else:
                    break
            except Exception as e:
                logging.warning(f"Error saat memproses client: {e}")
                break
        self.connection.close()


class Server(threading.Thread):
    def __init__(self, ipaddress='0.0.0.0', port=6666):
        threading.Thread.__init__(self)
        self.ipinfo = (ipaddress, port)
        self.the_clients = []

        # Inisialisasi socket dan aktifkan opsi reuse address
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        try:
            logging.warning(f"Server berjalan di ip address {self.ipinfo}")
            self.my_socket.bind(self.ipinfo)
            self.my_socket.listen(5)

            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"Connection from {client_address}")

                clt = ProcessTheClient(connection, client_address)
                clt.start()
                self.the_clients.append(clt)
        except Exception as e:
            logging.error(f"Gagal menjalankan server: {e}")
            self.my_socket.close()


def main():
    svr = Server(ipaddress='0.0.0.0', port=6767)
    svr.start()


if __name__ == "__main__":
    main()
    