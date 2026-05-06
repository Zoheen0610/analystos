import networkx as nx

workflow_graph = nx.DiGraph()


def initialize_dataset_node(dataset_name: str):

    workflow_graph.add_node(
        dataset_name,
        type="dataset"
    )


def add_profile_node(dataset_name: str):

    profile_node = f"{dataset_name}_profile"

    workflow_graph.add_node(
        profile_node,
        type="profile"
    )

    workflow_graph.add_edge(
        dataset_name,
        profile_node
    )


def get_graph_data():

    return {
        "nodes": list(workflow_graph.nodes(data=True)),
        "edges": list(workflow_graph.edges())
    }
