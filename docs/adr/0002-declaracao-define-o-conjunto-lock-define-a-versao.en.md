*[Versão em português](0002-declaracao-define-o-conjunto-lock-define-a-versao.md)*

# The Declaration defines the set, the Lock defines the version

The Declaration (`pyproject.toml`, `requirements.txt`) says **which** packages are direct but
rarely pins a version (`pandas>=3.0.1`); the Lock (`uv.lock`, `poetry.lock`) says **at which
version** everything resolved, but also lists hundreds of transitives. Each file answers half
the question, so we read both: the Declaration forms the audited set (Zombies/Ghosts) and the
Lock, when it exists, resolves the Used Version of each item in the set (Age/Size/Outdated).

Why record this: it is tempting to simplify to "just read the Lock, it has the name and
version of everything". That is what `_find_dependency_file` effectively did, by returning the
first file that matched — in a uv project this read `uv.lock` and reported every transitive as
a Zombie, because none of them is imported by the code. The Lock is **not** a source of the
set.

Consequence: without a Lock, the Used Version of an unpinned dependency is unknown — Age and
Size become unavailable for it. We prefer that to inventing a version. In particular, the
current behaviour of `outdated_analizer.py`, which copies the PyPI version into `Versão Atual`
when there is no declared version and marks it "Up to date", is wrong by this ruler: it
reports as up to date something whose version is not known.
