# data-viewer-py
A prototype ncurses CLI debugging tool for the nuts network in python (to be replaced with a go version later)

## Bugs & Limitations

There are known bugs and limitations to this software, and it is truly a proof of concept/prototype/sandbox for ideas. Consider yourself warned.

### _curses.error: addwstr() returned ERR

When you see this message it means your console was too small to render the desired data. Lower your font, resize your window, or otherwise get creative.

### Transaction #X vs lc (lamport clock)

The transaction number at the top of the interface is the index of the transaction in the total list of available transactions. As the DAG grows this differs from the lambort clock (lc) number shown in the transaction itself. This is either a bug or simply a very confusing matter and needs to be investigated.
