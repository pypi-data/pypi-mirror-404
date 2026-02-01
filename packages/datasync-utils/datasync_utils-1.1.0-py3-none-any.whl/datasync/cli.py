import typer
from datasync.core import DataSync

app = typer.Typer(help="DVC-based S3 data synchronization tool")


@app.command()
def init(s3_url: str, remote_name: str = "storage"):
    DataSync.init(s3_url, remote_name)


@app.command()
def pull(remote_name: str = None):
    DataSync(remote_name).pull()


@app.command()
def push(
    filepath: str,
    remote_name: str = None,
    message: str = "Update data",
):
    DataSync(remote_name).push(filepath, message)

@app.command()
def import_data(
    filepath: str,
    repo_url: str,
    message: str,
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite the existing local files"),
    remote_name: str = None
):
    DataSync(remote_name).import_data(repo_url, filepath, force)

@app.command()
def list(
    remote_name: str = None
):
    DataSync(remote_name).list()

def main():
    app()


if __name__ == "__main__":
    main()
