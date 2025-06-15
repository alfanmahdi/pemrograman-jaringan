from socket import *
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from my_http import HttpServer

httpserver = HttpServer()

#untuk menggunakan threadpool executor, karena tidak mendukung subclassing pada process,
#maka class ProcessTheClient dirubah dulu menjadi function, tanpda memodifikasi behaviour didalamnya

def ProcessTheClient(connection, address):
    """
    Fungsi diagnostik untuk melacak alur penanganan klien secara detail.
    """
    addr_str = f"[{address[0]}:{address[1]}]"
    logging.warning(f"{addr_str} >> Koneksi diterima, thread dimulai.")
    
    try:
        # 1. Baca headers
        headers = b""
        logging.warning(f"{addr_str} >> Mulai membaca headers...")
        while b"\r\n\r\n" not in headers:
            try:
                chunk = connection.recv(1024)
                if not chunk:
                    logging.warning(f"{addr_str} >> Koneksi ditutup klien saat membaca headers.")
                    break
                headers += chunk
            except socket.timeout:
                logging.warning(f"{addr_str} >> Timeout saat membaca headers.")
                break
        
        logging.warning(f"{addr_str} >> Selesai membaca headers. Total bytes diterima: {len(headers)}")

        # 2. Periksa kelengkapan headers
        if b"\r\n\r\n" not in headers:
            logging.error(f"{addr_str} >> Headers tidak lengkap. Menutup koneksi.")
            connection.close()
            return

        header_bytes, body_start = headers.split(b'\r\n\r\n', 1)
        header_str = header_bytes.decode('utf-8')
        logging.warning(f"{addr_str} >> Headers berhasil di-parse.")

        # 3. Cari Content-Length
        content_length = 0
        for line in header_str.split('\r\n'):
            if line.lower().startswith('content-length:'):
                try:
                    content_length = int(line.split(':', 1)[1].strip())
                except (ValueError, IndexError):
                    content_length = 0
                break
        logging.warning(f"{addr_str} >> Content-Length terdeteksi: {content_length}.")

        # 4. Baca body request
        body = body_start
        logging.warning(f"{addr_str} >> Mulai membaca body. Sudah ada {len(body)} bytes dari buffer.")
        
        while len(body) < content_length:
            try:
                bytes_to_read = min(4096, content_length - len(body))
                chunk = connection.recv(bytes_to_read)
                if not chunk:
                    logging.warning(f"{addr_str} >> Koneksi ditutup klien saat membaca body.")
                    break
                body += chunk
                logging.warning(f"{addr_str} >> Menerima chunk body, total body sekarang {len(body)} bytes.")
            except socket.timeout:
                logging.warning(f"{addr_str} >> Timeout saat membaca body.")
                break
        logging.warning(f"{addr_str} >> Selesai membaca body. Ukuran body final: {len(body)} bytes.")

        # 5. Proses request
        full_request = header_bytes + b'\r\n\r\n' + body
        logging.warning(f"{addr_str} >> Memproses request lengkap ({len(full_request)} bytes)...")
        
        hasil = httpserver.proses(full_request)
        
        logging.warning(f"{addr_str} >> Request diproses. Mengirim respons ({len(hasil)} bytes)...")
        connection.sendall(hasil)
        logging.warning(f"{addr_str} >> Respons berhasil dikirim.")

    except Exception as e:
        logging.error(f"{addr_str} >> Terjadi error tak terduga: {e}", exc_info=True)
    finally:
        logging.warning(f"{addr_str} >> Menutup koneksi.")
        connection.close()


def Server():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(('0.0.0.0', 8885))
    my_socket.listen(5)
    logging.warning("Thread Pool Server (DIAGNOSTIC MODE) running on port 8885")

    with ThreadPoolExecutor(20) as executor:
        while True:
            connection, client_address = my_socket.accept()
            # Set timeout untuk mencegah recv() hang selamanya
            connection.settimeout(2.0) 
            logging.warning(f"Connection from {client_address}")
            executor.submit(ProcessTheClient, connection, client_address)

def main():
    # Mengatur format logging untuk menyertakan waktu
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    Server()

if __name__ == "__main__":
    main()
