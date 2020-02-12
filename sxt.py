# -*- coding: utf-8 -*-
"""
Created on Wed May 30 17:54:35 2018

@author: xici

#https://www.bjsxt.com/down/8468.html
"""

import threading
import requests
import re
import json,os,shutil
from hyper.contrib import HTTP20Adapter
from bs4 import BeautifulSoup
import js2xml
from lxml import etree
import time,datetime
import math

from tempfile import TemporaryFile,NamedTemporaryFile


#消除https访问时的警告
#老版本
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#新版本
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



class sxt(object):

    #参数，存储位置，下载内容的地址list，下载内容的主页
    def __init__(self,driver,urls,indexurl=''):
        self.session=requests.Session()
        self.driver=driver
        self.urls=urls
        self.indexurl=indexurl
        self.http=None
        
        

    def getInfo(self,url):
        res=self.session.get(url,verify=False)
        html=str(res.content,'UTF-8')
        return html
        
    def analyze(self,html):
        #print(html)
        soup = BeautifulSoup(html, 'lxml')
        self.findList(soup)
        
    def findList(self,soup):
        #print('findList')
        #print(type(soup))
        chapters=soup.select('div[class="dlcontent"] > div.dlinfo.dlinfo2 > div[class="div_xlbtn"]')
        print('chapter count: %d'%len(chapters))
        
        courses=[]
        for case in chapters:
            if case.get_text().strip()=='':
                continue
            chapterCourses=self.findCase(case)
            courses=courses+chapterCourses
            #break
        
        print('get all %d'%len(courses))
        
        for course in courses:
            self.downloadCourse(course)
            pass
        
        
    def downloadCourse(self,course):
        print('')
        print('downloading...%s'%course.name)
        print('from %s'%course.url)
        surfix=course.url[course.url.rfind('.'):]
        if '?' in surfix:
            surfix=surfix[:surfix.find('?')]
        print(surfix)
        #surfix='.mp4'
        #driver='J:\\book\\ai\\python_400_spider'
        self.download(course.url,course.chapter,course.name+surfix,self.driver)
        
    #driver为空时，则指定存储位置，否则默认为当前运行路径下
    def download(self,url,folder,filename,driver=''):
        if driver=='':
            download_path = os.getcwd() + '\\'+folder
        else:
            download_path = driver + '\\'+folder
            
        if not os.path.exists(download_path):
            os.mkdir(download_path)
            
        dist=download_path+'\\'+filename
        print('save as %s'%dist)
        
        #method 1
        #r = self.session.get(url) 
        #with open(dist, "wb") as code:
        #    code.write(r.content)
        
        #method 3
        #self.downloader(url,dist) #ok , 只是速度有点慢，单线程
        
        #mehtod 4
        self.downloaderMultiple(url,dist,5) #有可能数据错乱
    
    #多线程，进度条显示有点问题
    def downloaderMultiple(self,url,path,threadnum=10):
        if os.path.isfile(path):#多线程暂不支持断点续传
            print('exists')
            return
            
        class Mythread(threading.Thread):
            def __init__(self,url,startpos,endpos,f):
                super(Mythread,self).__init__()
                self.url=url
                self.startpos=startpos
                self.endpos=endpos
                self.fd=f
            def download(self):
                #print('start thread: %s at %s'%(self.getName(),time.time()))
                print('start thread: %s at %s'%(self.getName(),time.strftime("%Y-%m-%d %H:%M:%S" ,  time.localtime() )))
                headers={'Range':'bytes=%s-%s'%(self.startpos,self.endpos)}
                res=requests.get(self.url,headers=headers)
                self.fd.seek(self.startpos)
                self.fd.write(res.content)
                print('Finish thread: %s at %s'%(self.getName(),time.strftime("%Y-%m-%d %H:%M:%S" ,  time.localtime() )))
                self.fd.close()
            def run(self):
                self.download()
        class MythreadProgress(threading.Thread):
            def __init__(self,url,startpos,endpos,f):
                super(MythreadProgress,self).__init__()
                self.url=url
                self.startpos=startpos
                self.endpos=endpos
                self.fd=f
                self.gotsize=0
                
            def download(self):
                print('thread[%s] fetch [%s,%s]'%(self.getName(),self.startpos,self.endpos))
                headers={'Range':'bytes=%s-%s'%(self.startpos,self.endpos)}
                res=requests.get(self.url,headers=headers,stream=True)
                content_size=int(res.headers['content-length'])
                chunk_size=1024
                size=0
                #print('thread:[%s] status code %s at %s'%(self.getName(),res.status_code,time.time()))
                
                #使用临时文件
                #用文件描述符来操作临时文件
                f = TemporaryFile()
                #f.seek(0)
                #f.read(100)
                ntf = NamedTemporaryFile()
                #返回文件路径
                #print('temp file name %s'%ntf.name)
                
                for data in res.iter_content(chunk_size=chunk_size):
                    #print('got data %d'%len(data))
                    f.write(data)
                    size+=len(data)
                    #print('got %d of %d'%(size,self.endpos-self.startpos+1))
                    print('\r'+'%s[下载进度]: %s%.2f%%'%(self.getName(),'>'*int(size*50/content_size),float(size/content_size*100)),end='') #当前行目前无法很好的同时在控制台输出显示。暂时更改为总的一个进度条
                    self.gotsize=size
                #print('writing %d bytes at %d'%(size,self.startpos))
                self.fd.seek(self.startpos)
                f.seek(0)
                self.fd.write(f.read(size))
                self.fd.close()
                print('\nthread:[%s] stop at %s'%(self.getName(),time.time()))
                
                
            def run(self):
                self.download()
                
        
        timestart=time.time()
        response=requests.get(url,stream=True)
        content_size=int(response.headers['content-length'])
        chunk_size=1024
        print('[文件大小]: %0.2f MB' %(content_size/1024/1024))
            
        threading.BoundedSemaphore(threadnum)#允许线程个数
        #step=content_size//threadnum
        step=math.ceil(content_size/threadnum)
        mtd_list=[]
        start=0
        end=-1
        
        tempf = open(path,'w')
        tempf.close()
        mtd_list=[]
        with open(path,'rb+')as f:
            #获得文件句柄
            fileno=f.fileno()#返回一个整型的文件描述符，可用于底层操作系统的 I/O 操作
            while end<content_size-1:
                start=end+1
                end=start+step-1
                if end>content_size:
                    end=content_size
                #print ('Start: %s, end: %s'%(start,end))
                dup=os.dup(fileno)#复制文件句柄
                fd=os.fdopen(dup,'rb+',-1)
                #t=MythreadProgress(url,start,end,fd)
                t=Mythread(url,start,end,fd)
                t.start()
                mtd_list.append(t)
            
            for i in mtd_list:
                i.join()
                
        f.close()
        
        timeend=time.time()
        print('\n'+'全部下载完成！用时%.2f秒'%(timeend-timestart))
        
    #支持断点续传
    def downloader(self,url,path):
        temp_size=0
        if os.path.isfile(path):
            temp_size = os.path.getsize(path)
            
        start=time.time()
        size=0
        #headers = {'Range': 'bytes=0-0'}
        response=requests.get(url,stream=True)
        chunk_size=1024
        content_size=int(response.headers['content-length'])
        print('%d of %d'%(temp_size,content_size))
        if temp_size>=content_size:
            print('it is completely downloaded.')
            return
        
        headers = {'Range': 'bytes=%d-' % temp_size}
        response = requests.get(url, stream=True,headers=headers)
        #if response.status_code==200:
        if True:
            print('[文件大小]: %0.2f MB' %(content_size/1024/1024))
            with open(path,'ab') as file: #新建用wb,ab为追加
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    size+=len(data)
                    print('\r'+'[下载进度]: %s%.2f%%'%('>'*int(size*50/content_size),float(size/content_size*100)),end='')
            end=time.time()
            print('\n'+'全部下载完成！用时%.2f秒'%(end-start))
        
    #取得一个章节的内容
    def findCase(self,case):
        chaptername=''
        #print(type(case))
        #print(case.select('p'))
        #print(case)
        chaptername=case.select('p')[0].get_text().strip()
        print('')
        print(chaptername)
        courseHtmls=case.select('a')
        courses=[]
        for courseHtml in courseHtmls:
            #print(courseHtml)
            clickjs=courseHtml.attrs['onclick']
            course=self.analyzeUrl(clickjs)
            course.chapter=chaptername
            courses.append(course)
            #print(course.toString())
            #break
        print('finding...%d'%len(courses))
        return courses
        
        
    #plays('https://2018bjsxt.cdn.bcebos.com/python%2F001.Python%E4%BB%8B%E7%BB%8D_%E7%89%B9%E6%80%A7_%E7%89%88%E6%9C%AC%E9%97%AE%E9%A2%98_%E5%BA%94%E7%94%A8%E8%8C%83%E5%9B%B4.mp4',false,'001.Python介绍_特性_版本问题_应用范围');
    #解析出 mp4地址,名字
    def analyzeUrl(self,clickjs):
        #print(clickjs)
        clickjs=clickjs[len('plays('):-2]
        #print(clickjs)
        args=re.findall('\\\'(.*?)\\\'',clickjs)
        #print(args)
        course=Course()
        course.url=args[0]
        course.name=args[1].strip()
        return course
        
    def getUrls(self):
        html=self.getInfo(self.indexurl)
        soup = BeautifulSoup(html, 'lxml')
        chapters=soup.select('div.video_course_right > a')
        print('url count: %d'%len(chapters))
        
        courses=[]
        for case in chapters:
            if case.get_text().strip()=='':
                continue
            self.urls.append(case.attrs['href'])
            #break
            
    def test(self):
        html=''
        with open('s.html', "r",encoding='utf-8') as f:
            html=f.read()
        if len(html)>0:
            self.analyze(html)
        
    def main(self):
        if self.indexurl:
            self.getUrls()
            
        for url in self.urls:
            #url='https://www.bjsxt.com/down/8468.html'
            self.analyze(self.getInfo(url))
        
    
