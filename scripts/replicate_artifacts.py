import csv
import subprocess as sp
from pathlib import Path
from typing import NamedTuple
from datetime import datetime


PROJECTS_CSV = Path("projects.csv")
VERSIONS_CSV = Path("versions.csv")
PROJECTS_DIR = Path("projects")
DEPS_DIR = Path("deps")
DBS_DIR = Path("dbs")
DEPENDS_JAR = Path("external", "depends.jar")
COCHANGE_TOOL_BIN = Path("external", "cochange-tool")


class Project(NamedTuple):
    name: str
    url: str


class Version(NamedTuple):
    tag: str
    hash: str
    date: datetime


def parse_date(date: str) -> datetime:
    return datetime.fromisoformat(date)


def get_project_path(project_name: str) -> Path:
    return Path(PROJECTS_DIR, project_name)


def get_db_path(project_name: str) -> Path:
    return Path(DBS_DIR, f"{project_name}.db")


def get_dep_path(project_name: str) -> Path:
    return Path(DEPS_DIR, f"{project_name}-deps-structure.json")


def load_projects() -> list[Project]:
    with open(PROJECTS_CSV) as file:
        return [Project(r[0], r[1]) for r in csv.reader(file)]


def load_versions() -> dict[str, Version]:
    with open(VERSIONS_CSV) as file:
        return {r[0]: Version(r[1], r[2], parse_date(r[3])) for r in csv.reader(file)}


def load_project_versions() -> list[tuple[Project, Version]]:
    versions = load_versions()
    return [(p, versions[p.name]) for p in load_projects()]


def clone(project: Project):
    print(f"Cloning {project.name}...")
    sp.run(["git", "clone", project.url, get_project_path(project.name)])


def checkout(project: Project, version: Version):
    print(f"Switching {project.name} to {version.tag} ({version.hash})")
    args = ["git", "-c", "advice.detachedHead=false", "checkout", version.tag]
    sp.run(args, cwd=get_project_path(project.name))


def dump_deps(project: Project):
    print(f"Extracting dependency info from {project.name}")
    DEPS_DIR.absolute().mkdir(parents=True, exist_ok=True)
    args = [
        "java",
        "-Xmx12G",
        "-jar",
        DEPENDS_JAR.absolute(),
        "java",
        ".",
        f"{project.name}-deps",
        f"--dir={DEPS_DIR.absolute()}",
        "--detail",
        "--output-self-deps",
        "--granularity=structure",
        "--namepattern=unix",
        "--strip-leading-path",
    ]
    sp.run(args, cwd=get_project_path(project.name))


def dump_cochange_db(project: Project, version: Version, years: int):
    print(f"Dumping cochange info into db for {project.name}...")
    db_path = get_db_path(project.name)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    since = str(version.date.replace(year=version.date.year - years).date())
    args = [
        COCHANGE_TOOL_BIN,
        "dump",
        "--db",
        str(db_path),
        "--repo",
        get_project_path(project.name),
        "--since",
        since,
        version.tag,
    ]
    sp.run(args)


def add_deps_to_db(project: Project, version: Version):
    print(f"Adding deps to the db of {project.name}...")
    db_path = get_db_path(project.name)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        COCHANGE_TOOL_BIN,
        "add-deps",
        "--db",
        str(db_path),
        "--commit",
        version.hash,
        "--dep-file",
        str(get_dep_path(project.name))
    ]
    sp.run(args)


if __name__ == "__main__":
    for project, version in load_project_versions():
        clone(project)
        checkout(project, version)
        dump_deps(project)
        dump_cochange_db(project, version, years=3)
        add_deps_to_db(project, version)