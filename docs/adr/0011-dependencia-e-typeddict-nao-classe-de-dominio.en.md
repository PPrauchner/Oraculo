*[Versão em português](0011-dependencia-e-typeddict-nao-classe-de-dominio.md)*

# The dependency is a `TypedDict`, not a domain class

Rule 01 of the assignment requires the **procedural paradigm: no domain classes**. This ADR
introduces `class Dependency(TypedDict)` and therefore needs to exist — whoever reads the code
without context will read this as a violation of the rule.

The trigger is the translation of the keys to English (ADR-0008): `Pacote` → `package`,
`Versão Usada` → `used_version`, and so on, in 383 occurrences spread across 25 files. A
mechanical rename of that scale, in a schema-less dictionary, is exactly the kind of change in
which a key slips — and a wrong key in a loose `dict` does not fail on the spot: it returns
`KeyError` in the middle of the UI, or worse, a `.get()` returns `None` and the report shows
blank without complaining.

**The dependency comes to be described by a `TypedDict`.** At runtime it stays a plain `dict`:
no instantiation, no `self`, no method, no behaviour. No business rule is moved into it —
whoever classifies a Zombie is still `zombie_analizer`, whoever computes Age is still
`pypi_client`. The functions keep receiving and returning dictionaries, and the pipeline stays
a sequence of transformations.

What Rule 01 forbids is modelling the domain in objects that carry state and behaviour — a
`Dependency` with `.is_zombie()` and `.age_in_days` would be the real violation, and that is
not what is being done. `TypedDict` uses the word `class` as type-declaration syntax, not as an
object constructor; it is erased at runtime and exists only for the type checker. The project
convention already requires type hints on every parameter and return — this is the same
requirement applied to the dictionary's shape, and not a change of paradigm.

The gain is known and immediate: during the rename, a mistyped key becomes a checking error,
not a runtime surprise. The 200 tests cover a lot, but they do not cover every key-reading path
in the UI, which is precisely where the loose `dict` fails silently.

Rejected: **constants for the key names** (`dep[KEY_PACKAGE]`). It catches the typo on the
spot, with no class syntax at all, and for that reason it was the most serious alternative. But
it pollutes the 383 read points with indirection, says nothing about the value's *type*, and
does not describe the record as a whole — there is no one place where it is written which
fields a dependency has.

Rejected: **keeping the loose `dict`**. It is the most conservative reading of Rule 01 and
costs nothing today, but it chooses to run the risk precisely on the change that creates it.
