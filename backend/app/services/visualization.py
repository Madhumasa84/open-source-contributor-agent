from app.schemas.repository import GraphEdge, GraphNode, RepositoryGraph, RepositoryOverview


class RepositoryVisualizationService:
    def from_overview(self, overview: RepositoryOverview) -> RepositoryGraph:
        nodes: dict[str, GraphNode] = {
            "repo": GraphNode(id="repo", label="Repository", type="repository")
        }
        edges: list[GraphEdge] = []

        for language in overview.languages:
            node_id = f"language:{language}"
            nodes[node_id] = GraphNode(id=node_id, label=language, type="language")
            edges.append(GraphEdge(source="repo", target=node_id, label="uses"))

        for framework in overview.frameworks:
            node_id = f"framework:{framework}"
            nodes[node_id] = GraphNode(id=node_id, label=framework, type="framework")
            edges.append(GraphEdge(source="repo", target=node_id, label="builds with"))

        for file in overview.entry_points[:12]:
            node_id = f"file:{file}"
            nodes[node_id] = GraphNode(id=node_id, label=file, type="entry_point")
            edges.append(GraphEdge(source="repo", target=node_id, label="entry"))

        for test in overview.test_frameworks:
            node_id = f"test:{test}"
            nodes[node_id] = GraphNode(id=node_id, label=test, type="test")
            edges.append(GraphEdge(source="repo", target=node_id, label="validated by"))

        for ecosystem, dependencies in overview.dependencies.items():
            ecosystem_id = f"dependency:{ecosystem}"
            nodes[ecosystem_id] = GraphNode(
                id=ecosystem_id,
                label=ecosystem,
                type="dependency_group",
            )
            edges.append(GraphEdge(source="repo", target=ecosystem_id, label="depends on"))
            for dependency in dependencies[:12]:
                node_id = f"dependency:{ecosystem}:{dependency}"
                nodes[node_id] = GraphNode(id=node_id, label=dependency, type="dependency")
                edges.append(GraphEdge(source=ecosystem_id, target=node_id, label="contains"))

        return RepositoryGraph(nodes=list(nodes.values()), edges=edges)

    def issue_knowledge_graph(
        self,
        issue_url: str,
        files: list[str],
        functions: list[str],
        dependencies: list[str],
        tests: list[str],
    ) -> RepositoryGraph:
        nodes: dict[str, GraphNode] = {
            "issue": GraphNode(id="issue", label=issue_url, type="issue")
        }
        edges: list[GraphEdge] = []

        for file in files:
            node_id = f"file:{file}"
            nodes[node_id] = GraphNode(id=node_id, label=file, type="file")
            edges.append(GraphEdge(source="issue", target=node_id, label="touches"))

        for function in functions:
            node_id = f"function:{function}"
            nodes[node_id] = GraphNode(id=node_id, label=function, type="function")
            parent = f"file:{function.split(':', 1)[0]}" if ":" in function else "issue"
            edges.append(GraphEdge(source=parent, target=node_id, label="contains"))

        for dependency in dependencies:
            node_id = f"dependency:{dependency}"
            nodes[node_id] = GraphNode(id=node_id, label=dependency, type="dependency")
            edges.append(GraphEdge(source="issue", target=node_id, label="depends on"))

        for test in tests:
            node_id = f"test:{test}"
            nodes[node_id] = GraphNode(id=node_id, label=test, type="test")
            edges.append(GraphEdge(source="issue", target=node_id, label="verified by"))

        return RepositoryGraph(nodes=list(nodes.values()), edges=edges)
