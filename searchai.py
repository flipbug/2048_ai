import random
import game
import sys
import math
from multiprocessing import Pool
import itertools
import numpy as np
from numba import jit, generated_jit, float32, float64, uint8, uint32

from util import UP, DOWN, LEFT, RIGHT

# Author:      chrn (original by nneonneo)
# Date:        11.11.2016
# Copyright:   Algorithm from https://github.com/nneonneo/2048-ai
# Description: The logic to beat the game. Based on expectimax algorithm.

MAX_DEPTH = 4
MIN_DEPTH = 3
MAX_NEW_BRANCHES = 5


SNAKE = [   [16, 12, 10, 8],
            [1, 2, 4, 6],
            [0.8, 0.6, 0.4, 0.2],
            [0.04, 0.06, 0.08, 0.1]]

# corner
CORNER = [  [10, 6, 4, 2],
            [6, 1, 1, 1],
            [4, 1, 0.5, 0.5],
            [2, 1, 0.5, 0.1]]

TILE_WEIGHTS = SNAKE

TILE_WEIGHTS_FLAT = np.array(TILE_WEIGHTS).flatten()


MOVES = [UP,DOWN,LEFT,RIGHT]


def find_best_move(board):
    """
    find the best move for the next turn.
    It will split the workload in 4 process for each move.
    """
    bestmove = -1
    
    """
    pool = Pool()
    result = pool.map(func_star, zip(MOVES, itertools.repeat(board)))
    bestmove = result.index(max(result))
    pool.close()
    pool.join()
    
    """
    result = list(map(func_star, zip(MOVES, itertools.repeat(board))))
    print(result)
    bestmove = result.index(max(result))

    # prevent the board from getting stuck
    if board_equals(board, execute_move(bestmove, board)):
        print('random')
        bestmove = random.choice([UP, DOWN, LEFT, RIGHT])
    
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
    
    flat_board = board.flatten()
    empty_tiles = count_empty_tiles(flat_board)
    max_depth = calculate_max_depth(empty_tiles, MAX_DEPTH)
    print("Depth: %d" % max_depth)

    return score_max_node(move, board, 0, max_depth)

@jit(float64(float32,uint32[:,:],uint8,uint8))
def score_chance_node(chance, board, depth, max_depth):
    """
    Chance node
    """
    score = 0
    for m in MOVES:
        if m != DOWN:
            score += score_max_node(m, board, depth, max_depth)

    # Use DOWN only if neccessary
    if score == 0:
        score += score_max_node(DOWN, board, depth, max_depth) * 0.5

    return score * chance

@jit(float64(uint8,uint32[:,:],uint8,uint8))
def score_max_node(move, board, depth, max_depth):
    """
    Max node
    """
    newboard = execute_move(move, board)

    if board_equals(board,newboard):
        return 0

    flat_board = newboard.flatten()
    # empty_tiles = count_empty_tiles(flat_board)
    # recalculate max_depth to allow for lowering it for deeper nodes
    # max_depth = calculate_max_depth(empty_tiles, max_depth)
    depth += 1
    score = 0

    if depth >= max_depth:
        return calculate_score(flat_board)

    empty_tiles_pos = []
    for i, row in enumerate(newboard):
        for j, number in enumerate(row):
            if number == 0:
                empty_tiles_pos.append((j,i))

    # limit the number of tiles used for further traversal
    if len(empty_tiles_pos) > MAX_NEW_BRANCHES:
        step = math.floor(len(empty_tiles_pos) / MAX_NEW_BRANCHES)
        empty_tiles_pos = empty_tiles_pos[::step]

    for pos in empty_tiles_pos:
        x = pos[0]
        y = pos[1]

        # create chance nodes
        newboard[y][x] = 2
        chance_one = score_chance_node(0.9, newboard, depth, max_depth)
        chance_two = 0
        if chance_one == 0:
            newboard[y][x] = 4
            chance_two = score_chance_node(0.1, newboard, depth, max_depth)

        # maximize score
        score = max(score, chance_one, 0)

    return score

@jit(nopython=True)
def calculate_score(flat_board):
    """
    Calculate the score of the board based on value of tiles and number of empty tiles
    """
    tile_score = 0
    empty_tiles = 0
    for i, value in enumerate(flat_board):
        if value == 0:
            empty_tiles += 1
        else:
            tile_score += value ** 2 * TILE_WEIGHTS_FLAT[i]

    return tile_score * empty_tiles
    # return tile_score

    
def calculate_penalty(board):
    """
    Calculate penalty based on the difference between the optimal board and the current one
    The optimal board is a snake pattern e.g. [8 7 6 5 1 2 3 4 0 0 0 0 ... ]
    """
    #  TODO fix or remove this function

    # flat_board = list(itertools.chain.from_iterable(board))
    flat_board = board.flatten()
    tile_score = sum(flat_board)

    optimal_board = flat_board.copy()
    optimal_board = sorted(optimal_board, reverse=True)

    for i in range(4, len(optimal_board) - 1, 4):
        # reverse every second "row" to get the snake patterns
        tmp = optimal_board[i]
        optimal_board[i] = optimal_board[i + 3]
        optimal_board[i + 3] = tmp

        tmp = optimal_board[i + 1]
        optimal_board[i + 1] = optimal_board[i + 2]
        optimal_board[i + 2] = tmp

    # Find mismatched numbers and add them as penalty to the score
    empty_tiles = 1
    penalty = 1
    for i, v in enumerate(flat_board):
        if v == 0:
            empty_tiles += 1
        if v != optimal_board[i] and v > 0:
            penalty += v * 2 # math.log(v)

    # print (penalty)
    # print (optimal_board)
    score = tile_score * empty_tiles

    # print('penalty: %d' % (penalty))
    # print('score: %d' % (score))

    # print(optimal_board)

    return penalty

@jit(nopython=True)     
def count_empty_tiles(flat_board):
    empty_tiles = 0
    for value in flat_board:
        if value == 0:
            empty_tiles += 1
    return empty_tiles

@jit(nopython=True)
def calculate_max_depth(empty_tiles, max_depth):
    empty_tiles = max(empty_tiles, 1)
    depth = math.floor(MAX_DEPTH / (empty_tiles/2) + 1)
    return max(depth, MIN_DEPTH) if depth <= max_depth else max_depth

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

@jit(nopython=True)     
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