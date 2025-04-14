# iMocket: incremental model checking guided testing for distributed systems
A tool demo for testing distributed system changes based on [Mocket](https://github.com/tcse-iscas/Mocket).
The repository contains two parts:
1. A java project ImplDiffIdentifier: identifying changes in two Java projects.
2. Python files: imocket.py: the main process of iMocket;
                 tla_parser.py: constructing TLA+ specification into ASTs;
                 extract_changes.py: extracting changes from TLA+ specifications;
                 identify_affected_regions.py: identifying affected nodes and edges in the changed graph;
                 path_generator.py: growth-based graph traversal
## Requirements
JDK 8
Maven 3
Python 3
Python NetworkX package

## Using iMocket
Using iMocket involves three steps:
1. Using ImplDiffIdentifier to identify changes in two distributed system implementations.
2. Using imocket.py to get paths as incremental test cases.
3. Using Mocket to test these incremental test cases.

### Using ImplDiffIdentifier

In the directory of ImplDiffIdentifier, we use Maven to build the project.
```bash
mvn clean package
```
A jar file "impldiffidentifier.jar" is generated in "target/".

Use the following command to get changes between two Java projects:
```bash
java -jar impldiffidentifier.jar <path/to/project1> <path/to/project2> <path/to/output_file>
```

### Using imocket.py
Use the following command to get incremental test cases:
```bash
py imocket.py original_spec.tla modified_spec.tla original_graph.json modified_graph.json action_changes.txt allowed_actions.txt forbidden_actions.txt output_paths.json
```

### Testing with Mocket
Refer to [Mocket](https://github.com/tcse-iscas/Mocket).