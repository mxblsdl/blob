import requests


# Code to interact with API from a python script
# TODO this would need to be reworked based on the user parameter
def upload_file(path: str) -> None:
    file = {"file": (path, open(path, "rb"))}
    response = requests.post("http://127.0.0.1:8000/upload/", files=file)
    return response.json()


def list_files() -> list[str]:
    res = requests.get("http://127.0.0.1:8000/files/max")
    if res.ok:
        filenames = res.json()
        return [f["filename"] for f in filenames["files"]]


print(list_files())
