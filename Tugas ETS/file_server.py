import socket
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import argparse

from file_protocol import FileProtocol
fp = FileProtocol()

def handle_connection(conn, addr):
    """
    Loop menerima perintah sampai client disconnect.
    Menggunakan delimiter '\r\n\r\n' untuk menandai akhir setiap request.
    """
    buffer = ""
    try:
        while True:
            chunk = conn.recv(1048576)
            if not chunk:
                break
            buffer += chunk.decode()
            while "\r\n\r\n" in buffer:
                cmd, _, buffer = buffer.partition("\r\n\r\n")
                logging.warning(f"[{addr}] Request: {cmd!r}")
                resp = fp.proses_string(cmd)
                conn.sendall((resp + "\r\n\r\n").encode())
    except Exception as e:
        logging.warning(f"[{addr}] Error: {e}")
    finally:
        conn.close()
        logging.warning(f"[{addr}] Disconnected")

def serve_threadpool(host, port, max_workers):
    """Server dengan ThreadPoolExecutor."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()
    logging.warning(f"ThreadPool server on {host}:{port}, workers={max_workers}")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        while True:
            conn, addr = sock.accept()
            logging.warning(f"Accepted {addr}")
            pool.submit(handle_connection, conn, addr)

def serve_processpool(host, port, max_workers):
    """Server dengan ProcessPoolExecutor."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()
    logging.warning(f"ProcessPool server on {host}:{port}, workers={max_workers}")

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        while True:
            conn, addr = sock.accept()
            logging.warning(f"Accepted {addr}")
            # NB: socket objects are picklable in Python3.7+
            pool.submit(handle_connection, conn, addr)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s %(levelname)s:%(message)s')
    p = argparse.ArgumentParser(description="File Server with pool concurrency")
    p.add_argument('--mode', choices=['thread','process'], default='thread',
                   help="Use thread-pool or process-pool")
    p.add_argument('--workers', type=int, default=5,
                   help="Number of workers in the pool")
    p.add_argument('--host', default='0.0.0.0')
    p.add_argument('--port', type=int, default=6767)
    args = p.parse_args()

    if args.mode == 'thread':
        serve_threadpool(args.host, args.port, args.workers)
    else:
        serve_processpool(args.host, args.port, args.workers)
        