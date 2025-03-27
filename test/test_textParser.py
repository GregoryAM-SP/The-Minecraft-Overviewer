import pytest
from overviewer_core.textParser import TextParser
from overviewer_core.textParser import TextStyleState


def test_sign_upgrade_170(mocker):
    logger = mocker.Mock()
    parser = TextParser(logger)
    poi = {
        "id": "Sign",
        "x": 0,
        "y": 0,
        "z": 0,
        "Text1": "test",
        "Text2": "",
        "Text3": "",
        "Text4": "",
    }

    parser._TextParser__sign_from_legacy(poi, TextParser.SIGN_FORMAT_1070)

    assert poi["id"] == "minecraft:sign"
    assert "Text1" not in poi
    assert "Text2" not in poi
    assert "Text3" not in poi
    assert "Text4" not in poi
    assert poi["front_text"]["messages"][0] == 'test'
    assert poi["front_text"]["messages"][1] == ''
    assert poi["front_text"]["messages"][2] == ''
    assert poi["front_text"]["messages"][3] == ''
    assert poi["front_text"]["color"] == "black"
    assert poi["front_text"]["has_glowing_text"] == 0
    assert poi["back_text"]["messages"][0] == ''
    assert poi["back_text"]["messages"][1] == ''
    assert poi["back_text"]["messages"][2] == ''
    assert poi["back_text"]["messages"][3] == ''
    assert poi["back_text"]["color"] == "black"
    assert poi["back_text"]["has_glowing_text"] == 0


def test_sign_upgrade_1140(mocker):
    logger = mocker.Mock()
    parser = TextParser(logger)
    poi = {
        "id": "minecraft:sign",
        "x": 0,
        "y": 0,
        "z": 0,
        "Color": "green",
        "Text1": '"test"',
        "Text2": '""',
        "Text3": '""',
        "Text4": '""',
    }

    parser._TextParser__sign_from_legacy(poi, TextParser.SIGN_FORMAT_1090)

    assert poi["id"] == "minecraft:sign"
    assert "Text1" not in poi
    assert "Text2" not in poi
    assert "Text3" not in poi
    assert "Text4" not in poi
    assert poi["front_text"]["messages"][0] == '"test"'
    assert poi["front_text"]["messages"][1] == '""'
    assert poi["front_text"]["messages"][2] == '""'
    assert poi["front_text"]["messages"][3] == '""'
    assert poi["front_text"]["color"] == "green"
    assert poi["front_text"]["has_glowing_text"] == 0
    assert poi["back_text"]["messages"][0] == '""'
    assert poi["back_text"]["messages"][1] == '""'
    assert poi["back_text"]["messages"][2] == '""'
    assert poi["back_text"]["messages"][3] == '""'
    assert poi["back_text"]["color"] == "black"
    assert poi["back_text"]["has_glowing_text"] == 0


def test_sign_upgrade_1170(mocker):
    logger = mocker.Mock()
    parser = TextParser(logger)
    poi = {
        "id": "minecraft:sign",
        "x": 0,
        "y": 0,
        "z": 0,
        "Color": "green",
        "GlowingText": 1,
        "Text1": '"test"',
        "Text2": '""',
        "Text3": '""',
        "Text4": '""',
    }

    parser._TextParser__sign_from_legacy(poi, TextParser.SIGN_FORMAT_1090)

    assert poi["id"] == "minecraft:sign"
    assert "Text1" not in poi
    assert "Text2" not in poi
    assert "Text3" not in poi
    assert "Text4" not in poi
    assert poi["front_text"]["messages"][0] == '"test"'
    assert poi["front_text"]["messages"][1] == '""'
    assert poi["front_text"]["messages"][2] == '""'
    assert poi["front_text"]["messages"][3] == '""'
    assert poi["front_text"]["color"] == "green"
    assert poi["front_text"]["has_glowing_text"] == 1
    assert poi["back_text"]["messages"][0] == '""'
    assert poi["back_text"]["messages"][1] == '""'
    assert poi["back_text"]["messages"][2] == '""'
    assert poi["back_text"]["messages"][3] == '""'
    assert poi["back_text"]["color"] == "black"
    assert poi["back_text"]["has_glowing_text"] == 0


