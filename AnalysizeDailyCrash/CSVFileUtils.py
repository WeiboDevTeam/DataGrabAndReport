import csv, codecs, cStringIO

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.DictReader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        if(isinstance(row,(list,tuple))):
            return [unicode(s, "utf-8") for s in row]
        elif(isinstance(row,dict)):
            for key in row.keys():
                value = row.get(key)
                if value!= None:
                    row[key]=unicode(value, "utf-8")
                else:
                    row[key]='None'
            return row

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, fieldnames=None, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.fieldnames = fieldnames
        self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writeHeader(self):
        if(self.fieldnames != None):
            self.writer.writeheader()
        else:
            pass

    def writerow(self, row):
        print row
        if(isinstance(row,(list,tuple))):
            self.writer.writerow([s.encode("utf-8") for s in row])
        elif(isinstance(row,dict)):
            for key in row.keys():
                value = row.get(key)
                if value!= None:
                    row[key]=value.encode("utf-8")
                else:
                    row[key]='None'
            self.writer.writerow(row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)