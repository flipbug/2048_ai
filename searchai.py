import random
import game
import sys
from multiprocessing import Pool
import itertools

from util import UP, DOWN, LEFT, RIGHT

# Author:      chrn (original by nneonneo)
# Date:        11.11.2016
# Copyright:   Algorithm from https://github.com/nneonneo/2048-ai
# Description: The logic to beat the game. Based on expectimax algorithm.

MAX_DEPTH = 3
"""
TILE_WEIGHTS = [[8, 7, 6, 5],
                [1, 1, 1, 4],
                [-1, -1, 1, 3],
                [-8, -1, 1, 2]]
"""
TILE_WEIGHTS = [[10, 8, 4, 2],
                [8, 1, 1, 1],
                [4, 1, 1, -1],
                [2, 1, -1, -1]]

MOVES = [UP,DOWN,LEFT,RIGHT]


def find_best_move(board):
    """
    find the best move for the next turn.
    It will split the workload in 4 process for each move.
    """
    bestmove = -1
    pool = Pool()
    
    result = pool.map(func_star, zip(MOVES, itertools.repeat(board)))
    bestmove = result.index(max(result))
    
    #for m in move_args:
    #    print(m)
    #    print(result[m])
    pool.close()
    pool.join()
    
    return bestmove
    
def score_toplevel_move(move, board):
    """
    Entry Point to score the first move.
    """
	# Implement the Expectimax Algorithm.
	# 1.) Start the recursion until it reach a certain depth
	# 2.) When you don't reach the last depth, get all possible board states and
	#	  calculate their scores dependence of the probability this will occur. (recursively)
	# 3.) When you reach the leaf calculate the board score with your heuristic.
    return score_max_node(move, board, 0)

def score_chance_node(chance, board, depth):
    """
    Chance node
    """
    score = 0
    for m in MOVES:
        score += score_max_node(m, board, depth)
    return score * chance

def score_max_node(move, board, depth):
    """
    Max node
    """
    newboard = execute_move(move, board)
    depth += 1
    score = 0

    if board_equals(board,newboard):
        return 0

    if depth >= MAX_DEPTH:
        return calculate_score(newboard)

    for i, row in enumerate(newboard):
        for j, number in enumerate(row):
            if number == 0:
                # create chance nodes
                newboard[i][j] = 2
                chance_one = score_chance_node(0.9, newboard, depth)
                newboard[i][j] = 4
                chance_two = score_chance_node(0.1, newboard, depth)
                
                # maximize score
                score = max(score, chance_one, chance_two)

    return score

def calculate_score(board):
    """
    Calculate the score of the board based on value of tiles and number of empty tiles
    """
    tile_score = 0
    empty_tiles = 0
    for i, row in enumerate(board):
        for j, value in enumerate(row):
            if value == 0:
                empty_tiles += 1
            else:
                tile_score += value * TILE_WEIGHTS[i][j]

    return tile_score * empty_tiles

def execute_move(move, board):
    """
    move and return the grid without a new random tile 
	It won't affect the state of the game in the browser.
    """

    if move == UP:
        return game.merge_up(board)
    elif move == DOWN:
        return game.merge_down(board)
    elif move == LEFT:
        return game.merge_left(board)
    elif move == RIGHT:
        return game.merge_right(board)
    else:
        sys.exit("No valid move")
        
def board_equals(board, newboard):
    """
    Check if two boards are equal
    """
    return  (newboard == board).all()  
    
def func_star(a_b):
    """
	Helper Method to split the programm in more processes.
	Needed to handle more than one parameter.
    """
    return score_toplevel_move (*a_b)