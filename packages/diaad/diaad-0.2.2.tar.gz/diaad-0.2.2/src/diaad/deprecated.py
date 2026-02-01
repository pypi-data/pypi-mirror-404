def main():
    import warnings
    warnings.warn(
        "DIAAD has been renamed to TAALCR. "
        "Please install and use the 'taalcr' package instead.",
        DeprecationWarning,
    )
    print(
        "DIAAD is deprecated.\n"
        "See: https://github.com/nmccloskey/TAALCR"
    )
