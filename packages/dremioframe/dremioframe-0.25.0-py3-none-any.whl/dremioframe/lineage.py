from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class LineageNode:
    """Represents a table, view, or dataset in the lineage graph"""
    id: str
    name: str
    type: str  # 'table', 'view', 'vds', 'pds'
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LineageEdge:
    """Represents a transformation between two nodes"""
    source_id: str
    target_id: str
    operation: str  # 'select', 'join', 'aggregate', 'insert', 'merge'
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

class LineageGraph:
    """
    Represents a data lineage graph showing relationships between datasets.
    """
    def __init__(self):
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: List[LineageEdge] = []

    def add_node(self, node: LineageNode):
        """Add a node to the graph"""
        self.nodes[node.id] = node

    def add_edge(self, edge: LineageEdge):
        """Add an edge to the graph"""
        self.edges.append(edge)

    def get_upstream(self, node_id: str, max_depth: int = None) -> Set[str]:
        """Get all upstream dependencies of a node"""
        upstream = set()
        to_visit = [(node_id, 0)]
        visited = set()
        
        while to_visit:
            current_id, depth = to_visit.pop(0)
            if current_id in visited:
                continue
            if max_depth and depth > max_depth:
                continue
                
            visited.add(current_id)
            
            # Find edges where current node is the target
            for edge in self.edges:
                if edge.target_id == current_id and edge.source_id != current_id:
                    upstream.add(edge.source_id)
                    to_visit.append((edge.source_id, depth + 1))
        
        return upstream

    def get_downstream(self, node_id: str, max_depth: int = None) -> Set[str]:
        """Get all downstream dependents of a node"""
        downstream = set()
        to_visit = [(node_id, 0)]
        visited = set()
        
        while to_visit:
            current_id, depth = to_visit.pop(0)
            if current_id in visited:
                continue
            if max_depth and depth > max_depth:
                continue
                
            visited.add(current_id)
            
            # Find edges where current node is the source
            for edge in self.edges:
                if edge.source_id == current_id and edge.target_id != current_id:
                    downstream.add(edge.target_id)
                    to_visit.append((edge.target_id, depth + 1))
        
        return downstream

    def to_dict(self) -> Dict[str, Any]:
        """Export graph to dictionary format"""
        return {
            'nodes': [
                {
                    'id': node.id,
                    'name': node.name,
                    'type': node.type,
                    'metadata': node.metadata
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {
                    'source': edge.source_id,
                    'target': edge.target_id,
                    'operation': edge.operation,
                    'timestamp': edge.timestamp,
                    'metadata': edge.metadata
                }
                for edge in self.edges
            ]
        }

    def to_networkx(self):
        """Convert to NetworkX DiGraph (requires networkx)"""
        try:
            import networkx as nx
        except ImportError:
            raise ImportError("networkx is required. Install with: pip install dremioframe[lineage]")
        
        G = nx.DiGraph()
        
        # Add nodes
        for node in self.nodes.values():
            G.add_node(node.id, name=node.name, type=node.type, **node.metadata)
        
        # Add edges
        for edge in self.edges:
            G.add_edge(edge.source_id, edge.target_id, 
                      operation=edge.operation, 
                      timestamp=edge.timestamp,
                      **edge.metadata)
        
        return G

class LineageTracker:
    """
    Tracks data lineage and transformations.
    """
    def __init__(self, client=None):
        self.client = client
        self.graph = LineageGraph()

    def track_transformation(self, source: str, target: str, operation: str, 
                           metadata: Dict[str, Any] = None):
        """
        Record a data transformation.
        
        Args:
            source: Source table/view path
            target: Target table/view path
            operation: Type of operation (select, join, insert, etc.)
            metadata: Additional metadata about the transformation
        """
        # Add nodes if they don't exist
        if source not in self.graph.nodes:
            self.graph.add_node(LineageNode(
                id=source,
                name=source.split('.')[-1],
                type='table',
                metadata={'path': source}
            ))
        
        if target not in self.graph.nodes:
            self.graph.add_node(LineageNode(
                id=target,
                name=target.split('.')[-1],
                type='table',
                metadata={'path': target}
            ))
        
        # Add edge
        self.graph.add_edge(LineageEdge(
            source_id=source,
            target_id=target,
            operation=operation,
            metadata=metadata or {}
        ))

    def get_lineage_graph(self, table: str, direction: str = 'both', 
                         max_depth: int = None) -> LineageGraph:
        """
        Build a lineage graph for a specific table.
        
        Args:
            table: Table path to analyze
            direction: 'upstream', 'downstream', or 'both'
            max_depth: Maximum depth to traverse
        
        Returns:
            LineageGraph containing relevant nodes and edges
        """
        result_graph = LineageGraph()
        
        # Always include the target node
        if table in self.graph.nodes:
            result_graph.add_node(self.graph.nodes[table])
        
        # Get relevant node IDs
        relevant_nodes = {table}
        
        if direction in ['upstream', 'both']:
            relevant_nodes.update(self.graph.get_upstream(table, max_depth))
        
        if direction in ['downstream', 'both']:
            relevant_nodes.update(self.graph.get_downstream(table, max_depth))
        
        # Add nodes
        for node_id in relevant_nodes:
            if node_id in self.graph.nodes:
                result_graph.add_node(self.graph.nodes[node_id])
        
        # Add edges
        for edge in self.graph.edges:
            if edge.source_id in relevant_nodes and edge.target_id in relevant_nodes:
                result_graph.add_edge(edge)
        
        return result_graph

    def visualize(self, graph: LineageGraph = None, format: str = 'html', 
                 output_file: str = None) -> Any:
        """
        Create a visual representation of the lineage graph.
        
        Args:
            graph: LineageGraph to visualize (uses full graph if None)
            format: Output format ('html', 'png', 'svg')
            output_file: Path to save the visualization
        
        Returns:
            Visualization object (format-dependent)
        """
        if graph is None:
            graph = self.graph
        
        if format == 'html':
            return self._visualize_html(graph, output_file)
        else:
            return self._visualize_graphviz(graph, format, output_file)

    def _visualize_html(self, graph: LineageGraph, output_file: str = None):
        """Create interactive HTML visualization using vis.js or similar"""
        # Simple HTML template with embedded data
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Data Lineage Graph</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        #lineage-graph {{
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <h1>Data Lineage</h1>
    <div id="lineage-graph"></div>
    <script>
        var nodes = new vis.DataSet({nodes_data});
        var edges = new vis.DataSet({edges_data});
        
        var container = document.getElementById('lineage-graph');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            nodes: {{
                shape: 'box',
                font: {{ size: 14 }}
            }},
            edges: {{
                arrows: 'to',
                font: {{ size: 12, align: 'middle' }}
            }},
            physics: {{
                enabled: true,
                barnesHut: {{ gravitationalConstant: -2000 }}
            }}
        }};
        
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>
        """
        
        # Convert graph to vis.js format
        nodes_data = [
            {
                'id': node.id,
                'label': node.name,
                'title': f"{node.type}: {node.id}",
                'color': self._get_node_color(node.type)
            }
            for node in graph.nodes.values()
        ]
        
        edges_data = [
            {
                'from': edge.source_id,
                'to': edge.target_id,
                'label': edge.operation,
                'title': edge.timestamp
            }
            for edge in graph.edges
        ]
        
        html = html_template.format(
            nodes_data=json.dumps(nodes_data),
            edges_data=json.dumps(edges_data)
        )
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(html)
        
        return html

    def _visualize_graphviz(self, graph: LineageGraph, format: str, output_file: str = None):
        """Create static visualization using graphviz"""
        try:
            import graphviz
        except ImportError:
            raise ImportError("graphviz is required. Install with: pip install dremioframe[lineage]")
        
        dot = graphviz.Digraph(comment='Data Lineage', format=format)
        dot.attr(rankdir='LR')
        
        # Add nodes
        for node in graph.nodes.values():
            dot.node(node.id, node.name, shape='box', 
                    style='filled', fillcolor=self._get_node_color(node.type))
        
        # Add edges
        for edge in graph.edges:
            dot.edge(edge.source_id, edge.target_id, label=edge.operation)
        
        if output_file:
            dot.render(output_file, cleanup=True)
        
        return dot

    def _get_node_color(self, node_type: str) -> str:
        """Get color for node based on type"""
        colors = {
            'table': '#lightblue',
            'view': '#lightgreen',
            'vds': '#lightyellow',
            'pds': '#lightcoral'
        }
        return colors.get(node_type, '#lightgray')

    def export_lineage(self, graph: LineageGraph = None, format: str = 'json', 
                      output_file: str = None) -> str:
        """
        Export lineage data to various formats.
        
        Args:
            graph: LineageGraph to export (uses full graph if None)
            format: Export format ('json', 'datahub', 'amundsen')
            output_file: Path to save the export
        
        Returns:
            Exported data as string
        """
        if graph is None:
            graph = self.graph
        
        if format == 'json':
            data = json.dumps(graph.to_dict(), indent=2)
        elif format == 'datahub':
            data = self._export_datahub(graph)
        elif format == 'amundsen':
            data = self._export_amundsen(graph)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(data)
        
        return data

    def _export_datahub(self, graph: LineageGraph) -> str:
        """Export in DataHub-compatible format"""
        # Simplified DataHub format
        lineage_data = {
            'upstreams': [],
            'downstreams': []
        }
        
        for edge in graph.edges:
            lineage_data['upstreams'].append({
                'dataset': edge.source_id,
                'type': 'TRANSFORMED'
            })
            lineage_data['downstreams'].append({
                'dataset': edge.target_id,
                'type': 'TRANSFORMED'
            })
        
        return json.dumps(lineage_data, indent=2)

    def _export_amundsen(self, graph: LineageGraph) -> str:
        """Export in Amundsen-compatible format"""
        # Simplified Amundsen format
        tables = []
        
        for node in graph.nodes.values():
            tables.append({
                'key': node.id,
                'name': node.name,
                'description': node.metadata.get('description', ''),
                'cluster': 'dremio',
                'schema': node.metadata.get('schema', 'default')
            })
        
        return json.dumps({'tables': tables}, indent=2)
