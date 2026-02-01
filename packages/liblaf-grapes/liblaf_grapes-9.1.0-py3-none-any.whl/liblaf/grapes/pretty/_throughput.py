import about_time


def pretty_throughput(value: float, unit: str = "") -> str:
    """.

    Examples:
        >>> pretty_throughput(1234, "it")
        '1.2kit/s'
    """
    throughput: about_time.HumanThroughput = about_time.HumanThroughput(value, unit)
    return throughput.as_human()
