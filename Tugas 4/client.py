import socket
import argparse
import os

def send_request(request):
    """Mengirim request ke server dan mengembalikan respons."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.port))
    sock.sendall(request.encode())
    response = sock.recv(4096).decode()
    sock.close()
    return response

def list_files():
    """Membuat dan mengirim request LIST."""
    request = "LIST / HTTP/1.1\r\nHost: {}\r\n\r\n".format(args.host)
    print("--- Sending LIST request ---")
    response = send_request(request)
    print("--- Server Response ---")
    print(response)

def upload_file(filepath):
    """Membaca file dan mengirimkannya via POST request."""
    filename = os.path.basename(filepath)
    try:
        with open(filepath, 'rb') as f:
            content_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return

    headers = [
        f"POST /{filename} HTTP/1.1",
        f"Host: {args.host}",
        f"Content-Length: {len(content_bytes)}",
        "Content-Type: application/octet-stream"
    ]
    header_text = "\r\n".join(headers) + "\r\n\r\n"

    request_bytes = header_text.encode('utf-8') + content_bytes
    
    print(f"--- Uploading {filepath} as {filename} ---")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.port))
    sock.sendall(request_bytes)
    response = sock.recv(4096).decode()
    sock.close()
    
    print("--- Server Response ---")
    print(response)

def delete_file(filename):
    """Membuat dan mengirim request DELETE."""
    request = f"DELETE /{filename} HTTP/1.1\r\nHost: {args.host}\r\n\r\n"
    print(f"--- Deleting {filename} ---")
    response = send_request(request)
    print("--- Server Response ---")
    print(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simple HTTP Client")
    parser.add_argument('command', choices=['list', 'upload', 'delete'], help="Command to execute.")
    parser.add_argument('path', nargs='?', help="File path for upload or delete command.")
    parser.add_argument('--host', default='localhost', help="Server host.")
    parser.add_argument('--port', type=int, default=8885, help="Server port for thread pool, 8889 for process pool.")
    
    args = parser.parse_args()

    if args.command == 'list':
        list_files()
    elif args.command == 'upload':
        if not args.path:
            print("Error: 'upload' command requires a file path.")
        else:
            upload_file(args.path)
    elif args.command == 'delete':
        if not args.path:
            print("Error: 'delete' command requires a file name.")
        else:
            delete_file(args.path)
            