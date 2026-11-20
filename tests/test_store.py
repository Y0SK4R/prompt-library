import json

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from prompt_library.data import PromptStore
from prompt_library.ui.main_window import MainWindow


def test_seed_persistence_filters_trash_and_restore(tmp_path):
    database = tmp_path / "prompts.sqlite3"
    store = PromptStore(database)
    assert store.seed_samples() == 3
    assert store.seed_samples() == 0
    category = store.add_category("QA")
    body = 'Unicode ñ 🌟\n\n```py\nprint("ok")\n```  '
    prompt = store.save_prompt(
        title="Boundary probe",
        description="needle description",
        body=body,
        category_id=category.id,
        tags=["special-tag"],
        favorite=True,
    )
    store.close()

    reopened = PromptStore(database)
    saved = reopened.get_prompt(prompt.id)
    assert saved.body == body
    assert saved.tags == ("special-tag",)
    assert saved.favorite is True
    assert saved.category_id == category.id
    assert [item.id for item in reopened.list_prompts(
        search="special-tag", category_id=category.id, favorite=True
    )] == [prompt.id]

    reopened.trash(prompt.id)
    assert prompt.id not in {item.id for item in reopened.list_prompts()}
    assert prompt.id in {item.id for item in reopened.list_prompts(include_deleted=True)}
    reopened.restore(prompt.id)
    assert reopened.get_prompt(prompt.id).body == body
    reopened.close()


def test_json_roundtrip_and_invalid_import_is_atomic(tmp_path):
    source = PromptStore(tmp_path / "source.sqlite3")
    category = source.add_category("Writing")
    body = "Keep whitespace\n\nCode: `x = 1` 🌟"
    source.save_prompt(
        title="Export me", description="description", body=body,
        category_id=category.id, tags=["tag"], favorite=True,
    )
    backup = source.export_json()

    destination = PromptStore(tmp_path / "destination.sqlite3")
    assert destination.import_json(backup) == 1
    imported = destination.list_prompts()[0]
    assert (imported.title, imported.description, imported.body) == (
        "Export me", "description", body
    )
    assert imported.tags == ("tag",)
    assert imported.favorite is True
    assert "Keep whitespace" in destination.export_markdown([imported.id])

    before = destination.export_json()
    malformed = json.loads(backup)
    malformed["categories"][0]["id"] = []
    with pytest.raises(ValueError):
        destination.import_json(json.dumps(malformed))
    assert destination.export_json() == before

    # JSON booleans are Python ints; IDs must reject them explicitly.
    malformed = json.loads(backup)
    malformed["categories"][0]["id"] = True
    with pytest.raises(ValueError):
        destination.import_json(json.dumps(malformed))
    assert destination.export_json() == before

    malformed = json.loads(backup)
    malformed["categories"].append(dict(malformed["categories"][0]))
    with pytest.raises(ValueError):
        destination.import_json(json.dumps(malformed))
    assert destination.export_json() == before
    source.close()
    destination.close()


def test_cancel_navigation_keeps_editor_and_selection_on_same_prompt(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    store = PromptStore(tmp_path / "ui.sqlite3")
    store.seed_samples()
    window = MainWindow(store)
    first = window.prompt_list.item(0)
    second = window.prompt_list.item(1)
    window.prompt_list.setCurrentItem(first)
    original_id = window._selected_id
    original_title = window.title_edit.text()
    window.title_edit.setText("Unsaved edit")
    monkeypatch.setattr(
        QMessageBox, "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
    )

    window.prompt_list.setCurrentItem(second)

    assert window.prompt_list.currentItem() is first
    assert window._selected_id == original_id
    assert window.title_edit.text() == "Unsaved edit"
    window.close()
    store.close()


def test_prompt_list_gets_readable_initial_splitter_width(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = PromptStore(tmp_path / "splitter.sqlite3")
    window = MainWindow(store)
    window.resize(1180, 760)
    window.show()
    app.processEvents()

    assert window.categories.width() <= 210
    assert window.prompt_list.width() >= 280
    assert window.body.width() >= 500

    window.close()
    store.close()
