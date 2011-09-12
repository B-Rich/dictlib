from dictlib.utils import walk
from dictlib.mapping import DotNotationAdapter
import collections

class Converter(object):
    """ A `Converter` can be used to convert a dictionary into another
    dictionary according to a set of rules.
    
    Rules:
    * `exclude`: a list of  
    """
    # Fields to exclude when converting to JSON (in dot notation)
    exclude = []
    # A dictionary of tuples for ordered renaming of fields
    rename = []
    factory = lambda o: o
    
    def __init__(self, exclude=None, rename=None, factory=None):
        self.exclude = list(self.exclude + (exclude or []))
        self.rename = list(self.rename + (rename or []))
        self.factory = factory if factory is not None else self.factory
        self.rename_inv = list((v, k) for k, v in self.rename)

    def from_schema(self, doc):
        # Exclude and map fields
        src_doc = DotNotationAdapter(doc)
        dest_doc = DotNotationAdapter()
        for key, value in walk(src_doc):
            if self.exclude_field(src_doc, key):
                continue
            dest_key, dest_value = self.map_from(key, value)
            if isinstance(value, collections.MutableMapping):
                dest_doc[dest_key] = dest_value.__class__()
            else:
                dest_doc[dest_key] = dest_value
        # Rename keys
        for rename_key, rename_value in self.rename:
            if rename_key in dest_doc:
                dest_doc[rename_value] = dest_doc[rename_key]
                del dest_doc[rename_key]
        return dest_doc.doc
    
    def to_schema(self, doc):
        # Work on a copy
        src_doc = DotNotationAdapter(dict(doc))
        dest_doc = DotNotationAdapter()
        # Rename fields
        for rename_key, rename_value in self.rename_inv:
            if rename_key in src_doc:
                dest_doc[rename_value] = src_doc[rename_key]
                del src_doc[rename_key]
        # Map fields
        for key, value in walk(src_doc):
            dest_key, dest_value = self.map_to(key, value)
            dest_doc[dest_key] = dest_value
        return dest_doc.doc
    
    def exclude_field(self, json_doc, key):
        return key in self.exclude
    
    def map_from(self, key, value):
        return (key, value)

    def map_to(self, key, value):
        return (key, value)
    
class JsonConverter(Converter):
    """ A `Converter` to convert a schemed dictionary to a JSON-stringifiable 
    dictionary.
    """
    def __init__(self, schema, **kwargs):
        """ Constructor. 
        :param schema: A schema instance
        :param kwargs: Any keyword arguments to the `Converter` constructor
        """
        super(JsonConverter, self).__init__(**kwargs)
        self.schema = schema

    def map_from(self, key, value):
        """ Convert the `value` from the internal Nete document representation 
        to the Nete API document representation. 
        """
        key = key.encode(u'utf-8') if isinstance(key, unicode) else key
        return (key, self.schema.get_field(key).to_json(value))

    def map_to(self, key, value):
        """ Convert the `value` from the Nete API document representation to the
        internal Nete document representation.
        """
        key = key.decode(u'utf-8') if isinstance(key, str) else key
        return (key, self.schema.get_field(key).from_json(value))

#class JsonSchemaConverter(Converter):
#    """ A basic `Schema` to JSON Schema converter.
#    
#    For reference, see http://tools.ietf.org/html/draft-zyp-json-schema-03
#    
#    Some features that don't work yet include:
#    * exclusive[Mininum,Maximum,minLength,maxLength]
#    * enum on any list
#    * AnyField (partially)
#    """
#    schema = Schema({unicode: FieldField(optional=True)})
#    factory = dict
#    
#    def to_json(self, schema):
#        schema = Schema(super(JsonSchemaConverter, self).to_json(schema.get_schema()))
#        return self._field_to_json(schema)
#
#    def _field_to_json(self, field):
#        json_schema_doc = {}
#        if not field.optional:
#            json_schema_doc[u'required'] = True
#        if field.title is not None:
#            json_schema_doc[u'title'] = field.title
#        if field.description is not None:
#            json_schema_doc[u'description'] = field.description
#        if field.default is not None:
#            json_schema_doc[u'default'] = field.default
#
#        if isinstance(field, DictField):
#            json_schema_doc[u'type'] = u'object'
#            json_schema_doc[u'properties']= {}
#            for subfield_name, subfield in field.get_schema().iteritems():
#                json_schema_doc[u'properties'][subfield_name] = self._field_to_json(subfield)
#        elif isinstance(field, ListField):
#            json_schema_doc[u'type'] = u'array'
#            if field.min_len is not None:
#                json_schema_doc[u'minItems'] = field.min_len
#            if field.max_len is not None:
#                json_schema_doc[u'maxItems'] = field.max_len
#            if len(field.fields) == 1:
#                json_schema_doc[u'items'] = self.to_json(field.fields[0])
#            else:
#                json_schema_doc[u'items'] = [self.to_json(field) for field in field.fields]
#        elif isinstance(field, NoneField):
#            json_schema_doc[u'type'] = u'null'
#        elif isinstance(field, AnyField):
#            json_schema_doc[u'type'] = u'any'
#        elif isinstance(field, AbstractNumericField):
#            json_schema_doc[u'type'] = u'number'
#            if field.min is not None:
#                json_schema_doc[u'minimum'] = field.min
#            if field.max is not None:
#                json_schema_doc[u'maximum'] = field.max
#        elif isinstance(field, UnicodeField):
#            json_schema_doc[u'type'] = u'string'
#
#        return json_schema_doc
#    
#    def from_json(self, json_schema_doc):
#        raise NotImplementedError(u'from_json for JSON schemas is not yet implemented')