import os
import random
import logging
import lmdb
import struct
import zlib
import numpy as np
from pathlib import Path
from typing import Any, Optional

from snowdrop_tangled_game_engine import Game, GameAgentBase

from snowdrop_tangled_special_agents.agents.mcts_utils.converters import (convert_to_az_board, convert_from_az_board,
                                        convert_erik_game_instance_to_tangled_game_state_instance,
                                        convert_tangled_move_to_erik_move)
from snowdrop_tangled_special_agents.agents.mcts_utils.mcts_tangled import TangledMove
from snowdrop_tangled_special_agents.agents.mcts_utils.infrastructure import hash_state_action, \
    reverse_hashing_state_action


def decode_action(action_int: int) -> tuple[int, int]:
    return (action_int // 3, (action_int % 3) + 1)


def load_policy_optimized(filepath: str) -> tuple[np.ndarray, int]:
    """
    Load policy from a compressed binary file.

    Returns:
        (policy_array, num_edges) where policy_array[state] is the action
    """
    with open(filepath, 'rb') as f:
        num_edges, num_states = struct.unpack('<II', f.read(8))
        compressed = f.read()

    data = zlib.decompress(compressed)
    policy = np.frombuffer(data, dtype=np.int8).copy()

    file_size = os.path.getsize(filepath)

    print(f"Loaded policy: {num_states:,} states, {num_edges} edges")
    print(f"  File size: {file_size / 1024**2:.1f} MB")
    print(f"  In memory: {policy.nbytes / 1024**2:.1f} MB")

    return policy, num_edges


def edges_to_state(edges: list[int]) -> int:
    result = 0
    for val in edges:
        result = (result << 2) | val
    return result


class MinimaxAgent(GameAgentBase):
    """
    This is an example of a Tangled agent. It makes random moves.

    Use this template to build your own agents. Here are the basic steps:

    1. Import the GameAgentBase class from snowdrop_tangled_game_engine.
        This will be the base class for your agent.
    2. Import the Game class from snowdrop_tangled_game_engine.
        This will be the state of the game that your agent will interact with. See the class for more details,
        but generally you'll have access to the full state of the game (the vertices and edges and their states)
        and some helpful methods for interacting with the game (get_legal_moves, etc.)
    3. Create a new class that inherits from GameAgentBase and implement the make_move method.
        The make_move method should take a Game object as an argument and return a tuple (move type,
        move index, move state).
        move_type is Game.MoveType IntEnum, and has values of NONE, EDGE, or QUIT.
        move_index is the index of the edge to change the state of, where the edges (i, j) i < j are in lexical order.
        move_state is the state to change the edge to.
                Edge.State.ZERO -- zero coupling / grey edge
                Edge.State.FM   -- FM coupling / green edge
                Edge.State.AFM  -- AFM coupling / purple edge
                (Edge.State.NONE is the initial state)

        The move should be returned as a tuple of these three values as integers.
        e.g. (Game.MoveType.EDGE.value, 3, Edge.State.FM.value) is a move that turns edge #3 green.
    """

    def __init__(self, player_id: str = None, **kwargs):
        super().__init__(player_id)
        self.rollout_adjudicator = 'lookup_table'
        # this loads policy into RAM
        self.policy, _ = load_policy_optimized(str(os.path.join(kwargs['policy_dir_path'], kwargs['policy_file_name'])))

    def make_move(self, game: Game) -> tuple[int, int, int] | None:
        """Make a move in the game.
        game: Game: The game instance

        Returns a tuple of integers (move_type, move_index, move_state) or None if there are no legal moves.
        """

        initial_tangled_game_state = convert_erik_game_instance_to_tangled_game_state_instance(game, rollout_adjudicator=self.rollout_adjudicator)

        tangled_move = self.minimax_agent(initial_tangled_game_state)

        legal_moves = game.get_legal_moves(self.id)

        if not legal_moves or (len(legal_moves) == 1 and legal_moves[0][0] == Game.MoveType.QUIT.value):
            logging.info("No legal moves available")
            return None

        while True:
            erik_move = convert_tangled_move_to_erik_move(len(game.vertices), tangled_move)
            if erik_move not in legal_moves:
                print('something went wrong, your agent picked an illegal move!')
            if erik_move[0] != Game.MoveType.QUIT.value:
                break

        return erik_move

    # def edges_to_state(self, edges: list[int]) -> int:
    #     """
    #     Convert a list of edge labels to a state integer.
    #
    #     Args:
    #         edges: List of edge labels (each in {0, 1, 2, 3})
    #
    #     Returns:
    #         Encoded state integer
    #     """
    #     result = 0
    #     for val in edges:
    #         result = (result << 2) | val
    #     return result

    def minimax_agent(self, initial_state):
        # eats initial_state (a TangledGameState instance) and returns a TangledMove instance

        legal_actions = initial_state.get_legal_actions()

        action = self.policy[edges_to_state(initial_state.edge_state)]

        if action != -1:
            edge_idx, label = decode_action(action)
        else:
            print('something is not good here')

        final_state_each = None
        for each in legal_actions:
            initial_state_each, final_state_each, action_each = reverse_hashing_state_action(each.hash_string)
            if final_state_each[initial_state.number_of_vertices+edge_idx] == label:
                return TangledMove(hash_state_action(initial_state.board, final_state_each, action_each), initial_state.next_to_move)
        if final_state_each is None:
            print('something went wrong, your agent picked an illegal move!')

        return None
