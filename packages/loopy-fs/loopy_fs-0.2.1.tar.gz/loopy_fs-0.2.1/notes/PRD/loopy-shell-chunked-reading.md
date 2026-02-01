PRD: Chunked Reading + Splitting in Loopy Shell

Goal
Provide bash-like primitives for reading large content and splitting it into manageable chunks in the Loopy shell:
1) head/tail (line chunks)
3) split (delimiter-based chunking)
5) cat --range (byte/char offsets)

We want these to feel natural and composable with pipes, while staying minimal and consistent with existing Loopy patterns.

User Stories
- Read the first or last N lines of a file quickly.
- Split a file or stdin by a delimiter into one item per line.
- Read a specific byte/char range from a file for chunked access.
- Compose these with pipes (cat --range ... | split , | head -n 10).

Non-Goals
- Full POSIX behavior (head -c, tail -f, locale-aware byte semantics).
- Binary-safe streaming; treat content as text strings.
- Full awk/cut/sed parity.

Commands and Semantics
1) head
- Syntax: head [-n N] [path]
- Behavior: Read from path if provided, else from stdin. Default N=10. Return first N lines.

2) tail
- Syntax: tail [-n N] [path]
- Behavior: Read from path if provided, else from stdin. Default N=10. Return last N lines.

3) split
- Syntax: split <delim> [path]
- Behavior: Read from path if provided, else from stdin. Split on delimiter string. Emit one token per line.
- Notes: Empty delimiter is an error. Preserve empty fields between delimiters (prints blank lines).

4) cat --range
- Syntax: cat [path] [--range start length]
- Behavior: Read from path if provided, else from stdin. Return substring starting at start for length chars.
- Constraints: start >= 0, length >= 0. Clamp out-of-bounds to available content.

Pipeline Behavior
- All commands accept stdin when no path is provided.
- Commands return text for downstream piping (no structured output).

Error Handling
- Unknown flags raise ValueError with a clear message.
- split with empty delimiter raises ValueError.
- cat --range missing start/length raises ValueError.

Design and Implementation Notes
- Add command handlers in src/loopy/shell.py.
- No core changes required for MVP; use tree.cat and string slicing.
- Parsing and error style should match existing shell commands.
- Add new commands to help output.

Medium-Level Tasks
- [x] Add head and tail command handlers with stdin support and -n parsing.
- [x] Add split command handler (delimiter string, stdin or path).
- [x] Extend cat to support --range start length (stdin or path).
- [x] Update help text to include head/tail/split and cat --range.
- [x] Add shell tests covering defaults, stdin piping, and edge cases.
- [x] Add docs/examples in README.md if command list is documented there.

Tests
- head: default 10 lines; -n 2; stdin piping.
- tail: default 10 lines; -n 2; stdin piping.
- split: delimiter on file; delimiter on stdin; preserves empty fields.
- cat --range: in-bounds slice; out-of-bounds returns empty; stdin slice.

Rollout
- MVP: head, tail, split, cat --range.
- Later: head -c, tail -c, tr alias, grep -o, cut.
