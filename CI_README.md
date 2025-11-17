CI setup for dbt build and artifact-based test coverage

This repository includes two GitHub Actions workflows:

- `.github/workflows/test-coverage.yml` — Artifact-based check that runs `python test-coverage.py` against `target/manifest.json` and `target/run_results.json`. Use this for PRs that include compiled dbt artifacts.

- `.github/workflows/dbt-build.yml` — Full CI workflow that runs `dbt deps` and `dbt build` in the workflow runner. It requires a `profiles.yml` to be provided via the `DBT_PROFILES_YML` repository secret.

How to configure `DBT_PROFILES_YML` (recommended)

1. Locally, create a `profiles.yml` that contains your profile and target with credentials. Example (Databricks adapter snippet):

```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: databricks
      catalog: my_catalog
      schema: my_schema
      host: <your-databricks-host>
      http_path: <your-http-path>
      token: <your-token>
      threads: 1
```

2. Copy the entire contents of your `profiles.yml` file and add it as a GitHub repository secret named `DBT_PROFILES_YML`.

Notes and security

- Storing the entire `profiles.yml` as a single secret is often simpler than storing multiple secrets and templating. The secret is masked in logs.
- If you prefer finer-grained control, you can store individual credentials (e.g., `DATABRICKS_HOST`, `DATABRICKS_TOKEN`) and modify the workflow to render a `profiles.yml` from those secrets.

Local testing tips

- To test locally, create `~/.dbt/profiles.yml` with your profile and run:

```bash
python -m venv venv
venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
dbt deps --profiles-dir ~/.dbt
dbt build --profiles-dir ~/.dbt
```

CI artifacts

- The `dbt-build.yml` workflow uploads the `target/` directory as an artifact (named `dbt-target`). The lightweight `test-coverage.yml` workflow expects `target/manifest.json` and `target/run_results.json` to exist and will fail if they are missing.

If you want, I can:
- Add an example script that renders `profiles.yml` from separate secrets,
- Add caching for `pip` and dbt packages to speed up CI,
- Add a matrix job to run multiple adapters.
