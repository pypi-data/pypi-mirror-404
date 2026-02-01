from typing import Any
from abc import ABC, abstractmethod

class ClosedRenderable(ABC):
    @abstractmethod
    def render(self, context: "ophinode.site.BuildContext"):
        pass

    @property
    def prevent_auto_newline_before_me(self):
        "Disallow inserting auto newline before this renderable."
        return False

    @property
    def prevent_auto_newline_after_me(self):
        "Disallow inserting auto newline after this renderable."
        return False

class OpenRenderable(ABC):
    @abstractmethod
    def render_start(self, context: "ophinode.site.BuildContext"):
        pass

    @abstractmethod
    def render_end(self, context: "ophinode.site.BuildContext"):
        pass

    @property
    def auto_newline_for_children(self):
        """Whether auto newline insertion is enabled for children.

        If True, a newline is inserted between each two children when
        rendering.
        """

        return False

    @property
    def pad_newline_after_opening(self):
        """Insert newline after render_start().

        A newline is inserted only if the render result of children is
        a non-empty string, and auto newline is enabled in the current
        context.
        """

        return False

    @property
    def pad_newline_before_closing(self):
        """Insert newline before render_end().

        A newline is inserted only if the render result of children is
        a non-empty string, and auto newline is enabled in the current
        context.
        """

        return False

    @property
    def prevent_auto_newline_before_me(self):
        "Disallow inserting auto newline before this renderable."
        return False

    @property
    def prevent_auto_newline_after_me(self):
        "Disallow inserting auto newline after this renderable."
        return False

    @property
    def auto_indent_for_children(self):
        "Automatically insert indentation in front of each child."
        return False

    @property
    def auto_indent_string(self):
        """A string to use as indentation before each child.

        If None, the parent's indentation string is used instead.
        """

        return None

class Expandable(ABC):
    @abstractmethod
    def expand(self, context: "ophinode.site.BuildContext"):
        pass

class Preparable(ABC):
    @abstractmethod
    def prepare(self, context: "ophinode.site.BuildContext"):
        pass

class Page:
    @property
    def layout(self):
        return None

    @property
    def default_file_name(self):
        return None

    @property
    def default_file_name_suffix(self):
        return None

    def prepare_site(self, context: "ophinode.site.BuildContext"):
        pass

    def prepare_page(self, context: "ophinode.site.BuildContext"):
        pass

    def export_page(self, context: "ophinode.site.BuildContext"):
        export_path = context.current_page_path

        page_default_file_name = self.default_file_name
        if page_default_file_name is None:
            page_default_file_name = context.get_config_value(
                "page_default_file_name"
            )
        if export_path.endswith("/") and page_default_file_name is not None:
            export_path += page_default_file_name

        page_default_file_name_suffix = self.default_file_name_suffix
        if page_default_file_name_suffix is None:
            page_default_file_name_suffix = context.get_config_value(
                "page_default_file_name_suffix"
            )
        if (
            not export_path.endswith("/")
            and page_default_file_name_suffix is not None
            and not export_path.endswith(page_default_file_name_suffix)
        ):
            export_path += page_default_file_name_suffix

        render_result = context.get_rendered_page(context.current_page_path)
        context.export_file(export_path, render_result)

    def finalize_page(self, context: "ophinode.site.BuildContext"):
        pass

    def finalize_site(self, context: "ophinode.site.BuildContext"):
        pass

class Layout(ABC):
    @abstractmethod
    def build(self, page: Page, context: "ophinode.site.BuildContext"):
        pass

