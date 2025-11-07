from abc import ABC, abstractmethod
import heapq

from dexory.connectivity_maps import ConnectivityMap


class PathFinder(ABC):
    """
    Abstract base class defining the interface for computing optimal paths between
    warehouse locations.

    Subclasses are expected to implement specific pathfinding algorithms (e.g., Dijkstra,
    A*, BFS) to determine the most efficient route between two nodes in a given
    `ConnectivityMap`. The base class holds a reference to the warehouse connectivity
    graph and defines the expected interface for path computation.

    """

    def __init__(self, connectivity_map: ConnectivityMap):
        self.connectivity_map = connectivity_map
        super().__init__()

    @abstractmethod
    def compute_optimal_path(self, node_a: str, node_b: str) -> tuple[list[str], float]:
        """Compute the optimal path and its total cost between two warehouse nodes.


        Args:
            node_a: source node name
            node_b: destination node name

        Returns:
            the optimal path (list of nodes), the optimal cost
        """
        pass


class DijkstraPathFinder(PathFinder):
    """
    Concrete implementation of `PathFinder` that computes the shortest path
    between two warehouse nodes using Dijkstra's algorithm.
    """

    def __init__(self, connectivity_map: ConnectivityMap):
        super().__init__(connectivity_map)

    def compute_optimal_path(self, node_a: str, node_b: str) -> tuple[list[str], float]:
        """
        Compute the shortest path and total movement cost between two nodes using Dijkstra's algorithm.

        The algorithm explores all reachable nodes in order of increasing total cost,
        maintaining the least-cost path to each node.
        """

        if not self.connectivity_map.has_node(
            node_a
        ) or not self.connectivity_map.has_node(node_b):
            raise ValueError(f"Start or goal node not in graph: {node_a}, {node_b}")

        queue: list[tuple[float, str]] = [(0.0, node_a)]
        visited: dict[str, float] = {node_a: 0.0}
        came_from: dict[str, str] = {}

        while queue:
            cost, node = heapq.heappop(queue)
            if node == node_b:
                break  # Found shortest path to goal

            # Skip outdated queue entries
            if cost > visited[node]:
                continue

            for neighbor in self.connectivity_map.get_neighbors(node):
                new_cost = cost + self.connectivity_map.calculate_move_cost(
                    node, neighbor
                )

                prev_cost = visited.get(neighbor)
                if prev_cost is None or new_cost < prev_cost:
                    visited[neighbor] = new_cost
                    came_from[neighbor] = node
                    heapq.heappush(queue, (new_cost, neighbor))

        if node_b not in visited:
            return [], float("inf")

        path: list[str] = [node_b]
        while path[-1] != node_a:
            path.append(came_from[path[-1]])
        path.reverse()

        return path, visited[node_b]
