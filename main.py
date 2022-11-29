#!/usr/bin/env python3
"""A prototype ncurses CLI debugging tool for the nuts network in python (to be replaced with a go version later)"""

# For maximum portability the packages used here are all part of the python stdlib (as of 3.11).
# Please keep it that way for any future changes to this project, as distributing python
# applications which use third-party modules is more trouble than we want for this tool.
import argparse
import curses
import json
import sys
import time

import nuts_node_api as API

# Keep the from imports separate
from textwrap import wrap


def parse_args():
    parser = argparse.ArgumentParser(prog='nuts-data-viewer', description=__doc__)
    parser.add_argument(
        '--base-url',
        default='http://127.0.0.1:1323',
        help='internal nuts API URL'
    )
    return parser.parse_args()


def _format_prevs(prevs: dict) -> dict:
    """Convert the prevs list to display format"""
    # Loop over the referenced transactions, building formatted text
    formatted = []
    for navigation_index, ref in enumerate(prevs, start=1):
        transaction = API.transaction(ref)
        content_type = transaction['cty']
        lamport_clock = transaction['lc'] # See https://martinfowler.com/articles/patterns-of-distributed-systems/lamport-clock.html
        formatted.append(f'#{lamport_clock} ({content_type}) [{navigation_index}]')

    # Return the formatted prevs list, which will be displayed to the user
    return formatted


def top_window(stdscr):
    # Setup curses
    stdscr.clear()
    stdscr.refresh()

    # Get all of the transactions available on the nuts node
    cursor = 0
    history = []

    while True:
        # Clear the screen
        stdscr.clear()

        # Get the transaction data at the cursor
        ref = API.ref(cursor)
        transaction = API.transaction(ref)
        
        # Print the cursor status
        stdscr.addstr(f'Transaction #{cursor} ({API.transaction_count()} total)\n')

        # Compute the displayed values for the transaction fields
        display_trx = {}

        # Iterate over the data fields of the transaction. I'm purposely avoiding
        # the term "key" here as the transaction refers to crypto keys and that may
        # prove confusing.
        for field, value in transaction.items():
            if field == 'prevs':
                value = _format_prevs(value)

            display_trx[field] = value

        for key in display_trx.keys():
            stdscr.addstr(f'''{key}: {json.dumps(display_trx[key], indent=2)}\n''')

        # Print the help line
        height, width = stdscr.getmaxyx()
        stdscr.addstr(height-1, 0, 'q to quit | left/right/home(g)/end(G) to browse | 1-9 to navigate links | b to go back')

        # Get the input key
        key = stdscr.getkey()

        # Left arrow key moves cursor back in the transaction list
        if key == 'KEY_LEFT':
            last_cursor = cursor
            cursor = max(0, cursor-1)

        # Right arrow key moves cursor forward in the transaction list
        if key == 'KEY_RIGHT':
            last_cursor = cursor
            cursor = min(API.transaction_count()-1, cursor+1)

        # Home goes to the 0th transaction in the list
        if key == 'KEY_HOME' or key == 'g':
            cursor = 0

        # End goes to the last transaction in the list
        if key == 'KEY_END' or key == 'G':
            cursor = API.transaction_count() - 1

        # Q/q quits the application
        if key == 'q' or key == 'Q':
            return

        # 1-9 navigates to the Nth specified prev transaction (if it exists)
        if key in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            prev_index = int(key) - 1
            if 'prevs' in transaction and len(transaction['prevs']) > prev_index:
                history.append(cursor)
                linked_transaction = API.transaction(transaction['prevs'][prev_index])
                cursor = linked_transaction['lc']

        # b navigates back to the previously shown transaction (if possible)
        if key == 'b':
            if history:
                cursor = history.pop()


def main():
    # Parse the command line arguments
    args = parse_args()

    # Update the API base URL from CLI arguments
    API.base_url = args.base_url

    # Start the main app loop
    curses.wrapper(top_window)


if __name__ == '__main__':
    sys.exit(main())
