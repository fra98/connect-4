# # Connect 4
from __future__ import annotations
from collections import Counter
import numpy as np

NUM_COLUMNS = 7
COLUMN_HEIGHT = 6
FOUR = 4

# Board can be initialized with `board = np.zeros((NUM_COLUMNS, COLUMN_HEIGHT), dtype=np.byte)`
# Notez Bien: Connect 4 "columns" are actually NumPy "rows"


def valid_moves(board):
    """Returns columns where a disc may be played"""
    return [n for n in range(NUM_COLUMNS) if board[n, COLUMN_HEIGHT - 1] == 0]


def play(board, column, player):
    """Updates `board` as `player` drops a disc in `column`"""
    (index,) = next((i for i, v in np.ndenumerate(board[column]) if v == 0))
    board[column, index] = player


def take_back(board, column):
    """Updates `board` removing top disc from `column`"""
    (index,) = [i for i, v in np.ndenumerate(board[column]) if v != 0][-1]
    board[column, index] = 0


def four_in_a_row(board, player):
    """Checks if `player` has a 4-piece line"""
    return (
        any(
            all(board[c, r] == player)
            for c in range(NUM_COLUMNS)
            for r in (list(range(n, n + FOUR)) for n in range(COLUMN_HEIGHT - FOUR + 1))
        )
        or any(
            all(board[c, r] == player)
            for r in range(COLUMN_HEIGHT)
            for c in (list(range(n, n + FOUR)) for n in range(NUM_COLUMNS - FOUR + 1))
        )
        or any(
            np.all(board[diag] == player)
            for diag in (
                (range(ro, ro + FOUR), range(co, co + FOUR))
                for ro in range(0, NUM_COLUMNS - FOUR + 1)
                for co in range(0, COLUMN_HEIGHT - FOUR + 1)
            )
        )
        or any(
            np.all(board[diag] == player)
            for diag in (
                (range(ro, ro + FOUR), range(co + FOUR - 1, co - 1, -1))
                for ro in range(0, NUM_COLUMNS - FOUR + 1)
                for co in range(0, COLUMN_HEIGHT - FOUR + 1)
            )
        )
    )


def _mc(board, player):
    p = -player
    while valid_moves(board):
        p = -p
        c = np.random.choice(valid_moves(board))
        play(board, c, p)
        if four_in_a_row(board, p):
            return p
    return 0


def montecarlo(board, player):
    montecarlo_samples = 100
    cnt = Counter(_mc(np.copy(board), player) for _ in range(montecarlo_samples))
    return (cnt[1] - cnt[-1]) / montecarlo_samples


def eval_board(board, player):
    if four_in_a_row(board, 1):
        # Alice won
        return 1
    elif four_in_a_row(board, -1):
        # Bob won
        return -1
    else:
        # Not terminal, let's simulate...
        return montecarlo(board, player)


PLAYERS = {1: "A", -1: "B"}
MAX_ROUNDS = NUM_COLUMNS * COLUMN_HEIGHT
NUM_ITERATIONS = 1000


def initialize_board():
    return np.zeros((NUM_COLUMNS, COLUMN_HEIGHT), dtype=np.byte)


def display(board):
    for j in reversed(range(COLUMN_HEIGHT)):
        for i in range(NUM_COLUMNS):
            cell = board[i][j]
            if cell == 1:
                print(PLAYERS[1], end=" ")
            elif cell == -1:
                print(PLAYERS[-1], end=" ")
            else:
                print("-", end=" ")
        print()


def round_number(board):
    return np.count_nonzero(board)


def terminal_state(board):
    if round_number(board) == MAX_ROUNDS:    # draw
        return 0
    if four_in_a_row(board, 1):
        return 1
    elif four_in_a_row(board, -1):
        return -1
    else:
        return None


class Node:
    def __init__(self, board: np.ndarray, player: int, parent: Node = None, move: int = None):
        self.board = np.copy(board)
        self.player = player    # player who did the previous move
        self.parent = parent
        self.move = move        # previous move that brought in this state
        self.num_visits = 0
        self.num_wins = 0
        self.childs = []
        self.next_moves = valid_moves(board)

    def selection(self):
        def UCB1(node):
            c = np.sqrt(2)
            exploitation = node.num_wins / node.num_visits
            exploration = c * np.sqrt(np.log(node.parent.num_visits) / node.num_visits)
            return exploitation + exploration
        
        return max(self.childs, key=UCB1)

    def expand(self, move):
        player = -self.player     
        new_board = np.copy(self.board)
        play(new_board, move, player)
        self.next_moves.remove(move)
        child = Node(new_board, player, self, move)
        self.childs.append(child)
        return child

    def simulate(self):
        p = -self.player
        board = np.copy(self.board)
        while valid_moves(board):
            move = np.random.choice(valid_moves(board))
            play(board, move, p)
            if four_in_a_row(board, p):
                return p
            p = -p
        
        return 0  # DRAW

    def backpropagate(self, winner):
        node = self
        while node is not None:
            if winner == 0:   # draw
                node.num_wins += 0.5
            elif winner == node.player:
                node.num_wins += 1      
            node.num_visits += 1
            node = node.parent


