
# define default directions
UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3


def get_possible_merges(board, threshold=0, direction_weight=[1,1,1,1]):
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
                    number *= direction_weight[move]
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