import os
import tempfile

from gemini_tree_token_counter.main import load_cli_patterns, load_ignore_patterns, scan_directory


def collect_rel_paths(node, root_path):
    paths = []
    if node.is_dir:
        for child in node.children:
            paths.extend(collect_rel_paths(child, root_path))
        return paths
    rel_path = os.path.relpath(node.path, root_path)
    return [rel_path.replace(os.sep, '/')]


def write_text(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_gtcignore_excludes_patterns():
    with tempfile.TemporaryDirectory() as tmp:
        write_text(os.path.join(tmp, "keep.txt"), "keep")
        write_text(os.path.join(tmp, "ignore.test.ts"), "ignore")
        write_text(os.path.join(tmp, "__snapshots__", "snap.txt"), "snap")
        write_text(os.path.join(tmp, "telemetry", "log.txt"), "log")
        write_text(os.path.join(tmp, "packages", "core", "src", "mcp", "x.txt"), "x")

        gtcignore_path = os.path.join(tmp, ".gtcignore")
        with open(gtcignore_path, "w", encoding="utf-8") as f:
            f.write(
                "\n".join(
                    [
                        "*.test.ts",
                        "__snapshots__/",
                        "telemetry/",
                        "packages/core/src/mcp/",
                    ]
                )
            )

        gtc_patterns = load_ignore_patterns(tmp, ".gtcignore", path_based="auto")
        node = scan_directory(tmp, tmp, None, gtc_patterns, [])
        rel_paths = set(collect_rel_paths(node, tmp))

        assert "keep.txt" in rel_paths
        assert "ignore.test.ts" not in rel_paths
        assert "__snapshots__/snap.txt" not in rel_paths
        assert "telemetry/log.txt" not in rel_paths
        assert "packages/core/src/mcp/x.txt" not in rel_paths


def test_cli_excludes_patterns():
    with tempfile.TemporaryDirectory() as tmp:
        write_text(os.path.join(tmp, "src", "app.py"), "app")
        write_text(os.path.join(tmp, "src", "app.test.ts"), "test")
        write_text(os.path.join(tmp, "generated", "big.json"), "data")

        cli_patterns = load_cli_patterns(["*.test.ts", "generated/"])
        node = scan_directory(tmp, tmp, None, [], cli_patterns)
        rel_paths = set(collect_rel_paths(node, tmp))

        assert "src/app.py" in rel_paths
        assert "src/app.test.ts" not in rel_paths
        assert "generated/big.json" not in rel_paths
