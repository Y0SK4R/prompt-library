"""Main three-pane Prompt Library window."""

from __future__ import annotations

import re

from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QSplitter, QStatusBar, QTextEdit, QVBoxLayout,
    QWidget,
)

from prompt_library.data import Prompt, PromptStore


class TemplateDialog(QDialog):
    """Collect named template values without changing the saved source text."""

    def __init__(self, template: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Fill prompt template")
        self.setMinimumWidth(420)
        self._fields: dict[str, QLineEdit] = {}
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter values for the placeholders in this prompt."))
        form = QFormLayout()
        for name in dict.fromkeys(re.findall(r"\{\{\s*([\w.-]+)\s*\}\}", template)):
            field = QLineEdit(self)
            field.setPlaceholderText(name.replace("_", " "))
            field.setAccessibleName(f"Value for {name}")
            self._fields[name] = field
            form.addRow(name.replace("_", " ").title(), field)
        if not self._fields:
            layout.addWidget(QLabel("This prompt has no named placeholders."))
        layout.addLayout(form)
        self.preview = QLabel("All placeholders will be replaced in the copied text.")
        self.preview.setWordWrap(True)
        layout.addWidget(self.preview)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        self.copy_button = self.buttons.addButton("Copy filled prompt", QDialogButtonBox.ButtonRole.AcceptRole)
        self.copy_button.setDefault(True)
        self.buttons.accepted.connect(self._accept_if_complete)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        for field in self._fields.values():
            field.textChanged.connect(self._update_state)
        self._update_state()

    def _update_state(self) -> None:
        missing = [name for name, field in self._fields.items() if not field.text().strip()]
        self.copy_button.setEnabled(not missing)
        self.preview.setText("Missing values: " + ", ".join(missing) if missing else "Ready to copy the filled prompt.")

    def _accept_if_complete(self) -> None:
        self._update_state()
        if self.copy_button.isEnabled():
            self.accept()

    def values(self) -> dict[str, str]:
        return {name: field.text() for name, field in self._fields.items()}


class MainWindow(QMainWindow):
    """Keyboard-friendly sidebar, prompt list, and editor shell."""

    def __init__(self, store: PromptStore | None = None):
        super().__init__()
        self.store = store or PromptStore()
        self._owns_store = store is None
        self._selected_id: int | None = None
        self._dirty = False
        self._loading = False
        self._show_trash = False
        self.setWindowTitle("Prompt Library")
        self.resize(1180, 760)
        self.setMinimumSize(820, 520)
        self.setStatusBar(QStatusBar(self))

        root = QWidget(self)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 14, 16, 14)
        heading = QHBoxLayout()
        self.trash_view_button = QPushButton("Show trash", root)
        self.trash_view_button.setCheckable(True)
        self.trash_view_button.setAccessibleName("Show trashed prompts")
        title = QLabel("Prompt Library")
        title.setObjectName("appTitle")
        heading.addWidget(title)
        heading.addWidget(self.trash_view_button)
        heading.addStretch(1)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search promptsâ€¦")
        self.search.setClearButtonEnabled(True)
        self.search.setAccessibleName("Search prompts")
        self.search.setMaximumWidth(340)
        heading.addWidget(self.search)
        outer.addLayout(heading)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.categories = QListWidget(splitter)
        self.categories.setAccessibleName("Prompt categories")
        self.categories.setMaximumWidth(210)
        self.prompt_list = QListWidget(splitter)
        self.prompt_list.setAccessibleName("Prompts")
        editor = QWidget(splitter)
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(14, 8, 0, 0)
        self.title_edit = QLineEdit(editor)
        self.title_edit.setPlaceholderText("Prompt title")
        self.title_edit.setAccessibleName("Prompt title")
        self.description = QLineEdit(editor)
        self.description.setPlaceholderText("Short description (optional)")
        self.description.setAccessibleName("Prompt description")
        row = QHBoxLayout()
        self.category = QComboBox(editor)
        self.category.setAccessibleName("Prompt category")
        self.tags = QLineEdit(editor)
        self.tags.setPlaceholderText("Tags, separated by commas")
        self.tags.setAccessibleName("Prompt tags")
        row.addWidget(self.category, 1)
        row.addWidget(self.tags, 2)
        self.favorite = QCheckBox("Favorite", editor)
        self.favorite.setAccessibleName("Favorite prompt")
        self.body = QTextEdit(editor)
        self.body.setPlaceholderText("Write or paste your prompt here. Text is stored as data and never executed.")
        self.body.setAccessibleName("Prompt body")
        self.body.setTabChangesFocus(False)
        self.save_button = QPushButton("Save prompt", editor)
        self.save_button.setDefault(True)
        self.save_button.setAccessibleName("Save prompt")
        self.new_button = QPushButton("New", editor)
        self.copy_button = QPushButton("Copy", editor)
        self.copy_filled_button = QPushButton("Fill template & copy", editor)
        self.trash_button = QPushButton("Move to trash", editor)
        self.restore_button = QPushButton("Restore", editor)
        actions = QHBoxLayout()
        for button in (self.new_button, self.save_button, self.copy_button, self.copy_filled_button, self.trash_button, self.restore_button):
            actions.addWidget(button)
        editor_layout.addWidget(self.title_edit)
        editor_layout.addWidget(self.description)
        editor_layout.addLayout(row)
        editor_layout.addWidget(self.favorite)
        editor_layout.addWidget(self.body, 1)
        editor_layout.addLayout(actions)
        splitter.addWidget(self.categories)
        splitter.addWidget(self.prompt_list)
        splitter.addWidget(editor)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 3)
        # QSplitter otherwise starts the prompt list at its small size hint,
        # leaving titles clipped even on a full-size window.
        splitter.setSizes([200, 360, 588])
        outer.addWidget(splitter, 1)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #f5f6f8; color: #202633; font-size: 14px; }
            #appTitle { font-size: 22px; font-weight: 700; }
            QLineEdit, QTextEdit, QListWidget, QComboBox { background: white; border: 1px solid #d8dce4; border-radius: 7px; padding: 8px; }
            QListWidget::item { padding: 9px 7px; border-radius: 5px; }
            QListWidget::item:selected { background: #e5edff; color: #173e83; }
            QPushButton { background: white; border: 1px solid #cdd3de; border-radius: 7px; padding: 8px 11px; }
            QPushButton:hover { background: #edf2fb; }
            QPushButton:default { background: #285ac5; color: white; border-color: #285ac5; }
            QPushButton:disabled { color: #969daa; }
        """)

        self.search.textChanged.connect(self.refresh_prompts)
        self.categories.currentItemChanged.connect(self.refresh_prompts)
        self.prompt_list.currentItemChanged.connect(self._select_item)
        self.new_button.clicked.connect(self.new_prompt)
        self.save_button.clicked.connect(self.save_prompt)
        self.copy_button.clicked.connect(self.copy_prompt)
        self.copy_filled_button.clicked.connect(self.copy_filled)
        self.trash_button.clicked.connect(self.trash_prompt)
        self.restore_button.clicked.connect(self.restore_prompt)
        self.trash_view_button.toggled.connect(self._toggle_trash)
        for signal in (self.title_edit.textChanged, self.description.textChanged, self.body.textChanged,
                       self.tags.textChanged, self.favorite.toggled, self.category.currentIndexChanged):
            signal.connect(self._mark_dirty)
        QShortcut(QKeySequence.StandardKey.Save, self, activated=self.save_prompt)
        QShortcut(QKeySequence.StandardKey.Find, self, activated=self.search.setFocus)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_prompt)
        self.store.seed_samples()
        self.refresh_categories()
        self.refresh_prompts()
        # Start in a clean editor without prompting about the initial empty form.
        self._reset_editor()

    def refresh_categories(self) -> None:
        _block = QSignalBlocker(self.categories)
        current = self.categories.currentRow()
        self.categories.clear()
        self.categories.addItem(QListWidgetItem("All prompts"))
        for category in self.store.list_categories():
            self.categories.addItem(QListWidgetItem(category.name))
            self.categories.item(self.categories.count() - 1).setData(Qt.ItemDataRole.UserRole, category.id)
        self.categories.setCurrentRow(max(0, current))
        self.category.clear()
        self.category.addItem("Uncategorized", None)
        for category in self.store.list_categories():
            if category.name != "Uncategorized":
                self.category.addItem(category.name, category.id)

    def refresh_prompts(self, *_args) -> None:
        self.prompt_list.clear()
        selected = self.categories.currentItem()
        category_id = selected.data(Qt.ItemDataRole.UserRole) if selected and selected.text() != "All prompts" else None
        for prompt in self.store.list_prompts(include_deleted=self._show_trash,
                                              search=self.search.text() if not self._show_trash else "",
                                              category_id=category_id if not self._show_trash else None):
            label = ("★  " if prompt.favorite else "") + prompt.title
            if prompt.description:
                label += "\n" + prompt.description
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, prompt.id)
            item.setToolTip(prompt.title + ("\n" + prompt.description if prompt.description else ""))
            self.prompt_list.addItem(item)
        if not self.prompt_list.count():
            self.statusBar().showMessage("Trash is empty." if self._show_trash else "No prompts found. Create one with Ctrl+N.")
        else:
            self.statusBar().showMessage(f"{self.prompt_list.count()} prompts")

    def _select_item(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None = None) -> None:
        if current is None:
            return
        if not self._confirm_discard():
            # QListWidget has already changed its current row when this signal
            # fires. Restore the editor's row so selection and edited record
            # cannot diverge after the user cancels navigation.
            with QSignalBlocker(self.prompt_list):
                self.prompt_list.setCurrentItem(_previous)
            return
        try:
            prompt = self.store.get_prompt(current.data(Qt.ItemDataRole.UserRole))
        except (KeyError, TypeError):
            return
        self._selected_id = prompt.id
        self._loading = True
        self.title_edit.setText(prompt.title)
        self.description.setText(prompt.description)
        self.body.setPlainText(prompt.body)
        self.tags.setText(", ".join(prompt.tags))
        self.favorite.setChecked(prompt.favorite)
        index = self.category.findData(prompt.category_id)
        self.category.setCurrentIndex(max(0, index))
        self._loading = False
        self._dirty = False
        self._update_actions()

    def new_prompt(self) -> None:
        if not self._confirm_discard():
            return
        self._reset_editor()

    def _reset_editor(self) -> None:
        self._loading = True
        self.prompt_list.clearSelection()
        self._selected_id = None
        self.title_edit.clear()
        self.description.clear()
        self.body.clear()
        self.tags.clear()
        self.favorite.setChecked(False)
        self.category.setCurrentIndex(0)
        self._loading = False
        self._dirty = False
        self._update_actions()
        self.title_edit.setFocus()
        self.statusBar().showMessage("New prompt")

    def save_prompt(self) -> None:
        try:
            prompt = self.store.save_prompt(
                prompt_id=self._selected_id,
                title=self.title_edit.text(), body=self.body.toPlainText(),
                description=self.description.text(), category_id=self.category.currentData(),
                tags=[tag.strip() for tag in self.tags.text().split(",") if tag.strip()],
                favorite=self.favorite.isChecked(),
            )
        except (ValueError, KeyError) as exc:
            QMessageBox.warning(self, "Could not save prompt", str(exc))
            self.title_edit.setFocus()
            return
        self._selected_id = prompt.id
        self._dirty = False
        self._update_actions()
        self.refresh_prompts()
        for i in range(self.prompt_list.count()):
            item = self.prompt_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == prompt.id:
                self.prompt_list.setCurrentItem(item)
                break
        self.statusBar().showMessage("Prompt saved", 3000)

    def copy_prompt(self) -> None:
        text = self.body.toPlainText()
        if not text:
            self.statusBar().showMessage("There is no prompt text to copy", 3000)
            return
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage("Prompt copied", 3000)

    def copy_filled(self) -> None:
        template = self.body.toPlainText()
        names = re.findall(r"\{\{\s*([\w.-]+)\s*\}\}", template)
        if not names:
            self.copy_prompt()
            return
        dialog = TemplateDialog(template, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        filled = re.sub(r"\{\{\s*([\w.-]+)\s*\}\}", lambda match: values[match.group(1)], template)
        QApplication.clipboard().setText(filled)
        self.statusBar().showMessage("Filled prompt copied; saved template is unchanged", 4000)

    def trash_prompt(self) -> None:
        if self._selected_id is None:
            self.statusBar().showMessage("Select a saved prompt first", 3000)
            return
        prompt_id = self._selected_id
        self.store.trash(prompt_id)
        self.new_prompt()
        self.refresh_prompts()
        self.statusBar().showMessage("Prompt moved to trash", 3000)

    def restore_prompt(self) -> None:
        if self._selected_id is None or not self._show_trash:
            return
        self.store.restore(self._selected_id)
        self.new_prompt()
        self.refresh_prompts()
        self.statusBar().showMessage("Prompt restored", 3000)

    def _toggle_trash(self, checked: bool) -> None:
        if not self._confirm_discard():
            with QSignalBlocker(self.trash_view_button):
                self.trash_view_button.setChecked(not checked)
            return
        self._show_trash = checked
        self.trash_view_button.setText("Show active prompts" if checked else "Show trash")
        self.trash_button.setVisible(not checked)
        self.restore_button.setVisible(checked)
        self.new_prompt()
        self.refresh_prompts()

    def _mark_dirty(self, *_args) -> None:
        if self._loading:
            return
        self._dirty = True
        self._update_actions()

    def _update_actions(self) -> None:
        self.save_button.setEnabled(self._dirty and not self._show_trash)
        self.trash_button.setEnabled(self._selected_id is not None and not self._show_trash)
        self.restore_button.setEnabled(self._selected_id is not None and self._show_trash)

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        answer = QMessageBox.question(self, "Discard unsaved changes?", "This prompt has unsaved changes. Discard them?",
                                      QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                      QMessageBox.StandardButton.Cancel)
        return answer == QMessageBox.StandardButton.Discard

    def closeEvent(self, event) -> None:
        if not self._confirm_discard():
            event.ignore()
            return
        if self._owns_store:
            self.store.close()
        event.accept()


