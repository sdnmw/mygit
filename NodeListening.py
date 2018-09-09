# coding = utf-8
import subprocess as sub
import time
import socket, fcntl, struct

controller = ['10.0.0.1']
CON = "".join(controller)
print time.ctime()
OTHER_IP = ['10.0.0.1']

# get host ip
def get_localip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])


# accept br0 ip_tail
def acc_ip():
    local_ip = get_localip("wlan0")
    ip_port = (local_ip, 9999)
    sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    sk.bind(ip_port)
    print "acc ip"
    data = sk.recv(1024)
    sub.call("ifconfig br0 20.0.0.{}".format(data), shell=True)


# contribute the vxlan between host and others
def acc_other_ip(a):
    global OTHER_IP
    local_ip = get_localip("wlan0")
    print "acc other"
    ip_port1 = (local_ip, 8888)
    sk1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    sk1.bind(ip_port1)
    data1 = sk1.recv(1024)

    print data1
    data1 = data1.split(',')
    if OTHER_IP == data1:
        print "no new node"
        pass
    else:
        for otherip in data1:
            if otherip not in OTHER_IP:
                if otherip != local_ip:
                    if otherip != CON:
                        ovs_cmd11 = 'ovs-vsctl add-port br0 vport{0}'.format(a)
                        ovs_cmd22 = 'ovs-vsctl set interface vport{0} type=vxlan options:remote_ip={1}'.format(a, otherip)
                        cmd = ovs_cmd11 + "&&" + ovs_cmd22
                        sub.call(cmd, shell=True)
                if otherip == CON:
                    sub.call('ovs-vsctl set-controller br0 tcp:{}:6653'.format(CON), shell=True)
                    a += 1
    OTHER_IP = data1


# split the con_ip
def get_request_ip(line):
    line_list = line.strip().split(' ')
    if line_list[1] == 'IP':
        return line_list[2]


# vxlan
def ovs_bridge():
    global cmd1, CON
    ovs_cmd1 = 'ovs-vsctl add-br br0'
    ovs_cmd2 = 'ovs-vsctl add-port br0 vport1'
    ovs_cmd3 = 'ovs-vsctl set interface vport1 type=vxlan options:remote_ip={}'.format(CON)
    # ovs_cmd4 = 'ifconfig br0 20.0.0.{}'.format()
    cmd1 = ovs_cmd1 + "&&" + ovs_cmd2 + "&&" + ovs_cmd3  # + "&&" + ovs_cmd4


def operative_cmd():
    ovs_bridge()
    sub.call(cmd1, shell=True)


def main():
    global new_adoc_ip
    # cmdd = ['tcpdump', '-i', 'wlp58s0', 'icmp[icmptype]=icmp-echo']
    p = sub.Popen('tcpdump -i wlan0 ', shell=True, stdout=sub.PIPE)
    while True:
        line = p.stdout.readline()
        line = line.strip()
        if line == '':
            break
        a = 2
        con_ip = get_request_ip(line)
        if con_ip in controller:
            print 'con_ip is searched ' + time.ctime()
            operative_cmd()
            acc_ip()
            acc_other_ip(a)
            print 'yes'


if __name__ == "__main__":

    main()









