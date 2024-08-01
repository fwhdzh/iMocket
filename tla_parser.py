import re

class Statement:
    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return f"Statement({self.content})"

class BasicBlock:
    def __init__(self, parent_name):
        self.parent_name = parent_name
        self.statements = []

    def add_statement(self, statement):
        self.statements.append(Statement(statement))

    def __repr__(self):
        return f"BasicBlock(parent={self.parent_name}, statements={self.statements})"

class Spec:
    def __init__(self, basic_blocks, variables):
        self.basic_blocks = basic_blocks
        self.variables = variables

    def __repr__(self):
        return f"Spec(basic_blocks={self.basic_blocks}, variables={self.variables})"

def parse_tla_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    basic_blocks = []
    variables = []
    current_block = None
    action_names = []
    reading_next = False

    # Process each line to identify parts of the specification
    for line in lines:
        line = line.strip()
        if line.startswith("VARIABLES"):
            # Extract variables from this line
            var_line = line[len("VARIABLES"):].strip()
            variables.extend([var.strip() for var in var_line.split(',')])
        elif "Next ==" in line:
            reading_next = True
        elif reading_next and line.startswith("\\/"):
            match = re.search(r':\s*(\w+)', line)
            if match:
                action_names.append(match.group(1))
        elif reading_next and not line.startswith("\\/"):
            reading_next = False
        elif any(line.startswith(name) for name in ["Init"] + action_names):
            # Start of a new basic block
            current_block = BasicBlock(line.split()[0])
            basic_blocks.append(current_block)
        elif line.startswith("∧"):
            # New statement in current basic block
            if current_block:
                current_block.add_statement(line[1:].strip())  # Remove leading ∧
        elif line and current_block:
            # Continue adding statements to the current basic block
            current_block.add_statement(line)

    return Spec(basic_blocks, variables)