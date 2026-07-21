from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class GraphProvider(ABC):
    """
    Abstract Base Class defining the contract for graph database providers.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the graph database."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Cleanly close database connections."""
        pass

    @abstractmethod
    def create_node(self, label: str, properties: Dict[str, Any]) -> None:
        """Create or update a single node in the graph."""
        pass

    @abstractmethod
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a relationship between two nodes."""
        pass

    @abstractmethod
    def batch_insert_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """Optimized insertion of multiple nodes in a batch."""
        pass

    @abstractmethod
    def batch_insert_relationships(self, relationships: List[Dict[str, Any]]) -> None:
        """Optimized insertion of multiple relationships in a batch."""
        pass

    @abstractmethod
    def query(self, query_str: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Run custom query statement and return rows."""
        pass

    @abstractmethod
    def save_edge(
        self,
        project_id: str,
        source_class: str,
        target_class: str,
        relationship_type: str
    ) -> bool:
        """Save a class edge for backward compatibility."""
        pass

    @abstractmethod
    def get_edges(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all edges for a project."""
        pass

    @abstractmethod
    def get_outgoing_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        """Get outgoing edges from a class."""
        pass

    @abstractmethod
    def get_incoming_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        """Get incoming edges to a class."""
        pass

    @abstractmethod
    def get_all_class_edges(self, project_id: str, class_name: str) -> List[Dict[str, Any]]:
        """Get all incoming/outgoing class edges."""
        pass

    @abstractmethod
    def get_graph_stats(self, project_id: str) -> Dict[str, Any]:
        """Get graph counts / metrics."""
        pass

    @abstractmethod
    def delete_class_edges(self, project_id: str, class_name: str) -> None:
        """Delete class edges from a specific class."""
        pass

    @abstractmethod
    def delete_project(self, project_id: str) -> None:
        """Remove all nodes and relationships under a project namespace."""
        pass
