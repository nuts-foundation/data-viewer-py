# data-viewer-py
A prototype ncurses CLI debugging tool for the nuts network in python (to be replaced with a go version later)

## Bugs & Limitations

There are known bugs and limitations to this software, and it is truly a proof of concept/prototype/sandbox for ideas. Consider yourself warned.

### _curses.error: addwstr() returned ERR

When you see this message it means your console was too small to render the desired data. Lower your font, resize your window, or otherwise get creative.
