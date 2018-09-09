# coding=utf-8
from threading import Thread
import subprocess
from Queue import Queue
import time
import socket, fcntl, struct
OTHER_IP=['192.168.0.181']
ips = []
j=1
q = Queue()
for i in range(180, 183):
    ip = '192.168.0.{}'.format(i)
    ips.append(ip)


# send to node ip_tail
def set_ip(client_ip, byte):
    ip_port = (client_ip, 9999)
    sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    inp = byte
    sk.sendto(bytes(inp), ip_port)
    sk.close()


# get host_ip
def get_localip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])


# ping ad-hoc host in specific area
def pingClient(queue):


    for ip in ips:
        q.put(ip)

    while True:
        ip = queue.get()
        print 'pinging %s' % ip
        ret = subprocess.call('ping -c 4 %s' % ip, shell=True, stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
        if ret == 0:
            adhoc_ip.append(ip)

        elif ret == 1:
            pass
        q.task_done()

        if queue.empty():

            print adhoc_ip
            break


# send to node ip of others in ad-hoc area
def other_ovs():
    global client_ip,j
    for i in OTHER_IP:
        print i
        print adhoc_ip
        for otherip in adhoc_ip:
            print otherip
            if otherip != i:
                    client_ip = ''.join(otherip)
                    byte = client_ip[-1]
                    set_ip(client_ip, byte)

                    subprocess.call("ovs-vsctl add-port br0 vport{0}".format(j), shell=True)
                    subprocess.call(
                        "ovs-vsctl set interface vport{0} type=vxlan options:remote_ip={1} ".format(j, client_ip),
                        shell=True)
                    j += 1

                    ip_port = (client_ip, 8888)
                    sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
                    other_ip = ','.join(adhoc_ip)
                    print other_ip
                    print type(other_ip)
                    sk.sendto(other_ip, ip_port)
                    sk.close()



def main():
    global q,adhoc_ip,OTHER_IP
    while True:
        adhoc_ip = []
        pingClient(q)
        print 'Seek ad-hoc host...'
        q.join()
        adhoc_ip = sorted(adhoc_ip)
        other_ovs()

        print 'Done'
        OTHER_IP = adhoc_ip
        time.sleep(3)


if __name__ == '__main__':
    subprocess.call('ovs-vsctl add-br br0', shell=True)
    local_ip = get_localip("wlp58s0").split(".")[3]
    subprocess.call("ifconfig br0 20.0.0.{}".format(local_ip), shell=True)
    main()
