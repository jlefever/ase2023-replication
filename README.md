# ASE 2023 Replication Package

The package includes two base files: `projects.csv` and `versions.csv`. These files are used by scripts in `scripts/` to derive the rest of the artifacts needed to replicate our results.

- The `projects.csv` provides a name and a git url for the projects that we used as subjects for our experiments.

- The `versions.csv` provides the versions used for these projects. Each project has both a tag name, an explicit commit hash, and a date.

## FAQ

### How did we select projects?

We selected projects maintained by Android and Apache that are written primarily in Java and that are currently undergoing active development.

### How did we determine which version of each project to use?

For each project, we manually ran
```
git log --no-walk --tags --format=fuller --decorate=full --date=iso --date-order
```
and chose a recently tagged release.