def test_sign_text_process(mocker):
    logger = mocker.Mock()
    parser = TextParser(logger)
    poi = {
        "id": "minecraft:sign",
        "x": 0,
        "y": 0,
        "z": 0,
        "front_text": {
            "messages": ['"f1"', '"f2"', '"f3"', '"f4"'],
            "color": "black",
            "has_glowing_text": 0,
        },
        "back_text": {
            "messages": ['"b1"', '"b2"', '"b3"', '"b4"'],
            "color": "black",
            "has_glowing_text": 0,
        },
    }

    parser.parse_sign(poi, TextParser.SIGN_FORMAT_1200)

    assert poi["id"] == "minecraft:sign"
    assert poi["front_text"]["messages"][0] == 'f1'
    assert poi["front_text"]["messages"][1] == 'f2'
    assert poi["front_text"]["messages"][2] == 'f3'
    assert poi["front_text"]["messages"][3] == 'f4'
    assert poi["front_text"]["messagesHtml"][0] == 'f1'
    assert poi["front_text"]["messagesHtml"][1] == 'f2'
    assert poi["front_text"]["messagesHtml"][2] == 'f3'
    assert poi["front_text"]["messagesHtml"][3] == 'f4'
    assert poi["back_text"]["messages"][0] == 'b1'
    assert poi["back_text"]["messages"][1] == 'b2'
    assert poi["back_text"]["messages"][2] == 'b3'
    assert poi["back_text"]["messages"][3] == 'b4'
    assert poi["back_text"]["messagesHtml"][0] == 'b1'
    assert poi["back_text"]["messagesHtml"][1] == 'b2'
    assert poi["back_text"]["messagesHtml"][2] == 'b3'
    assert poi["back_text"]["messagesHtml"][3] == 'b4'

def test_1215_string(mocker):
    logger = mocker.Mock()
    parser = TextParser(logger)
    data = "test"

    result = parser.parse_text_component(data, TextParser.SIGN_FORMAT_1215, False)

    assert result == "test"

def test_1215_xss(mocker):
    logger = mocker.Mock()
    parser = TextParser(logger)
    data = "<script>alert('')/*"

    result = parser.parse_text_component(data, TextParser.SIGN_FORMAT_1215, True)

    assert result == "&lt;script&gt;alert(&#x27;&#x27;)/*"

def test_1215_xss_nonrendered(mocker):
    """
    I'm purposefully *not* escaping non-HTML rendered things here. The documentation states that you
    need to escape it already, and changing this to escape all text could break existing filter functions
    that rely on searching for < and >.

    Really, non-HTML messages should never be written to the client and only used within filter functions
    themselves. Rely on messagesHtml for things you want to write to the client.
    """
    logger = mocker.Mock()
    parser = TextParser(logger)
    data = "<script>alert('')/*"

    result = parser.parse_text_component(data, TextParser.SIGN_FORMAT_1215, False)

    assert result == "<script>alert('')/*"

def test_1215_basic_component(mocker):
    logger = mocker.Mock()
    parser = TextParser(logger)
    data = {"text": "test"}

    result = parser.parse_text_component(data, TextParser.SIGN_FORMAT_1215, False)

    assert result == "test"

# All these test cases have been verified in-game via
# /data modify block <x> <y> <z> front_text.messages[0] set value <data>
@pytest.mark.parametrize('data,expected',[
  pytest.param({"text": "test"}, "test", id="basic"),
  pytest.param({"text":"goo","color":"#FF00FF"}, "goo", id="basic_coloured"),
  pytest.param({"text":"a","color":"red","extra":["b", "c"]}, "abc", id="basic_extra_strings"),
  pytest.param({"text":"a","extra":[{"text":"b"},{"text":"c"}]}, "abc", id="extra_components"),
  pytest.param({"text":"a","extra":[{"text":"b"},{"":"c"}]}, "abc", id="extra_components_with_empty_object"),
  pytest.param({"text":"a","extra":[{"text":"b","extra":[{"text":"c"}]}]}, "abc", id="nested_components"),
  pytest.param({"text":"a","extra":[{"text":"b","extra":[{"text":"c"},"d"]},{"text":"e","extra":[{"text":"f"},{"text":"g"}]}]}, "abcdefg", id="confusing_nesting"),
  pytest.param({"extra":["b", "c"],"text":"a"}, "abc", id="odd_order"),
])
def test_1215_components_plain(mocker, data, expected):
    logger = mocker.Mock()
    parser = TextParser(logger)

    result = parser.parse_text_component(data, TextParser.SIGN_FORMAT_1215, False)

    assert result == expected

