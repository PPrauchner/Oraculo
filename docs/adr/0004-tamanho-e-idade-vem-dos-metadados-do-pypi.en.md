*[Versão em português](0004-tamanho-e-idade-vem-dos-metadados-do-pypi.md)*

# Size and Age come from PyPI metadata

The assignment requires Size and Age without defining of what. We define Size as the bytes of
the wheel (sdist as fallback) of the Used Version, and Age as today minus the `upload_time` of
that same version — both read from `releases[version]` in the `/pypi/NAME/json` response, the
same request that already brings the latest version. One request per package resolves all
three data points.

We chose metadata over measuring `site-packages` because ingestion is dual (ADR-0001): on-disk
size would be impossible in upload mode — the venv does not go in the ZIP — and impossible for
Ghosts, which are not even installed. One and the same package must give the same number in
both modes, otherwise the metric means nothing.

Consequence not to "fix": Size is not the space taken on disk (the wheel is compressed) and
does not include transitives. As US-07 compares reports over time, changing this definition
later invalidates all history already exported.
