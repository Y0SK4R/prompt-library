"""SQLite storage for prompts, categories, tags, and recoverable trash."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import Category, Prompt

SAMPLE_PROMPTS = (
    ("Explain a concept", "A sample prompt you can edit or delete.", "Explain {{concept}} clearly for a curious beginner. Use one concrete example and define any technical terms."),
    ("Review code", "A sample prompt for thoughtful code review.", "Review the code below for correctness, security, and maintainability. List findings by severity and include a concise fix for each.\n\n{{code}}"),
    ("Brainstorm options", "A sample prompt for structured ideation.", "Generate {{count}} distinct ideas for {{goal}}. For each, include the benefit, main tradeoff, and a practical first step."),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_data_path(app_name: str = "PromptLibrary") -> Path:
    """Return the platform's per-user application data location."""
    import os
    import sys

    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / app_name / "prompts.sqlite3"


class PromptStore:
    """A small SQLite repository. The connection is owned by the calling thread."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else default_data_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("PRAGMA journal_mode = WAL")
        self.initialize()

    def close(self) -> None:
        self._db.close()

    def initialize(self) -> None:
        with self._db:
            self._db.executescript("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
                    body TEXT NOT NULL, category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                    favorite INTEGER NOT NULL DEFAULT 0 CHECK(favorite IN (0,1)),
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL, deleted_at TEXT
                );
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE
                );
                CREATE TABLE IF NOT EXISTS prompt_tags (
                    prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
                    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                    PRIMARY KEY(prompt_id, tag_id)
                );
                CREATE INDEX IF NOT EXISTS prompts_updated_idx ON prompts(updated_at DESC);
                CREATE INDEX IF NOT EXISTS prompts_deleted_idx ON prompts(deleted_at);
                INSERT OR IGNORE INTO categories(name, created_at) VALUES ('Uncategorized', '1970-01-01T00:00:00+00:00');
            """)

    def seed_samples(self) -> int:
        """Insert starter records only into a truly empty prompt collection."""
        if self._db.execute("SELECT 1 FROM prompts LIMIT 1").fetchone():
            return 0
        now = _now()
        with self._db:
            self._db.executemany(
                "INSERT INTO prompts(title,description,body,created_at,updated_at) VALUES(?,?,?,?,?)",
                [(title, desc, body, now, now) for title, desc, body in SAMPLE_PROMPTS],
            )
        return len(SAMPLE_PROMPTS)

    def list_categories(self) -> list[Category]:
        rows = self._db.execute("SELECT * FROM categories ORDER BY name COLLATE NOCASE").fetchall()
        return [Category(r["id"], r["name"], r["created_at"]) for r in rows]

    def add_category(self, name: str) -> Category:
        name = self._clean_name(name, "category")
        with self._db:
            cur = self._db.execute("INSERT INTO categories(name,created_at) VALUES(?,?)", (name, _now()))
        row = self._db.execute("SELECT * FROM categories WHERE id=?", (cur.lastrowid,)).fetchone()
        return Category(row["id"], row["name"], row["created_at"])

    def save_prompt(self, *, title: str, body: str, description: str = "", category_id: int | None = None,
                    tags: Iterable[str] = (), favorite: bool = False, prompt_id: int | None = None) -> Prompt:
        title = self._clean_name(title, "title")
        if not isinstance(body, str):
            raise ValueError("body must be text")
        if not isinstance(description, str):
            raise ValueError("description must be text")
        tag_names = tuple(dict.fromkeys(self._clean_name(t, "tag") for t in tags if str(t).strip()))
        now = _now()
        with self._db:
            if category_id is not None and not self._db.execute("SELECT 1 FROM categories WHERE id=?", (category_id,)).fetchone():
                raise ValueError("category does not exist")
            if prompt_id is None:
                cur = self._db.execute("INSERT INTO prompts(title,description,body,category_id,favorite,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                                       (title, description, body, category_id, int(favorite), now, now))
                prompt_id = cur.lastrowid
            else:
                cur = self._db.execute("UPDATE prompts SET title=?,description=?,body=?,category_id=?,favorite=?,updated_at=? WHERE id=? AND deleted_at IS NULL",
                                       (title, description, body, category_id, int(favorite), now, prompt_id))
                if not cur.rowcount:
                    raise ValueError("active prompt does not exist")
                self._db.execute("DELETE FROM prompt_tags WHERE prompt_id=?", (prompt_id,))
            for name in tag_names:
                self._db.execute("INSERT OR IGNORE INTO tags(name) VALUES(?)", (name,))
                self._db.execute("INSERT INTO prompt_tags(prompt_id,tag_id) SELECT ?,id FROM tags WHERE name=?", (prompt_id, name))
        return self.get_prompt(prompt_id)

    @staticmethod
    def _clean_name(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must not be empty")
        return value.strip()

    def get_prompt(self, prompt_id: int, *, include_deleted: bool = False) -> Prompt:
        sql = "SELECT * FROM prompts WHERE id=?" + ("" if include_deleted else " AND deleted_at IS NULL")
        row = self._db.execute(sql, (prompt_id,)).fetchone()
        if row is None:
            raise KeyError(prompt_id)
        tags = tuple(r[0] for r in self._db.execute("SELECT t.name FROM tags t JOIN prompt_tags pt ON pt.tag_id=t.id WHERE pt.prompt_id=? ORDER BY t.name COLLATE NOCASE", (prompt_id,)))
        return Prompt(row["id"], row["title"], row["description"], row["body"], row["category_id"], tags,
                      bool(row["favorite"]), row["created_at"], row["updated_at"], row["deleted_at"])

    def list_prompts(self, *, include_deleted: bool = False, search: str = "", category_id: int | None = None,
                     favorite: bool | None = None) -> list[Prompt]:
        clauses, args = [], []
        clauses.append("p.deleted_at IS NOT NULL" if include_deleted else "p.deleted_at IS NULL")
        if category_id is not None:
            clauses.append("p.category_id=?"); args.append(category_id)
        if favorite is not None:
            clauses.append("p.favorite=?"); args.append(int(favorite))
        if search.strip():
            clauses.append("(p.title LIKE ? OR p.description LIKE ? OR p.body LIKE ? OR EXISTS(SELECT 1 FROM prompt_tags pt JOIN tags t ON t.id=pt.tag_id WHERE pt.prompt_id=p.id AND t.name LIKE ?))")
            pattern = f"%{search.strip()}%"; args.extend([pattern] * 4)
        ids = [r[0] for r in self._db.execute("SELECT p.id FROM prompts p WHERE " + " AND ".join(clauses) + " ORDER BY p.updated_at DESC,p.id DESC", args)]
        return [self.get_prompt(pid, include_deleted=include_deleted) for pid in ids]

    def trash(self, prompt_id: int) -> None:
        with self._db:
            cur = self._db.execute("UPDATE prompts SET deleted_at=?,updated_at=? WHERE id=? AND deleted_at IS NULL", (_now(), _now(), prompt_id))
            if not cur.rowcount:
                raise KeyError(prompt_id)

    def restore(self, prompt_id: int) -> None:
        with self._db:
            cur = self._db.execute("UPDATE prompts SET deleted_at=NULL,updated_at=? WHERE id=? AND deleted_at IS NOT NULL", (_now(), prompt_id))
            if not cur.rowcount:
                raise KeyError(prompt_id)

    def export_json(self) -> str:
        """Serialize active prompts and categories as a versioned portable backup."""
        categories = [{"id": c.id, "name": c.name, "created_at": c.created_at} for c in self.list_categories()]
        prompts = []
        for p in self.list_prompts():
            prompts.append({"id": p.id, "title": p.title, "description": p.description, "body": p.body,
                            "category_id": p.category_id, "tags": list(p.tags), "favorite": p.favorite,
                            "created_at": p.created_at, "updated_at": p.updated_at})
        return json.dumps({"format": "prompt-library-backup", "version": 1, "categories": categories, "prompts": prompts}, ensure_ascii=False, indent=2)

    def import_json(self, content: str) -> int:
        """Validate the whole backup before transactionally adding records; IDs are remapped."""
        try:
            data = json.loads(content)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid JSON backup") from exc
        if not isinstance(data, dict) or data.get("format") != "prompt-library-backup" or data.get("version") != 1:
            raise ValueError("unsupported backup format or version")
        categories, prompts = data.get("categories"), data.get("prompts")
        if not isinstance(categories, list) or not isinstance(prompts, list):
            raise ValueError("backup categories and prompts must be lists")
        cat_names: set[str] = set()
        cat_ids: set[int] = set()
        for c in categories:
            if (not isinstance(c, dict)
                    or isinstance(c.get("id"), bool)
                    or not isinstance(c.get("id"), int)
                    or not isinstance(c.get("name"), str)
                    or not c["name"].strip()):
                raise ValueError("invalid category record")
            if c["id"] in cat_ids:
                raise ValueError("duplicate category ID")
            cat_ids.add(c["id"])
            key = c["name"].strip().casefold()
            if key in cat_names: raise ValueError("duplicate category name")
            cat_names.add(key)
        for p in prompts:
            if not isinstance(p, dict) or not all(isinstance(p.get(k), str) for k in ("title", "description", "body")) or not p["title"].strip():
                raise ValueError("invalid prompt record")
            if not isinstance(p.get("tags"), list) or not all(isinstance(t, str) and t.strip() for t in p["tags"]):
                raise ValueError("invalid prompt tags")
            if not isinstance(p.get("favorite"), bool): raise ValueError("invalid favorite value")
            category_id = p.get("category_id")
            if category_id is not None and (isinstance(category_id, bool) or not isinstance(category_id, int) or category_id not in cat_ids):
                raise ValueError("prompt references an unknown category")
        now = _now(); count = 0
        try:
            with self._db:
                category_map: dict[int, int] = {}
                for c in categories:
                    old_id = c.get("id")
                    existing = self._db.execute("SELECT id FROM categories WHERE name=?", (c["name"].strip(),)).fetchone()
                    if existing:
                        category_map[old_id] = existing[0]
                    else:
                        cur = self._db.execute("INSERT INTO categories(name,created_at) VALUES(?,?)", (c["name"].strip(), c.get("created_at") or now))
                        category_map[old_id] = cur.lastrowid
                for p in prompts:
                    cur = self._db.execute("INSERT INTO prompts(title,description,body,category_id,favorite,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                        (p["title"].strip(), p["description"], p["body"], category_map.get(p.get("category_id")), int(p["favorite"]), p.get("created_at") or now, p.get("updated_at") or now))
                    for name in dict.fromkeys(t.strip() for t in p["tags"]):
                        self._db.execute("INSERT OR IGNORE INTO tags(name) VALUES(?)", (name,))
                        self._db.execute("INSERT INTO prompt_tags(prompt_id,tag_id) SELECT ?,id FROM tags WHERE name=?", (cur.lastrowid, name))
                    count += 1
        except sqlite3.Error as exc:
            raise ValueError("backup could not be imported") from exc
        return count

    def export_markdown(self, prompt_ids: Iterable[int] | None = None) -> str:
        """Export selected active prompts as readable Markdown, preserving body text."""
        prompts = self.list_prompts()
        if prompt_ids is not None:
            selected = set(prompt_ids)
            prompts = [p for p in prompts if p.id in selected]
        blocks = []
        for p in prompts:
            tags = f"\n\nTags: {', '.join(p.tags)}" if p.tags else ""
            description = f"\n\n{p.description}" if p.description else ""
            blocks.append(f"# {p.title}{description}\n\n{p.body}{tags}")
        return "\n\n---\n\n".join(blocks)
