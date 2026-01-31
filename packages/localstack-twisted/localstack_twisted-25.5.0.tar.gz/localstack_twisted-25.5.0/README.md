# LocalStack Distribution of Twisted

This package re-distributes the unmodified twisted code for use in localstack.

## Build project

### Clone

Clone the repository with submodules

    git clone --recurse-submodules git@github.com:localstack/twisted-distribution

### Build

    python -m build

## Upgrade to latest tagged version

To check out the latest tag and update the submodule, you can run this:

```bash
cd ./twisted
git fetch --tags
git checkout "$(git describe --tags "$(git rev-list --tags --max-count=1)")"

cd ..
git add twisted
```
