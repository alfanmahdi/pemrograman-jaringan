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
    Membaca seluruh request HTTP dari client, memprosesnya,
    dan mengirimkan respons kembali.
    """
    # Baca header terlebih dahulu sampai menemukan \r\n\r\n
    headers = b""
    while b"\r\n\r\n" not in headers:
        try:
            chunk = connection.recv(1024)
            if not chunk:
                break
            headers += chunk
        except socket.timeout:
            break

    # Jika tidak ada header, tutup koneksi
    if not headers:
        connection.close()
        return

    # Pisahkan header dan body
    header_text, body_start = headers.split(b'\r\n\r\n', 1)
    header_str = header_text.decode('utf-8')

    # Cari Content-Length untuk request POST
    content_length = 0
    for line in header_str.split('\r\n'):
        if line.lower().startswith('content-length:'):
            try:
                content_length = int(line.split(':', 1)[1].strip())
            except ValueError:
                content_length = 0
            break

    # Baca sisa body jika ada
    body = body_start
    while len(body) < content_length:
        try:
            chunk = connection.recv(4096)
            if not chunk:
                break
            body += chunk
        except socket.timeout:
            break
            
    # Gabungkan kembali request lengkap untuk diproses
    full_request = header_text.encode('utf-8') + b'\r\n\r\n' + body

    try:
        # Proses request dan kirim respons
        hasil = httpserver.proses(full_request)
        connection.sendall(hasil)
    except Exception as e:
        logging.error(f"Error processing request from {address}: {e}")
        error_response = httpserver.response(500, 'Internal Server Error', str(e))
        connection.sendall(error_response)
    finally:
        connection.close()

def Server():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(('0.0.0.0', 8885))
    my_socket.listen(5)
    logging.warning("Thread Pool Server running on port 8885")

    with ThreadPoolExecutor(20) as executor:
        while True:
            connection, client_address = my_socket.accept()
            connection.settimeout(1.0) # Timeout untuk mencegah hang
            logging.warning(f"Connection from {client_address}")
            executor.submit(ProcessTheClient, connection, client_address)

def main():
    logging.basicConfig(level=logging.WARNING)
    Server()

if __name__ == "__main__":
    main()
