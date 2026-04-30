#!/usr/bin/env python3
import socket
import sys
import threading
import select

HOST = "127.0.0.1"
PORT = 5051

last_client_addr = None
quit_flag = False
lock = threading.Lock()
single_client_set = False
period_count = 0

def console_input():
    global last_client_addr, quit_flag
    while not quit_flag:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            text = line.rstrip("\n")
        except (KeyboardInterrupt, EOFError):
            break

        if text.strip().lower() == "quit":
            print("Quit command received from console. Exiting.")
            with lock:
                quit_flag = True
            break

        with lock:
            if last_client_addr is None:
                print("No client address known to send message to.")
                continue
            client_addr = last_client_addr

        try:
            sock.sendto((text + "\n").encode("utf-8"), client_addr)
            print(f"Sent to client: {text}")
        except OSError as exc:
            print(f"Failed to send message: {exc}")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
print(f"UDP server listening on {HOST}:{PORT}")

console_thread = threading.Thread(target=console_input, daemon=True)
console_thread.start()

hello_printed = False

while not quit_flag:
    try:
        ready = select.select([sock], [], [], 1.0)
        if not ready[0]:
            with lock:
                if single_client_set:
                    try:
                        sock.sendto(b".", last_client_addr)
                        period_count += 1
                        print(f"Sent period {period_count} due to inactivity.")
                        if period_count >= 30:
                            print("30 periods sent. Disconnecting client.")
                            single_client_set = False
                            last_client_addr = None
                            hello_printed = False
                            period_count = 0
                    except OSError as exc:
                        print(f"Failed to send period: {exc}")
            continue
        data, addr = sock.recvfrom(1024)
        with lock:
            if not single_client_set:
                last_client_addr = addr
                single_client_set = True
            elif addr != last_client_addr:
                print(f"Ignoring message from {addr}: only one client allowed.")
                continue
        if not hello_printed:
            try:
                sock.sendto(b"hello world!", addr)
                print("Sent hello world! to client.")
                hello_printed = True
            except OSError as exc:
                print(f"Failed to send hello world!: {exc}")
        message = data.decode("utf-8", errors="replace").rstrip("\n")
        print(f"Received from {addr}: {message}")
        with lock:
            period_count = 0
        if not message:
            print(f"Empty message received from {addr}. Disconnecting client.")
            try:
                sock.sendto(b"", addr)
                print("Sent empty message back to client.")
            except OSError as exc:
                print(f"Failed to send empty message: {exc}")
            with lock:
                single_client_set = False
                last_client_addr = None
                hello_printed = False
                period_count = 0
            continue
    except OSError:
        break

sock.close()

