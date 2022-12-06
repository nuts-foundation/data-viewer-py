#!/usr/bin/env python3
"""A prototype ncurses CLI debugging tool for the nuts network in python (to be replaced with a go version later)"""

# For maximum portability the packages used here are all part of the python stdlib (as of 3.11).
# Please keep it that way for any future changes to this project, as distributing python
# applications which use third-party modules is more trouble than we want for this tool.
import argparse
import curses
import json
import os
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
    # Empty prevs are not displayed at all
    if not prevs:
        return ''

    # Loop over the referenced transactions, building formatted text
    formatted = []
    for navigation_index, ref in enumerate(prevs, start=1):
        transaction = API.transaction(ref)
        content_type = transaction['cty']
        global_index = transaction['index']
        formatted.append(f'   🔗 [{navigation_index}] {content_type} #{global_index}')

    # Return the formatted prevs list, which will be displayed to the user
    return '\n' + '\n'.join(formatted)


def top_window(stdscr):
    # Use the default colors of the terminal in addstr()
    curses.use_default_colors()
    curses.init_pair(1, -1, -1)

    # Prevent WERR exceptions from ncurses when the 
    # content exceeds the size of the terminal
    stdscr.scrollok(True)

    # Clear the screen
    stdscr.clear()
    stdscr.refresh()

    # Get all of the transactions available on the nuts node
    cursor = 0
    history = []

    while True:
        # Clear the screen
        stdscr.clear()

        # Determine the terminal dimensions, which can change at any moment
        height, width = stdscr.getmaxyx()

        # Ensure at least 80 character terminals are in use at all times
        if width < 80:
            stdscr.addstr('A terminal width of at least 80 characters is required. \n')
            stdscr.addstr('Resize your terminal or press crtl-c to exit.')
            stdscr.getkey()
            continue

        # Get the transaction data at the cursor
        ref = API.ref(cursor)
        transaction = API.transaction(ref)
        
        # Print the cursor status
        stdscr.addstr(f'Trx #{cursor} ({API.transaction_count()} total)\n')

        # Print the ref field on the right
        ref_message = f'''ref {transaction.get('ref')}'''
        stdscr.addstr(0, width-len(ref_message), ref_message)

        # Print the content type (cty) field on the right
        if 'cty' in transaction:
            cty_emoji = content_type_emoji(transaction.get('cty'))
            cty_message = f'''{cty_emoji} {transaction.get('cty')}'''
            stdscr.addstr(1, width-len(cty_message)-1, cty_message)

        # Compute the displayed values for the transaction fields
        dump_fields = {}

        # Iterate over the data fields of the transaction. I'm purposely avoiding
        # the term "key" here as the transaction refers to crypto keys and that may
        # prove confusing.
        for field, value in transaction.items():
            # The prevs have a special formatting
            if field == 'prevs':
                dump_fields[field] = _format_prevs(value)
                continue

            # Some fields are dislayed elsewhere in the application and are not dumped here
            if field in ['ref', 'index', 'cty', 'privs']:
                continue

            dump_fields[field] = json.dumps(value, indent=2)

        for field, value in dump_fields.items():
            stdscr.addstr(f'''{emoji(transaction,field)}{field}: {value}\n''')
        
        if prevs := transaction.get('prevs'):
            stdscr.addstr(f'''{emoji(transaction,'prevs')}: {prevs}\n''')

        payload = API.payload(transaction['ref'])
        stdscr.addstr(f'''payload: {payload}''')

        # Print the help line
        help_items = ['q: quit', 'left/right/home(g)/end(G): browse', '1-9: navigate prevs', 'r: reload']
        if history:
            help_items.append(f'b: back to #{history[-1]}')
        stdscr.addstr(height-1, 0, ' | '.join(help_items))

        # Wait for and read an input key
        keyboard_input = stdscr.getkey()

        # Left arrow key moves cursor back in the transaction list
        if keyboard_input == 'KEY_LEFT':
            last_cursor = cursor
            cursor = max(0, cursor-1)

        # Right arrow key moves cursor forward in the transaction list
        elif keyboard_input == 'KEY_RIGHT':
            last_cursor = cursor
            cursor = min(API.transaction_count()-1, cursor+1)

        # Home goes to the 0th transaction in the list
        elif keyboard_input == 'KEY_HOME' or keyboard_input == 'g':
            cursor = 0

        # End goes to the last transaction in the list
        elif keyboard_input == 'KEY_END' or keyboard_input == 'G':
            cursor = API.transaction_count() - 1

        # Q/q quits the application
        elif keyboard_input == 'q' or keyboard_input == 'Q':
            return

        # r clear the cache, reloading data from the API
        elif keyboard_input == 'r':
            API.cache_clear()

        # 1-9 navigates to the Nth specified prev transaction (if it exists)
        elif keyboard_input in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            prev_index = int(keyboard_input) - 1
            if 'prevs' in transaction and len(transaction['prevs']) > prev_index:
                history.append(cursor)
                linked_transaction = API.transaction(transaction['prevs'][prev_index])
                cursor = linked_transaction['index']

        # b navigates back to the previously shown transaction (if possible)
        elif keyboard_input == 'b':
            if history:
                cursor = history.pop()

        # B clears the navigation history
        elif keyboard_input == 'B':
            history = []
        
        # ? shows the help screen
        elif keyboard_input == '?':
            help_screen(stdscr)


def emoji(transaction: dict, field: str) -> str:
    # By default show no emoji
    return '   '


def help_screen(stdscr):
    # Define the tooltips for the application
    tips = {
        'q': 'quit application',
        '← →': 'select transaction',
        'home': 'first transaction',
        'end': 'last transaction',
        '1-9': 'navigate prevs',
        'b': 'back in history',
        'B': 'clear history',
        'r': 'reload data',
        '?': 'show help screen',
        'del': 'close window',
    }

    # Show the tooltips for the application
    stdscr.clear()
    for buttons, tip in tips.items():
         stdscr.addstr(f'{buttons}\t\t{tip}\n')

    # wait for the delete or backspace key to be pressed
    keyboard_input = None
    while keyboard_input not in ['KEY_DC', 'KEY_BACKSPACE', 127]:
        # Wait for and read an input key
        keyboard_input = stdscr.getkey()

        # Allow the application to be stopped from the help menu
        # to prevent confusion
        if keyboard_input in ['q', 'Q']:
            sys.exit()

def content_type_emoji(content_type: str) -> str:
    if content_type == 'application/vc+json':
        return '🔑'

    if content_type == 'application/did+json':
        return '🆔'

    if content_type == 'application/ld+json;type=revocation':
        return ''
    
    return '❓'
        
def main():
    # Parse the command line arguments
    args = parse_args()

    # Update the API base URL from CLI arguments
    API.base_url = args.base_url

    # Start the main app loop
    curses.wrapper(top_window)


if __name__ == '__main__':
    sys.exit(main())
