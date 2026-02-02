# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from ..remote.webdriver import WebDriver as RemoteWebDriver
from ..common.desired_capabilities import DesiredCapabilities
from .service import Service
import os,requests

class WebDriver(RemoteWebDriver):
    """
    Wrapper to communicate with PhantomJS through Ghostdriver.

    You will need to follow all the directions here:
    https://github.com/detro/ghostdriver
    """

    def __init__(self, executable_path="",
                 port=0, desired_capabilities=DesiredCapabilities.PHANTOMJS,
                 service_args=None, service_log_path=None):
        """
        Creates a new instance of the PhantomJS / Ghostdriver.

        Starts the service and then creates new instance of the driver.

        :Args:
         - executable_path - path to the executable. If the default is used it assumes the executable is in the $PATH
         - port - port you would like the service to run, if left as 0, a free port will be found.
         - desired_capabilities: Dictionary object with non-browser specific
           capabilities only, such as "proxy" or "loggingPref".
         - service_args : A List of command line arguments to pass to PhantomJS
         - service_log_path: Path for phantomjs service to log to.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        # print("current_directory",current_directory)
        if not executable_path:
            if os.name == 'posix':
                executable_path=current_directory+'/phantomjs'
                downloadurl="https://file.kwebapp.cn/phantomjs/phantomjs"
            elif os.name == 'nt':
                executable_path=current_directory+'/phantomjs.exe'
                downloadurl="https://file.kwebapp.cn/phantomjs/phantomjs.exe"
            else:
                raise Exception("不支持当前操作系统")
            if not os.path.exists(executable_path):
                print("正在初始化可执行文件",downloadurl)
                response=requests.get(downloadurl)
                f=open(executable_path,"wb")
                tsize=f.write(response.content)
                f.close()
                if tsize<10*1024*1024:
                    os.remove(executable_path)
                    raise Exception('文件下载失败'+downloadurl)
                if os.name == 'posix':
                    os.system("chmod -R 777 "+executable_path)
            executable_path=r""+executable_path+""
        self.service = Service(
            executable_path,
            port=port,
            service_args=service_args,
            log_path=service_log_path)
        self.service.start()

        try:
            RemoteWebDriver.__init__(
                self,
                command_executor=self.service.service_url,
                desired_capabilities=desired_capabilities)
        except Exception:
            self.quit()
            raise

        self._is_remote = False

    def quit(self):
        """
        Closes the browser and shuts down the PhantomJS executable
        that is started when starting the PhantomJS
        """
        try:
            RemoteWebDriver.quit(self)
        except Exception:
            # We don't care about the message because something probably has gone wrong
            pass
        finally:
            self.service.stop()
