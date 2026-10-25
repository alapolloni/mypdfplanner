#!/bin/zsh
./planner.py 
./pdfbook2.py --short-edge time_block_pages.pdf
open ./time_block_pages-book.pdf
