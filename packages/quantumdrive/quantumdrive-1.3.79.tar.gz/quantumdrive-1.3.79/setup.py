#!/usr/bin/env python
import os
import subprocess
from setuptools import setup, find_packages

def get_version():
    try:
        # Get the full git description (e.g., v1.3.44 or v1.3.44-5-g1234567)
        version_str = subprocess.check_output(
            ["git", "describe", "--tags"],
            stderr=subprocess.STDOUT
        ).decode().strip()
        
        # Remove 'v' prefix if present
        if version_str.startswith('v'):
            version_str = version_str[1:]
        
        final_version = version_str
        
        # Check if we are ahead of the tag (e.g., 1.3.44-5-g1234567)
        if '-' in version_str:
            parts = version_str.split('-')
            if len(parts) >= 3:
                tag = parts[0]
                distance = parts[1]
                # commit_hash = parts[2]  # Unused for PyPI public releases
                
                # Construct PEP 440 compliant public post-release version
                # e.g., 1.3.44.post5 (Local version segments like +g123456 are rejected by PyPI)
                final_version = f"{tag}.post{distance}"
        
        # Write version to file so it's included in sdist and available
        # when building wheel from sdist (where .git is missing)
        with open(os.path.join(os.path.dirname(__file__), 'VERSION'), 'w') as vf:
            vf.write(final_version)
            
        return final_version
        
    except subprocess.CalledProcessError:
        # Fallback to VERSION file if present (for sdist installs without .git)
        version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
        if os.path.exists(version_file):
            with open(version_file, 'r') as vf:
                return vf.read().strip()
        return "0.0.0"

# read in requirements.txt, ignoring comments and blank lines
req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
if os.path.exists(req_file):
    with open(req_file, encoding="utf-8") as f:
        install_requires = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]
else:
    install_requires = []

# optionally read a README if you have one
long_description = ""
readme_file = os.path.join(os.path.dirname(__file__), "README.md")
if os.path.exists(readme_file):
    with open(readme_file, encoding="utf-8") as f:
        long_description = f.read()

packages = find_packages(
    include=[
        "agentfoundry",
        "agentfoundry.*",
        "core",
        "core.*",
        "webapp",
        "webapp.*",
    ],
    exclude=[
        "tests*",
        "demo*",
        "data*",
        "dist*",
        "logs*",
    ],
)

# Ensure namespace-only asset dirs under webapp are treated as packages to
# avoid setuptools warnings about importable-but-unlisted namespaces.
asset_packages = [
    "webapp.static",
    "webapp.static.css",
    "webapp.static.images",
    "webapp.static.js",
    "webapp.templates",
]

setup(
    # Distributed package name published to PyPI / internal index
    name="quantumdrive",
    # Keep the version in-sync with pyproject.toml to avoid confusion
    version=get_version(),
    author="Chris Steel",
    author_email="chris.steel@alphsix.com",
    description="QuantumDrive platform and SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # SPDX-compatible custom proprietary identifier
    license="LicenseRef-AlphSix-Proprietary",
    license_files=("LICENSE",),
    # The runtime Python import packages that should be included in the
    # distribution.  The project is published as `quantumdrive`, but the
    # actual import roots currently live under the `core` and `webapp`
    # directories.  We therefore include those while excluding assets and
    # test data that shouldn't be shipped.
    # Automatically discover python import packages rooted at the project
    # top-level while skipping directories that are not meant for
    # distribution (test suites, demos, large data bundles, etc.).
    packages=list(dict.fromkeys(packages + asset_packages)),
    install_requires=install_requires,
    python_requires=">=3.11,<3.14",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    entry_points={
        # if you later want to expose a CLI, you can add:
        # "console_scripts": [
        #     "agentforge-orch = agentforge.orchestrator:main",
        # ],
    },
)
