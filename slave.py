import socket
import random
import time
import struct
import sys
import wx
import threading
import traceback

ip_port = {
    1: ("127.0.0.1", 60001),
    2: ("127.0.0.1", 60002),
    3: ("127.0.0.1", 60003),
    4: ("127.0.0.1", 60004)
}


class Modbus:
    num = 10
    #组件
    coil = [0 for i in range(num)]  #线圈
    input_status = [0 for i in range(num)]  #离散量
    holding_register = [0 for i in range(num)]  #保持寄存器
    input_register = [0 for i in range(num)]  #输入寄存器

    #报文头MBAP
    id = 0
    protocol = 0
    length = 0
    addr = -1

    #PDU
    func_code = -1
    data = b''

    send_data = b''
    recv_data = b''

    #socket
    s = 0

    def __init__(self, addr):
        self.addr = addr
        for i in range(len(self.input_status)):
            self.input_status[i] = random.randint(0, 1)
            # self.input_status[i] = 1
        for i in range(len(self.input_register)):
            self.input_register[i] = random.randint(0, 0xFFFF)
        pass

    def __pack(self):
        #报文头MBAP
        self.length = len(self.data) + 1
        self.send_data = int(self.id).to_bytes(length=2, byteorder="big")
        self.send_data += int(self.protocol).to_bytes(length=2,
                                                      byteorder="big")
        self.send_data += int(self.length).to_bytes(length=2, byteorder="big")
        self.send_data += int(self.addr).to_bytes(length=1, byteorder="big")
        #PDU
        self.send_data += self.data

    def read_coil(self):
        start = int.from_bytes(self.recv_data[1:3], byteorder="big")
        length = int.from_bytes(self.recv_data[3:5], byteorder="big")
        cnt = 0
        cur = 0
        data = b''
        for i in range(start, start + length):
            cur |= self.coil[i] << cnt
            cnt = cnt + 1
            if (cnt >= 8 or i + 1 == start + length):
                data += int(cur).to_bytes(length=1, byteorder="big")
                cur = 0
                cnt = 0
        self.data += int(len(data)).to_bytes(length=1, byteorder="big")
        self.data += data

    def read_input_status(self):
        start = int.from_bytes(self.recv_data[1:3], byteorder="big")
        length = int.from_bytes(self.recv_data[3:5], byteorder="big")
        cnt = 0
        cur = 0
        data = b''
        for i in range(start, start + length):
            cur |= self.input_status[i] << cnt
            cnt = cnt + 1
            if (cnt >= 8 or i + 1 == start + length):
                data += int(cur).to_bytes(length=1, byteorder="big")
                cur = 0
                cnt = 0
        self.data += int(len(data)).to_bytes(length=1, byteorder="big")
        self.data += data

    def read_holding_register(self):
        start = int.from_bytes(self.recv_data[1:3], byteorder="big")
        length = int.from_bytes(self.recv_data[3:5], byteorder="big")
        data = b''
        for i in range(start, start + length):
            data += int(self.holding_register[i]).to_bytes(length=2,
                                                           byteorder="big")

        self.data += int(len(data)).to_bytes(length=1, byteorder="big")
        self.data += data

    def read_input_register(self):
        start = int.from_bytes(self.recv_data[1:3], byteorder="big")
        length = int.from_bytes(self.recv_data[3:5], byteorder="big")
        data = b''
        for i in range(start, start + length):
            data += int(self.input_register[i]).to_bytes(length=2,
                                                         byteorder="big")

        self.data += int(len(data)).to_bytes(length=1, byteorder="big")
        self.data += data

    def write_singel_coil(self):
        addr = int.from_bytes(self.recv_data[1:3], byteorder="big")
        value = int.from_bytes(self.recv_data[3:5], byteorder="big")
        value = 0 if value == 0x0000 else 1
        self.coil[addr] = value
        self.data += self.data[1:5]

    def write_singel_register(self):
        addr = int.from_bytes(self.recv_data[1:3], byteorder="big")
        value = int.from_bytes(self.recv_data[3:5], byteorder="big")
        self.holding_register[addr] = value
        self.data += self.data[1:5]

    def write_multiple_coil(self):  #写多个线圈
        start = int.from_bytes(self.recv_data[1:3], byteorder="big")
        length = int.from_bytes(self.recv_data[3:5], byteorder="big")
        value = int.from_bytes(self.recv_data[5:7], byteorder="big")
        for i in range(start, start + length):
            self.coil[i] = value
        self.data += self.data[1:5]

    def write_multiple_register(self):  #写多个保持寄存器
        start = int.from_bytes(self.recv_data[1:3], byteorder="big")
        length = int.from_bytes(self.recv_data[3:5], byteorder="big")
        value = int.from_bytes(self.recv_data[5:7], byteorder="big")
        for i in range(start, start + length):
            self.holding_register[i] = value
        self.data += self.data[1:5]

    def __print(self, data, text_MBAP, text_PDU):
        t = data[0:7]
        res = ''
        for i in t:
            res += '%#x' % i + ' '
        text_MBAP.SetValue(res)
        t = data[7:]
        res = ''
        for i in t:
            res += '%#x' % i + ' '
        text_PDU.SetValue(res)

    def __verify(self):
        try:
            self.func_code = 0x77
            tmp_data=self.data
            self.data = b'OIANpINInpsoinOISDinsf'
            self.__pack()
            self.conn.send(self.send_data)
            self.conn.recv(4)
            length = int().from_bytes(self.conn.recv(2), byteorder="big")
            self.conn.recv(1)
            password = self.conn.recv(length)
            print("password",password)
            self.data=tmp_data
            if password == b"AKoinIbiBIUBIbisubfie":
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False

    def listen(self):
        global ip_port
        ip = ip_port[self.addr][0]
        port = ip_port[self.addr][1]
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((ip, port))
        self.s.listen(10)
        print("wait connect")
        conn, addr = self.s.accept()
        self.conn = conn
        if (self.__verify() is False):
            conn.close()
            return

        sum = b''
        t = conn.recv(2)
        sum += t
        self.id = int().from_bytes(t, byteorder="big")
        t = conn.recv(2)
        sum += t
        self.protocol = int().from_bytes(t, byteorder="big")
        t = conn.recv(2)
        sum += t
        self.length = int().from_bytes(t, byteorder="big")
        t = conn.recv(1)
        sum += t
        addr = int().from_bytes(t, byteorder="big")

        print(
            "id: " + str(self.id) + "protocol:  " + str(self.protocol) +
            "   length: ",
            str(self.length) + "  addr: " + str(self.addr))
        self.recv_data = conn.recv(self.length - 1)
        sum += self.recv_data
        self.__print(sum, frame.text_recv_MBAP, frame.text_recv_PDU)
        print("recv_data:   " + str(self.recv_data))
        self.func_code = int().from_bytes(self.recv_data[0:1], byteorder="big")

        if (addr != self.addr):
            self.func_code ^= 1 << 7
            self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        else:
            self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
            if (self.func_code == 0x01):  #读线圈状态
                self.read_coil()
            elif (self.func_code == 0x02):  #读离散输入状态
                self.read_input_status()
            elif (self.func_code == 0x03):  #读保持寄存器
                self.read_holding_register()
            elif (self.func_code == 0x04):  #读输入寄存器
                self.read_input_register()
            elif (self.func_code == 0x05):  #写线圈状态
                self.write_singel_coil()
            elif (self.func_code == 0x06):  #写单个保持寄存器
                self.write_singel_register()
            elif (self.func_code == 0x0F):  #写多个线圈
                self.write_multiple_coil()
            elif (self.func_code == 0x10):  #写多个保持寄存器
                self.write_multiple_register()
            else:
                pass
        self.__pack()
        self.__print(self.send_data, frame.text_send_MBAP, frame.text_send_PDU)
        conn.send(self.send_data)
        print("send_data:   " + str(self.send_data))
        time.sleep(0.5)
        conn.close()

    def update(self):
        #线圈
        res = "线圈：         "
        for i in range(len(self.coil)):
            res += str(i) + ":" + str(self.coil[i]) + ' '
        frame.text_coil.SetLabelText(res)
        #离散量
        res = "离散量：      "
        for i in range(len(self.input_status)):
            res += str(i) + ":" + str(self.input_status[i]) + ' '
        frame.text_input_status.SetLabelText(res)
        #输入寄存器
        res = "输入寄存器："
        for i in range(len(self.input_register)):
            res += str(i) + ":" + str(self.input_register[i]) + ' '
        frame.text_input_register.SetLabelText(res)
        #输入寄存器
        res = "保持寄存器："
        for i in range(len(self.holding_register)):
            res += str(i) + ":" + str(self.holding_register[i]) + ' '
        frame.text_holding_register.SetLabelText(res)


