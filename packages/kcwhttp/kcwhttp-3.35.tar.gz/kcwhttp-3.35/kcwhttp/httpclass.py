# -*- coding: utf-8 -*-
import requests,traceback,time
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
from .selenium3 import webdriver as webdriver3
from .selenium3.webdriver.support import expected_conditions
import io
class Http:
    # By.CLASS_NAME
    webdriver3=webdriver3
    expecteds=expected_conditions
    "http请求类"
    set_session=True #是否启用会话
    set_impersonate=None #设置模拟浏览器指纹（chrome99、chrome100、chrome110、chrome118、chrome120,firefox100、firefox110,safari15、safari16） 
    set_proxies=None  #设置代理
    set_cookies={} #设置请求cookie
    set_header={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'} #请求头
    set_timeout=(6.05,10) #超时时间  6.05表示连接采时时间  3030表示读取超时时间  #注意 set_timeout参数主要关注的是“无响应”的时间段，而不是整个请求的处理时间
    set_max_retries=2 #重试次数 (实际请求3次)
    set_verify=False  #SSL 证书的验证 sll证书路径
    set_encoding="" #设置text输出编码 如utf-8 不填表示自动
    

    get_header={} #获取响应头
    get_cookies={} #获取最后的响应cookie
    get_cookie_str='' #获取最后的响应cookie 字符串
    get_text='' #获取body响应内容
    get_content='' #获取body响应二进制内容
    get_response='' #获取响应对象
    get_status_code=None #获取响应状态码
    keep_alive=True #默认的http connection是keep-alive的  False表示关闭
    req=None
    def __init(self):
        self.set_proxies=None  #设置代理
        self.set_cookies={} #设置请求cookie
        self.set_header={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'} #请求头
        self.set_timeout=(6.05,10) #超时时间  6.05表示连接采时时间  3030表示读取超时时间  #注意 set_timeout参数主要关注的是“无响应”的时间段，而不是整个请求的处理时间
        self.set_max_retries=2 #重试次数 (实际请求3次)
        self.set_verify=False  #SSL 证书的验证 sll证书路径
        self.set_encoding="" #设置text输出编码
        self.set_session=True #是否启用会话

        self.get_header={} #获取响应头
        self.get_cookies={} #获取最后的响应cookie
        self.get_cookie_str='' #获取最后的响应cookie 字符串
        self.get_text='' #获取body响应内容
        self.get_content='' #获取body响应二进制内容
        self.get_response='' #获取响应对象
        self.get_status_code=None #获取响应状态码
        self.keep_alive=True #默认的http connection是keep-alive的  False表示关闭
        self.req=None
        self.set_impersonate=None
    def __init__(self):
        self.__init()
    def __del__(self):
        self.__init()
    def gettext(self):
        """得到响应text"""
        return self.get_text
    def wait(self,wait_pq=[],wait_pq_type='element',sleep=1,Obj=None,url=''):
        from pyquery import PyQuery as kcwebspq
        """等待其中一个元素出现

        wait_pq 基于pyquery表达式 等待其中一个元素出现 (传入pyquery表达式 列表格式) 如 [['表达式1','表达式2'],['表达式3','表达式4']] 表示 表达式1或表达式2其中一个成立 并且 表达式3或表达式4其中一个成立

        wait_pq_type 等待类型： element表示等待元素出现 text表示等待元素内的文本出现  其他值表示等待标签属性值出现

        sleep 最多等待时间 建议配合wait_pq使用

        Obj webdriver的Chrome或PhantomJS对象
        """
        if wait_pq:
            if not Obj:
                if self.PhantomJsObj and self.ChromeObj:
                    raise Exception('Chrome和PhantomJS不可同时存在')
                if self.ChromeObj:
                    Obj=self.ChromeObj
                elif self.PhantomJsObj:
                    Obj=self.PhantomJsObj
            elif not Obj:
                raise Exception('Chrome对象和PhantomJS对象不存在')
            if sleep<10:
                sleep=10

            sfdsf=False
            for sdsa in range(10000):
                if sdsa>sleep*2:
                    self.get_text = Obj.page_source
                    raise Exception('max-wait_pq:'+url)
                time.sleep(0.5)
                doc=kcwebspq(Obj.page_source)
                sfdsf1=0
                for wait_pq1 in wait_pq:
                    if isinstance(wait_pq1, list) or isinstance(wait_pq1, tuple):
                        for wait_pq2 in wait_pq1:
                            tt=self.__get_pyquery_rules_obj(wait_pq2,doc)
                            if tt and tt.length:
                                if wait_pq_type=='text':
                                    if len(tt.text().replace(' ','').replace('\n','').replace('\r','').replace('\t',''))>0:
                                        sfdsf1+=1
                                        break
                                elif wait_pq_type=='element':
                                    sfdsf1+=1
                                    break
                                elif wait_pq_type:
                                    if tt.attr(wait_pq_type):
                                        sfdsf1+=1
                                        break
                    else:
                        tt=self.__get_pyquery_rules_obj(wait_pq1,doc)
                        if tt and tt.length:
                            if wait_pq_type=='text':
                                # print('tt.text()',wait_pq1)
                                if len(tt.text().replace(' ','').replace('\n','').replace('\r','').replace('\t',''))>0:
                                    sfdsf=True
                                    break
                            elif wait_pq_type=='element':
                                sfdsf=True
                                break
                            elif wait_pq_type:
                                if tt.attr(wait_pq_type):
                                    sfdsf=True
                                    break
                if sfdsf or sfdsf1==len(wait_pq):
                    break
        self.get_text = Obj.page_source
    PhantomJsObj=None
    def open_PhantomJS(self,url,executable_path='',closedriver=True,wait_pq=[],wait_pq_type='element',sleep=1):
        """通过PhantomJS引擎模拟浏览器请求 可以获取到js渲染后的html

        wait_pq 基于pyquery表达式 等待其中一个元素出现 (传入pyquery表达式 列表格式) 如 [['表达式1','表达式2'],['表达式3','表达式4']] 表示 表达式1或表达式2其中一个成立 并且 表达式3或表达式4其中一个成立

        wait_pq_type 等待类型： element表示等待元素出现 text表示等待元素内的文本出现  其他值表示等待标签属性值出现
        
        sleep 最多等待时间 建议配合wait_pq使用
        
        """
        if self.set_cookies and isinstance(self.set_cookies,str):
            self.set_cookies=self.cookieserTdict(self.set_cookies)
        if not self.PhantomJsObj:
            self.PhantomJsObj=webdriver3.PhantomJS(executable_path=executable_path)
        # if self.set_session:
        #     self.get_cookies=self.set_cookies
        #     for k in self.PhantomJsObj.get_cookies():
        #         self.get_cookies=self.__merge(self.get_cookies,k)
        #     if self.get_cookies:
        #         self.get_cookie_str=self.cookieTdictstr(self.get_cookies)
        #         self.get_cookies=self.cookieserTdict(self.get_cookie_str)
        #     if self.get_cookies!=self.set_cookies:
        #         self.PhantomJsObj.delete_all_cookies()
        #         for k in self.set_cookies:
        #             t={'name':k, 'value':self.set_cookies[k]}
        #             self.PhantomJsObj.add_cookie(t)
        
        i=0
        while True:
            try:
                self.PhantomJsObj.get(url)
            except Exception as e:
                estr=str(e)
                print('estr',estr)
                if 'error: net::ERR_CONNECTION_CLOSED' in estr or  'timeout: Timed out receiving message from rendere' in estr or 'error: net::ERR_CONNECTION_RESET' in estr or 'error: net::ERR_NAME_NOT_RESOLVED' in estr or 'unknown error: net::ERR_CONNECTION_TIMED_OUT' in estr or 'Max retries exceeded with url' in estr or 'error: net::ERR_SSL_VERSION_OR_CIPHER_MISMATCH' in estr or 'error: net::ERR_CONNECTION_REFUSED' in estr:
                    if i>self.set_max_retries:
                        raise Exception('max_retries'+estr)
                    i+=1
                else:
                    raise
            else:
                break
        if not closedriver:
            try:
                response = requests.head(url,cookies=self.set_cookies,allow_redirects=True)
            except:pass
            else:
                resheader=dict(response.headers)
                self.get_header={}
                for k in resheader:
                    self.get_header[k.lower()]=resheader[k]
        if not wait_pq and sleep:
            time.sleep(sleep)
        self.wait(wait_pq=wait_pq,wait_pq_type=wait_pq_type,sleep=sleep,Obj=self.PhantomJsObj,url=url)
        # self.get_text = self.PhantomJsObj.page_source
        # self.get_cookies=self.set_cookies
        for k in reversed(self.PhantomJsObj.get_cookies()):
            zd={k['name']:k['value']}
            self.get_cookies=self.__merge(self.get_cookies,zd)
        if self.get_cookies:
            self.get_cookie_str=self.cookieTdictstr(self.get_cookies)
            self.get_cookies=self.cookieserTdict(self.get_cookie_str)
        # if self.set_session:
        #     self.set_cookies=self.get_cookies
        if closedriver:
            self.PhantomJsObj.quit()
            self.PhantomJsObj=None
    ChromeObj=None
    def open_Chrome(self,url,executable_path='',closedriver=True,setheadless=True,wait_pq=[],wait_pq_type='element',sleep=1,devtools=False):
        """通过Chrome浏览器引擎模拟浏览器请求 可以获取到js渲染后的html

        closedriver 是否关闭退出

        setheadless 是否设置无头

        wait_pq 基于pyquery表达式 等待其中一个元素出现 (传入pyquery表达式 列表格式) 如 [['表达式1','表达式2'],['表达式3','表达式4']] 表示 表达式1或表达式2其中一个成立 并且 表达式3或表达式4其中一个成立

        wait_pq_type 等待类型： element表示等待元素出现 text表示等待元素内的文本出现  其他值表示等待标签属性值出现

        sleep 最多等待时间 建议配合wait_pq使用

        """
        # if wait_pq_type not in ['element','text']:
        #     raise Exception('wait_pq_type 错误')
        if self.set_cookies and isinstance(self.set_cookies,str):
            self.set_cookies=self.cookieserTdict(self.set_cookies)
        # print('self.set_cookiesself.set_cookiesself.set_cookies',self.set_cookies)
        if not self.ChromeObj:
            chrome_options = webdriver3.chrome.options.Options()
            
            if setheadless:
                chrome_options.add_argument("--headless") #设置无头
            else:
                if devtools:
                    chrome_options.add_argument("--auto-open-devtools-for-tabs")  # 打开开发者工具
                chrome_options.add_argument('--disable-infobars') # 隐藏 "Chrome 正受到自动测试软件控制" 提示栏
            if self.set_proxies:
                # chrome_options.add_argument("--proxy-server=http://proxyserver:port")
                if self.set_proxies['http']:
                    chrome_options.add_argument("--proxy-server="+self.set_proxies['http'])
                elif self.set_proxies['https']:
                    chrome_options.add_argument("--proxy-server="+self.set_proxies['https'])
                # print(self.set_proxies)
                # exit()

            chrome_options.add_argument("--disable-gpu")  # 禁用GPU硬件加速，适用于Linux和Windows系统
            chrome_options.add_argument("--no-sandbox")  # 禁用沙盒模式，在某些Linux系统上需要

            # chrome_options.add_argument('--log-level=3')  # 关闭所有非致命日志
            # chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁止 Selenium 自身日志
            
            

            # 禁用自动化控制特征（减少被检测风险）
            chrome_options.add_argument('--disable-blink-features=AutomationControlled') 
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])

            chrome_options.add_argument('--ignore-certificate-errors') # 忽略所有证书错误
            chrome_options.add_argument('--ignore-ssl-errors') # 忽略 SSL 相关错误（如握手失败）

            try:
                self.ChromeObj = webdriver3.Chrome(executable_path=executable_path,chrome_options=chrome_options)
            except Exception as e:
                import os
                print("\033[93mChromeChromeChromeChromeChromeChromeChromeChromeChromeChromeChromeChromeve\033[0m",e)
                if os.name == 'nt' and 'Driver info: chromedriver=142.0.7444.175' in str(e):
                    # print("\033[93mchromedriver与您操作系统的Chrome不兼容性 下载地址参考",'https://file.kwebapp.cn/sh/install/chrome/chromedriver-win64-142/GoogleChrome.msi\033[0m')
                    response=requests.get('https://file.kwebapp.cn/sh/install/chrome/chromedriver-win64-142/GoogleChrome.msi')
                    f=open('Chrome.msi',"wb")
                    tsize=f.write(response.content)
                    f.close()
                    if tsize<10*1024*1024:
                        os.remove('Chrome.msi')
                        raise Exception('文件下载失败:https://file.kwebapp.cn/sh/install/chrome/chromedriver-win64-142/GoogleChrome.msi')
                    print('\033[93mchromedriver与您操作系统的Chrome不兼容/不存在，正在为您安装Chrome...\033[0m')
                    os.system("msiexec /i Chrome.msi")
                    os.remove('Chrome.msi')
                    # print('\033[93m安装完成，请重试\033[0m')
                    self.open_Chrome(url=url,executable_path=executable_path,closedriver=closedriver,setheadless=setheadless)
                elif os.name == 'posix' and 'Driver info: chromedriver=106.0.5249.21' in str(e):
                    def systemtypes():
                        try:
                            with open('/etc/os-release', 'r') as f:
                                content = f.read()
                                if 'CentOS-7' in content or 'CentOS Linux 7' in content:
                                    return 'CentOS7'
                        except FileNotFoundError:
                            pass
                        return False
                    t=systemtypes()
                    if t=='CentOS7':
                        # print("\033[93mchromedriver与您操作系统的Chrome不兼容性 下载地址参考",'https://file.kwebapp.cn/sh/install/chrome/google-chrome-unstable-106.0.5249.12-1.x86_64.rpm\033[0m')
                        response=requests.get('https://file.kwebapp.cn/sh/install/chrome/google-chrome-unstable-106.0.5249.12-1.x86_64.rpm')
                        f=open('google-chrome-unstable-106.0.5249.12-1.x86_64.rpm',"wb")
                        tsize=f.write(response.content)
                        f.close()
                        if tsize<10*1024*1024:
                            os.remove('google-chrome-unstable-106.0.5249.12-1.x86_64.rpm')
                            raise Exception('文件下载失败:https://file.kwebapp.cn/sh/install/chrome/google-chrome-unstable-106.0.5249.12-1.x86_64.rpm')
                
                        print('\033[93mchromedriver与您操作系统的Chrome不兼容/不存在，正在为您安装Chrome...\033[0m')
                        os.system("sudo yum -y install google-chrome-unstable-106.0.5249.12-1.x86_64.rpm")
                        os.remove('google-chrome-unstable-106.0.5249.12-1.x86_64.rpm')
                        # print('\033[93m安装完成，请重试\033[0m')
                        self.open_Chrome(url=url,executable_path=executable_path,closedriver=closedriver,setheadless=setheadless)
                    else:
                        raise Exception('暂不支持该操作系统版本，目前仅支持CentOS7和windows10。'+str(e))
                else:
                    raise Exception('暂不支持该操作系统版本，目前仅支持CentOS7和windows10'+str(e))
        
        if self.ChromeObj:
            # if self.set_session:
            #     self.get_cookies=self.set_cookies
            #     for k in self.ChromeObj.get_cookies():
            #         self.get_cookies=self.__merge(self.get_cookies,k)
            #     if self.get_cookies:
            #         self.get_cookie_str=self.cookieTdictstr(self.get_cookies)
            #         self.get_cookies=self.cookieserTdict(self.get_cookie_str)
            #     if self.get_cookies!=self.set_cookies:
            #         self.ChromeObj.delete_all_cookies()
            #         for k in self.set_cookies:
            #             t={'name':k, 'value':self.set_cookies[k]}
            #             # print('ttttt',t)
            #             self.ChromeObj.add_cookie(t)
            
            i=0
            while True:
                try:
                    self.ChromeObj.get(url)
                except Exception as e:
                    estr=str(e)
                    if 'error: net::ERR_CONNECTION_CLOSED' in estr or  'timeout: Timed out receiving message from rendere' in estr or 'error: net::ERR_CONNECTION_RESET' in estr or 'error: net::ERR_NAME_NOT_RESOLVED' in estr or 'unknown error: net::ERR_CONNECTION_TIMED_OUT' in estr or 'Max retries exceeded with url' in estr or 'error: net::ERR_SSL_VERSION_OR_CIPHER_MISMATCH' in estr or 'error: net::ERR_CONNECTION_REFUSED' in estr:
                        if i>self.set_max_retries:
                            raise Exception('max_retries'+estr)
                        i+=1
                    else:
                        raise
                else:
                    break
            if not closedriver:
                try:
                    response = requests.head(url,cookies=self.set_cookies,allow_redirects=True)
                except:pass
                else:
                    resheader=dict(response.headers)
                    self.get_header={}
                    for k in resheader:
                        self.get_header[k.lower()]=resheader[k]
            if not wait_pq and sleep:
                time.sleep(sleep)
            self.wait(wait_pq=wait_pq,wait_pq_type=wait_pq_type,sleep=sleep,Obj=self.ChromeObj,url=url)
            # self.get_text = self.ChromeObj.page_source
            # self.get_cookies=self.set_cookies
            for k in reversed(self.ChromeObj.get_cookies()):
                zd={k['name']:k['value']}
                self.get_cookies=self.__merge(self.get_cookies,zd)
            if self.get_cookies:
                self.get_cookie_str=self.cookieTdictstr(self.get_cookies)
                self.get_cookies=self.cookieserTdict(self.get_cookie_str)
            # if self.set_session:
            #     self.set_cookies=self.get_cookies
            if closedriver:
                self.ChromeObj.quit()
                self.ChromeObj=None
    def Chrome_screenshot(self,xpath,outfile):
        """Chrome截图

        xpath  元素 xpath

        outfile 截图保存位置
        
        """
        from PIL import Image
        element=self.ChromeObj.find_element(self.webdriver3.common.by.By.XPATH,xpath)
        screenshot = self.ChromeObj.get_screenshot_as_png()
        screenshot_img = Image.open(io.BytesIO(screenshot))
        location = element.location
        size = element.size
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        screenshot_img = screenshot_img.crop((left, top, right, bottom))
        # 保存或显示裁剪后的图片
        screenshot_img.save(outfile)
    def close_webdriver(self):
        if self.ChromeObj:
            self.ChromeObj.quit()
            self.ChromeObj=None
        if self.PhantomJsObj:
            self.PhantomJsObj.quit()
            self.PhantomJsObj=None
            
    def openurl(self,url,method="GET",data=None,params=None,jsonparams=None,files=None,allow_redirects=True):
        """模拟浏览器请求

        url : 目标地址

        method ：GET POST 等

        data：请求参数

        params:请求参数

        jsonparams:请求json参数

        file 上传文件

        allow_redirects 是否重定向
        """
        if self.set_impersonate:
            from curl_cffi import requests as curl_cffi_requests
        if self.set_session:
            if self.req is None:
                if self.set_impersonate:
                    self.req = curl_cffi_requests.Session(impersonate=self.set_impersonate)
                else:
                    self.req = requests.Session()
                    self.req.mount('http://', requests.adapters.HTTPAdapter(max_retries=self.set_max_retries))
                    self.req.mount('https://', requests.adapters.HTTPAdapter(max_retries=self.set_max_retries))
        else:
            if self.req is None:
                if self.set_impersonate:
                    self.req = curl_cffi_requests
                else:
                    self.req = requests
        if not self.keep_alive:
            self.req.keep_alive=False
        if self.set_cookies and isinstance(self.set_cookies,str):
            self.set_cookies=self.cookieserTdict(self.set_cookies)
        if self.set_impersonate:
            method=method.lower()
            if self.set_session:
                if method=='get':
                    response=self.req.get(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects)
                elif method=='post':
                    response=self.req.post(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects)
                elif method=='put':
                    response=self.req.put(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects)
                elif method=='patch':
                    response=self.req.patch(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects)
                elif method=='delete':
                    response=self.req.delete(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects)
                # elif method=='head':
                #     response=self.req.head(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects)
                else:
                    raise Exception('不支持method='+method)
            else:
                if method=='get':
                    response=self.req.get(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects,impersonate=self.set_impersonate)
                elif method=='post':
                    response=self.req.post(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects,impersonate=self.set_impersonate)
                elif method=='put':
                    response=self.req.put(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects,impersonate=self.set_impersonate)
                elif method=='patch':
                    response=self.req.patch(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects,impersonate=self.set_impersonate)
                elif method=='delete':
                    response=self.req.delete(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects,impersonate=self.set_impersonate)
                # elif method=='head':
                #     response=self.req.head(url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects)
                else:
                    raise Exception('不支持method='+method)
            # if self.set_encoding:
            #     response.encoding=self.set_encoding
            # else:
            #     response.encoding=response.apparent_encoding
            resheader=dict(response.headers)
            self.get_header={}
            for k in resheader:
                self.get_header[k.lower()]=resheader[k]
            cookie=dict(response.cookies)
            if self.get_cookies and cookie:
                self.get_cookies=self.__merge(self.get_cookies,cookie)
            elif cookie:
                self.get_cookies=cookie
            if self.set_cookies:
                self.get_cookies=self.__merge(self.set_cookies,self.get_cookies)
            if self.get_cookies:
                self.get_cookie_str=self.cookieTdictstr(self.get_cookies)
            self.get_text=response.text
            self.get_content=response.content
            self.get_response=response
            self.get_status_code=int(response.status_code)
        else:
            response=self.req.request(method, url,data=data,params=params,json=jsonparams,files=files,proxies=self.set_proxies,cookies=self.set_cookies,headers=self.set_header,timeout=self.set_timeout,verify=self.set_verify,allow_redirects=allow_redirects)
            if self.set_encoding:
                response.encoding=self.set_encoding
            else:
                response.encoding=response.apparent_encoding
            resheader=dict(response.headers)
            self.get_header={}
            for k in resheader:
                self.get_header[k.lower()]=resheader[k]
            cookie=requests.utils.dict_from_cookiejar(response.cookies)
            if self.get_cookies and cookie:
                self.get_cookies=self.__merge(self.get_cookies,cookie)
            elif cookie:
                self.get_cookies=cookie
            if self.set_cookies:
                self.get_cookies=self.__merge(self.set_cookies,self.get_cookies)
            if self.get_cookies:
                self.get_cookie_str=self.cookieTdictstr(self.get_cookies)
            self.get_text=response.text
            self.get_content=response.content
            self.get_response=response
            self.get_status_code=int(response.status_code)
    def __is_index(self,params,index):
        """判断列表或字典里的索引是否存在

        params  列表或字典

        index   索引值

        return Boolean类型
        """
        try:
            params[index]
        except KeyError:
            return False
        except IndexError:
            return False
        else:
            return True
    def __merge(self,dict1, dict2):
        "合并两个字典"
        C_dict = {}
        if dict1:
            for key,value in dict1.items():
                C_dict[key]=value
        for key,value in dict2.items():
            if value:
                if isinstance(value, str) or (self.__is_index(C_dict,key) and isinstance(C_dict[key], str)):
                    if self.__is_index(C_dict,key):
                        t1,t2=len(str(value)),len(str(C_dict[key]))
                        if t1>=t2:
                            C_dict[key]=value
                    else:
                        C_dict[key]=value
                else:
                    C_dict[key]=value
        return C_dict
    def cookieserTdict(self,cookiesstr):
        "cookies字符串转换字典"
        if isinstance(cookiesstr,str):
            cok={}
            for line in cookiesstr.split(";"):
                lists=line.split("=")
                # print("listslists",lists)
                if lists[0] and len(lists)==2:
                    cok[lists[0]]=lists[1]
            return cok
    def cookieTdictstr(self,cookie):
        cookiestr=''
        for key in cookie:
            if not cookie[key]:
                cookie[key]=''
            cookiestr+=str(key)+"="+str(cookie[key])+";"
        return cookiestr
    def __get_pyquery_rules(self,rulestext):
        """获取pyquery规则
        
        rulestext 规则字符串 参考 (.page-tip{0} 表示选择第一个 .page-tip{1} 表示选择第二个)
        
        """
        tkevalarr=rulestext.split('}')
        tkevalarr1=[]
        for tttt in tkevalarr:
            eq='null'
            if '{' in tttt:
                tttttt=tttt.split('{')
                eq=int(tttttt[1])
                tttt=tttttt[0]
            if tttt:
                tkevalarr1.append({'val':tttt,'eq':eq})
        return tkevalarr1
    def __get_pyquery_rules_obj(self,rulestext,pyqueryobj):
        """通过pyquery规则获取列表对象
        
        rulestext 规则字符串 参考 .gknb-box[1]ul li

        pyqueryobj pyquery装载html后的对象  pq(html)

        return 返回 pyquery选中的对象

        """
        if ',' in rulestext:
            pqobj=None
            rulestextarr=rulestext.split(',')
            for rulestext in rulestextarr:
                tkevalarr1=self.__get_pyquery_rules(rulestext)
                pqobj=None
                lists=pyqueryobj
                for tttt in tkevalarr1:
                    lists=lists.find(tttt['val'])
                    if tttt['eq']>=1:
                        lists=lists.eq(tttt['eq'])
                
                if lists.length:
                    pqobj=lists
                    break
            return pqobj
        else:
            tkevalarr1=self.__get_pyquery_rules(rulestext)
            pqobj=None
            lists=pyqueryobj
            for tttt in tkevalarr1:
                lists=lists.find(tttt['val'])
                if tttt['eq']!='null':
                    lists=lists.eq(tttt['eq'])
            
            if lists.length:
                pqobj=lists
            return pqobj
