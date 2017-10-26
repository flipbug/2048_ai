#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author:      chrn (original by nneonneo)
# Date:        11.11.2016
# Copyright:   https://github.com/nneonneo/2048-ai
# Description: Helps the user achieve a high score in a real game of 2048 by using a move searcher.
#              This Script initialize the AI and controls the game flow.


from __future__ import print_function

import time
import os
import searchai    #for task 3
import heuristicai #for task 2

from statistics import median

def print_board(m):
    for row in m:
        for c in row:
            print('%8d' % c, end=' ')
        print()

def _to_val(c):
    if c == 0: return 0
    return c

def to_val(m):
    return [[_to_val(c) for c in row] for row in m]

def _to_score(c):
    if c <= 1:
        return 0
    return (c-1) * (2**c)

def to_score(m):
    return [[_to_score(c) for c in row] for row in m]

def find_best_move(board):
    #return heuristicai.find_best_move(board)
    return searchai.find_best_move(board)

def movename(move):
    return ['up', 'down', 'left', 'right'][move]

def start_game(gamectrl, iterations=1, verbose=0):
    highest_score = 0
    highest_maxval = 0
    scores = []
    for i in range(iterations):
        gamectrl.restart_game()
        score, maxval = play_game(gamectrl, verbose)
        highest_maxval = max(highest_maxval, maxval)
        highest_score = max(highest_score, score)
        scores.append(score)

    average = sum(scores) / iterations
    print("Games: %d, highest score: %d, median: %d, average: %d, highest tile: %d" % (iterations, highest_score, median(scores), average, highest_maxval))

def play_game(gamectrl, verbose):
    moveno = 0
    start = time.time()
    while 1:
        state = gamectrl.get_status()
        if state == 'ended':
            break
        elif state == 'won':
            time.sleep(0.75)
            gamectrl.continue_game()

        moveno += 1
        board = gamectrl.get_board()
        move = find_best_move(board)
        if move < 0:
            break
        if verbose >= 2:
            print("%010.6f: Score %d, Move %d: %s" % (time.time() - start, gamectrl.get_score(), moveno, movename(move)))
        gamectrl.execute_move(move)

    score = gamectrl.get_score()
    board = gamectrl.get_board()
    maxval = max(max(row) for row in to_val(board))
    if verbose >= 1:
        print("Game over. Final score %d; highest tile %d." % (score, maxval))
    
    return score, maxval

def parse_args(argv):
    import argparse

    parser = argparse.ArgumentParser(description="Use the AI to play 2048 via browser control")
    parser.add_argument('-p', '--port', help="Port number to control on (default: 32000 for Firefox, 9222 for Chrome)", type=int)
    parser.add_argument('-b', '--browser', help="Browser you're using. Only Firefox with the Remote Control extension, and Chrome with remote debugging, are supported right now.", default='firefox', choices=('firefox', 'chrome'))
    parser.add_argument('-k', '--ctrlmode', help="Control mode to use. If the browser control doesn't seem to work, try changing this.", default='hybrid', choices=('keyboard', 'fast', 'hybrid'))
    parser.add_argument('-n', '--iterations', help="Number of games to play in a row.", default='1', type=int)
    parser.add_argument('-v', '--verbose', help="Verbose Output. Show every move.", action='count')

    return parser.parse_args(argv)

def main(argv):
    args = parse_args(argv)

    verbose = args.verbose

    if args.browser == 'firefox':
        from ffctrl import FirefoxRemoteControl
        if args.port is None:
            args.port = 32000
        ctrl = FirefoxRemoteControl(args.port)
    elif args.browser == 'chrome':
        from chromectrl import ChromeDebuggerControl
        if args.port is None:
            args.port = 9222
        ctrl = ChromeDebuggerControl(args.port)

    if args.ctrlmode == 'keyboard':
        from gamectrl import Keyboard2048Control
        gamectrl = Keyboard2048Control(ctrl)
    elif args.ctrlmode == 'fast':
        from gamectrl import Fast2048Control
        gamectrl = Fast2048Control(ctrl)
    elif args.ctrlmode == 'hybrid':
        from gamectrl import Hybrid2048Control
        gamectrl = Hybrid2048Control(ctrl)

    if gamectrl.get_status() == 'ended':
        gamectrl.restart_game()

    start_game(gamectrl, args.iterations, args.verbose)

if __name__ == '__main__':
    import sys
    exit(main(sys.argv[1:]))
