# data-viewer-py
A prototype ncurses CLI debugging tool for the nuts network in python (to be replaced with a go version later)

![image](https://user-images.githubusercontent.com/773275/204584571-59614c62-3a5a-4c0b-a01d-6979c69d34e2.png)

## Bugs & Limitations

There are known bugs and limitations to this software, and it is truly a proof of concept/prototype/sandbox for ideas. Consider yourself warned, and treat this as unsupported software.

### _curses.error: addwstr() returned ERR -- (Possibly fixed?)

This exception along with visual issues may occur if your console is too small, or the data in a transaction is too large. There are no plans to fix this issue in this prototype.

### Transaction #X vs lc (lamport clock)

The transaction number at the top of the interface is the index of the transaction in the total list of available transactions. As the DAG grows this differs from the lamport clock (lc) number shown in the transaction itself. There are no plans to fix this issue in this prototype.
