from __future__ import annotations

from naive_svg import *  # noqa: F403

# TODO, same sample code

if __name__ == "__main__":
    import fire

    fire.core.Display = lambda lines, out: print(*lines, file=out)  # no pager for fire
    fire.Fire()
