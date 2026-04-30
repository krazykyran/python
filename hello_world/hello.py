#!/usr/bin/env python3

from datetime import datetime


def main():
    now = datetime.now()
    hour = now.hour
    if hour < 12:
        print("Good morning!")
    elif hour < 18:
        print("Good afternoon!")
    else:
        print("Good evening!")
    print(f"The local time is {now:%I:%M %p}")


if __name__ == "__main__":
    main()
