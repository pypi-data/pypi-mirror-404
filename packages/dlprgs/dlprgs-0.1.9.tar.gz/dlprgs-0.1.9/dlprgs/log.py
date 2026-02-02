from importlib import resources

def print_file(id: str):
    filename = f"{id}.txt"

    try:
        with resources.files("dlprgs.data").joinpath(filename).open("r") as f:
            print(f.read())
    except FileNotFoundError:
        raise ValueError(f"No file found for id: {id}")
