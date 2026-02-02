# Python Project Mask File


## clean

> This command cleans the build artifacts

```bash
rm -rf dist/
rm -rf build/
rm -rf .nox/
rm -rf htmlcov/
rm -rf target/
find src -name "*.so" -delete
rm -rf .coverage*
rm -rf Cargo.lock
```

## build [clean]

> This command builds the project via uv

```bash
if [ -n "$clean" ]; then
    $MASK clean
fi
NOT_IN_WORKFLOW="true" unbuffer uv build --wheel --no-build-isolation 2>&1 | grep -v "Building wheel" 1>&2
```

## ruff

> Fix linting issues with ruff

```bash
nox -s ruff_fix
```

## ty

> Run type checking with Ty (Astral's Type Checker)

```bash
nox -s ty
```

## test

> This command runs the tests using nox

```bash
nox -s tests
```

## check

> Run all quality checks (lint + typecheck + test)

```bash
$MASK ruff
$MASK ty
$MASK test
```

## bump (patch_version)

> Bump the version of the local project specifying the patch level: `minor`, `major`, `patch`. This will trigger a release on PyPi.

```bash
uv sync
path_to_script=build-cub
current_version=$(${path_to_script} version)
echo "Current version: ${current_version}"
if [ -z "${patch_version}" ]; then
    echo "Please specify a patch version: minor, major, or patch"
    exit 1
fi
if [ "${patch_version}" != "minor" ] && [ "${patch_version}" != "major" ] && [ "${patch_version}" != "patch" ]; then
    echo "Invalid patch version specified. Use minor, major, or patch."
    exit 1
fi
if [ -z "${current_version}" ]; then
    echo "Current version is not set. Please run '${path_to_script} version' first."
    exit 1
fi
new_version=$(${path_to_script} bump "${patch_version}")
if [ $? -ne 0 ]; then
    echo "Failed to bump version. Please check the current version and try again."
    exit 1
fi
if [ -z "${new_version}" ]; then
    echo "Failed to bump version. Please check the current version and try again."
    exit 1
fi
echo "New version: ${new_version}"  
git tag -a "v${new_version}" -m "Bump version to v${new_version}"
git push origin "v${new_version}"
```

<!-- NOT NEEDED if we are publishing correctly. Needed for some broken situations. -->
<!-- ## publish (publish_location)

> This command publishes the package to a local repository! Isn't that great?

```bash
if [ "${publish_location}" = "twine" ]; then
    source .venv/bin/activate && twine upload -r local dist/* # uploads to a local repository
else
    export UV_PUBLISH_TOKEN=$(op read "op://Private/PyPI Prod/api_key")
    uv publish --index pypi dist/* --token $UV_PUBLISH_TOKEN
fi
```

 ## publish_test

> Publish to TestPyPI for practicing the release flow

```bash
export UV_PUBLISH_TOKEN=$(op read "op://Private/PyPI Test/api_key")
uv publish --index https://test.pypi.org/simple/ dist/* --token $UV_PUBLISH_TOKEN
```

## full (patch_version) (publish_location)

> This command runs the full build and publish process

```bash
$MASK clean
$MASK bump ${patch_version}
$MASK build
$MASK publish ${publish_location}
``` -->
