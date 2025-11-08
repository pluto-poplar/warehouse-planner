import random
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from tqdm import tqdm

from dexory.models import WarehouseLayoutModel
from dexory.move_cost import (
    CachingMoveCostCalculator,
)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

WarehouseGraphType = dict[str, set[str]]


class ConnectivityMap(ABC):
    """
    Abstract base class for representing and managing connectivity within a warehouse layout.

    This class defines the interface and core logic for building a graph of warehouse
    locations and allowable movement paths. It requires a `CachingMoveCostCalculator` instance
    to explicitly compute movement costs between nodes.

    Subclasses must implement the `construct_graph` method to define how connectivity
    is derived from the given warehouse layout.
    """

    def __init__(
        self,
        warehouse_layout: WarehouseLayoutModel,
    ) -> None:
        """Initialise.

        Args:
            warehouse_layout: a warehouse layout dataclass.
            move_cost_calculator: a caching cost calculator to efficiently compute cost between nodes.
        """
        self._warehouse_layout = warehouse_layout
        self._graph: WarehouseGraphType = defaultdict(set)  # An empty graph...
        self._move_cost_calculator: CachingMoveCostCalculator | None = None

    @abstractmethod
    def construct_graph(self) -> None:
        """Construct the graph where nodes are warehouse locations and edges are allowable paths."""
        pass

    def compute_graph_size(self) -> tuple[int, int]:
        """Compute the size of the graph."""
        num_nodes = len(self._graph)
        num_edges = 0
        for edges in self._graph.values():
            num_edges += len(edges)
        return num_nodes, num_edges

    def calculate_move_cost(self, node_a: str, node_b: str) -> float:
        """Calculate the move cost between two nodes."""
        if self._move_cost_calculator is None:
            raise ValueError("Cost calculator not defined.")
        if node_b not in self._graph[node_a]:
            raise ValueError(f"Edge does not exist between {node_a} and {node_b}.")
        warehouse_location_a = self._warehouse_layout.get_location(node_a)
        warehouse_location_b = self._warehouse_layout.get_location(node_b)
        return self._move_cost_calculator.get_cost(
            warehouse_location_a, warehouse_location_b
        )

    def add_edge(self, node_a: str, node_b: str, bidirectional: bool = False) -> None:
        """Add an edge to the graph."""
        if node_a == node_b:
            return
        self._graph[node_a].add(node_b)  # set prevents duplicate edges
        if bidirectional:
            self._graph[node_b].add(node_a)

    def get_neighbors(self, node: str) -> list[str]:
        """Return a list of neighboring node names."""
        return list(self._graph.get(node, []))

    def has_node(self, node: str) -> bool:
        """Check if the node exists in the graph."""
        return node in self._graph

    def set_move_cost_calculator(
        self, move_cost_calculator: CachingMoveCostCalculator
    ) -> None:
        """Sets the move cost calculator to be used within this instance. This could be a pre-cached or fresh
        calculator.

        Args:
            move_cost_calculator: the calculator object.
        """
        self._move_cost_calculator = move_cost_calculator


class RandomConnectivityMap(ConnectivityMap):
    """
    Concrete implementation of `ConnectivityMap` that builds a random undirected graph
    of warehouse locations.

    The graph ensures that all nodes are connected through random bidirectional
    edges, allowing pathfinding and cost-calculation logic to be exercised without relying
    on a physical warehouse layout.

    """

    def __init__(
        self,
        layout: WarehouseLayoutModel,
        seed: int | None = None,
    ) -> None:
        """Initialise.

        Args:
            seed: a random seed.
        """
        super().__init__(layout)
        self._seed = seed
        self.construct_graph()

    def construct_graph(self) -> None:
        """Builds a random connectivity graph that facilitates paths between all nodes.
        Useful for testing purposes.
        """
        if self._seed is not None:
            random.seed(self._seed)

        nodes = list(self._warehouse_layout.locations.keys())
        # Perform several random shuffles to introduce randomized connectivity patterns
        for _ in range(4):
            random.shuffle(nodes)  # Randomly reorder nodes in place
            # Pair consecutive nodes in the shuffled list to create bidirectional edges
            for node_0, node_1 in tqdm(zip(nodes[:-1], nodes[1:])):
                self.add_edge(node_0, node_1, bidirectional=True)

        num_nodes, num_edges = self.compute_graph_size()
        logging.info(
            f"Generated random graph with {num_nodes} nodes, {num_edges} directed edges. "
        )
