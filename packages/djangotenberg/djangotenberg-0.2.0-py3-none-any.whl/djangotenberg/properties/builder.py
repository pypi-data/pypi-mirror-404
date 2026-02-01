from .properties import PageSize
from .validate import validate_properties

class Builder:
    def __init__(self):
        self.properties = []

    def add_property(self, property: dict) -> None:
        """
            Add a property to the builder.

            Args:
                property (dict): The property to add.
        """
        self.properties.append(property)

    def build(self) -> dict:
        """
            Build the properties.

            Returns:
                dict: The properties.
        """
        properties = {}
        for property in self.properties:
            properties[property["key"]] = property["value"]
        return properties


class Property(Builder):
    def single_page(self, single_page: bool) -> "Property":
        """
            Add a single page to the builder.

            Args:
                single_page (bool): The single page to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "singlePage", "value": single_page})
        return self

    def page_size(self, page_size: PageSize) -> "Property":
        """
            Add a page size to the builder.

            Args:
                page_size (PageSize): The page size to add.

            Returns:
                Property: The builder.
        """
        w, h = page_size.value
        self.add_property({"key": "paperWidth", "value": w})
        self.add_property({"key": "paperHeight", "value": h})
        return self

    def margin_top(self, margin: float) -> "Property":
        """
            Add a margin top to the builder.

            Args:
                margin (float): The margin top to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "marginTop", "value": margin})
        return self
    
    def margin_bottom(self, margin: float) -> "Property":
        """
            Add a margin bottom to the builder.

            Args:
                margin (float): The margin bottom to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "marginBottom", "value": margin})
        return self
    
    def margin_left(self, margin: float) -> "Property":
        """
            Add a margin left to the builder.

            Args:
                margin (float): The margin left to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "marginLeft", "value": margin})
        return self
    
    def margin_right(self, margin: float) -> "Property":
        """
            Add a margin right to the builder.

            Args:
                margin (float): The margin right to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "marginRight", "value": margin})
        return self 

    def prefer_css_page_size(self, prefer_css_page_size: bool) -> "Property":
        """
            Add a prefer CSS page size to the builder.

            Args:
                prefer_css_page_size (bool): The prefer CSS page size to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "preferCssPageSize", "value": prefer_css_page_size})
        return self

    def print_background(self, print_background: bool) -> "Property":
        """
            Add a print background to the builder.

            Args:
                print_background (bool): The print background to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "printBackground", "value": print_background})
        return self

    def omit_background(self, omit_background: bool) -> "Property":
        """
            Add a omit background to the builder.

            Args:
                omit_background (bool): The omit background to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "omitBackground", "value": omit_background})
        return self

    def landscape(self, landscape: bool) -> "Property":
        """
            Add a landscape to the builder.

            Args:
                landscape (bool): The landscape to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "landscape", "value": landscape})
        return self

    def scale(self, scale: float) -> "Property":
        """
            Add a scale to the builder.

            Args:
                scale (float): The scale to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "scale", "value": scale})
        return self
    
    def native_page_range(self, native_page_range: str) -> "Property":
        """
            Add a native page range to the builder.

            Args:
                native_page_range (str): The native page range to add.

            Returns:
                Property: The builder.
        """
        self.add_property({"key": "nativePageRange", "value": native_page_range})
        return self
    