def test_textstyle_no_html():
    style = TextStyleState(False)
    style.bold = True
    style.color = "#FF0000"
    style.obfuscated = True

    assert style.open_tag() == ''
    assert style.close_tag() == ''

def test_textstyle_unstyled_html():
    style = TextStyleState(True)

    assert style.open_tag() == ''
    assert style.close_tag() == ''

def test_textstyle_styled_html():
    style = TextStyleState(True)

    style.bold = True
    style.colour = "red"

    assert style.open_tag() == '<span class="mctext-red mctext-bold">'
    assert style.close_tag() == '</span>'


def test_textstyle_allbool_styled():
    style = TextStyleState(True)

    style.bold = True
    style.italic = True
    style.underlined = True
    style.strikethrough = True
    style.obfuscated = True

    assert style.open_tag() == '<span class="mctext-bold mctext-italic mctext-underlined mctext-strikethrough mctext-obfuscated">'
    assert style.close_tag() == '</span>'


def test_textstyle_custom_colour():
    style = TextStyleState(True)

    style.colour = '#ffbb33'

    assert style.open_tag() == '<span class="" style="color: #ffbb33;">'
    assert style.close_tag() == '</span>'

def test_textstyle_custom_colour_obfuscated():
    style = TextStyleState(True)

    style.colour = '#ffbb33'
    style.obfuscated = True

    assert style.open_tag() == '<span class="" style="text-shadow: 0 0 6px #ffbb33, 0 0 6px #ffbb33, 0 0 6px #ffbb33, 0 0 6px #ffbb33, 0 0 8px #ffbb33, 0 0 8px #ffbb33;color: transparent;">'
    assert style.close_tag() == '</span>'

@pytest.mark.parametrize('data,expected',[
  pytest.param({"text": "test"}, 'test', id="basic"),
  pytest.param({"text":"goo","color":"#FF00FF"}, '<span class="" style="color: #FF00FF;">goo</span>', id="basic_coloured"),
  pytest.param({"text":"a","color":"red","extra":["b", "c"]}, '<span class="mctext-red">a</span><span class="mctext-red">b</span><span class="mctext-red">c</span>', id="basic_extra_strings"),
  pytest.param({"text":"a","color":"red","extra":[{"text":"b","color":"blue"}, "c"]}, '<span class="mctext-red">a</span><span class="mctext-blue">b</span><span class="mctext-red">c</span>', id="overriden"),
  pytest.param({"text":"a","color":"red","extra":[{"text":"b","color":"blue"}, {"": "c"}]}, '<span class="mctext-red">a</span><span class="mctext-blue">b</span><span class="mctext-red">c</span>', id="overriden_with_empty_component"),
  pytest.param({"text":"a","color":"red","bold":True,"extra":[{"text":"b","color":"blue"}, "c"]}, '<span class="mctext-red mctext-bold">a</span><span class="mctext-blue mctext-bold">b</span><span class="mctext-red mctext-bold">c</span>', id="overriden_bold"),
  pytest.param({"text":"a","color":"red","bold":True,"extra":[{"text":"b","color":"blue","bold":False}, "c"]}, '<span class="mctext-red mctext-bold">a</span><span class="mctext-blue">b</span><span class="mctext-red mctext-bold">c</span>', id="overriden_unbold")
])
def test_1215_components_html(mocker, data, expected):
    logger = mocker.Mock()
    parser = TextParser(logger)

    result = parser.parse_text_component(data, TextParser.SIGN_FORMAT_1215, True)

    assert result == expected