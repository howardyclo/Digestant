#!/usr/bin/env python
import sys, pycurl
try:
    from StringIO import StringIO
    from BytesIO import BytesIO
except ImportError:
    from io import StringIO,BytesIO
import sys
from lxml import etree
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
import json
try:
    reload(sys) 
    sys.setdefaultencoding('utf8') 
except:
    from importlib import reload
useragent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.2 (KHTML, like Gecko) Chrome/22.0.1216.0 Safari/537.2'

try:
    unicode('123')
except:
    def unicode(x):
        return x

class WebPage:
    def __init__(self):
        self.content = ''
        self.hitrule = []
        self.url = 'https://www.google.com.tw/search?q='

    def prune(self,query):
        querys = [x for(x) in query.split(" ") if len(x)>0]
        query = '+'.join(querys)
        return query

    def doquery(self,query):
        self.query = query

        import os.path
        if os.path.exists(query+".html"):
            self.content = open(query+".html").read()
            return self.content	

        qurl = self.url+query+'&num=100'
        #print qurl,'ok', type(qurl)

        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, qurl)
        c.setopt(c.USERAGENT, useragent)
        c.setopt(c.WRITEFUNCTION, buffer.write)
        c.perform()
        c.close()
        self.content = buffer.getvalue().decode('UTF-8')#buffer.getvalue()
        return self.content

    def showpage(self):        
        parser = etree.HTMLParser()
        xpath1 = '//*[@id="rso"]/div/div'
        xpath2 = '//*[@id="rso"]/div[2]/div/div[1]/div/h3/a'
        xpath3 = '//*[@id="rso"]/div[2]/div/div[9]/div/div/div/span'
        tree = etree.parse(StringIO(unicode(self.content)),parser)
        for i,tr in enumerate(tree.xpath(xpath1)[0].getchildren()):        
            arr = tree.xpath('//*[@id="rso"]/div/div/div['+str(i+1)+']/div/h3/a')
            for j,_ in enumerate(arr):
                #print arr[j].text
                #print "---> url:", arr[0].attrib['href']
                desc = tree.xpath('//*[@id="rso"]/div/div/div['+str(i+1)+']/div/div/div/span')
                for k,_ in enumerate(desc):
                    #print "---> sum:", desc[k].text
                    a =1


    def showpage(self,imax=3):

        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(unicode(self.content)),parser)

        import re
        def cleanhtml(raw_html):
            try:
                cleanr = re.compile('<.*?>')
                cleantext = re.sub(cleanr, '', raw_html)
            except:
                from bs4 import BeautifulSoup
                cleantext = BeautifulSoup(raw_html).text
            return cleantext
	
        def xcheck(tree,xpath0,n):
            r1 = ''
            u1 = ''
            t1 = tree.xpath(xpath0)
            if n<len(t1):
                if 'href' in t1[n].attrib:
                    u1 =  t1[n].attrib['href']
                r1 = cleanhtml(etree.tostring(t1[n],pretty_print=True))
                return r1.strip(),u1.strip()
            else:
                return None,None

        import HTMLParser
        hparser = HTMLParser.HTMLParser()    
        hparser.unescape('')
        xpath1 = '//*[@id="rso"]/div/div/div/div/div/h3/a'
        xpath2 = '//*[@id="rso"]/div/div/div/div/div/div/div/span'
        results = []
        for i in range(imax):
            r1,u1 = xcheck(tree,xpath1,i)
            r2,u2 = xcheck(tree,xpath2,i)
            if r1 is None: break
            r1d = hparser.unescape(r1.replace("\n",""))
            r2d = hparser.unescape(r2.replace("\n",""))
            results.append((r1d,u1,r2d,u2))
        return results

    def cache(self):
        f1 = open(self.query+".html","w")
        f1.write(self.content)
        f1.close()        

if __name__ == "__main__":
    go = WebPage()
    query = go.prune(sys.argv[1])
    #print query
    n = 3
    if len(sys.argv)>2:
        n = int(sys.argv[2])
    content = go.doquery(query)
    go.cache()
    result = go.showpage(n) 
    print (result)




