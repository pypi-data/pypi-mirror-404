import os
from flask import Blueprint, send_from_directory
from jinja2 import FileSystemLoader, ChoiceLoader

from hrenpack.typings import PathLike


class MultiTemplateAndStaticMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._template_folders = list()
        self._static_folders = list()
        self._static_folders_blueprints = list()

    def add_template_folder(self, folder_path: PathLike):
        """Добавляет папку с шаблонами"""
        if os.path.exists(folder_path) and folder_path not in self._template_folders:
            self._template_folders.append(str(folder_path))
            self._update_template_loader()

    def add_static_folder(self, name: str, folder_path: PathLike):
        """Добавляет папку со статическими файлами"""
        if os.path.exists(folder_path) and folder_path not in self._static_folders:
            self._static_folders.append(str(folder_path))
            blueprint = Blueprint(name, self.import_name, static_folder=folder_path, static_url_path=f'/static/{name}')
            self._static_folders_blueprints.append(blueprint)
            self.register_blueprint(blueprint)

    def serve_static(self, filename):
        """Обработчик для статических файлов из всех папок"""
        # Ищем файл в дополнительных папках
        for static_folder in self._static_folders:
            file_path = os.path.join(static_folder, filename)
            if os.path.exists(file_path):
                directory = os.path.dirname(file_path)
                actual_filename = os.path.basename(file_path)
                return send_from_directory(directory, actual_filename)

        # Если не нашли в дополнительных папках, используем стандартную логику Flask
        return super().send_static_file(filename)

    def _update_template_loader(self):
        """Обновляет загрузчик шаблонов с учетом всех папок"""
        all_template_folders = [self.template_folder] + self._template_folders
        existing_folders = [f for f in all_template_folders if f and os.path.exists(f)]

        loaders = [FileSystemLoader(folder) for folder in existing_folders]
        if hasattr(self, 'jinja_loader') and self.jinja_loader:
            loaders.append(self.jinja_loader)

        self.jinja_loader = ChoiceLoader(loaders)
        