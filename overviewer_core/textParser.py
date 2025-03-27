import html
import json
from logging import Logger


class TextParser(object):
    """A class to wrap up all the text component format logic into one easy-to-use
    and hopefully easy-to-debug format
    """

    # No DataVersion attribute available. Pre 1.9.
    SIGN_FORMAT_1070 = 0
    # First used DataVersion (15w32a / 1.9)
    SIGN_FORMAT_1090 = 100
    # hanging sign = 3205 / 22w42a / 1.19.3
    SIGN_FORMAT_1193 = 3205
    # sign text on both sides = 3442 / 23w12a / 1.20
    SIGN_FORMAT_1200 = 3442
    # new text component data format = 4298 / 25w02a / 1.21.5
    SIGN_FORMAT_1215 = 4298

    JSON_TEXT_COLOURS = [
        "black", "dark_blue", "dark_green", "dark_aqua",
        "dark_red", "dark_purple", "gold", "gray",
        "dark_gray", "blue", "green", "aqua",
        "red", "light_purple", "yellow", "white"
    ]

    def __init__(self, logger: Logger):
        self.logger = logger

    def parse_sign(self, poi: dict, chunk_data_version: int) -> None:
        """
        Takes a sign POI and parses the text components into a plain text format,
        and provides an HTML formatted version of the text.

        This mutates the original POI object.
        """

        if poi['id'] in ['Sign', 'minecraft:sign', 'minecraft:hanging_sign']:
            pass

        if 'Text1' in poi:
            # Legacy sign; upgrade to modern NBT layout
            self.__sign_from_legacy(poi, chunk_data_version)

        poi['front_text']['messagesHtml'] = [self.parse_text_component(i, chunk_data_version, True) for i in
                                             poi['front_text']['messages']]
        poi['front_text']['messages'] = [self.parse_text_component(i, chunk_data_version, False) for i in
                                         poi['front_text']['messages']]

        poi['back_text']['messagesHtml'] = [self.parse_text_component(i, chunk_data_version, True) for i in
                                            poi['back_text']['messages']]
        poi['back_text']['messages'] = [self.parse_text_component(i, chunk_data_version, False) for i in
                                        poi['back_text']['messages']]

    def __sign_from_legacy(self, poi: dict, chunk_data_version: int) -> None:
        """
        Upgrades a sign POI from the legacy Text1/Text2/etc format to the modern 1.20
        front_text.messages/back_text.messages format

        This mutates the original POI object.
        """

        if 'Text1' not in poi:
            # Not a legacy sign?
            return

        if poi['id'] == 'Sign':
            poi['id'] = 'minecraft:sign'

        empty_text = '""'
        if chunk_data_version == self.SIGN_FORMAT_1070:
            # Don't know if this should be old or not. See if there's precedent.
            # If not, assume 1.8 format. There's no good options here.
            if '' in [poi["Text1"], poi["Text2"], poi["Text3"], poi["Text4"]]:
                empty_text = ''

        poi.update({
            "back_text": {
                "has_glowing_text": 0,
                "color": "black",
                "messages": [empty_text, empty_text, empty_text, empty_text],
            },
            "front_text": {
                "has_glowing_text": poi.get('GlowingText', 0),
                "color": poi.get('Color', 'black'),
                "messages": [poi["Text1"], poi["Text2"], poi["Text3"], poi["Text4"]],
            },
            "keepPacked": 0,
            "is_waxed": 0,
        })

        poi.pop('Text1', None)
        poi.pop('Text2', None)
        poi.pop('Text3', None)
        poi.pop('Text4', None)
        poi.pop('GlowingText', None)
        poi.pop('Color', None)

    def parse_text_component(self, data, chunk_data_version: int, html_output: bool) -> str:
        if chunk_data_version >= self.SIGN_FORMAT_1215:
            # Guaranteed to be 1.21.5 format.
            return self.__parse_text_component_1215(data, html_output)

        if not isinstance(data, str):
            # All other earlier formats used text representations.
            # Something is really wrong.
            self.logger.error(
                "Requested parse of text component %s with data version %d, but text component is not a string!", data,
                chunk_data_version)
            return ''

        if chunk_data_version >= self.SIGN_FORMAT_1090:
            # Guaranteed to be 1.8 format.
            return self.__parse_text_component_1080(data, html_output)

        if chunk_data_version == self.SIGN_FORMAT_1070:
            if data is None or data == "null":
                return ""
            if data.startswith('"') and data.endswith('"'):
                # Starts and ends with string markers. Probably 1.8 format, but not guaranteed.
                return self.__parse_text_component_1080(data, html_output)
            if data.startswith('{') and data.endswith('}'):
                # Starts and ends with object markers. Probably 1.8 format, but not guaranteed.
                return self.__parse_text_component_1080(data, html_output)

            # Unlikely to be 1.8 format, so assume 1.7 format.
            return html.escape(data) if html_output else data

        self.logger.error("Unknown text component format %d", chunk_data_version)
        return ''

    def __parse_text_component_1080(self, data: str, html_output: bool) -> str:
        try:
            js = json.loads(data)
        except ValueError as ex:
            self.logger.warning("Failed parsing JSON text `%s`", data, exc_info=ex)
            return html.escape(data) if html_output else data

        # This format is essentially the same as the new format
        return self.__parse_text_component_1215(js, html_output)

    def __parse_text_component_1215(self, data, html_output: bool) -> str:
        # This format pulls the old JSON format up into the real NBT data structure.

        if isinstance(data, str):
            # If there's a string here, it's a real string
            return html.escape(data) if html_output else data

        style = TextStyleState(html_output)
        all_components = []

        def parse_recursive(component, parent_style: TextStyleState) -> None:
            """
            Recursively parse a text component based on its type.
            """
            if isinstance(component, str):
                # It's a string, so there's no style overrides here. Just use the parent
                # style.
                all_components.append((component, parent_style))
            if isinstance(component, list):
                # List, fall back to the list parser
                parse_list(component, parent_style)
            if isinstance(component, dict):
                # Dict, fall back to the dict parser
                parse_dict(component, parent_style)

        def parse_list(component: list, parent_style: TextStyleState) -> None:
            """
            Handle a text component that happens to be a list.

            If there's a single component, then just treat that as a component on its own

            If there's multiple, the documentation says that it should be:
              " Same as having all components after the first one appended to the first's extra array"
            """
            if len(component) == 0:
                # nothing to do
                pass
            if len(component) == 1:
                parse_recursive(component[0], parent_style)
            if len(component) > 1:
                # Lists are treated as a single component with other items forming
                # part of the "extra" list.
                new_component = component[0]
                new_component['extra'] = component[1:]
                parse_recursive(new_component, parent_style)

        def parse_dict(component: dict, parent_style: TextStyleState) -> None:
            """
            A "proper" text component, with style overrides etc.

            We're not going to handle different fonts. That's too far.
            """
            # Some components are stored as an empty dict with a single empty key to work around NBT storage constraints
            if '' in component:
                # This will only ever be plain text.
                all_components.append((component[''], parent_style))
                return

            component_style = parent_style.copy()

            if 'color' in component:
                if component['color'] in self.JSON_TEXT_COLOURS:
                    component_style.colour = component['color']
                elif component['color'].startswith('#'):
                    component_style.colour = component['color']

            if 'bold' in component:
                component_style.bold = component['bold']
            if 'italic' in component:
                component_style.italic = component['italic']
            if 'underlined' in component:
                component_style.underlined = component['underlined']
            if 'strikethrough' in component:
                component_style.strikethrough = component['strikethrough']
            if 'obfuscated' in component:
                component_style.obfuscated = component['obfuscated']

            if 'text' in component:
                all_components.append((component['text'], component_style))

            if "extra" in component and len(component["extra"]) > 0:
                for extra in component["extra"]:
                    parse_recursive(extra, component_style)

        parse_recursive(data, style)

        return ''.join([y.open_tag() + y.escape(x) + y.close_tag() for (x, y) in all_components])


