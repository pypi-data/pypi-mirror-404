# Contributing to BEEhaviourLab
First of all, thank you for your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

We have a [code of conduct](CODE_OF_CONDUCT.md) that describes how to participate in our community.

## Contributions

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests.

### Setting up your own local development environment

This project uses `pip` along with a `pyproject.toml` file for packaging and dependency management. As such, if you want to make your own changes to the code, it is suggested that you:

1. Create and activate a new Python environment using your favourite tool (e.g. conda or uv).
2. Fork the repo and then clone the forked repository to your machine.
3. `cd` to the repository directory and run `pip install -e ".[dev]"` to install the package and dependencies to your environment.
4. To run the tests use `pytest tests/`.
5. If you've added methods to the public API, make sure that docstrings have been added/updated.
6. Upload your changes to a new branch and issue a pull request :sparkles:. 

### License - Any contributions you make will be under the Apache Software License v2.0
In short, when you submit code changes, your submissions are understood to be under the same [Apache v2.0 License](LICENSE) that covers the project. Feel free to contact the maintainers if that's a concern.

## Reporting bugs

### Report bugs using GitHub's [issues](https://github.com/BEEhaviourLab/BEEhaviourLab/issues)
We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/BEEhaviourLab/BEEhaviourLab/issues/new/choose).

### Write bug reports with detail, background, and sample code

**Good Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)


## References
This document was adapted from the open-source contribution guidelines for [Transcriptase](https://gist.github.com/briandk/3d2e8b3ec8daf5a27a62) which were in turn adapted from [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md)
