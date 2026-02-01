from djangotenberg.properties import Property, PageSize


def test_properties_build():
    props = Property()
    props = props.page_size(PageSize.A4_PAGE_SIZE)\
                .margin_top(1)\
                .margin_bottom(1)\
                .margin_left(1)\
                .margin_right(1)\
                .scale(2)
    
    properties = props.build()

    w, h = PageSize.A4_PAGE_SIZE.value

    assert "paperWidth" in properties and properties.get("paperWidth") == w
    assert "paperHeight" in properties and properties.get("paperHeight") == h
    assert "marginTop" in properties and properties.get("marginTop") == 1
    assert "marginBottom" in properties and properties.get("marginBottom") == 1
    assert "marginLeft" in properties and properties.get("marginLeft") == 1
    assert "marginRight" in properties and properties.get("marginRight") == 1
    assert "scale" in properties and properties.get("scale") == 2
