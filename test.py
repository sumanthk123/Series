import subprocess
import sqlite3
import os
import time
DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")

def query_new_greetings(last_rowid):
    """
    Returns a list of tuples (msg_rowid, handle_id, full_text)
    for any new incoming iMessage whose text starts with our welcome prompt.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # look for any incoming (is_from_me=0) message matching our exact-prefix
    c.execute("""
        SELECT m.ROWID, h.id, m.text
          FROM message AS m
          JOIN handle  AS h ON m.handle_id = h.ROWID
         WHERE m.is_from_me = 0
           AND m.ROWID > ?
           AND m.text LIKE 'Welcome to Series! Text your color to get started:%'
         ORDER BY m.ROWID ASC
    """, (last_rowid,))
    rows = c.fetchall()
    conn.close()
    return rows

def send_imessage(text, handle_id):
    """
    Use osascript / AppleScript to send `text` back to the given handle_id
    (phone number or iCloud email) via iMessage.
    """
    applescript = f'''
    tell application "Messages"
      set targetService to 1st service whose service type = iMessage
      set theBuddy to buddy "{handle_id}" of targetService
      send "{text}" to theBuddy
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript], check=True)

seen_handles = set()
POLL_INTERVAL = 5

print("[*] Starting iMessage scanner… (polling every", POLL_INTERVAL, "s)")
last_rowid = 0
while True:
        try:
            new_msgs = query_new_greetings(last_rowid)
            if not new_msgs:
                # no matching new greetings → do absolutely nothing until next poll
                time.sleep(POLL_INTERVAL)
                continue

            for rowid, handle_id, text in new_msgs:
                last_rowid = max(last_rowid, rowid)  # advance watermark

                # # color = extract_color(text)
                # if not color:
                #     continue  # should never happen since we filtered, but safe

                # print(f"[+] Got '{color}' from {handle_id}")
                reply = "Hi man"
                print(f"    → Replying: {reply!r}")
                send_imessage(reply, handle_id)

        except Exception as e:
            print(f"[!] Error: {e}")
            time.sleep(POLL_INTERVAL)