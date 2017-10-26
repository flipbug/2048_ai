import random
import game
import sys

# Author:			chrn (original by nneonneo)
# Date:				11.11.2016
# Description:		The logic of the AI to beat the game.

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

THRESHOLD = 8
MIN_THRESHOLD = 2
OPTIMAL_POSITION_WEIGHT = 2
BEST_MERGE_WEIGHT = 2
FUTURE_MERGE_WEIGHT = 2
DIRECTION_WEIGHT = [1, 1, 1, 1]

def find_best_move(board):
    bestmove = -1

	# Build a heuristic agent on your own that is much better than the random agent.
	# Your own agent don't have to beat the game.
    bestmove = find_best_move_rule_agent(board, THRESHOLD)
    if bestmove == -1:
        # Fallback to random agent if no optimal move has been found
        # print('random')
        bestmove = find_best_move_random_agent()
    return bestmove

def find_best_move_random_agent():
    return random.choice([UP, DOWN, LEFT, RIGHT])

def find_best_move_rule_agent(board, threshold=0):
    possible_moves = []

    # 1. Rule
    move, value = find_move_by_highest_merge(board, threshold)
    possible_moves.append((move, value))

    # 2. Rule
    move, value = find_move_by_future_outcome(board, threshold)
    possible_moves.append((move, value))

    # 3. Rule (disabled)
    move, value = find_move_by_optimal_position(board)
    possible_moves.append((-1, value))

    # 4. Rule
    move, value = find_move_by_number_of_merges(board)
    possible_moves.append((move, value))

    # select move with highest value
    move = select_best_possible_move(possible_moves, board)

    if move == -1:
        if threshold > MIN_THRESHOLD:
            # try again with lower threshold
            move = find_best_move_rule_agent(board, threshold/2)
        else:
            # 3. Rule as fallback
            move, value = find_move_by_optimal_position(board)
            # print('Rule 3 fallback')

    return move

def find_move_by_highest_merge(board, threshold=8):
    """
    Search for possible merges and use the move with the biggest number and 
    larger than the threshold.
    """
    move = -1
    value = -1
    possible_merges = get_possible_merges(board)

    if possible_merges and possible_merges[0]['number'] > threshold:
        move = possible_merges[0]['move']
        value = possible_merges[0]['number']

    # weight adjustment
    value = value * BEST_MERGE_WEIGHT

    return move, value

def find_move_by_future_outcome(board, threshold=8):
    """
    Move tiles to get a good merge (larger than the threshold) in the next round
    """
    move = -1
    value = -1
    next_moves = {UP: 0, DOWN: 0, LEFT: 0, RIGHT: 0}
    for m in next_moves.keys():
        new_board = execute_move(m, board)
        new_possible_moves = get_possible_merges(new_board)
        next_moves[m] = new_possible_moves[0]['number'] if new_possible_moves else -1

    possible_move, value = find_best_move_in_dict(next_moves)
    if value > threshold:
        move = possible_move

    # weight adjustment
    value = value * FUTURE_MERGE_WEIGHT

    return move, value

def find_move_by_number_of_merges(board):
    """
    Use direction with the most merges
    """
    move = -1
    value = -1
    possible_merges = get_possible_merges(board)
    amount_of_merges = {UP: 0, DOWN: 0, LEFT: 0, RIGHT: 0}
    for merge in possible_merges:
        amount_of_merges[merge['move']] += 1

    # search direction with th most merges
    possible_move, value = find_best_move_in_dict(amount_of_merges)
    if value > 2:
        move = possible_move

    # weight adjustment
    value = value^2

    return move, value

def find_move_by_optimal_position(board):
    """
    Maximize the top and left column to keep higher tiles together and out of the middle
    """
    move = -1
    value = -1
    moves = [(),()]

    # first check top column
    top_sum = sum(board[0])
    for row in board:
        row_sum = sum(row)
        if top_sum < row_sum:
            moves[0] = (UP, row_sum)

    # second check left column
    left_sum = sum([row[0] for row in board])

    for index,_ in enumerate(board):
        col_sum = sum([row[index] for row in board])
        if left_sum < col_sum:
            moves[1] = (LEFT, col_sum)

    # check if a move is possible
    for m in moves:
        if len(m) == 2 and not board_equals(board, execute_move(m[0], board)):
            move = m[0]
            value = m[1]

    # small cheat
    value = OPTIMAL_POSITION_WEIGHT

    return move, value

def select_best_possible_move(moves, board):
    """
    Select the best possible move by value. Additionaly check if the board gets stuck and 
    choose another move to prevent this.
    """
    move = -1
    max_value = 0
    index = 0
    for idx, item in enumerate(moves):
        # set a weight for directions 
        # value = item[1] * DIRECTION_WEIGHT[item[0]]
        value = item[1]
        if value > max_value and item[0] >= 0:
            max_value = value
            move = item[0]
            index = idx

    #print(moves)

    # check if the move is possible, otherwise discard it and try again
    if move > -1 and board_equals(board, execute_move(move, board)):
        del moves[index]
        move = select_best_possible_move(moves, board)

    #print('Used Rule: {}'.format(index + 1))

    return move

def get_possible_merges(board, threshold=0):
    """
    Get all possible merges on the current board and sort them descending by
    value
    """
    moves = []
    for y, row in enumerate(board):
        for x, number in enumerate(row):
            move = -1
            if number > 0 and number > threshold:
                # check if there are any possible merges with current number
                if x > 1 and has_horizontal_merge(x, y, number, board, True): # board[y][x - 1] == number:
                    move = LEFT
                elif x < len(board[y]) - 1 and has_horizontal_merge(x, y, number, board): # board[y][x + 1] == number:
                    move = RIGHT
                elif y > 1 and has_vertical_merge(x, y, number, board, True): # board[y - 1][x] == number:
                    move = UP
                elif y < len(board) - 1 and has_vertical_merge(x, y, number, board): # board[y + 1][x] == number:
                    move = DOWN

                if move > 0:
                    # make sure the preferred directions come at first
                    number *= DIRECTION_WEIGHT[move]
                    moves.append({'number':number, 'move': move})

    return  sorted(moves, key=lambda x: x['number'], reverse=True)

def has_horizontal_merge(x, y, number, board, backwards=False):
    if not backwards:
        start = x + 1
        step = 1
        end = len(board[y])
    else:
        start = x - 1
        step = -1
        end = 0

    for i in range(start, end, step):
        n = board[y][i]
        if n > 0 and n != number:
            return False
        elif n == number:
            return True

    return False

def has_vertical_merge(x, y, number, board, backwards=False):
    if not backwards:
        start = y + 1
        step = 1
        end = len(board)
    else:
        start = y - 1
        step = -1
        end = 0

    for i in range(start, end, step):
        n = board[i][x]
        if n > 0 and n != number:
            return False
        elif n == number:
            return True

    return False

def find_best_move_in_dict(move_dict):
    move = -1
    max_value = 0
    for key, value in move_dict.items():
        if value > max_value:
            max_value = value
            move = key
    return move, max_value

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
