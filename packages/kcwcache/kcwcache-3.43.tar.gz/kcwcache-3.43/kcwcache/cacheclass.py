# -*- coding: utf-8 -*-
import os,time,hashlib,copy,threading
def feagesgvresgaeagis_index(params,index):
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
try:
    import kcwredis
    from kcwebs.config import cache as cacheconfig
    if not feagesgvresgaeagis_index(cacheconfig,'th_lock'):
        cacheconfig['th_lock']=False
    if not feagesgvresgaeagis_index(cacheconfig,'th_lock'):
        cacheconfig['debug']=False
except:
    cacheconfig={}
    cacheconfig['th_lock']=False
    cacheconfig['debug']=False
    cacheconfig['type']='File' #驱动方式 支持 File Redis Python
    cacheconfig['path']='app/runtime/cachepath' #缓存保存目录 
    cacheconfig['expire']=120 #缓存有效期 0表示永久缓存
    cacheconfig['host']='127.0.0.1' #Redis服务器地址
    cacheconfig['port']=6379 #Redis 端口
    cacheconfig['password']='' #Redis登录密码
    cacheconfig['db']=1 #Redis数据库    注：Redis用1或2或3等表示
cachevalue={}
def kcwcache_print_log(*strs):
    print(time.strftime("%Y-%m-%d %H:%M:%S"),*strs)
