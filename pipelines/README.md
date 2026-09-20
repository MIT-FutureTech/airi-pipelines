# Information Processing Pipelines

## Creating a New Pipeline

```bash
mkdir my-new-pipeline/
cd my-new-pipeline/
uv init --app --package --no-pin-python
uv add toolbox
# Add other dependencies as needed
```

### `basedpyright` setup

Create an empty `py.typed` file in the new project. This tells `basedpyright`
that the project contains type annotations. Without this, `basedpyright` may
complain about missing stubs.

```bash
touch src/my_new_pipeline/py.typed
```

Also add your new pipeline to the `executionEnvironments` in
[the root `pyproject.toml` file](/pyproject.toml) within the
`[tool.basedpyright]` section. This tells `basedpyright` that test code is
allowed to access private attributes of objects.

```diff
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -33,9 +33,11 @@
 executionEnvironments = [
     # Tests are allowed to access private attributes
     { root = "toolbox-lib/tests", reportPrivateUsage = false },
     { root = "pipelines/risk-repository/tests", reportPrivateUsage = false },
+    { root = "pipelines/my-new-pipeline/tests", reportPrivateUsage = false },
 ]
```
