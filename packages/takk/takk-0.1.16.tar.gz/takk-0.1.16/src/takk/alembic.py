import ast
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from pathlib import Path


class Revision(BaseModel):
    file_path: str
    revision_id: str
    down_revision: str | None
    branch_labels: list[str] | None
    depends_on: list[str] | None

    created_at: datetime
    name: str
    code: str

    upgrade_ops: list[str] = Field(default_factory=list)
    downgrade_ops: list[str] = Field(default_factory=list)


def ops_from_node(node: ast.stmt, module_name: str) -> list[str]:
    ops = []

    if isinstance(node, ast.Expr):
        if isinstance(node.value, ast.Call):
            val = node.value
            if isinstance(val.func, ast.Attribute):
                if isinstance(val.func.value, ast.Name):
                    name = val.func.value.id
                    if name == module_name:
                        ops.append(val.func.attr)


    elif hasattr(node, "body"):
        for sub in node.body:
            ops.extend(ops_from_node(sub, module_name))

    return ops


def revisions_at(directory: Path, root_dir: Path) -> list[Revision]:
    revisions: list[Revision] = []
    files = directory.glob("*.py")

    for file in files:
        code = file.read_text()
        tree = ast.parse(code)

        module_name = "op"

        context = None

        revision = Revision(
            file_path=file.relative_to(root_dir).as_posix(),
            revision_id="",
            down_revision=None,
            branch_labels=None,
            depends_on=None,
            created_at=datetime.now(tz=timezone.utc),
            name="",
            code=code
        )

        for sub in tree.body:

            if isinstance(sub, ast.Expr):
                if context is None and isinstance(sub.value, ast.Constant) and isinstance(sub.value.value, str):
                    revision.name = sub.value.value.splitlines()[0]
                    context = sub.value.value

            elif isinstance(sub, ast.ImportFrom):
                if sub.module == "alembic":
                    for mod in sub.names:
                        if mod.name == "op":
                            module_name = mod.asname or mod.name

            elif isinstance(sub, ast.FunctionDef):
                if sub.name == "upgrade":
                    revision.upgrade_ops = ops_from_node(sub, module_name)
                elif sub.name == "downgrade":
                    revision.downgrade_ops = ops_from_node(sub, module_name)

            elif isinstance(sub, ast.Assign):
                if isinstance(sub.value, ast.Constant):
                    if len(sub.targets) == 1 and isinstance(sub.targets[0], ast.Name):
                        var_name = sub.targets[0].id
                        match var_name:
                            case "revision":
                                revision.revision_id = sub.value.value
                            case "down_revision":
                                revision.down_revision = sub.value.value
                            case "branch_labels":
                                revision.branch_labels = sub.value.value
                            case "depends_on":
                                revision.depends_on = sub.value.value

        revisions.append(revision)
    return revisions


def revisions_for_alembic_config(path: Path) -> list[Revision]:
    
    script_location = None
    for file in path.read_text().splitlines():
        if file.lstrip().startswith("script_location"):
            script_location = file.split("=")[-1].strip()
            break

    if not script_location:
        return []

    return revisions_at(path.parent / script_location / "versions", path.parent)