class vsregrsgtrdhbrhtrsgrshydtrsegregsresgr:
    __name=None
    __values=None
    __config=copy.deepcopy(cacheconfig)
    __redisobj=None

    __thlock={
        'obj':None,
        'status':False
    }
    def __md5(self,strs):
        """md5加密"""
        if not strs:
            return strs
        m = hashlib.md5()
        b = strs.encode(encoding='utf-8')
        m.update(b)
        return m.hexdigest()
    def __times(self):
        """时间戳 精确到秒"""
        return int(time.time())
    def __json_decode(self,jsonstr):
        """json字符串转python类型"""
        try:
            return eval(jsonstr)
        except Exception:
            return {}
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
    def set_config(self,config,th_lock='no'):
        """设置缓存配置

        th_lock 是否开启线程锁 多线程中建议开启 注意 这个python多线程锁 而不是redis库事务锁 也可以在配置信息中全局开启 
        """
        if th_lock!='no':
            config['th_lock']=th_lock
        if config['th_lock']:
            self.__start_th_lock()
        self.__config=copy.deepcopy(config)
        return self
    def __setredisobj(self):
        "设置redis链接实例"
        conf=copy.deepcopy(cacheconfig)
        if 'host' in self.__config and self.__config['host']:
            conf['host']=self.__config['host']
        if 'port' in self.__config and self.__config['port']:
            conf['port']=self.__config['port']
        if 'password' in self.__config and self.__config['password']:
            conf['password']=self.__config['password']
        if 'db' in self.__config and self.__config['db']:
            conf['db']=self.__config['db']
        if not self.__redisobj:
            self.__redisobj=kcwredis.redis
        self.__redisobj.connect(conf)
    def set_cache(self,name,values,expire = 'no'):
        """设置缓存

        参数 name：缓存名

        参数 values：缓存值

        参数 expire：缓存有效期 0表示永久  单位 秒
        
        return Boolean类型
        """
        # print(name)
        # exit()
        self.__name=name
        self.__values=values
        if expire != 'no':
            self.__config['expire']=int(expire)
        return self.__seltype('set')
    def get_cache(self,name):
        """获取缓存

        return 或者的值
        """
        self.__name=name
        return self.__seltype('get')
    def del_cache(self,name):
        """删除缓存

        return Boolean类型
        """
        self.__name=name
        return self.__seltype('del')
    

    
    def __seltype(self,types):
        """选择缓存"""
        self.__name=self.__md5(self.__name)
        if self.__config['type'] == 'File':
            if types == 'set':
                res = self.__setfilecache()
            elif types=='get':
                res = self.__getfilecache()
            elif types=='del':
                res = self.__delfilecache()
        elif self.__config['type'] == 'Redis':
            self.__setredisobj()
            if types == 'set':
                res = self.__setrediscache()
            elif types=='get':
                res = self.__getrediscache()
            elif types=='del':
                res = self.__delrediscache()
        # elif self.__config['type'] == 'MySql':
        #     self.__setmysqlonj()
        #     if types == 'set':
        #         res =res self.__setmysqlcache()
        #     elif types == 'get':
        #         res = self.__getmysqlcache()
        #     elif types == 'del':
        #         res = self.__delmysqlcache()
        elif self.__config['type'] == 'Python':
            if types == 'set':
                res = self.__setpythoncache()
            elif types == 'get':
                res = self.__getpythoncache()
            elif types == 'del':
                res = self.__delpythoncache()
        else:
            raise Exception("缓存类型错误")
        self.__config=copy.deepcopy(cacheconfig)
        self.__close_th_lock()
        return res
    def __setpythoncache(self):
        """设置python缓存
        
        return Boolean类型
        """
        data={
            'expire':self.__config['expire'],
            'time':self.__times(),
            'values':self.__values
        }
        cachevalue[self.__name]=data
        return True
    def __getpythoncache(self):
        """获取python缓存
        
        return 缓存的值
        """
        try:
            ar=cachevalue[self.__name]
        except KeyError:
            return ""
        else:
            if ar['expire'] > 0:
                if (self.__times()-ar['time']) > ar['expire']:
                    self.__delpythoncache()
                    return ""
                else:
                    return ar['values']
            else:
                return ar['values']
    def __delpythoncache(self):
        """删除python缓存
        
        return Boolean类型
        """
        try:
            del cachevalue[self.__name]
        except KeyError:
            pass
        return True
    # def __setmysqlcache(self): ########################################################################################
    #     """设置mysql缓存
        
    #     return Boolean类型
    #     """
    #     data=[str(self.__values)]
    #     strs="["
    #     for k in data:
    #         strs=strs+k
    #     strs=strs+"]"
    #     k=self.__mysqlobj.table('fanshukeji_core_cache').where("name",self.__name).count('id')
    #     self.__setmysqlonj()
    #     if k:
    #         return self.__mysqlobj.table('fanshukeji_core_cache').where("name",self.__name).update({"val":strs,"expire":self.__config['expire'],"time":self.__times()})
    #     else:
    #         return self.__mysqlobj.table('fanshukeji_core_cache').insert({"name":self.__name,"val":strs,"expire":self.__config['expire'],"time":self.__times()})
    # def __getmysqlcache(self):
    #     """获取mysql缓存
        
    #     return 缓存的值
    #     """
    #     data=self.__mysqlobj.table('fanshukeji_core_cache').where("name",self.__name).find()
    #     if data :
    #         if data['expire']>0 and self.__times()-data['time']>data['expire']:
    #             self.__setmysqlonj()
    #             self.__mysqlobj.table('fanshukeji_core_cache').where("name",self.__name).delete()
    #             return False
    #         else:
    #             return eval(data['val'])[0]
    #     else:
    #         return False
    # def __delmysqlcache(self):
    #     """删除mysql缓存
        
    #     return Boolean类型
    #     """
    #     return self.__mysqlobj.table('fanshukeji_core_cache').where("name",self.__name).delete()
    def __setrediscache(self):
        """设置redis缓存
        
        return Boolean类型
        """
        data=self.__values
        try:
            if self.__config['expire']:
                self.__redisobj.set(self.__name,data,self.__config['expire'])
            else:
                self.__redisobj.set(self.__name,data)
        except:
            return False
        return True
    def __getrediscache(self):
        """获取redis缓存
        
        return 缓存的值
        """
        lists=self.__redisobj.get(self.__name)
        if lists:
            return lists
        else:
            return False
    def __delrediscache(self):
        """删除redis缓存
        
        return int类型
        """
        return self.__redisobj.delete(self.__name)
    def __setfilecache(self):
        """设置文件缓存
        
        return Boolean类型
        """
        data={
            'expire':self.__config['expire'],
            'time':self.__times(),
            'values':self.__values
        }
        if not os.path.exists(self.__config['path']):
            os.makedirs(self.__config['path']) #多层创建目录
        f=open(self.__config['path']+"/"+self.__name,"w")
        f.write(str(data))
        f.close()
        return True
    def __getfilecache(self):
        """获取文件缓存
        
        return 缓存的值
        """
        try:
            f=open(self.__config['path']+"/"+self.__name,"r")
        except Exception:
            return ""
        json_str=f.read()
        f.close()
        ar=self.__json_decode(json_str)
        
        if ar and feagesgvresgaeagis_index(ar,'expire') and ar['expire'] > 0:
            if (self.__times()-ar['time']) > ar['expire']:
                self.__delfilecache()
                return ""
            else:
                return ar['values']
        elif ar and feagesgvresgaeagis_index(ar,'values'):
            return ar['values']
        else:
            return ''
    def __delfilecache(self):
        """删除文件缓存
        
        return Boolean类型
        """
        if not os.path.exists(self.__config['path']+"/"+self.__name):
            return True
        try:
            os.remove(self.__config['path']+"/"+self.__name)
        except:
            return False
        return True