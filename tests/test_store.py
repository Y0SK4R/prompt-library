import json

import pytest

from prompt_library.data import PromptStore


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
