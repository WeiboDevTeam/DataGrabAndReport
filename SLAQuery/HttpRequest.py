from urllib2 import Request,urlopen,URLError
from StringIO import StringIO
import gzip
import urllib2

__metaclass__ = type
class HttpRequest(object):

	def __init__(self, httpRequestUrl):
		super(HttpRequest, self).__init__()
		self.httpRequestUrl = httpRequestUrl

	def request(self):
		req = urllib2.Request(self.httpRequestUrl, headers=self.getHeaders())
		try:
			response = urllib2.urlopen(req)
			if response.info().get('Content-Encoding') == 'gzip':
				buf = StringIO(response.read())
				f = gzip.GzipFile(fileobj = buf)
				data = f.read()
			else :
				data = response.read()
			return data
		except URLError, e:
			if hasattr(e, 'reason'):
				print 'failed to reach a server'
				print 'Reason:',e.reason
				raise e
			elif hasattr(e, 'code'):
				print 'The server couldn\'t fulfill the request'
				print 'Error code: ',e.code
				raise e
		else:
			print 'request successed'
		return None

	def getHeaders(self):
		headers={'Accept-Encoding':"gzip, deflate, sdch",
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.86 Safari/537.36',
		'X-Requested-With': 'XMLHttpRequest',
		'Connection': 'keep-alive'}
		return headers
		




