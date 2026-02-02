# -*- coding: utf-8 -*-
import time,decimal,copy,hashlib
import threading
def kcwmysql_print_log(*strs):
    print(time.strftime("%Y-%m-%d %H:%M:%S"),*strs)
def kcwpymysql_is_index(params,index):
    try:
        params[index]
    except KeyError:
        return False
    except IndexError:
        return False
    else:
        return True
try:
    import kcwcache,pymysql
    import kcwebs.config as config
    kcwdbconfig=config.database
    kcwmysqlcache=copy.deepcopy(config.cache)
    if not kcwpymysql_is_index(kcwdbconfig,'th_lock'):
        kcwdbconfig['th_lock']=False
        kcwdbconfig['debug']=False
        
except:
    kcwmysqlcache={}
    kcwmysqlcache['type']='Python'
    kcwmysqlcache['type']='File' #驱动方式 支持 File Redis Python
    kcwmysqlcache['path']='app/runtime/cachepath' #缓存保存目录 
    kcwmysqlcache['expire']=120 #缓存有效期 0表示永久缓存
    kcwmysqlcache['host']='127.0.0.1' #Redis服务器地址
    kcwmysqlcache['port']='6379' #Redis 端口
    kcwmysqlcache['password']='' #Redis登录密码
    kcwmysqlcache['db']=1 #Redis数据库    注：Redis用1或2或3等表示

    kcwdbconfig={}
    kcwdbconfig['th_lock']=False #是否开启线程锁
    kcwdbconfig['debug']=False  #是否开启数据库调试描述
    kcwdbconfig['host']=['127.0.0.1']#服务器地址 [地址1,地址2,地址3...] 多个地址分布式(主从服务器)下有效
    kcwdbconfig['port']=[3306] #端口 [端口1,端口2,端口3...]
    kcwdbconfig['user']=['root']  #用户名 [用户名1,用户名2,用户名3...]
    kcwdbconfig['password']=['root']  #密码 [密码1,密码2,密码3...]
    kcwdbconfig['db']=['test']  #数据库名 [数据库名1,数据库名2,数据库名3...]
    kcwdbconfig['charset']='utf8mb4'   #数据库编码默认采用utf8mb4
    kcwdbconfig['pattern']=False # True数据库长连接模式 False数据库短连接模式  注：建议web应用有效，cli应用方式下，如果长时间运行建议使用mysql().close()关闭
    kcwdbconfig['cli']=False # 是否以cli方式运行
    kcwdbconfig['dbObjcount']=1 # 连接池数量（单个数据库地址链接数量），数据库链接实例数量 mysql长链接模式下有效
    kcwdbconfig['deploy']=0 # 数据库部署方式:0 集中式(单一服务器),1 分布式(主从服务器)  mysql数据库有效
    kcwdbconfig['master_num']=1 #主服务器数量 不能超过host服务器数量  （等于服务器数量表示读写不分离：主主复制。  小于服务器表示读写分离：主从复制。） mysql数据库有效
    kcwdbconfig['master_dql']=False #主服务器是否可以执行dql语句 是否可以执行select语句  主服务器数量大于等于host服务器数量时必须设置True
    kcwdbconfig['break']=0 #断线重连次数，0表示不重连
    kcwdbconfig['autocommit']=False #自动提交查询事务  命令行运行时开启 web运行时关闭


def kcwpymysqlmd5(strs):
    """md5加密"""
    if not strs:
        return strs
    m = hashlib.md5()
    b = strs.encode(encoding='utf-8')
    m.update(b)
    return m.hexdigest()


class thlockobj:
    obj=None  #锁对象
    status=None #锁状态
    timeout_time=60 #超时 最都锁多少秒
    start_locktime=0 #上锁时间
    stop_locktime=0 #结束锁时间