def MCTS(board: np.ndarray, player: int, num_iterations: int = NUM_ITERATIONS):
    # the player in the node is the one who did the previous move
    root = Node(board, -player, parent=None, move=None)

    for _ in range(num_iterations):
        node = root

        # SELECTION (tree traversal)
        while len(node.childs) != 0 and len(node.next_moves) == 0:  # until terminal or not fully expanded node
            node = node.selection()

        # EXPANSION        
        if len(node.next_moves) > 0:
            move = np.random.choice(node.next_moves)
            node = node.expand(move)

        # SIMULATION (ROLLOUT)
        winner = terminal_state(node.board)
        if winner is None:
            winner = node.simulate()

        # BACKPROPAGATION
        node.backpropagate(winner)
            
    # Return most promising move from root (highest score)
    best_node = max(root.childs, key=lambda x: x.num_wins/x.num_visits)
    return best_node.move


# MINIMAX
MAX_DEPTH = 3
MC_ITERATIONS = 20
SEARCH_ORDER = [3, 2, 4, 1, 5, 0, 6]


def can_win_next_move(board, player, moves=None, round_num=None):
    if moves is None:
        moves = valid_moves(board)
    
    if round_num is None:
        round_num = round_number(board)

    for m in moves:
        play(board, m, player)
        score = None
        if four_in_a_row(board, player):
            score = (MAX_ROUNDS - (round_num - 1)) // 2
        take_back(board, m)
        if score:
            return score, m

    return None, None


def mc_simulation(board: np.ndarray, player: int):
    best_score = -MAX_ROUNDS
    best_move = None
    
    for _ in range(MC_ITERATIONS):
        move = np.random.choice(valid_moves(board))
        
        tmp_board = np.copy(board)
        tmp_player = player
        tmp_move = move
        while True:
            play(tmp_board, tmp_move, tmp_player)

            # Terminal conditions
            if round_number(tmp_board) == MAX_ROUNDS:
                score = 0
                break
            if four_in_a_row(tmp_board, tmp_player):
                if tmp_player == player:
                    score = (MAX_ROUNDS - (round_number(tmp_board) - 1)) // 2
                else:
                    score = -((MAX_ROUNDS - (round_number(tmp_board) - 1)) // 2)
                break

            tmp_move = np.random.choice(valid_moves(tmp_board))
            tmp_player = -tmp_player

        if score > best_score:
            best_score = score
            best_move = move
        
    return best_score, best_move


def minimax(board: np.ndarray, player: int, depth: int, alpha: int, beta: int, max_depth: int = MAX_DEPTH):
    # CHECK FOR TERMINAL CONDITIONS (DRAW OR WIN WITHIN NEXT MOVE)
    round_num = round_number(board)

    # Case draw
    if round_num == MAX_ROUNDS:
        return 0, None

    moves = valid_moves(board)

    # Check if current player can win with the next move
    score, m = can_win_next_move(board, player, moves, round_num)
    if score:
        return score, m

    # NON TERMINAL
    
    # Cap beta to maximum possible score (already considering next round -> + 1)
    max_score = (MAX_ROUNDS - (round_num + 1)) // 2
    if beta > max_score:
        beta = max_score
    
    # Prune
    if alpha >= beta:
        return beta, None

    # Montecarlo simulation if DEPTH too high
    if depth > max_depth:
        return mc_simulation(board, player)

    # MinMax exploration if DEPTH is low enough
    # start searching from middle columns because there is more probability of higher score, therefore more pruning
    best_move = None
    for m in SEARCH_ORDER:
        if m in moves:
            play(board, m, player)
            score, _ = minimax(board, -player, depth+1, -beta, -alpha)
            score = -score
            take_back(board, m)

            if score >= beta:
                return score, m

            if score > alpha:
                alpha = score
                best_move = m

    return alpha, best_move


def choose_move(board: np.ndarray, player: int, v):
    # FIRST/SECOND MOVE -> always play central
    if not board.any() or round_number(board) == 1:
        play(board, 3, player)
        return 3

    # THIRD MOVE -> always play in one of the 3 cells in the center
    if round_number(board) == 2:
        move = np.random.choice([2, 3, 4])
        play(board, move, player)
        return move

    # MCTS
    if v == 1:
        move = MCTS(board, player, NUM_ITERATIONS)
    else:
        _, move = minimax(board, player, depth=1, alpha=-1000, beta=1000, max_depth=MAX_DEPTH)

    if move is not None:
        play(board, move, player)

    return move


def main_AI_vs_AI():
    board = initialize_board()
    player = 1

    while True:
        if player == 1:
            move = choose_move(board, player, v=1)
        else:
            move = choose_move(board, player, v=2)

        if move is None:
            print("DRAW")
            return

        print(f"{PLAYERS[player]} TURN -> {move + 1}")
        display(board)

        if four_in_a_row(board, player):
            print(f"\nPlayer {PLAYERS[player]} WON")
            return

        print()
        player = -player


if __name__ == "__main__":
    main_AI_vs_AI()