class TextStyleState(object):
    def __init__(self, html_output: bool) -> None:
        self.html_output = html_output
        self.closing_tag = ''

        self.bold = False
        self.italic = False
        self.underlined = False
        self.strikethrough = False
        self.obfuscated = False
        self.colour = None

    def copy(self) -> "TextStyleState":
        new = TextStyleState(self.html_output)
        new.bold = self.bold
        new.italic = self.italic
        new.underlined = self.underlined
        new.strikethrough = self.strikethrough
        new.obfuscated = self.obfuscated
        new.colour = self.colour

        return new

    def close_tag(self):
        return self.closing_tag

    def open_tag(self) -> str:
        if not self.html_output:
            self.closing_tag = ''
            return ''

        style_attr = ''
        classes = []
        custom_colour = False

        if self.colour is not None:
            if self.colour in TextParser.JSON_TEXT_COLOURS:
                classes.append(f'mctext-{self.colour}')
            else:
                if not self.obfuscated:
                    style_attr += f'color: {self.colour};'
                custom_colour = True

        if self.bold:
            classes.append('mctext-bold')
        if self.italic:
            classes.append('mctext-italic')
        if self.underlined:
            classes.append('mctext-underlined')
        if self.strikethrough:
            classes.append('mctext-strikethrough')

        if self.obfuscated:
            if not custom_colour:
                classes.append('mctext-obfuscated')
            else:
                # thanks, I hate it.
                style_attr += f'text-shadow: 0 0 6px {self.colour}, 0 0 6px {self.colour}, 0 0 6px {self.colour}, 0 0 6px {self.colour}, 0 0 8px {self.colour}, 0 0 8px {self.colour};color: transparent;'

        if len(classes) == 0 and len(style_attr) == 0:
            # No styling needed
            self.closing_tag = ''
            return ''

        if style_attr != '':
            style_attr = f' style="{style_attr}"'

        self.closing_tag = '</span>'
        combined_classes = ' '.join(classes)
        return f'<span class="{combined_classes}"{style_attr}>'

    def escape(self, data) -> str:
        if self.html_output:
            return html.escape(data)

        return data