import os
import sys
import subprocess
import shlex
import shutil
from urllib.parse import urlparse


class DataSync:
    """
    Unified DVC-based data synchronization helper for local environments,
    Jupyter notebooks, and Google Colab.
    """

    def __init__(self, remote_name=None):
        """
        Initialize the DataSync helper.

        Args:
            remote_name (str | None): Optional DVC remote name.
        """
        self.remote_name = remote_name
        self._setup_environment()

    def _in_colab(self):
        """
        Detect whether the current runtime is Google Colab.
        """
        return "google.colab" in sys.modules

    def _setup_environment(self):
        """
        Prepare runtime environment and credentials.
        """
        if self._in_colab():
            self._load_colab_secrets()
            self._ensure_dvc()
        else:
            self._ensure_aws_credentials()

    def _load_colab_secrets(self):
        """
        Load AWS credentials from Google Colab Secrets.
        """
        from google.colab import userdata

        for key, default in [
            ("AWS_ACCESS_KEY_ID", None),
            ("AWS_SECRET_ACCESS_KEY", None),
            ("AWS_DEFAULT_REGION", "eu-north-1"),
        ]:
            try:
                value = userdata.get(key)
                if value:
                    os.environ[key] = value
                elif default:
                    os.environ[key] = default
            except Exception:
                if default:
                    os.environ[key] = default

    def _ensure_aws_credentials(self):
        """
        Ensure AWS credentials exist in non-Colab environments.
        """
        if "AWS_ACCESS_KEY_ID" not in os.environ and not os.path.exists(
            os.path.expanduser("~/.aws/credentials")
        ):
            raise RuntimeError(
                "AWS credentials not found. "
                "Set environment variables or ~/.aws/credentials."
            )

    def _ensure_dvc(self):
        """
        Ensure DVC with S3 support is installed.
        """
        try:
            subprocess.check_call(
                ["dvc", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "dvc[s3]"],
                stdout=subprocess.DEVNULL,
            )

        if not shutil.which("dvc"):
            raise RuntimeError("DVC installed but not found in PATH.")

    def _run(self, cmd):
        """
        Execute a command safely.
        """
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        subprocess.check_call(cmd)

    def _ensure_remote(self):
        """
        Ensure the requested DVC remote exists.
        """
        result = subprocess.check_output(["dvc", "remote", "list"]).decode()
        if self.remote_name:
            if self.remote_name not in result:
                raise RuntimeError(f"DVC remote '{self.remote_name}' not found.")
        elif not result.strip():
            raise RuntimeError("No DVC remote configured.")

    @classmethod
    def init(cls, s3_url, remote_name="storage"):
        """
        Initialize DVC and configure a default S3 remote.

        Args:
            s3_url (str): Existing S3 bucket or prefix.
            remote_name (str): Name of the DVC remote.
        """
        try:
            subprocess.check_call(
                ["dvc", "status"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            subprocess.check_call(["dvc", "init"], stdout=subprocess.DEVNULL)

        subprocess.check_call(
            ["dvc", "remote", "add", "-f", "-d", remote_name, s3_url]
        )

    def pull(self):
        """
        Pull data from the configured DVC remote.
        """
        self._ensure_remote()
        if self.remote_name:
            self._run(["dvc", "pull", "-r", self.remote_name])
        else:
            self._run(["dvc", "pull"])

    def push(self, filepath, message="Update data"):
        """
        Add a file to DVC and push it to remote storage.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        self._ensure_remote()
        self._run(["dvc", "add", filepath])

        if self.remote_name:
            self._run(["dvc", "push", "-r", self.remote_name])
        else:
            self._run(["dvc", "push"])

        if self._in_colab():
            return

        self._run(["git", "add", f"{filepath}.dvc", ".gitignore"])
        try:
            self._run(["git", "commit", "-m", message])
        except Exception as e:
            raise SystemError(e)
    
    def import_data(self, repo_url, filepath, force: bool=False, message="Import data from"):
        """
        import dvc data from any repo with dvc tracked files from a certain filepath in that repo (*.dvc files)
        """
        url = urlparse(repo_url)
        if not url.netloc and not url.scheme:
            raise ValueError(repo_url, "Not a valid repo_url URL")
        
        self._ensure_remote()
        
        # possibly overwrite the local file
        if force:
            self._run(["dvc", "import", repo_url, filepath, "--force"])
        else:
            self._run(["dvc", "import", repo_url, filepath])

        self._run(["git", "add", f"{filepath}.dvc", ".gitignore"])

        message = " ".join([message, repo_url])
        
        try:
            self._run(["git", "commit", "-m", message])
        except Exception as e:
            raise SystemError(e)

    def list(self, git_url):
        
        self._ensure_remote()

        url = urlparse(git_url)
        
        if not url.netloc and not url.scheme:
            raise ValueError(git_url, "Not a valid repo_url URL")

        self._run(["dvc", "list", git_url, "--dvc-only"])