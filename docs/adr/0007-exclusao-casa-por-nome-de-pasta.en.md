*[Versão em português](0007-exclusao-casa-por-nome-de-pasta.md)*

# The Exclusion matches by folder name, at any depth

The multiselect offered folders the filter was incapable of excluding. `get_unique_folders`
collected every segment of the path, at any depth; `is_path_in_ignored_folders` matched only
from the root. Anything not at the first level was offered in the UI and ignored by the
filter: the user marked `tests`, nothing complained, and the files kept being audited (issue
#26).

An **Exclusion is a folder's name, and holds at any depth**. Marking `tests` excludes
`tests/` and `src/tests/`. The two functions come to talk about the same thing, which is what
guarantees the missing property: no offered folder fails to exclude. A file whose name
coincides with the Exclusion is not excluded — an Exclusion is a folder, not a path.

The accepted cost is that two folders of the same name at different levels stop being
distinguishable: whoever marks `tests` cannot exclude `src/tests` while keeping `tests/`. In
exchange, the UI stops lying, and whoever downloads the Target Project from GitHub can exclude
`tests` — which the root-anchored semantics did not allow, because "Download ZIP" wraps
everything in `<repo>-<branch>/`.

Orthogonal and also adopted: the wrapper folder **disappears in the normalisation** of the
file source (ADR-0006), before any filtering. This was not optional — without peeling it off,
the same project audited as a directory and as a ZIP would give different reports, and
ADR-0001 requires that they give the same.

Rejected: **offering only what the filter knows how to match**, keeping the root-anchored
semantics. Either the UI would offer only the first level — and a project in `src/` layout
could not exclude `src/tests` without excluding all of `src`, losing all the code —, or it
would offer full relative paths, trading short names for a long list and still not resolving
the wrapper on its own.
