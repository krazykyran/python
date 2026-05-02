#!/usr/bin/env python3
"""
Linux serial echo tool.

- Opens /dev/ttyV3 (or user-specified port) with chosen baud rate
- Uses a 0.1 second serial timeout
- Prints incoming serial data
- Sends received data back to the serial port
- Monitors console commands: help, quit
"""

import argparse
import select
import sys
import time
import string
import serial


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Linux serial echo tool")
    parser.add_argument(
        "--port",
        default="/dev/ttyV3",
        help="Serial port path (default: /dev/ttyV3)",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=9600,
        help="Baud rate (default: 9600)",
    )
    return parser.parse_args()


def print_help() -> None:
    print("Available commands:")
    print("  help  - show this help")
    print("  quit  - exit the program")


def main() -> int:
    args = parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
    except serial.SerialException as exc:
        print(f"Failed to open serial port: {exc}")
        return 1

    print(f"Opened serial port {args.port} @ {args.baud} baud (timeout=0.1s)")
    print("Type 'help' for commands.")

    try:
        while True:
            # Read and echo incoming serial bytes.
            incoming = ser.read(ser.in_waiting or 1)
            if incoming:
                text = incoming.decode("utf-8", errors="replace")
                text_clean = ''.join(c if c in string.printable else '.' for c in text)
                print(f"[RX] {text_clean}")
                if incoming[-1:] == b"\r":
                    outgoing = incoming + b"\n"
                    ser.write(outgoing)
                    print("[TX] echoed data back (+LF appended after trailing CR)")
                else:
                    outgoing = incoming
                    ser.write(outgoing)
                    print("[TX] echoed data back")

            # Check console input without blocking serial handling.
            readable, _, _ = select.select([sys.stdin], [], [], 0)
            if readable:
                command = sys.stdin.readline()
                if not command:
                    # stdin closed (e.g. piped input ended)
                    break

                command = command.strip().lower()
                if command == "quit":
                    print("Quit command received. Exiting...")
                    break
                if command == "help":
                    print_help()
                elif command:
                    print(f"Unknown command: {command}. Type 'help'.")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting...")
    finally:
        ser.close()
        print("Serial port closed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())