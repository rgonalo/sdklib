import json

from urllib3.filepost import encode_multipart_formdata
from urllib3.fields import RequestField, guess_content_type

from .util.files import guess_filename_stream
from .util.structures import to_key_val_list, to_key_val_dict
from .compat import urlencode, quote_plus


def to_string(value):
    if isinstance(value, bool) and value:
        return "true"
    elif isinstance(value, bool):
        return "false"
    elif value is None:
        return "null"
    else:
        return unicode(value)


class MultiPartRender(object):

    def __init__(self, boundary="----------ThIs_Is_tHe_bouNdaRY_$"):
        self.boundary = boundary

    def encode_params(self, data=None, files=None, **kwargs):
        """
        Build the body for a multipart/form-data request.
        Will successfully encode files when passed as a dict or a list of
        tuples. Order is retained if data is a list of tuples but arbitrary
        if parameters are supplied as a dict.
        The tuples may be string (filepath), 2-tuples (filename, fileobj), 3-tuples (filename, fileobj, contentype)
        or 4-tuples (filename, fileobj, contentype, custom_headers).
        """
        if isinstance(data, basestring):
            raise ValueError("Data must not be a string.")

        # optional args
        boundary = kwargs.get("boundary", None)

        new_fields = []
        fields = to_key_val_list(data or {})
        files = to_key_val_list(files or {})

        for field, val in fields:
            if isinstance(val, basestring) or not hasattr(val, '__iter__'):
                val = [val]
            for v in val:
                # Don't call str() on bytestrings: in Py3 it all goes wrong.
                if not isinstance(v, bytes):
                    v = to_string(v)

                new_fields.append(
                    (field.decode('utf-8') if isinstance(field, bytes) else field,
                     v.encode('utf-8') if isinstance(v, str) else v))

        for (k, v) in files:
            # support for explicit filename
            ft = None
            fh = None
            if isinstance(v, (tuple, list)):
                if len(v) == 2:
                    fn, fp = v
                elif len(v) == 3:
                    fn, fp, ft = v
                else:
                    fn, fp, ft, fh = v
            else:
                fn, fp = guess_filename_stream(v)
                ft = guess_content_type(fn)

            if isinstance(fp, (str, bytes, bytearray)):
                fdata = fp
            else:
                fdata = fp.read()

            rf = RequestField(name=k, data=fdata, filename=fn, headers=fh)
            rf.make_multipart(content_type=ft)
            new_fields.append(rf)

        if boundary is None:
            boundary = self.boundary
        body, content_type = encode_multipart_formdata(new_fields, boundary=boundary)

        return body, content_type


class FormRender(object):

    VALID_COLLECTION_FORMATS = ['multi', 'csv', 'ssv', 'tsv', 'pipes', 'encoded']
    COLLECTION_SEPARATORS = {"csv": ",", "ssv": " ", "tsv": "\t", "pipes": "|"}

    def __init__(self, collection_format='multi'):
        self.content_type = 'application/x-www-form-urlencoded'
        self.collection_format = collection_format

    @property
    def collection_format(self):
        return self._collection_format

    @collection_format.setter
    def collection_format(self, value):
        assert value in self.VALID_COLLECTION_FORMATS

        self._collection_format = value

    def encode_params(self, data=None, **kwargs):
        """
        Encode parameters in a piece of data.
        Will successfully encode parameters when passed as a dict or a list of
        2-tuples. Order is retained if data is a list of 2-tuples but arbitrary
        if parameters are supplied as a dict.
        """
        collection_format = kwargs.get("collection_format", self.collection_format)

        if data is None:
            return "", self.content_type
        elif isinstance(data, (str, bytes)):
            return data, self.content_type
        elif hasattr(data, 'read'):
            return data, self.content_type
        elif collection_format == 'multi' and hasattr(data, '__iter__'):
            result = []
            for k, vs in to_key_val_list(data):
                if isinstance(vs, basestring) or not hasattr(vs, '__iter__'):
                    vs = [vs]
                for v in vs:
                    result.append(
                        (k.encode('utf-8') if isinstance(k, str) else k,
                         v.encode('utf-8') if isinstance(v, str) else to_string(v)))
            return urlencode(result, doseq=True), self.content_type
        elif collection_format == 'encoded' and hasattr(data, '__iter__'):
            return urlencode(data, doseq=False), self.content_type
        elif hasattr(data, '__iter__'):
            results = []
            for k, vs in to_key_val_dict(data).items():
                if isinstance(vs, list):
                    v = self.COLLECTION_SEPARATORS[collection_format].join(quote_plus(e) for e in vs)
                    key = k + '[]'
                else:
                    v = quote_plus(vs)
                    key = k
                results.append("%s=%s" % (key, v))

            return '&'.join(results), self.content_type
        else:
            return data, self.content_type


