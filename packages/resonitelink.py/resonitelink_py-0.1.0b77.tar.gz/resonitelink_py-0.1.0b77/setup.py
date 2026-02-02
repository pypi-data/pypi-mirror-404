from setuptools import setup, find_namespace_packages
from typing import Union
import re


def derive_version() -> str:
    version = ''
    with open('resonitelink/__init__.py') as f:
        version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1) # type: ignore

    if not version:
        raise RuntimeError('version is not set')

    if version.endswith(('a', 'b', 'rc')):
        # Append version identifier based on commit count
        try:
            import os
            
            commit_count_suffix : Union[str, None] = None
            current_path = os.getcwd()

            git_dir = os.path.join(current_path, ".git/")
            if os.path.exists(git_dir):
                # We are in the git repository folder, we can retrieve the comit count via git command
                import subprocess
                
                p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                if out:
                    commit_count_suffix = out.decode('utf-8')
            
            if not commit_count_suffix:
                # Suffix not found via GIT or not in GIT directory.
                # Depending on the build step, it might already be present in the path though!
                escaped_version = re.escape(version)
                commit_count_suffix = re.search(r'(?:' + escaped_version + r')(\d*)', current_path).group(1) # type: ignore
            
            if not commit_count_suffix:
                raise RuntimeError("Version identifier needed, but unable to be determined!")

            version += commit_count_suffix.strip()
        
        except Exception as ex:
            print(f"EXCEPTION DERIVING VERSION: {ex}")

    return version

setup(
    version=derive_version(),
    py_modules=[ ], # All included modules / files defined via MANIFEST.in 
    packages=find_namespace_packages(include=[ "resonitelink", "resonitelink.*" ])
)
