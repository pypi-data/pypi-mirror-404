try:
    import importlib.metadata

    __version__ = importlib.metadata.version("gist_neko")

except importlib.metadata.PackageNotFoundError:
    __version__ = "1.27"