class Course(object):
    def __init__(self):
        self.name=''
        self.url=''
        self.chapter=''
        
    def toString(self):
        return (self.chapter+'\t'+self.name+'\t'+self.url)
        
if __name__ == '__main__':
    #下载python 400集
    #sxt=sxt('J:\\book\\ai\\python_400_spider',['https://www.bjsxt.com/down/8468.html'])
    #sxt.test()
    #sxt.main()
    
    #下载ai
    sxt=sxt('J:\\book\\ai\\sxt_ai',[],'https://www.bjsxt.com/rengongzhinengshipin.html')
    sxt.main()
    
    #test
    #sxt.downloaderMultiple('http://2018bjsxt.bj.bcebos.com/ai%2F01_%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%BC%80%E5%8F%91%E5%8F%8A%E8%BF%9C%E6%99%AF%E4%BB%8B%E7%BB%8D%2F2_%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E4%B8%8E%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0%E5%85%B3%E7%B3%BB.mp4','J:\\book\\ai\\sxt_ai\\t.mp4',3) #OK 只是显示进度有点小问题，多个线程都显示到了一行
    #test
    #sxt.downloaderMultiple('https://img-blog.csdn.net/20170212212717104?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvZ3diYmlnYmFuZw==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast','J:\\book\\ai\\sxt_ai\\t.png',3) #ok
    