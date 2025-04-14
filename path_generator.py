import networkx as nx
import random

PATHS = [[]]


##################################### General functions #########################################

"""
Find the root node for a state space graph

Parameters:
    diGraph: the state space networkx graph

Returns:
    node: the root node (initial state)
"""
def find_root(diGraph):
    node = None
    for n in diGraph.nodes(data=True):
        predecessors = diGraph.predecessors(n[0])
        if len(list(predecessors)) == 0:
            node = n
            break
    return node

"""
Output paths to files, in which '.node' file stores maps of 
state ID and contents, and '.edge' file stores paths.

Parameters:
    graph: the state space networkx graph
    output: the directory to store path files
Returns:
    None
"""
def output(graph, output):
    label = nx.get_node_attributes(graph, 'label')
    node_file = open(output+'.node','w')
    edge_file = open(output+'.edge','w')
    # Write all node information
    for i, node in enumerate(graph):
        if node.isdigit() or node.startswith('-'):
            node_file.write(node + ' ' + label[node] + '\n')
    # Write all edge information
    for path in PATHS:
        for i, node in enumerate(path):
            if i == 0:
                edge_file.write(node + ' ')
            else:
                action = graph[path[i-1]][node]['label']
                edge_file.write(action + ' ' + node + ' ')
        edge_file.write('\n')


"""
Reads a file containing edges and constructs a list of edges.
Each line in the file should contain two node identifiers separated by a space.

Parameters:
file_path (str): The path to the file containing the edges.

Returns:
list of tuples: A list where each tuple represents an edge (node1, node2).
"""
def read_edges_from_file(file_path):
    edges = []
    with open(file_path, 'r') as file:
        for line in file:
            # Strip newline and any leading/trailing whitespace
            clean_line = line.strip()
            if clean_line:  # ensure the line is not empty
                node1, node2 = clean_line.split()
                edges.append((node1, node2))
    return edges

##################################### iMocket functions #########################################

def traverse_path(G, init_state, end_states, affected_edges):
    paths = []
    while affected_edges:
        edge = random.choice(list(affected_edges))
        affected_edges.remove(edge)
        path = [edge]
        backward_traverse(edge[0], path, G, init_state, affected_edges)
        forward_traverse(edge[1], path, G, end_states, affected_edges)
        paths.append(path)
    return paths

def backward_traverse(node, path, graph, init_state, affected_edges):
    if node == init_state:
        return
    preds = list(graph.predecessors(node))
    pred_edge = prior_visit(preds, node, affected_edges)
    path.insert(0, pred_edge)
    backward_traverse(pred_edge[0], path, graph, init_state, affected_edges)

def forward_traverse(node, path, graph, end_states, affected_edges):
    if node in end_states or not list(graph.successors(node)):
        return
    succs = list(graph.successors(node))
    succ_edge = prior_visit(node, succs, affected_edges)
    path.append(succ_edge)
    forward_traverse(succ_edge[1], path, graph, end_states, affected_edges)

def prior_visit(node, targets, affected_edges):
    potential_edges = [(node, target) for target in targets if (node, target) in affected_edges]
    if potential_edges:
        edge = random.choice(potential_edges)
        affected_edges.remove(edge)
    else:
        edge = (node, random.choice(targets))
    return edge
