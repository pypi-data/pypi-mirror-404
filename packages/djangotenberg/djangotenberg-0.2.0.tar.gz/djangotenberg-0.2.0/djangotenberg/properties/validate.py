
expect_key = [
    "singlePage",
    "paperWidth", 
    "paperHeight", 
    "marginTop", 
    "marginBottom", 
    "marginLeft", 
    "marginRight", 
    "preferCssPageSize", 
    "printBackground", 
    "omitBackground", 
    "landscape", 
    "scale", 
    "nativePageRange"
]

def validate_properties(properties: dict) -> None:
    for property in properties.keys():
        if property not in expect_key:
            raise ValueError(f"Invalid property: {property}")