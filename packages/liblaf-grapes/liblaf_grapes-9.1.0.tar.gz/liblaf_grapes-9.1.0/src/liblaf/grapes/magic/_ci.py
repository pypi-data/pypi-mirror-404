from environs import env


def in_ci() -> bool:
    return env.bool("CI", False)
