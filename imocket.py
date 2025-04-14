import networkx as nx
import json
import sys

import extract_changes
import identify_affected_regions
import path_generator

def load_graph(filename):
    """Load a graph from a JSON file."""
    with open(filename, 'r') as file:
        data = json.load(file)
    G = nx.DiGraph()
    for node in data['nodes']:
        G.add_node(node['id'], **node)
    for edge in data['edges']:
        G.add_edge(edge['source'], edge['target'], action=edge['action'])
    return G

def load_action_sequences(filename):
    """Load action sequences from a file."""
    with open(filename, 'r') as file:
        return [tuple(line.strip().split(',')) for line in file if line.strip()]

def load_action_changes(filename):
    """Load action changes from a file."""
    with open(filename, 'r') as file:
        return {line.split(',')[0]: line.split(',')[1].strip() for line in file if line.strip()}
    
def main(original_spec_file, modified_spec_file, original_graph_file, modified_graph_file,
         action_changes_file, allowed_actions_file, forbidden_actions_file, output_file):

    # Load TLA+ specifications
    original_spec = extract_changes.parse_tla_file(original_spec_file)
    modified_spec = extract_changes.parse_tla_file(modified_spec_file)

    # Compare specifications
    var_diff_set, block_diff_set = extract_changes.compare_specs(original_spec, modified_spec)

    # Load state graphs
    graph = load_graph(original_graph_file)
    modified_graph = load_graph(modified_graph_file)

    # Load action sequences
    allowed_action_seqs = load_action_sequences(allowed_actions_file)
    forbidden_action_seqs = load_action_sequences(forbidden_actions_file)

    # Load modified actions
    modified_actions = load_action_changes(action_changes_file)

    # Identify affected regions in the graph
    affected_nodes, affected_edges = identify_affected_regions.identify(
        graph, modified_graph, allowed_action_seqs,
        forbidden_action_seqs, modified_actions, block_diff_set
    )

    # Generate and output paths
    paths = path_generator.traverse(graph, affected_edges)
    with open(output_file, 'w') as file:
        json.dump(paths, file)


def usage():
    sys.stdout.write("iMocket \n")
    sys.stdout.write("USAGE: py imocket.py original_spec.tla modified_spec.tla original_graph.json " +
            "modified_graph.json action_changes.txt allowed_actions.txt forbidden_actions.txt output_paths.json")

if __name__ == "__main__":
    if (len(sys.argv) > 7):
        ori_spec = sys.argv[1]
        mod_spec = sys.argv[2]
        ori_graph = sys.argv[3]
        mod_graph = sys.argv[4]
        act_changes = sys.argv[5]
        allowed_actions = sys.argv[6]
        forbid_actions = sys.argv[7]
        output_paths = sys.argv[8]

    main(ori_spec, mod_spec, ori_graph, mod_graph, act_changes, allowed_actions, forbid_actions, output_paths)