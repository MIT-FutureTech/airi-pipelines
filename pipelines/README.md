# Information Processing Pipelines

## Creating a New Pipeline

```bash
mkdir my-new-pipeline/
cd my-new-pipeline/
uv init --app --package --no-pin-python
uv add toolbox
# Add other dependencies as needed
```

Then add your new pipeline to the `executionEnvironments` in
[the root `pyproject.toml` file](/pyproject.toml) within the
`[tool.basedpyright]` section.

```diff
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -33,9 +33,11 @@
 executionEnvironments = [
     # Add each pipeline to the search path for imports
     { root = "pipelines/risk-repository/src" },
+    { root = "pipelines/my-new-pipeline/src" },
     # Tests are allowed to access private attributes
     { root = "toolbox-lib/tests", reportPrivateUsage = false },
     { root = "pipelines/risk-repository/tests", reportPrivateUsage = false },
+    { root = "pipelines/my-new-pipeline/tests", reportPrivateUsage = false },
 ]
```

If you skip this step, my get errors from `basedpyright`.