class MyFrame(wx.Frame):
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, title='test', size=(1000, 300))
        self.panel = wx.Panel(self)
        self.text_coil = wx.StaticText(self.panel,
                                       label='线圈：         ',
                                       pos=(20, 30))
        self.text_input_status = wx.StaticText(self.panel,
                                               label='离散量：      ',
                                               pos=(20, 60))
        self.text_input_register = wx.StaticText(self.panel,
                                                 label='输入寄存器：',
                                                 pos=(20, 90))
        self.text_holding_register = wx.StaticText(self.panel,
                                                   label='保持寄存器：',
                                                   pos=(20, 120))
        wx.StaticText(self.panel, label='发送:', pos=(20, 150))
        wx.StaticText(self.panel, label='收到:', pos=(20, 180))
        self.text_send_MBAP = wx.TextCtrl(self.panel,
                                          pos=(50, 150),
                                          size=(200, 20))
        self.text_send_PDU = wx.TextCtrl(self.panel,
                                         pos=(260, 150),
                                         size=(600, 20))
        self.text_recv_MBAP = wx.TextCtrl(self.panel,
                                          pos=(50, 180),
                                          size=(200, 20))
        self.text_recv_PDU = wx.TextCtrl(self.panel,
                                         pos=(260, 180),
                                         size=(600, 20))


class App(wx.App):
    def OnInit(self):
        print('App start')
        return super().OnInit()

    def OnExit(self):
        sys.exit(0)


def thread_listen():
    while True:
        try:
            t.listen()
        except:
            pass


def thread_upate():
    while True:
        t.update()
        time.sleep(0.1)


if __name__ == '__main__':
    app = App()
    app.locale = wx.Locale(wx.LANGUAGE_CHINESE_SIMPLIFIED)
    frame = MyFrame(
        parent=None,
        id=-1,
    )
    t = Modbus(1)
    threading.Thread(target=thread_listen).start()
    threading.Thread(target=thread_upate).start()
    frame.Show()
    app.MainLoop()
