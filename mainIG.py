import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import traceback
import re
import time
import requests
import tkinter as tk
from tkinter import simpledialog
from VShipCRM.booking_lookup import getIDNumber
from VShipCRM.make_VShip_note import post_note
from parseFile import DataException, get_bookingNums_from_file
from VShipCRM.signInVShipCRM import sign_in_vshipcrm
from dotenv import load_dotenv

exe_file = sys.executable
exe_parent = os.path.dirname(exe_file)
dotenv_path = os.path.join(exe_parent, ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)
FILENAME = os.path.join(exe_parent, 'listOfBookings.txt') if getattr(sys, 'frozen', False) else 'listOfBookings.txt'
USERNAME = os.getenv('VSHIP_USER_NAME') if os.getenv('VSHIP_USER_NAME')!=None else ""
PASSWORD = os.getenv('VSHIP_PASSWORD') if os.getenv('VSHIP_PASSWORD')!=None else ""

def pause_before_exit():
    try:
        input("\nPress ENTER to close this window...")
    except EOFError:
        pass

def get_comment_from_user() -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    comment = simpledialog.askstring("Note Comment", "Enter the comment for the bookings:", parent=root)
    root.destroy()
    if comment is None or not comment.strip():
        print("No comment was entered. Exiting without creating any notes.")
        pause_before_exit()
        sys.exit(1)
    return comment.upper().strip()

class NoteError(Exception):
    pass

def normalize(s) -> str:
    return (
        s.split(",")[0]
        .split("_")[0]
        .split(" ")[0]
        .strip()
    )

CARRIER_PATTERNS = [
    (r"EBKG\d{8}",        "msc"),
    (r"2\d{8}",         "maersk"),
    (r"NAM\d{7}",         "cma"),
    (r"S3\d{8}",          "grimaldi"),
]


def carrierID(booking_num: str) -> str:
    """Identify carrier from a booking number string."""
    for pattern, carrier in CARRIER_PATTERNS:
        if carrier == "maersk":
            if re.fullmatch(pattern, booking_num.upper()):
                return carrier
        else:
            if re.search(pattern, booking_num.upper()):
                return carrier
    return "Error"
    
def main():
    if getattr(sys, 'frozen', False):
        missing = [p for p in (dotenv_path, FILENAME) if not os.path.isfile(p)]
        if missing:
            print("Required file(s) not found in the same folder as the .exe:\n" + "\n".join(missing))
            pause_before_exit()
            sys.exit(1)
    comment = get_comment_from_user()
    if Path('auth_for_VshipCRM.txt').exists() and datetime.now() - datetime.fromtimestamp(Path('auth_for_VshipCRM.txt').stat().st_mtime) < timedelta(hours = 1):
        print("Using existing authentication state.")
        with open('auth_for_VshipCRM.txt', 'r') as f:
            token = f.read().strip()
    else:
        token = sign_in_vshipcrm(USERNAME, PASSWORD) 
    try:
        data = get_bookingNums_from_file(FILENAME)
        if data is None:
            raise DataException("The program ran into an error trying to parse out the booking numbers in the file...There is either nothing in the file, or the file is returning nothing.")
    except DataException as e:
        print(f"{e}")
        pause_before_exit()
        sys.exit(1)
    except Exception as e:
        print(f"Ran into an unknown error trying to parse the file: {e}")
        pause_before_exit()
        sys.exit(1)        
    l_not_found = []
    with open('listOfBookingsFailed.txt', 'w') as f:
        for booking_no in data:
            print(f'Finding booking id for {booking_no}...')
            try:
                booking_id = getIDNumber(booking_no)
            except (KeyError, IndexError,AttributeError) as e:
                print(f"Error parsing response JSON for ref Number: {e}")
                f.write(f"{booking_no} Skipped Due to Booking's ID Not Found\n")
                l_not_found.append(booking_no)
                continue
            try:
                print(f'Creating note for {booking_no}...')
                resp_note = post_note(booking_id, comment, token)
                if resp_note.status_code != 201 and resp_note.status_code not in [400,401,403]:
                    raise ValueError(f"Note creation failed with status code: {resp_note.status_code}\n{resp_note.text}")
                elif resp_note.status_code in [400,401,403] and (datetime.now() - datetime.fromtimestamp(Path('auth_for_VshipCRM.txt').stat().st_mtime) > timedelta(minutes = 3)):
                    print(f"Note creation failed with status code: {resp_note.status_code}. ReSigning In")
                    token = sign_in_vshipcrm(USERNAME, PASSWORD)       
                    resp_note = post_note(booking_id, comment, token)
                    resp_note.raise_for_status()
                elif resp_note.status_code in [400,401,403] and (datetime.now() - datetime.fromtimestamp(Path('auth_for_VshipCRM.txt').stat().st_mtime) <= timedelta(minutes = 3)):
                    f.write(f"{booking_no} Skipped Due to Note creation failed with status code: {resp_note.status_code}\n{resp_note.text}\n")
                    raise ValueError(f"Note creation failed with status code: {resp_note.status_code}\n{resp_note.text}")
            except Exception as e:
                f.write(f"{booking_no} Skipped Due to generic Error\n{e}\n")
                raise NoteError(f"Error creating note: {e}")
        f.close()            
    print(f"List of booking numbers with no Note : {l_not_found}")    
    

if __name__ == "__main__":
    try:
        main()
        pause_before_exit()
    except Exception as e:
        print(f"\nAn error occurred:\n{e}\n")
        traceback.print_exc()
        pause_before_exit()
        sys.exit(1)
    