class PlainTextRender(object):
    VALID_COLLECTION_FORMATS = ['multi', 'csv', 'ssv', 'tsv', 'pipes', 'plain']
    COLLECTION_SEPARATORS = {"csv": ",", "ssv": " ", "tsv": "\t", "pipes": "|"}

    def __init__(self, charset='utf-8', collection_format='multi'):
        self.charset = charset
        self.collection_format = collection_format

    @property
    def collection_format(self):
        return self._collection_format

    @collection_format.setter
    def collection_format(self, value):
        assert value in self.VALID_COLLECTION_FORMATS

        self._collection_format = value

    def get_content_type(self, charset=None):
        if charset is None:
            charset = self.charset
        if charset:
            return "text/plain; charset=%s" % self.charset
        return 'text/plain'

    @staticmethod
    def _encode(data, charset=None):
        return to_string(data).encode(charset) if charset else to_string(data)

    def encode_params(self, data=None, **kwargs):
        """
        Encode to plain text.
        Will successfully encode parameters when passed as a dict or a list of
        2-tuples. Order is retained if data is a list of 2-tuples but arbitrary
        if parameters are supplied as a dict.
        """
        charset = kwargs.get("charset", self.charset)
        collection_format = kwargs.get("collection_format", self.collection_format)

        if data is None:
            return "", self.get_content_type(charset)
        elif isinstance(data, (str, bytes)):
            return data, self.get_content_type(charset)
        elif hasattr(data, 'read'):
            return data, self.get_content_type(charset)
        elif collection_format == 'multi' and hasattr(data, '__iter__'):
            result = []
            for k, vs in to_key_val_list(data):
                if isinstance(vs, basestring) or not hasattr(vs, '__iter__'):
                    vs = [vs]
                for v in vs:
                    result.append("%s=%s" % (self._encode(k, charset), self._encode(v, charset)))
            return '\n'.join(result), self.get_content_type(charset)
        elif collection_format == 'plain' and hasattr(data, '__iter__'):
            results = []
            for k, vs in to_key_val_dict(data).items():
                results.append("%s=%s" % (self._encode(k, charset), self._encode(vs, charset)))

            return '\n'.join(results), self.get_content_type(charset)
        elif hasattr(data, '__iter__'):
            results = []
            for k, vs in to_key_val_dict(data).items():
                if isinstance(vs, list):
                    v = self.COLLECTION_SEPARATORS[collection_format].join(e for e in vs)
                    key = k + '[]'
                else:
                    v = vs
                    key = k
                results.append("%s=%s" % (self._encode(key, charset), self._encode(v, charset)))

            return '\n'.join(results), self.get_content_type(charset)
        else:
            return unicode(data).encode(charset) if charset else unicode(data), self.get_content_type(charset)


class JSONRender(object):

    def __init__(self):
        self.content_type = 'application/json'

    def encode_params(self, data=None, **kwargs):
        """
        Build the body for a application/json request.
        """
        if isinstance(data, basestring):
            raise ValueError("Data must not be a string.")
        if data is None:
            return "", self.content_type

        fields = to_key_val_dict(data or "")
        try:
            body = json.dumps(fields)
        except:
            body = json.dumps(fields, encoding='latin-1')

        return body, self.content_type
