# -*- coding: utf-8 -*-
import time,threading
def kcwcache_print_log(*strs):
    print(time.strftime("%Y-%m-%d %H:%M:%S"),*strs)
class vsregrsgtrdhbrhtrsgrshydtrsegregsresgr:
    wsobj=None
    __config={
        'debug':False,
        'th_lock':False,
        'url':'',
        'break':5 #断线重连次数，0表示不重连
    }
    __thlock={
        'obj':None,
        'status':False
    }
    def __connect(self):
        import websocket
        for i in range(100):
            self.wsobj = websocket.WebSocket()
            try:
                self.wsobj.connect(self.__config['url'])
            except websocket._exceptions.WebSocketBadStatusException:
                try:self.wsobj.close()
                except:pass
                self.wsobj=None
                if i>=self.__config['break']:
                    self.__close_th_lock()
                    raise Exception('连接已中止，请重新连接')
                time.sleep(0.1)
            except:
                try:self.wsobj.close()
                except:pass
                self.wsobj=None
                self.__close_th_lock()
                raise
            else:
                break
    def __start_th_lock(self):
        """开启线程锁 多线程中建议开启 注意 这个python多线程锁 而不是数据库事务锁"""
        if not self.__thlock['obj']:
            self.__thlock['obj']=threading.Lock()
        self.__thlock['obj'].acquire()
        self.__thlock['status']=True
        if self.__config['debug']:
            kcwcache_print_log('开启线程锁cache')
    def __close_th_lock(self):
        """退出线程锁 这个python多线程锁 而不是数据库事务锁"""
        if self.__thlock['status']:
            self.__thlock['obj'].release()
            self.__thlock['status']=False
            if self.__config['debug']:
                kcwcache_print_log('退出线程锁cache')
    def connect(self,url,th_lock=False):
        """设置连接

        url 连接地址 如  wss://websocket.kwebapp.cn/?unionid=1&token=1232

        th_lock 是否开启线程锁 多线程中建议开启 注意 这个python多线程锁 而不是redis库事务锁 也可以在配置信息中全局开启 
        
        """
        if th_lock!='no':
            self.__config['th_lock']=th_lock
        if self.__config['th_lock']:
            self.__start_th_lock()
        self.__config['url']=url
        return self

    def send(self,text):
        for i in range(100):
            if not self.wsobj:
                self.__connect()
            try:
                self.wsobj.send(text)
            except ConnectionAbortedError:
                try:self.wsobj.close()
                except:pass
                self.wsobj=None
                if i>=self.__config['break']:
                    self.__close_th_lock()
                    raise Exception('连接已中止，请重新连接')
                time.sleep(0.1)
            except:
                try:self.wsobj.close()
                except:pass
                self.wsobj=None
                self.__close_th_lock()
                raise
            else:
                self.__close_th_lock()
                break
    def recv(self):
        """接收数据"""
        for i in range(100):
            if not self.wsobj:
                self.__connect()
            try:
                data = self.wsobj.recv()
            except ConnectionAbortedError:
                try:self.wsobj.close()
                except:pass
                self.wsobj=None
                if i>=self.__config['break']:
                    self.__close_th_lock()
                    raise Exception('连接已中止，请重新连接')
                time.sleep(0.1)
            except:
                try:self.wsobj.close()
                except:pass
                self.wsobj=None
                self.__close_th_lock()
                raise
            else:
                self.__close_th_lock()
                break
        return data
            
        