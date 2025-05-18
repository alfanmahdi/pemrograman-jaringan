import os
import socket
import json
import base64
import logging

# Alamat dan port server—sesuaikan dengan yang kamu pakai
server_address = ('172.16.16.101', 6767)

def send_command(command_str=""):
    """Kirim command ke server, tunggu respons JSON hingga delimiter \r\n\r\n"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message: {command_str.split()[0]}")
        sock.sendall(command_str.encode())

        data_received = ""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            data_received += chunk.decode()
            if "\r\n\r\n" in data_received:
                break

        return json.loads(data_received)
    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        return {'status':'ERROR','data':str(e)}
    finally:
        sock.close()

def remote_list():
    hasil = send_command("LIST")
    if hasil.get('status') == 'OK':
        print("Daftar file di server:")
        for fn in hasil['data']:
            print(f"- {fn}")
    else:
        print("LIST Gagal:", hasil.get('data'))

def remote_get(filename, save_to=None):
    hasil = send_command(f"GET {filename}")
    if hasil.get('status') == 'OK':
        # Ambil konten base64 dari respons
        b64data = hasil['data_file']
        # Decode ke bytes asli
        file_bytes = base64.b64decode(b64data)
        # Tentukan nama file target (default sama dengan filename)
        target = save_to if save_to else filename
        # Tulis bytes asli ke disk
        with open(target, 'wb') as f:
            f.write(file_bytes)
        print(f"File '{filename}' berhasil diunduh sebagai '{target}'.")
    else:
        print("GET Gagal:", hasil.get('data'))

def remote_upload(filepath):
    if not os.path.isfile(filepath):
        print(f"[UPLOAD ERROR] File lokal '{filepath}' tidak ditemukan.")
        return
    fn = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    hasil = send_command(f"UPLOAD {fn} {b64}")
    if hasil.get('status') == 'OK':
        print(f"[UPLOAD] {hasil['data']}")
    else:
        print("[UPLOAD ERROR]", hasil.get('data'))

def remote_delete(filename):
    hasil = send_command(f"DELETE {filename}")
    if hasil.get('status') == 'OK':
        print(f"[DELETE] {hasil['data']}")
    else:
        print("[DELETE ERROR]", hasil.get('data'))

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    remote_list()
    remote_upload('contoh.txt')
    remote_list()
    remote_get('contoh.txt')
    remote_delete('contoh.txt')
    remote_list()
    remote_get('donalbebek.jpg')
    