class grsegrsezgrgtrdrgregrsgrgssrgrdfrsgregsregre:
    """数据库实例"""
    __config=kcwdbconfig
    __conn={} #数据库链接对象
    __cursor=None #游标对象
    __errorcount=0 #允许最大链接错误次数
    __errorcounts=0 #默认链接错误次数 
    __dbObjcount=1 #数据库链接实例数量
    __sql=''
    __sqls=''
    __masteridentifier=None # 主服务器标识
    def __init__(self):
        pass
    def __del__(self):
        self.__close(all=True,pool=True,oeconn=True)
    def close(self,pool=False,oeconn=True):
        """关闭连接： web模式下该方法http响应结束后会自动调用， 命令行模式下 命令结束时会自动调用

        pool 是否关闭连接池
        
        """
        self.__close(all=True,pool=pool,oeconn=oeconn)
    def __close(self,all=False,pool=False,oeconn=False,th_lock=True):
        """关闭连接

        all 是否关闭全部连接

        pool 是否关闭连接池

        oeconn 是否关闭长连接

        th_lock 是否退出线程锁
        """
        if self.__conn:
            if all:
                tarr=copy.copy(self.__conn)
                for bs in tarr:
                    if kcwpymysql_is_index(self.__conn,bs):
                        if self.__conn[bs]['pattern']==1:
                            if oeconn :
                                if self.__conn[bs]['db']:
                                    self.__conn[bs]['db'].close()
                                    if self.__config['debug']:
                                        kcwmysql_print_log('关闭mysql长连接',self.__conn[bs],bs)
                                del self.__conn[bs]
                        
                        elif self.__conn[bs]['pattern']==2:
                            if self.__conn[bs]['db']:
                                self.__conn[bs]['db'].close()
                                self.__conn[bs]['db']=None
                                if self.__config['debug']:
                                    kcwmysql_print_log('回收mysql连接池',self.__conn[bs],bs)
                            if pool:
                                if kcwpymysql_is_index(self.__conn[bs],'pool'):
                                    if self.__conn[bs]['pool']:
                                        self.__conn[bs]['pool'].close()
                                        if self.__config['debug']:
                                            kcwmysql_print_log('关闭mysql连接池',self.__conn[bs],bs)
                                    del self.__conn[bs]
                        else:
                            if self.__conn[bs]['db']:
                                self.__conn[bs]['db'].close()
                                if self.__config['debug']:
                                    kcwmysql_print_log('关闭mysql短连接',self.__conn[bs],bs)
                            del self.__conn[bs]
            else:
                bs=self.__masteridentifier
                if kcwpymysql_is_index(self.__conn,bs):
                    if self.__conn[bs]['pattern']==1:
                        if oeconn :
                            if self.__conn[bs]['db']:
                                self.__conn[bs]['db'].close()
                                if self.__config['debug']:
                                    kcwmysql_print_log('关闭mysql长连接',self.__conn[bs],bs)
                            del self.__conn[bs]
                    
                    elif self.__conn[bs]['pattern']==2:
                        if self.__conn[bs]['db']:
                            self.__conn[bs]['db'].close()
                            self.__conn[bs]['db']=None
                            if self.__config['debug']:
                                kcwmysql_print_log('回收mysql连接池',self.__conn[bs],bs)
                        if pool:
                            if kcwpymysql_is_index(self.__conn[bs],'pool'):
                                if self.__conn[bs]['pool']:
                                    self.__conn[bs]['pool'].close()
                                    if self.__config['debug']:
                                        kcwmysql_print_log('关闭mysql连接池',self.__conn[bs],bs)
                                del self.__conn[bs]
                    else:
                        if self.__conn[bs]['db']:
                            self.__conn[bs]['db'].close()
                            if self.__config['debug']:
                                kcwmysql_print_log('关闭mysql短连接',self.__conn[bs],bs)
                        del self.__conn[bs]
            self.__masteridentifier=None
        if th_lock:
            self.close_th_lock()
        else:
            thlockobj.start_locktime=time.time()
    def __connects(self,typess="DQL"):
        """设置数据库链接
        
        参数 typess ：数据查询语言DQL，数据操纵语言DML，数据定义语言DDL，数据控制语言DCL
        """
        from dbutils.pooled_db import PooledDB
        try:
            if self.__config['deploy']==0: # 集中式(单一服务器)
                
                self.__masteridentifier=self.__config['host'][0]+str(self.__config['port'][0])+self.__config['user'][0]+self.__config['password'][0]+self.__config['db'][0]+kcwpymysqlmd5(str(self.__config)) # 服务器标识
                # kcwmysql_print_log('self.__config',self.__config)
                # kcwmysql_print_log('self.__masteridentifier',self.__masteridentifier)
                if self.__config['pattern']==1: # 长连接
                    try:
                        self.__conn[self.__masteridentifier]
                    except KeyError: # 铺获未知异常
                        db=pymysql.connect(autocommit=self.__config['autocommit'],host=self.__config['host'][0], port=self.__config['port'][0], user=self.__config['user'][0], password=self.__config['password'][0], db=self.__config['db'][0], charset=self.__config['charset'])
                        self.__conn[self.__masteridentifier]={'db':db,'pattern':self.__config['pattern']}
                        if self.__config['debug']:
                            kcwmysql_print_log("mysql长连接已创建",self.__masteridentifier,self.__conn[self.__masteridentifier])
                elif self.__config['pattern']==2: # 连接池
                    try:
                        self.__conn[self.__masteridentifier]
                    except KeyError: # 铺获未知异常
                        pool=PooledDB(creator=pymysql,maxconnections=self.__dbObjcount,autocommit=self.__config['autocommit'],host=self.__config['host'][0], port=self.__config['port'][0], user=self.__config['user'][0], password=self.__config['password'][0], db=self.__config['db'][0], charset=self.__config['charset'])
                        
                        self.__conn[self.__masteridentifier]={
                            'pool':pool,
                            'db':pool.connection(),'pattern':self.__config['pattern']
                        }
                        if self.__config['debug']:
                            kcwmysql_print_log("mysql连接池已创建1",self.__masteridentifier,self.__conn[self.__masteridentifier])
                    else:
                        try:
                            self.__conn[self.__masteridentifier]['db']=self.__conn[self.__masteridentifier]['pool'].connection()
                        except:
                            if self.__startTrans:
                                raise
                            try:self.__conn[self.__masteridentifier]['db']=self.__conn[self.__masteridentifier]['pool'].close()
                            except:pass
                            pool=PooledDB(creator=pymysql,maxconnections=self.__dbObjcount,autocommit=self.__config['autocommit'],host=self.__config['host'][0], port=self.__config['port'][0], user=self.__config['user'][0], password=self.__config['password'][0], db=self.__config['db'][0], charset=self.__config['charset'])
                            self.__conn[self.__masteridentifier]={
                                'pool':pool,
                                'db':pool.connection(),'pattern':self.__config['pattern']
                            }
                            if self.__config['debug']:
                                kcwmysql_print_log("mysql连接池已创建2",self.__masteridentifier,self.__conn[self.__masteridentifier])
                else:# 短连接
                    db=pymysql.connect(autocommit=self.__config['autocommit'],host=self.__config['host'][0], port=self.__config['port'][0], user=self.__config['user'][0], password=self.__config['password'][0], db=self.__config['db'][0], charset=self.__config['charset'])
                    self.__conn[self.__masteridentifier]={'db':db,'pattern':self.__config['pattern']}
                    if self.__config['debug']:
                        kcwmysql_print_log("mysql短连接已创建",self.__masteridentifier,self.__conn[self.__masteridentifier])
            elif self.__config['deploy']==1: # 分布式(主从服务器)
                # if not self.__masteridentifier:
                #     self.__masteridentifier=self.__config['host'][0]+str(self.__config['port'][0])+self.__config['user'][0]+self.__config['password'][0]+self.__config['db'][0]+kcwpymysqlmd5(str(self.__config)) # 服务器标识
                raise Exception('暂不支持')
        except pymysql.OperationalError as e:
            if self.__startTrans:
                raise e
            if e.args[0] in [2003,2013]:  # 2003连接失败 2013连接中断连接丢失
                self.__errorcounts+=1
                if self.__errorcounts>=self.__errorcount:
                    self.__errorcounts=0
                    raise Exception(e)
                else:
                    if self.__config['debug']:
                        kcwmysql_print_log("无法链接到数据库服务器，开始重新链接")
                    self.__close(oeconn=True,th_lock=False)
                    time.sleep(0.1)
                    if self.__config['cli']:
                        time.sleep(10)
                    self.__connects(typess)
            else:
                self.__errorcounts=0
                raise e
        except:
            self.__close(oeconn=True)
            raise
        else:
            self.__errorcounts=0

    def getconfig(self):
        return self.__config

    def get_th_lock(self):
        """获取线程锁"""
        return thlockobj
    def __start_th_lock(self,config=None):
        """开启线程锁 多线程中建议开启 注意 这个python多线程锁 而不是数据库事务锁"""
        if not thlockobj.obj:
            thlockobj.obj=threading.Lock()
        if thlockobj.status and time.time()-thlockobj.start_locktime>thlockobj.timeout_time:
            self.close_th_lock()
        thlockobj.obj.acquire()
        thlockobj.status=True
        thlockobj.start_locktime=time.time()
        if self.__config['debug'] or (kcwpymysql_is_index(config,'debug') and config['debug']):
            kcwmysql_print_log('开启线程锁mysql')
    def close_th_lock(self):
        """退出线程锁 这个python多线程锁 而不是数据库事务锁"""
        if thlockobj.status:
            thlockobj.obj.release()
            thlockobj.status=False
            thlockobj.stop_locktime=time.time()
            if self.__config['debug']:
                kcwmysql_print_log('退出线程锁mysql')
        # elif self.__config['th_lock']:
        #     try:
        #         thlockobj.obj.release()
        #         thlockobj.status=False
        #         thlockobj.stop_locktime=time.time()
        #     except:
        #         if self.__config['debug']:
        #             kcwmysql_print_log('退出线程锁mysql失败，未开启')
    def __setconfig(self,config,pattern):
        self.__config=copy.deepcopy(kcwdbconfig)
        try:
            if config:
                if isinstance(config,dict):
                    if "type" in config:
                        self.__config['type']=config['type']
                    if "host" in config:
                        self.__config['host']=config['host']
                    if "port" in config:
                        self.__config['port']=config['port']
                    if "user" in config:
                        self.__config['user']=config['user']
                    if "password" in config:
                        self.__config['password']=config['password']
                    if "db" in config:
                        self.__config['db']=config['db']
                    if "charset" in config:
                        self.__config['charset']=config['charset']
                    if "pattern" in config:
                        self.__config['pattern']=config['pattern']
                    if "cli" in config:
                        self.__config['cli']=config['cli']
                    if "dbObjcount" in config:
                        self.__config['dbObjcount']=config['dbObjcount']
                    if "deploy" in config:
                        self.__config['deploy']=config['deploy']
                    if "master_num" in config:
                        self.__config['master_num']=config['master_num']
                    if "master_dql" in config:
                        self.__config['master_dql']=config['master_dql']
                    if "break" in config:
                        self.__config['break']=config['break']
                    if "autocommit" in config:
                        self.__config['autocommit']=config['autocommit']
                    if "debug" in config:
                        self.__config['debug']=config['debug']
                elif isinstance(config,str):
                    self.__config['db']=[]
                    i=0
                    if not self.__dbcount:
                        self.__dbcount=len(self.__config['host'])
                    while i<self.__dbcount:
                        self.__config['db'].append(config)
                        i=i+1
                else:
                    kcwmysql_print_log("config类型错误，设置连接不生效")
            if pattern:
                if pattern in [1,2,3]:
                    self.__config['pattern']=pattern
                else:
                    kcwmysql_print_log("pattern错误，设置连接不生效")
            self.__errorcount=self.__config['break']
            self.__dbObjcount=self.__config['dbObjcount']
            if self.__config['debug']:
                kcwmysql_print_log("__setconfig",self.__config)
        except:
            self.close_th_lock()
            raise
    def connect(self,config=None,pattern=None):
        """设置数据库链接信息 

        参数 config 参考配置信息格式  可以设置数据库名（以字符串形式）

        pattern 连接方式 连接方式 1：长连接  2：连接池  3：短连接

        th_lock 是否开启线程锁 多线程中建议开启 注意 这个python多线程锁 而不是数据库事务锁 也可以在配置信息中全局开启 如果调用startTrans方法后线程锁将不生效

        返回 mysql对象
        """
        if kcwdbconfig['th_lock'] and not self.__startTrans:
            self.__start_th_lock(config)
        self.__setconfig(config=config,pattern=pattern)
        return self
    __table=""
    def table(self,table):
        """设置表名

        参数 table：str 表名

        
        """
        self.__None()
        self.__table=table
        if self.__config['debug']:
            kcwmysql_print_log('set mysql table',table)
        return self
    def __setcursor(self,typess='DQL'):
        """设置游标

        参数 type ：数据查询语言DQL，数据操纵语言DML，数据定义语言DDL，数据控制语言DCL
        """
        self.__dbObjcount=self.__config['dbObjcount']
        self.__errorcount=self.__config['break']
        self.__connects(typess)
        try:
            if self.__config['deploy']==0: # 集中式(单一服务器)
                if self.__config['pattern']==1: # 长连接
                    self.__cursor=self.__conn[self.__masteridentifier]['db'].cursor()
                elif self.__config['pattern']==2: # 连接池
                    self.__cursor=self.__conn[self.__masteridentifier]['db'].cursor()
                else:# 短连接
                    self.__cursor=self.__conn[self.__masteridentifier]['db'].cursor()
            elif self.__config['deploy']==1: # 分布式(主从服务器)
                raise Exception('暂不支持')
        except:
            self.__close(oeconn=True)
            raise
        return self.__cursor
    
    def get_exec_cursor(self):
        """获取执行游标（不推荐使用）
        
        参数 type ：数据查询语言DQL，数据操纵语言DML，数据定义语言DDL，数据控制语言DCL
        """
        cursor=self.__setcursor("DML")
        return cursor
    def get_query_cursor(self):
        """获取查询游标（不推荐使用）
        
        参数 type ：数据查询语言DQL，数据操纵语言DML，数据定义语言DDL，数据控制语言DCL
        """
        cursor=self.__setcursor("DQL")
        return cursor
    def __execute(self,typess='DQL',affair_retry=True):
        """执行sql语句
        
        参数 type ：数据查询语言DQL，数据操纵语言DML，数据定义语言DDL，数据控制语言DCL

        affair_retry 是否开启重试机制
        """
        self.__dbObjcount=self.__config['dbObjcount']
        self.__errorcount=self.__config['break']
        
        for i in range(101):
            self.__setcursor(typess)
            try:
                if self.__config['debug'] and self.__config['th_lock']:
                    kcwmysql_print_log('执行sql',self.__sql)
                res=self.__cursor.execute(self.__sql)
            except pymysql.OperationalError as e:
                if self.__startTrans:
                    self.__close(oeconn=True)
                    raise e
                if affair_retry and e.args[0] in [1053,2006,2013,2014]:  # 1053连接正在被关闭时 2006服务器丢失 2013连接中断连接丢失 2014未正确提交或回滚事务
                    if i>=self.__errorcount:
                        self.__close(oeconn=True)
                        raise e
                    else:
                        if self.__config['debug']:
                            kcwmysql_print_log("服务器正在被关闭，关闭当前连接后重试")
                        self.__close(oeconn=True,th_lock=False)
                        time.sleep(0.1)
                        if self.__config['cli']:
                            time.sleep(10)
                else:
                    self.__close(oeconn=True)
                    raise e
            except pymysql.InterfaceError as e:
                if self.__startTrans:
                    self.__close(oeconn=True)
                    raise e
                if i>=self.__errorcount:
                    self.__close(oeconn=True)
                    raise e
                else:
                    if self.__config['debug']:
                        kcwmysql_print_log("未知错误，关闭当前连接后重试")
                    self.__close(oeconn=True,th_lock=False)
                    time.sleep(0.1)
                    if self.__config['cli']:
                        time.sleep(10)
            except pymysql.InternalError as e:
                if self.__startTrans:
                    raise e
                if e.args[0] in [1205]:  # 1205 锁等待超时
                    if i>=self.__errorcount:
                        self.__close(oeconn=True)
                        raise e
                    else:
                        if self.__config['debug']:
                            kcwmysql_print_log("锁等待超时，关闭当前连接后重试")
                        self.__close(pool=True,oeconn=True,th_lock=False)
                        time.sleep(0.1)
                        if self.__config['cli']:
                            time.sleep(10)
                else:
                    self.__close(oeconn=True)
                    raise e
            except:
                self.__close(oeconn=True)
                raise
            else:
                break
        return res
    def execute(self,sql):
        """执行sql语句 DML

        参数 sql 字符串

        返回 列表  或  数字
        """
        self.__sql=sql
        res=self.__execute('DML')
        try:
            self.__cursor.close()
            if self.__startTrans==False:
                self.__close()
            return res
        except:
            self.__close(oeconn=True)
            raise
    def query(self,sql):
        """执行sql语句 DQL

        参数 sql 字符串

        返回 列表  或  数字
        """
        self.__sql=sql
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"select")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        for i in range(101):
            self.__execute()
            try:
                description=self.__cursor.description #获取字段
                result = self.__cursor.fetchall() #获取查询结果
                self.__cursor.close()
                if not description:
                    if self.__startTrans or i>=self.__errorcount:
                        raise Exception('获取字段失败，result='+str(result)+",sql="+self.__sql)
                    kcwmysql_print_log('获取字段失败 即将重试')
                    self.__close(oeconn=True,th_lock=False)
                    time.sleep(0.1)
                    if self.__config['cli']:
                        time.sleep(10)
                else:
                    break
            except:
                self.__close(oeconn=True)
                raise
        try:
            lists=[]
            keys =[]
            for field in description:#获取字段
                keys.append(field[0])
            key_number = len(keys)
            for row in result:
                item = dict()
                for q in range(key_number):
                    k=row[q]
                    if type(row[q])==decimal.Decimal:
                        k=float(row[q])
                    item[keys[q]] = k
                lists.append(item)
            if lists and self.__cache and self.__cache[0]:
                if isinstance(self.__cache[1], int):
                    kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,lists,self.__cache[1])
                else:
                    kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,lists)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return lists
    
    def select(self,id=None):
        """select查询 

        返回 list(列表)
        """
        if id :
            self.__where="id=%d" % id
        self.__setsql()
        if self.__buildSql:
            self.__sqls="("+self.__sql+")"
            if self.__startTrans==False:
                self.__close()
            return self.__sqls
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"select")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        for i in range(101):
            self.__execute()
            try:
                description=self.__cursor.description #获取字段
                result = self.__cursor.fetchall() #获取查询结果
                self.__cursor.close()
                if not description:
                    if self.__startTrans or i>=self.__errorcount:
                        raise Exception('获取字段失败，result='+str(result)+",sql="+self.__sql)
                    kcwmysql_print_log('获取字段失败 即将重试')
                    self.__close(oeconn=True,th_lock=False)
                    time.sleep(0.1)
                    if self.__config['cli']:
                        time.sleep(10)
                else:
                    break
            except:
                self.__close(oeconn=True)
                raise
        try:
            lists=[]
            keys =[]
            for field in description:#获取字段
                keys.append(field[0])
            key_number = len(keys)
            for row in result:
                item = dict()
                for q in range(key_number):
                    k=row[q]
                    if type(row[q])==decimal.Decimal:
                        k=float(row[q])
                    item[keys[q]] = k
                lists.append(item)
            if lists and self.__cache and self.__cache[0]:
                if isinstance(self.__cache[1], int):
                    kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,lists,self.__cache[1])
                else:
                    kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,lists)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return lists
    def find(self,id=None):
        """查询一条记录
        
        返回 字典
        """
        if id :
            self.__where="id=%s" % id
        self.limit(1)
        self.__setsql()
        if self.__buildSql:
            self.__sqls="("+self.__sql+")"
            if self.__startTrans==False:
                self.__close()
            return self.__sqls
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"find")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        for i in range(101):
            self.__execute()
            try:
                description=self.__cursor.description #获取字段
                result = self.__cursor.fetchall() #获取查询结果
                self.__cursor.close()
                if not description:
                    if self.__startTrans or i>=self.__errorcount:
                        raise Exception('获取字段失败，result='+str(result)+",sql="+self.__sql)
                    kcwmysql_print_log('获取字段失败 即将重试')
                    self.__close(oeconn=True,th_lock=False)
                    time.sleep(0.1)
                    if self.__config['cli']:
                        time.sleep(10)
                else:
                    break
            except:
                self.__close(oeconn=True)
                raise
        try:
            item = dict()
            keys =[]
            for field in description:#获取字段
                keys.append(field[0])
            key_number = len(keys)
            for row in result:
                for q in range(key_number):
                    k=row[q]
                    if type(row[q])==decimal.Decimal:
                        k=float(row[q])
                    item[keys[q]] = k
            if item and self.__cache and self.__cache[0]:
                if isinstance(self.__cache[1], int):
                    kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,item,self.__cache[1])
                else:
                    kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,item)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return item
    def value(self,field):
        """查询指定字段值
        
        返回 一个字段
        """
        self.__field=field
        self.limit(1)
        self.__setsql()
        if self.__buildSql:
            self.__sqls="("+self.__sql+")"
            if self.__startTrans==False:
                self.__close()
            return self.__sqls
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"value")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        self.__execute()
        try:
            result = self.__cursor.fetchall() #获取查询结果
            self.__cursor.close()
            strs=''
            if result:
                strs=result[0][0]
            if strs and self.__cache and self.__cache[0]:
                if isinstance(self.__cache[1], int):
                    kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,strs,self.__cache[1])
                else:
                    kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,strs)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return strs
    def count(self,field="*"):
        """查询数量
        
        返回 int 数字
        """
        self.__field=field
        self.__setsql('count')
        if self.__buildSql:
            self.__sqls="("+self.__sql+")"
            if self.__startTrans==False:
                self.__close()
            return self.__sql
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"count")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        self.__execute()
        try:
            result = self.__cursor.fetchall() #获取查询结果
            self.__cursor.close()
            if self.__group:
                cou=len(result)
            else:
                try:
                    cou=int(result[0][0])
                except IndexError:
                    cou=0
            if cou and self.__cache and self.__cache[0]:
                if isinstance(self.__cache[1], int):
                    kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,cou,self.__cache[1])
                else:
                    kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,cou)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return cou
    def max(self,field):
        """查询某字段的最大值
        
        返回 int 数字
        """
        self.__field=field
        self.__setsql('max')
        if self.__buildSql:
            self.__sqls="("+self.__sql+")"
            if self.__startTrans==False:
                self.__close()
            return self.__sql
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"max")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        self.__execute()
        try:
            result = self.__cursor.fetchall() #获取查询结果
            self.__cursor.close()
            if result[0][0]:
                cou=int(result[0][0])
            else:
                cou=''
            if cou and self.__cache and self.__cache[0]:
                if isinstance(self.__cache[1], int):
                    kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,cou,self.__cache[1])
                else:
                    kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,cou)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return cou
    def min(self,field):
        """查询某字段的最小值
        
        返回 int 数字
        """
        self.__field=field
        self.__setsql('min')
        if self.__buildSql:
            self.__sqls="("+self.__sql+")"
            if self.__startTrans==False:
                self.__close()
            return self.__sql
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"min")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        self.__execute()
        try:
            result = self.__cursor.fetchall() #获取查询结果
            self.__cursor.close()
            if result[0][0]:
                cou=int(result[0][0])
            else:
                cou=''
            if cou and self.__cache and self.__cache[0]:
                if isinstance(self.__cache[1], int):
                    kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,cou,self.__cache[1])
                else:
                    kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,cou)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return cou
    def avg(self,field):
        """查询某字段的平均值
        
        返回 int 数字
        """
        self.__field=field
        self.__setsql('avg')
        if self.__buildSql:
            self.__sqls="("+self.__sql+")"
            if self.__startTrans==False:
                self.__close()
            return self.__sql
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"avg")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        self.__execute()
        try:
            result = self.__cursor.fetchall() #获取查询结果
            self.__cursor.close()
            if result[0][0]:
                cou=int(result[0][0])
            else:
                cou=''
            if cou and self.__cache and self.__cache[0]:
                if isinstance(self.__cache[1], int):
                    kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,cou,self.__cache[1])
                else:
                    kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,cou)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return cou
    def sum(self,field):
        """查询某字段之和
        
        返回 int 数字
        """
        self.__field=field
        self.__setsql('sum')
        if self.__buildSql:
            self.__sqls="("+self.__sql+")"
            if self.__startTrans==False:
                self.__close()
            return self.__sql
        if self.__cache and self.__cache[0]:
            cachename=kcwpymysqlmd5(self.__sql+str(self.__config['db'][0])+str(self.__config['host'][0])+"sum")
            if isinstance(self.__cache[1], int):
                cou=kcwcache.cache.set_config(kcwmysqlcache).get_cache(cachename)
            else:
                cou=kcwcache.cache.set_config(self.__cache[1]).get_cache(cachename)
            if cou:
                if self.__startTrans==False:
                    self.__close()
                return cou
        self.__execute()
        try:
            result = self.__cursor.fetchall() #获取查询结果
            self.__cursor.close()
            cou=result[0][0]
            if not cou:
                cou=0
            else:
                if self.__cache and self.__cache[0]:
                    if isinstance(self.__cache[1], int):
                        kcwcache.cache.set_config(kcwmysqlcache).set_cache(cachename,cou,self.__cache[1])
                    else:
                        kcwcache.cache.set_config(self.__cache[1]).set_cache(cachename,cou)
        except:
            self.__close(oeconn=True)
            raise
        if self.__startTrans==False:
            self.__close()
        return cou

    def setinc(self,field,key=1,affair_retry=True):
        """更新字段增加
         
        参数 field 要更新的字段

        参数 key 字段需要加多少

        affair_retry 是否开启重试机制
        """
        data={"field":field,"key":key}
        self.__setsql('setinc',data)
        if self.__startTrans==False:
            for i in range(101):
                try:
                    res=self.__execute('DML',affair_retry=False)
                    self.__cursor.close()
                    self.commit()
                # except pymysql.OperationalError as e:
                #     if self.__startTrans:
                #         self.__close(oeconn=True)
                #         raise e
                #     if affair_retry and e.args[0] in [1053,2006,2013,2014]:  # 1053连接正在被关闭时 2006服务器丢失 2013连接中断连接丢失 2014未正确提交或回滚事务
                #         if i>=self.__errorcount:
                #             self.__close(oeconn=True)
                #             raise e
                #         else:
                #             if self.__config['debug']:
                #                 kcwmysql_print_log("服务器正在被关闭，关闭当前连接后重试")
                #             self.__close(oeconn=True,th_lock=False)
                #             time.sleep(0.1)
                #             if self.__config['cli']:
                #                 time.sleep(10)
                #     else:
                #         self.__close(oeconn=True)
                #         raise e
                except:
                    self.__close(oeconn=True)
                    raise
                else:
                    break
        else:
            res=self.__execute('DML')
            try:
                self.__cursor.close()
            except:
                self.__close(oeconn=True)
                raise
        return res
    def update(self,data,affair_retry=True):
        """数据表更新
         
        参数 data 要更新的内容  格式：{"name":"测试","age":20}

        affair_retry 是否开启重试机制
        """
        self.__setsql('update',data)
        if self.__startTrans==False:
            for i in range(101):
                try:
                    res=self.__execute('DML',affair_retry=False)
                    self.__cursor.close()
                    self.commit()
                except pymysql.OperationalError as e:
                    if self.__startTrans:
                        self.__close(oeconn=True)
                        raise e
                    if affair_retry and e.args[0] in [1053,2006,2013,2014]:  # 1053连接正在被关闭时 2006服务器丢失 2013连接中断连接丢失 2014未正确提交或回滚事务
                        if i>=self.__errorcount:
                            self.__close(oeconn=True)
                            raise e
                        else:
                            if self.__config['debug']:
                                kcwmysql_print_log("服务器正在被关闭，关闭当前连接后重试")
                            self.__close(oeconn=True,th_lock=False)
                            time.sleep(0.1)
                            if self.__config['cli']:
                                time.sleep(10)
                    else:
                        self.__close(oeconn=True)
                        raise e
                except:
                    self.__close(oeconn=True)
                    raise
                else:
                    break
        else:
            res=self.__execute('DML')
            try:
                self.__cursor.close()
            except:
                self.__close(oeconn=True)
                raise
        return res
    def delete(self,affair_retry=True):
        """数据表删除

        affair_retry 是否开启重试机制
        """
        self.__setsql('delete')
        if self.__where:
            if self.__startTrans==False:
                for i in range(101):
                    try:
                        res=self.__execute('DML',affair_retry=False)
                        self.__cursor.close()
                        self.commit()
                    except pymysql.OperationalError as e:
                        if self.__startTrans:
                            self.__close(oeconn=True)
                            raise e
                        if affair_retry and e.args[0] in [1053,2006,2013,2014]:  # 1053连接正在被关闭时 2006服务器丢失 2013连接中断连接丢失 2014未正确提交或回滚事务
                            if i>=self.__errorcount:
                                self.__close(oeconn=True)
                                raise e
                            else:
                                if self.__config['debug']:
                                    kcwmysql_print_log("服务器正在被关闭，关闭当前连接后重试")
                                self.__close(oeconn=True,th_lock=False)
                                time.sleep(0.1)
                                if self.__config['cli']:
                                    time.sleep(10)
                        else:
                            self.__close(oeconn=True)
                            raise e
                    except:
                        self.__close(oeconn=True)
                        raise
                    else:
                        break
            else:
                res=self.__execute('DML')
                try:
                    self.__cursor.close()
                except:
                    self.__close(oeconn=True)
                    raise
        else:
            res=0
        return res
    def insert(self,dicts,affair_retry=True):
        """插入数据库 单条插入或多条插入

        参数 dicts 要插入的内容 单条格式：{"name":"测试","age":20}  。     多条格式：[{"name":"测试","age":20},{"name":"测试","age":20}]

        affair_retry 是否开启重试机制

        返回插入的数量
        """
        self.__setsql('insert',dicts)
        if self.__startTrans==False:
            for i in range(101):
                try:
                    res=self.__execute('DML',affair_retry=False)
                    self.__cursor.close()
                    self.commit()
                except pymysql.OperationalError as e:
                    if self.__startTrans:
                        self.__close(oeconn=True)
                        raise e
                    if affair_retry and e.args[0] in [1053,2006,2013,2014]:  # 1053连接正在被关闭时 2006服务器丢失 2013连接中断连接丢失 2014未正确提交或回滚事务
                        if i>=self.__errorcount:
                            self.__close(oeconn=True)
                            raise e
                        else:
                            if self.__config['debug']:
                                kcwmysql_print_log("服务器正在被关闭，关闭当前连接后重试")
                            self.__close(oeconn=True,th_lock=False)
                            time.sleep(0.1)
                            if self.__config['cli']:
                                time.sleep(10)
                    else:
                        self.__close(oeconn=True)
                        raise e
                except:
                    self.__close(oeconn=True)
                    raise
                else:
                    break
        else:
            res=self.__execute('DML')
            try:
                self.__cursor.close()
            except:
                self.__close(oeconn=True)
                raise
        return res

    __startTrans=False
    def startTrans(self):
        "开启事务,仅对 setinc方法、update方法、delete方法、install方法有效"
        self.__startTrans=True
    def commit(self):
        """事务提交

        增删改后的任务进行提交

        affair_retry 是否开启事务重试机制
        """
        if self.__masteridentifier and self.__conn[self.__masteridentifier]['db']:
            self.__conn[self.__masteridentifier]['db'].commit()
            self.__close()
        self.__startTrans=False
    def rollback(self):
        """事务回滚

        增删改后的任务进行撤销
        """
        if self.__masteridentifier and self.__conn[self.__masteridentifier]['db']:
            self.__conn[self.__masteridentifier]['db'].rollback()
            self.__close()
        self.__startTrans=False
    def getsql(self):
        """得到生成的sql语句"""
        return self.__sql
    __buildSql=None
    def buildSql(self):
        """构造子查询"""
        self.__buildSql=True
        return self
    def __None(self):
        "清除所有赋值条件"
        if self.__config['debug']:
            kcwmysql_print_log('清除所有赋值条件')
        self.__lock=None
        self.__distinct=None
        self.__join=None
        self.__joinstr=''
        self.__alias=None
        self.__having=None
        self.__group=None
        self.__group1=None
        self.__order=None
        self.__order1=None
        self.__limit=None
        self.__field="*"
        self.__where=None
        self.__wheres=()
        self.__table=None
        self.__buildSql=None
        self.__cache=None
    
    __where=None
    __wheres=()
    def where(self,where = None,*wheres):
        """设置过滤条件

        传入方式:
        "id",2 表示id='2'

        "id","in",2,3,4,5,6,...表示 id in (2,3,4,5,6,...)

        "id","in",[2,3,4,5,6,...]表示 id in (2,3,4,5,6,...)


        [("id","gt",6000),"and",("name","like","%超")] 表示 ( id > "6000" and name LIKE "%超" )

        "id","eq",1 表示 id = '1'

        eq 等于
            neq 不等于
            gt 大于
            egt 大于等于
            lt 小于
            elt 小于等于
            like LIKE
        """
        self.__where=where
        self.__wheres=wheres
        return self
    __field='*'
    def field(self,field = "*"):
        """设置过滤显示条件

        参数 field：str 字符串
        """
        self.__field=field
        return self
    __limit=[]
    def limit(self,offset=1, length = None):
        """设置查询数量

        参数 offset：int 起始位置

        参数 length：int 查询数量
        """
        if not offset:
            offset=1
        offset=int(offset)
        if length:
            length=int(length)
        self.__limit=[offset,length]
        return self
    def page(self,pagenow=1, length = 20):
        """设置分页查询

        参数 pagenow：int 页码

        参数 length：int 查询数量
        """
        if not pagenow:
            pagenow=1
        if not length:
            length=20
        pagenow=int(pagenow)
        length=int(length)
        offset=(pagenow-1)*length
        self.__limit=[offset,length]
        return self
    __order=None
    __order1=None
    def order(self,strs=None,*strs1):
        """设置排序查询

        传入方式:

        "id desc"

        "id",'name','appkey','asc'

        "id",'name','appkey'   不包含asc或desc的情况下 默认是desc

        ['id','taskid',{"task_id":"desc"}]
        """
        self.__order=strs
        self.__order1=strs1
        return self
    __group=None
    __group1=None
    def group(self,strs=None,*strs1):
        """设置分组查询

        传入方式:

        "id,name"

        "id","name"
        """
        self.__group=strs
        self.__group1=strs1
        return self
    __having=None
    def having(self,strs=None):
        """用于配合group方法完成从分组的结果中筛选（通常是聚合条件）数据

        参数 strs：string 如："count(time)>3"
        """
        self.__having=strs
        return self
    __alias=None
    def alias(self,strs=None):
        """用于设置当前数据表的别名，便于使用其他的连贯操作例如join方法等。

        参数 strs：string 默认当前表作为别名
        """
        if strs:
            self.__alias=strs
        else:
            self.__alias=self.__table
        return self
    __join=None
    __joinstr=''
    def join(self,strs,on=None,types='INNER'):
        """用于根据两个或多个表中的列之间的关系，从这些表中查询数据

        参数 strs  string 如："test t1"   test表设置别名t1

        参数 on  string 如："t1.id=t2.pid"   设置连接条件

        参数 types  支持INNER、LEFT、RIGHT、FULL  默认INNER

        """
        joinstr=''
        if strs and on:
            joinstr=joinstr+types+" JOIN "+strs+" ON "+on+" "
        if joinstr:
            self.__joinstr=self.__joinstr+joinstr
        return self
    __distinct=None
    def distinct(self,bools=None):
        "用于返回唯一不同的值,配合field方法使用生效,来消除所有重复的记录，并只获取唯一一次记录。"
        self.__distinct=bools
        return self
    __lock=None
    def lock(self,strs=None):
        """用于数据库的锁机制，在查询或者执行操作的时候使用

        排他锁 (FOR UPDATE)

        共享锁 (lock in share mode)
        
        参数 strs  如：True表示自动在生成的SQL语句最后加上FOR UPDATE，

        
        """
        self.__lock=strs
        return self
   
    __cache=[]
    def cache(self,status=None,endtime=86400):
        """设置查询缓存
        status  缓存开关

        参数 endtime：int 缓存时间  0永久 / 或缓存配置信息
        """
        self.__cache=[status,endtime]
        return self
    def __setsql(self,types=None,data = {}):
        """生成sql语句"""
        import pymysql
        if types==None:
            self.__sql="SELECT"
            if self.__distinct and self.__field:
                self.__sql=self.__sql+" DISTINCT"
            if self.__alias:
                self.__sql=self.__sql+" %s FROM %s %s" % (self.__field,self.__table,self.__alias)
            else:
                self.__sql=self.__sql+" %s FROM %s" % (self.__field,self.__table)
        elif types=='count':
            self.__sql="SELECT COUNT(%s) FROM %s" % (self.__field,self.__table)
        elif types=='max':
            self.__sql="SELECT MAX(%s) FROM %s" % (self.__field,self.__table)
        elif types=='min':
            self.__sql="SELECT MIN(%s) FROM %s" % (self.__field,self.__table)
        elif types=='avg':
            self.__sql="SELECT AVG(%s) FROM %s" % (self.__field,self.__table)
        elif types=='sum':
            self.__sql="SELECT SUM(%s) FROM %s" % (self.__field,self.__table)
        elif types=='setinc':
            self.__sql="update %s set %s=%s+%s" % (self.__table,data['field'],data['field'],data['key'])
        elif types=='update':
            strs=''
            for k in data:
                if isinstance(data[k],str):
                    strs=strs+" %s = '%s' ," % (k,pymysql.escape_string(data[k]))
                    # strs=strs+" %s = '%s' ," % (k,(data[k]))
                elif data[k]==None:
                    strs=strs+" %s = %s ," % (k,"NULL")
                else:
                    strs=strs+" %s = %s ," % (k,data[k])
            strs=strs[:-1]
            self.__sql="UPDATE %s SET %s" % (self.__table,strs)
        elif types=='delete':
            self.__sql="DELETE FROM %s" % self.__table
        elif types=='insert':
            if isinstance(data,dict):
                strs=''
                val=''
                for k in data:
                    strs=strs+"%s," % k
                    if isinstance(data[k],str):
                        val=val+"'%s'," % pymysql.escape_string(data[k])
                        # val=val+"'%s'," % (data[k])
                    elif data[k]==None:
                        val=val+"%s," % 'NULL'
                    else:
                        val=val+"%s," % data[k]
                strs=strs[:-1]
                val=val[:-1]
                self.__sql="INSERT INTO %s (%s) VALUES (%s)" % (self.__table,strs,val)
            elif isinstance(data,list):
                strs=''
                val='('
                for k in data[0]:
                    strs=strs+" , "+k
                for k in data:
                    for j in k:
                        if isinstance(k[j],str):
                            val=val+"'"+str(k[j])+"',"
                        elif data[k]==None:
                            val=val+"NULL,"
                        else:
                            val=val+str(k[j])+","
                    val=val[:-1]
                    val=val+"),("
                val=val[:-2]
                self.__sql="INSERT INTO "+self.__table+" ("+strs[3:]+") VALUES "+val
        if self.__joinstr:
            self.__sql=self.__sql+" "+self.__joinstr
        if self.__where:
            if isinstance(self.__where,str):
                if self.__wheres:
                    if len(self.__wheres) == 2:
                        if isinstance(self.__wheres[1],list):
                            self.__sql=self.__sql + " WHERE %s %s (" % (self.__where,self.__operator(self.__wheres[0]))
                            for k in self.__wheres[1]:
                                self.__sql=self.__sql+str(k)+","
                            self.__sql=self.__sql[:-1]+")"
                        else:
                            self.__sql=self.__sql + " WHERE  %s %s '%s'" % (self.__where,self.__operator(self.__wheres[0]),self.__wheres[1])
                    elif len(self.__wheres) > 2:
                        if self.__wheres[0]=='in':
                            strs=str(self.__wheres[1])
                            i=0
                            for k in self.__wheres:
                                if i > 1:
                                    strs=strs+","+str(k)
                                i=i+1
                            self.__sql=self.__sql + " WHERE  %s in (%s)" % (self.__where,strs)
                    else:
                        self.__sql=self.__sql + " WHERE  %s = '%s'" % (self.__where,self.__wheres[0])
                else:
                    self.__sql=self.__sql + " WHERE  %s" % self.__where
            elif isinstance(self.__where,list):
                self.__sql=self.__sql + " WHERE  %s" % self.__listTrans()
            else:
                kcwmysql_print_log("参数where类型错误")
        if self.__group:
            s=self.__group
            if self.__group1:
                for key in self.__group1:
                    s=s+","+key
            self.__sql=self.__sql+" GROUP BY "+s
        if self.__order:
            s=''
            if isinstance(self.__order,list):
                for strs in self.__order:
                    if isinstance(strs,str):
                        s=s+strs+","
                    else:
                        pass
                        for key in strs:
                            s=s+key+" "+strs[key]
                        s=s+","
                s=s[:-1]
            if isinstance(self.__order,str):
                if self.__order1:
                    if len(self.__order1) > 1:
                        if self.__order1[len(self.__order1)-1] == 'desc' or self.__order1[len(self.__order1)-1] == 'asc':
                            i=0
                            while i<len(self.__order1)-1:
                                s=s+self.__order1[i]+","
                                i=i+1
                            s=s[:-1]+" "+self.__order1[len(self.__order1)-1]
                        else:
                            for key in self.__order1:
                                s=s+key+","
                            s=s[:-1]
                            s=s+" asc"
                        s=self.__order+","+s
                    else:
                        s=s[:-1]+self.__order1[0]
                        s=self.__order+" "+s
                else:
                    s=self.__order
            self.__sql=self.__sql+" ORDER BY "+s
        if self.__having:
            self.__sql=self.__sql+" HAVING "+self.__having
        if self.__limit:
            if self.__limit[1]:
                self.__sql=self.__sql+" LIMIT %d,%d" % (self.__limit[0],self.__limit[1])
            else:
                self.__sql=self.__sql+" LIMIT %d" % self.__limit[0]
        if self.__lock:
            if isinstance(self.__lock,str):
                self.__sql=self.__sql+" "+self.__lock
            else:
                self.__sql=self.__sql+' FOR UPDATE'
    def __listTrans(self):
        """列表转换sql表达式
        返回 字符串
        """
        strs=''
        #[('id', 'eq', '1'), 'or', ('id', 'eq', '2')]
        for k in self.__where:
            if isinstance(k,tuple):
                t=0
                for j in k:
                    if t==0:
                        strs=strs+' '+str(j)+' '
                    elif t==1:
                        strs=strs+self.__operator(j)
                    if t==2:
                        strs=strs+' "'+str(j)+'" '
                    t=t+1
            elif isinstance(k,str):
                strs=strs+k
        return "("+strs+")"
    def __operator(self,strs):
        """运算符转换
        参数 strs 待转的字符串
        返回 已转换的运算符

        符号定义
            eq 等于
            neq 不等于
            gt 大于
            egt 大于等于
            lt 小于
            elt 小于等于
            like LIKE
        """
        strss=strs.upper()
        if strss == 'EQ':
            k='='
        elif strss == 'NEQ':
            k='<>'
        elif strss == 'GT':
            k='>'
        elif strss == 'EGT':
            k='>='
        elif strss == 'LT':
            k='<'
        elif strss == 'ELT':
            k='<='
        elif strss == 'LIKE':
            k='LIKE'
        else:
            k=strss
        return k
    
