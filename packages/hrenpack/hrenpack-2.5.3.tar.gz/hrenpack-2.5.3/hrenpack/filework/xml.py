from typing import Callable, Optional, Union
from bs4 import BeautifulSoup
from hrenpack.filework import TextFile


def xml_save(func: Callable):
    def wrapper(self, *args, **kwargs):
        output = func(self, *args, **kwargs)
        # Avoid calling save if the method is save itself or prettify
        if func.__name__ not in ['save', 'prettify']:
            self.save()
        return output
    return wrapper


class XMLParser(BeautifulSoup):
    def __init__(self, markup: str, features=None, builder=None, parse_only=None, from_encoding=None,
                 exclude_encodings=None, element_classes=None, **kwargs):
        super().__init__(markup, features, builder, parse_only, from_encoding,
                         exclude_encodings, element_classes, **kwargs)

    def del_tag(self, item: str):
        tags = self.find_all(item)
        for tag in tags:
            tag.decompose()
        return tags


class ParserMixin:
    parser: XMLParser

    @xml_save
    def append(self, tag):
        return self.parser.append(tag)

    @xml_save
    def childGenerator(self):
        return self.parser.childGenerator()

    @xml_save
    def clear(self, decompose=False):
        return self.parser.clear(decompose)

    @xml_save
    def copy_self(self):
        return self.parser.copy_self()

    @xml_save
    def decode(self, indent_level=None, eventual_encoding='utf-8', formatter='minimal', iterator=None, **kwargs):
        return self.parser.decode(indent_level, eventual_encoding, formatter, iterator, **kwargs)

    @xml_save
    def decode_contents(self, indent_level=None, eventual_encoding='utf-8', formatter='minimal'):
        return self.parser.decode_contents(indent_level, eventual_encoding, formatter)

    @xml_save
    def decompose(self):
        return self.parser.decompose()

    @xml_save
    def encode(self, encoding='utf-8', indent_level=None, formatter='minimal', errors="xmlcharrefreplace"):
        return self.parser.encode(encoding, indent_level, formatter, errors)

    @xml_save
    def encode_contents(self, indent_level=None, encoding='utf-8', formatter='minimal'):
        return self.parser.encode_contents(indent_level, encoding, formatter)

    @xml_save
    def endData(self, container_class=None):
        return self.parser.endData(container_class)

    @xml_save
    def extend(self, tags):
        return self.parser.extend(tags)

    @xml_save
    def extract(self, _self_index=None):
        return self.parser.extract(_self_index)

    @xml_save
    def fetchAllPrevious(self, *args, **kwargs):
        return self.parser.fetchAllPrevious(*args, **kwargs)

    @xml_save
    def fetchNextSiblings(self, *args, **kwargs):
        return self.parser.fetchNextSiblings(*args, **kwargs)

    @xml_save
    def fetchParents(self, *args, **kwargs):
        return self.parser.fetchParents(*args, **kwargs)

    @xml_save
    def fetchPreviousSiblings(self, *args, **kwargs):
        return self.parser.fetchPreviousSiblings(*args, **kwargs)

    @xml_save
    def find(self, name=None, attrs=None, recursive=True, string=None, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find(name, attrs, recursive, string, **kwargs)

    @xml_save
    def find_all(self, name=None, attrs=None, recursive: bool = True, string=None, limit: Optional[int] = None,
                 _stacklevel: int = 2, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.findAll(name, attrs, recursive, string, limit, _stacklevel, **kwargs)

    @xml_save
    def findAllNext(self, *args, **kwargs):
        return self.parser.findAllNext(*args, **kwargs)

    @xml_save
    def findAllPrevious(self, *args, **kwargs):
        return self.parser.findAllPrevious(*args, **kwargs)

    @xml_save
    def findChild(self, *args, **kwargs):
        return self.parser.findChild(*args, **kwargs)

    @xml_save
    def findChildren(self, *args, **kwargs):
        return self.parser.findChildren(*args, **kwargs)

    @xml_save
    def findNext(self, *args, **kwargs):
        return self.parser.findNext(*args, **kwargs)

    @xml_save
    def findNextSibling(self, *args, **kwargs):
        return self.parser.findNextSibling(*args, **kwargs)

    @xml_save
    def findNextSiblings(self, *args, **kwargs):
        return self.parser.findNextSiblings(*args, **kwargs)

    @xml_save
    def findParent(self, *args, **kwargs):
        return self.parser.findParent(*args, **kwargs)

    @xml_save
    def findParents(self, *args, **kwargs):
        return self.parser.findParents(*args, **kwargs)

    @xml_save
    def findPrevious(self, *args, **kwargs):
        return self.parser.findPrevious(*args, **kwargs)

    @xml_save
    def findPreviousSibling(self, *args, **kwargs):
        return self.parser.findPreviousSibling(*args, **kwargs)

    @xml_save
    def findPreviousSiblings(self, *args, **kwargs):
        return self.parser.findPreviousSiblings(*args, **kwargs)

    @xml_save
    def find_all_next(self, name=None, attrs=None, string=None, limit=None, _stacklevel: int = 2, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_all_next(name, attrs, string, limit, _stacklevel, **kwargs)

    @xml_save
    def find_all_previous(self, name=None, attrs=None, string=None, limit=None, _stacklevel: int = 2, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_all_previous(name, attrs, string, limit, _stacklevel, **kwargs)

    @xml_save
    def find_next(self, name=None, attrs=None, string=None, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_next(name, attrs, string, **kwargs)

    @xml_save
    def find_next_sibling(self, name=None, attrs=None, string=None, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_next_sibling(name, attrs, string, **kwargs)

    @xml_save
    def find_next_siblings(self, name=None, attrs=None, string=None, limit=None, _stacklevel=2, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_next_siblings(name, attrs, string, limit, _stacklevel, **kwargs)

    @xml_save
    def find_parent(self, name=None, attrs=None, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_parent(name, attrs, **kwargs)

    @xml_save
    def find_parents(self, name=None, attrs=None, limit=None, _stacklevel=2, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_parents(name, attrs, limit, _stacklevel, **kwargs)

    @xml_save
    def find_previous(self, name=None, attrs=None, string=None, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_previous(name, attrs, string, **kwargs)

    @xml_save
    def find_previous_sibling(self, name=None, attrs=None, string=None, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_previous_sibling(name, attrs, string, **kwargs)

    @xml_save
    def find_previous_siblings(self, name=None, attrs=None, string=None, limit=None, _stacklevel=2, **kwargs):
        if attrs is None:
            attrs = {}
        return self.parser.find_previous_siblings(name, attrs, string, limit, _stacklevel, **kwargs)

    @xml_save
    def format_string(self, s, formatter):
        return self.parser.format_string(s, formatter)

    @xml_save
    def formatter_for_name(self, formatter_name):
        return self.parser.formatter_for_name(formatter_name)

    @xml_save
    def get(self, key, default=None):
        return self.parser.get(key, default)

    @xml_save
    def getText(self, separator="", strip=False, types=()):
        return self.parser.getText(separator, strip, types)

    @xml_save
    def get_attribute_list(self, key, default=None):
        return self.parser.get_attribute_list(key, default)

    @xml_save
    def get_text(self, separator="", strip=False, types=()):
        return self.parser.get_text(separator, strip, types)

    @xml_save
    def handle_data(self, data):
        return self.parser.handle_data(data)

    @xml_save
    def handle_endtag(self, name, nsprefix=None):
        return self.parser.handle_endtag(name, nsprefix)

    @xml_save
    def handle_starttag(self, name, namespace, nsprefix, attrs, sourceline=None, sourcepos=None, namespaces=None):
        return self.parser.handle_starttag(name, namespace, nsprefix, attrs, sourceline, sourcepos, namespaces)

    @xml_save
    def has_attr(self, key):
        return self.parser.has_attr(key)

    @xml_save
    def has_key(self, key):
        return self.parser.has_key(key)

    @xml_save
    def index(self, element):
        return self.parser.index(element)

    @xml_save
    def insert(self, position, new_child):
        return self.parser.insert(position, new_child)

    @xml_save
    def insert_after(self, new_child):
        return self.parser.insert_after(new_child)

    @xml_save
    def insert_before(self, new_child):
        return self.parser.insert_before(new_child)

    @xml_save
    def isSelfClosing(self):
        return self.parser.isSelfClosing()

    @xml_save
    def new_string(self, s, subclass=None):
        return self.parser.new_string(s, subclass)

    @xml_save
    def new_tag(self, name, namespace=None, nsprefix=None, attrs=None, sourceline=None, sourcepos=None, string=None):
        return self.parser.new_tag(name, namespace, nsprefix, attrs, sourceline, sourcepos, string)

    @xml_save
    def nextGenerator(self):
        return self.parser.nextGenerator()

    @xml_save
    def nextSiblingGenerator(self):
        return self.parser.nextSiblingGenerator()

    @xml_save
    def object_was_parsed(self, o, parent=None, most_recent_element=None):
        return self.parser.object_was_parsed(o, parent, most_recent_element)

    @xml_save
    def parentGenerator(self):
        return self.parser.parentGenerator()

    @xml_save
    def popTag(self):
        return self.parser.popTag()

    @xml_save
    def prettify(self, encoding=None, formatter='minimal'):
        return self.parser.prettify(encoding, formatter)

    @xml_save
    def previousGenerator(self):
        return self.parser.previousGenerator()

    @xml_save
    def previousSiblingGenerator(self):
        return self.parser.previousSiblingGenerator()

    @xml_save
    def pushTag(self, tag):
        return self.parser.pushTag(tag)

    @xml_save
    def recursiveChildGenerator(self):
        return self.parser.recursiveChildGenerator()

    @xml_save
    def renderContents(self):
        return self.parser.renderContents()

    @xml_save
    def replaceWith(self, new_element):
        return self.parser.replaceWith(new_element)

    @xml_save
    def replaceWithChildren(self):
        return self.parser.replaceWithChildren()

    @xml_save
    def replace_with(self, new_element):
        return self.parser.replace_with(new_element)

    @xml_save
    def replace_with_children(self):
        return self.parser.replace_with_children()

    @xml_save
    def reset(self):
        return self.parser.reset()

    @xml_save
    def select(self, selector, namespaces=None, limit=0, **kwargs):
        return self.parser.select(selector, namespaces, limit, **kwargs)

    @xml_save
    def select_one(self, selector, namespaces=None, **kwargs):
        return self.parser.select_one(selector, namespaces, **kwargs)

    @xml_save
    def setup(self, parent=None, previous_element=None, next_element=None, previous_sibling=None, next_sibling=None):
        return self.parser.setup(parent, previous_element, next_element, previous_sibling, next_sibling)

    @xml_save
    def smooth(self):
        return self.parser.smooth()

    @xml_save
    def string_container(self, base_class=None):
        return self.parser.string_container(base_class)

    @xml_save
    def unwrap(self):
        return self.parser.unwrap()

    @xml_save
    def wrap(self, wrap_inside):
        return self.parser.wrap(wrap_inside)

    @xml_save
    def del_tag(self, item):
        return self.parser.del_tag(item)


class ExtensibleMarkupLanguageFile(ParserMixin, TextFile):
    _default_parser: str = 'xml'

    def __init__(self, path: str, encoding: Union[str, int] = 'utf-8', **kwargs):
        super().__init__(path, encoding, **kwargs)
        self.parser = XMLParser(self.read(), kwargs.get('parser', self._default_parser))

    def save(self):
        """Сохраняет изменения в файл."""
        self.rewrite(self.prettify())


class HyperTextMarkupLanguageFile(ExtensibleMarkupLanguageFile):
    _default_parser = 'html.parser'