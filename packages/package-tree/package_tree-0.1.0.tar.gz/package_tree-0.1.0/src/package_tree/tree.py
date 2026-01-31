import argparse
import subprocess
import tempfile
from importlib.metadata import distributions

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


class inf_loop(list):

    def __init__(self, *args):
        for x in args:
            self.append(x)

    def __iter__(self):
        while True:
            for x in list.__iter__(self):
                yield x


class Style(dict):

    _colors = iter(inf_loop('#a6cee3', '#b2df8a', '#fb9a99', '#fdbf6f',
                            '#cab2d6', '#ffff99', '#1f78b4', '#33a02c',
                            '#e31a1c', '#ff7f00', '#6a3d9a', '#b15928'))

    def __init__(self, color=None):
        self['color'] = color or next(self._colors)
        self['shape'] = 'box'
        self['style'] = 'filled'

    def __str__(self):
        return ', '.join('%s="%s"' % x for x in self.items())


class Graph:

    def __init__(self, args):
        self.args = args
        self.styles = {}

    def format_label(self, pkg):
        lines = [pkg.name]
        if self.args.paths:
            lines.append('<font point-size="10">%s</font>' % pkg.locate_file(""))
        lines.append(f'<font point-size="10">{pkg.version}</font>')
        return "<br/>".join(lines)

    def get_style(self, pkg):
        if self.args.paths:
            site_package = pkg.locate_file("")
            if site_package not in self.styles:
                self.styles[site_package] = Style()
            return self.styles[site_package]
        else:
            return Style(color="#a6cee3")

    def get_graph(self):
        """
        Packages and dependencies in dot language.

        Return:
            List of lines
        """
        deps = set()

        for pkg in distributions():
            if pkg.requires:
                deps.update(
                    (canonicalize_name(pkg.name), canonicalize_name(req.name))
                    for req in (Requirement(x) for x in pkg.requires)
                    if not req.marker or req.marker.evaluate()
                )

        result = []
        result.append("rankdir=LR;")

        for pkg in distributions():
            result.append(
                '"%s" [%s, label=<%s>]'
                % (
                    canonicalize_name(pkg.name),
                    self.get_style(pkg),
                    self.format_label(pkg),
                )
            )
        for relation in sorted(deps):
            result.append('"%s" -> "%s";' % relation)

        return result

    def write_dot_file(self, stream):
        """
        Write full dot script to stream.
        """
        stream.write("digraph G {\n")
        for l in self.get_graph():
            stream.write("    ")
            stream.write(l)
            stream.write("\n")
        stream.write("}\n")


def build(script_file, outfile, fmt="png"):
    """
    Invoke dot.
    """
    subprocess.call(['dot', '-T' + fmt], stdin=script_file, stdout=outfile)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a dependency graph of installed Python packages."
    )
    parser.add_argument("filename", help="Output file path for the generated graph.")
    parser.add_argument(
        "-f",
        "--format",
        choices=["png", "svg", "dot"],
        default="png",
        help="Output file format (default: png).",
    )
    parser.add_argument(
        "--paths",
        action="store_true",
        default=False,
        help="Include the filesystem paths where each package is installed.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.format == 'dot':
        with open(args.filename, 'w') as outfile:
            Graph(args).write_dot_file(outfile)
    else:
        with tempfile.TemporaryFile('w') as script_file, \
             open(args.filename, 'wb') as outfile:
            Graph(args).write_dot_file(script_file)
            script_file.seek(0)
            build(script_file, outfile, args.format)
