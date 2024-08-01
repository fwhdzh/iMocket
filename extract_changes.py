import tla_parser

def has_corresponding_block(spec, block):
    """Check if there is a corresponding block in the specification."""
    for other_block in spec.basic_blocks:
        if block == other_block:
            return True
    return False

def get_corresponding_block(spec, block):
    """Retrieve the corresponding block in the specification."""
    for other_block in spec.basic_blocks:
        if block == other_block:
            return other_block
    return None

def diff_statement(blockA, blockB):
    """Identify differences in statements within the basic blocks."""
    setA = {str(stmt) for stmt in blockA.statements}
    setB = {str(stmt) for stmt in blockB.statements}
    return setA.symmetric_difference(setB)

def is_unmodified_statement_modified(blockA, blockB, var_diff_set):
    """Determine if an unmodified statement is considered modified based on variable differences."""
    statement_diff = diff_statement(blockA, blockB)
    affected_vars = {stmt.split('=')[0].strip() for stmt in statement_diff if '=' in stmt}
    return not affected_vars.isdisjoint(var_diff_set)

def compare_specs(original_spec, modified_spec):
    var_diff_set = set()
    block_diff_set = set()

    # Detect variable differences
    original_vars = set(original_spec.variables)
    modified_vars = set(modified_spec.variables)

    # Variables deleted in the modified specification
    for var in original_vars:
        if var not in modified_vars:
            var_diff_set.add(('DELETE', var))

    # Variables added in the modified specification
    for var in modified_vars:
        if var not in original_vars:
            var_diff_set.add(('ADD', var))

    # Detect basic block differences
    for block in original_spec.basic_blocks:
        if has_corresponding_block(modified_spec, block):
            corresponding_block = get_corresponding_block(modified_spec, block)
            if is_unmodified_statement_modified(block, corresponding_block, var_diff_set):
                modified_spec.basic_blocks.remove(corresponding_block)
            continue
        else:
            block_diff_set.add(('DELETE', block))

    for block in modified_spec.basic_blocks:
        if not has_corresponding_block(original_spec, block):
            block_diff_set.add(('ADD', block))

    return var_diff_set, block_diff_set