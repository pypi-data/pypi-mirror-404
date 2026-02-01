# GitGlasses

Visualize git branch relationships in a commit range.

## Installation

```bash
uv sync
```

## Usage

```bash
gitglasses <start_ref> <end_ref>
```

### Examples

```bash
# Show branches between HEAD and main
gitglasses HEAD main

# Show branches in last 5 commits
gitglasses HEAD~5 HEAD

# Show branches between feature-a and main
gitglasses feature-a main
```

## Output

GitGlasses displays branches as an ASCII tree with box-drawing characters:

```
main
├── branch-a (a1b2c3d, e4f5g6h)
│   └── branch-b (i7j8k9l)
└── branch-c (m1n2o3p)
```

Each branch shows the abbreviated commit hashes of commits in the specified range.
