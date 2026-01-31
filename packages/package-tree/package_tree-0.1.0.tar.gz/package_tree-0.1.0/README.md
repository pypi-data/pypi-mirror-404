# package-tree

`package-tree` is a command-line tool that builds a dependency graph
of the Python packages installed in the current environment.

It inspects installed distributions and generates a Graphviz graph
using the `dot` command.

## Exemple

![Exemple](graph.png)

---

## Requirements

- Python ≥ 3.8
- Graphviz (`dot` command available in PATH)

---

## Example

```bash
package-tree -f svg graph.svg
```

See `package-tree --help` for more details.
