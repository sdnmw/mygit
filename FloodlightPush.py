#coding=utf-8
import httplib
import json
import datetime,time
import math
import socket
import cv2
import numpy
class StaticFlowPusher(object):    
    def __init__(self, server):
        self.server = server
    def get(self, data):
        ret = self.rest_call({}, 'GET')
        return json.loads(ret[2])
    def set(self, data,path):
        path=path
        ret = self.rest_call(data, 'POST',path)
        return ret[0] == 200
    def remove(self, objtype, data,path):
        path=path
        ret = self.rest_call(data, 'DELETE',path)
        return ret[0] == 200
    def rest_call(self, data, action,path):
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            }
        body = json.dumps(data)
        conn = httplib.HTTPConnection(self.server, 8080)
        conn.request(action, path, body, headers)
        response = conn.getresponse()
        ret = (response.status, response.reason, response.read())
        print ret
        conn.close()
        return ret
path0 = '/wm/staticflowpusher/json'
pusher = StaticFlowPusher('10.0.0.1')
dst_ip = raw_input()
flow1 = {
    'switch':'00:00:0a:bb:a1:04:cf:41',
    "name":"flow-mod-1",
    "cookie":"0",
    "priority":"32768",
    "ingress-port":"1",
    "dl_type":"0x0800",
    "dst_ip":dst_ip,
    "active":"true",
    "actions":"group=2"
}
pusher.set(flow1,path0)
while True:
	ip_port = (dst_ip,8888)
	sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
	data = raw_input()
	sk.sendto(data, ip_port)
        sk.close()
        if data == 'p':
            def recv_size(sock, count):
                buf = b''
                while count:
                    newbuf = sock.recv(count)
                    if not newbuf: return None
                    buf += newbuf
                    count -= len(newbuf)
                return buf

            # 接收图片
            def recv_all(sock, count):
                buf = ''
                while count:
                    # 这里每次只接收一个字节的原因是增强python与C++的兼容性
                    # python可以发送任意的字符串，包括乱码，但C++发送的字符中不能包含'\0'，也就是字符串结束标志位
                    newbuf = sock.recv(1)
                    if not newbuf: return None
                    buf += newbuf
                    count -= len(newbuf)
                return buf

            # socket.AF_INET用于服务器与服务器之间的网络通信
            # socket.SOCK_STREAM代表基于TCP的流式socket通信
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置地址与端口，如果是接收任意ip对本服务器的连接，地址栏可空，但端口必须设置
            address = ('', 8010)
            s.bind(address) # 将Socket（套接字）绑定到地址
            s.listen(True) # 开始监听TCP传入连接
            print ('Waiting for images...')
            # 接受TCP链接并返回（conn, addr），其中conn是新的套接字对象，可以用来接收和发送数据，addr是链接客户端的地址。4
            conn, addr = s.accept()
            i=0
            while 1:
                length = recv_size(conn,16) #首先接收来自客户端发送的大小信息
                if isinstance (length,str): #若成功接收到大小信息，进一步再接收整张图片
                    stringData = recv_all(conn, int(length))
                    data = numpy.fromstring(stringData, dtype='uint8')
                    decimg=cv2.imdecode(data,1) #解码处理，返回mat图片
                    cv2.imshow('SERVER',decimg)

                    
                    if cv2.waitKey(10)==ord('s'):
                        cv2.imwrite(str(i)+'.jpg',decimg)
                        i+=1
            #	print('photo recieved successfully!')
            #	conn.send("Server has recieved photo!")
                            
                    if cv2.waitKey(10) == 27:
                        break 
                    print('Image recieved successfully!')
                    conn.send("Server has recieved messages!")
            #    if cv2.waitKey(10) == 27:
            #        break 
                if cv2.waitKey(10)&0XFF == ord('q'):
                    break    
            s.close()
            cv2.destroyAllWindows() 




