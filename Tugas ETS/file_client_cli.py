import os
import socket
import json
import base64
import logging
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# DEFAULT server; bisa di-override lewat CLI
SERVER_HOST = '172.16.16.101'
SERVER_PORT = 6767

def send_command(command_str):
    """Kirim satu perintah lengkap, terima dan kembalikan dict JSON."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((SERVER_HOST, SERVER_PORT))
        sock.sendall((command_str + "\r\n\r\n").encode())
        data = ""
        while True:
            chunk = sock.recv(1048576)
            if not chunk:
                break
            data += chunk.decode()
            if "\r\n\r\n" in data:
                break
        raw, _, _ = data.partition("\r\n\r\n")
        return json.loads(raw)

def remote_list():
    return send_command("LIST")

def remote_get(filename):
    resp = send_command(f"GET {filename}")
    if resp['status']=='OK':
        data = base64.b64decode(resp['data_file'])
        with open(f"dl_{filename}", 'wb') as f:
            f.write(data)
    return resp

def remote_upload(filepath):
    fn = os.path.basename(filepath)
    data = base64.b64encode(open(filepath,'rb').read()).decode()
    return send_command(f"UPLOAD {fn} {data}")

def remote_delete(filename):
    return send_command(f"DELETE {filename}")

def single_op(op, volume_mb):
    """
    Buat dummy file jika perlu, lalu jalankan satu operasi upload atau download
    dan kembalikan (success:bool, bytes_processed:int, duration:float).
    """
    if op=='upload':
        fname = f"dummy_{volume_mb}MB.bin"
        # generate dummy
        with open(fname, 'wb') as f:
            f.write(os.urandom(volume_mb * 1024 * 1024))
        start = time.time()
        r = remote_upload(fname)
        dur = time.time() - start
        size = volume_mb * 1024 * 1024
        return r['status']=='OK', size, dur
    else:  # download
        # pastikan file di server sudah ada
        fname = f"dummy_{volume_mb}MB.bin"
        start = time.time()
        r = remote_get(fname)
        dur = time.time() - start
        size = volume_mb * 1024 * 1024
        return r['status']=='OK', size, dur

def stress_test(mode, op, volume, client_workers, server_workers):
    """
    Jalankan stress test untuk satu kombinasi:
    - mode: 'thread' atau 'process' (client side)
    - op: 'upload' atau 'download'
    - volume: ukuran file dalam MB
    - client_workers: jumlah worker di client pool
    - server_workers: jumlah worker di server pool (untuk info)
    """
    # Catat start
    start_all = time.time()
    successes = 0
    total_bytes = 0

    if mode=='thread':
        Pool = ThreadPoolExecutor
    else:
        Pool = ProcessPoolExecutor

    # Jalankan pool client
    with Pool(max_workers=client_workers) as pool:
        futures = [pool.submit(single_op, op, volume) for _ in range(client_workers)]
        for f in futures:
            ok,size,dur = f.result()
            if ok:
                successes += 1
                total_bytes += size
    total_dur = time.time() - start_all

    # Output metrics
    throughput = total_bytes / total_dur if total_dur>0 else 0
    return {
        'mode': mode,
        'operation': op,
        'volume_MB': volume,
        'client_workers': client_workers,
        'server_workers': server_workers,
        'total_time_s': round(total_dur,3),
        'throughput_Bps': round(throughput,2),
        'client_success': successes,
        'client_fail': client_workers - successes,
        'server_success': client_workers,   # asumsikan server worker berhasil memproses semua
        'server_fail': 0
    }

def main():
    logging.basicConfig(level=logging.WARNING,
                        format='%(asctime)s %(levelname)s:%(message)s')
    p = argparse.ArgumentParser(description="File Client + Stress Test")
    p.add_argument('--mode', choices=['thread','process'], default='thread',
                   help="Client concurrency mode")
    p.add_argument('--op', choices=['upload','download'], required=True)
    p.add_argument('--volume', type=int, choices=[10,50,100], required=True,
                   help="File size in MB")
    p.add_argument('--client_workers', type=int, choices=[1,5,50], required=True)
    p.add_argument('--server_workers', type=int, choices=[1,5,50], required=True)
    args = p.parse_args()

    # OPTIONAL: you must start server separately with matching --mode and --workers
    print("Stress test config:", args)

    result = stress_test(args.mode, args.op, args.volume,
                         args.client_workers, args.server_workers)
    # Print hasil sebagai CSV line
    print(",".join(map(str, [
        f"{args.mode}-{args.op}-{args.volume}MB-{args.client_workers}c-{args.server_workers}s",
        args.op,
        args.volume,
        args.client_workers,
        args.server_workers,
        result['total_time_s'],
        result['throughput_Bps'],
        f"{result['client_success']}/{args.client_workers}",
        f"{result['server_success']}/{args.server_workers}"
    ])))

if __name__ == "__main__":
    main()
    