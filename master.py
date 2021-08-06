import socket
import sys
import wx
from wx.core import Size
import threading
import time
import traceback

id_cnt = 0

ip_ports = {
    1: ("127.0.0.1", 60001),
    2: ("127.0.0.1", 60002),
    3: ("127.0.0.1", 60003),
    4: ("127.0.0.1", 60004)
}

mu = threading.Lock()


class Modbus:
    #报文头MBAP
    id = -1
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
        global id_cnt, ip_ports
        id_cnt = id_cnt + 1
        self.id = id_cnt
        self.addr = addr
        pass

    def __pack(self):
        self.length = len(self.data) + 1
        self.send_data = int(self.id).to_bytes(length=2, byteorder="big")
        self.send_data += int(self.protocol).to_bytes(length=2,
                                                      byteorder="big")
        self.send_data += int(self.length).to_bytes(length=2, byteorder="big")
        self.send_data += int(self.addr).to_bytes(length=1, byteorder="big")
        self.send_data += self.data

    def read_coil(self, start, length):  #读线圈
        self.func_code = 0x01
        self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        self.data += int(start).to_bytes(length=2, byteorder="big")
        self.data += int(length).to_bytes(length=2, byteorder="big")

    def read_input_status(self, start, length):  #读离散输入状态
        self.func_code = 0x02
        self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        self.data += int(start).to_bytes(length=2, byteorder="big")
        self.data += int(length).to_bytes(length=2, byteorder="big")

    def read_holding_register(self, start, length):  #读保持寄存器
        self.func_code = 0x03
        self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        self.data += int(start).to_bytes(length=2, byteorder="big")
        self.data += int(length).to_bytes(length=2, byteorder="big")

    def read_input_register(self, start, length):  #读输入寄存器
        self.func_code = 0x04
        self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        self.data += int(start).to_bytes(length=2, byteorder="big")
        self.data += int(length).to_bytes(length=2, byteorder="big")

    def write_singel_coil(self, write_addr, value):  #写单个线圈
        self.func_code = 0x05
        self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        self.data += int(write_addr).to_bytes(length=2, byteorder="big")
        self.data += int(0x0000 if value == 0 else 0xFF00).to_bytes(
            length=2, byteorder="big")

    def write_singel_register(self, write_addr, value):  #写单个保持寄存器
        self.func_code = 0x06
        self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        self.data += int(write_addr).to_bytes(length=2, byteorder="big")
        self.data += int(value).to_bytes(length=2, byteorder="big")

    def write_multiple_coil(self, start, length, value):  #写多个线圈
        self.func_code = 0x0F
        self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        self.data += int(start).to_bytes(length=2, byteorder="big")
        self.data += int(length).to_bytes(length=2, byteorder="big")
        self.data += int(value).to_bytes(length=2, byteorder="big")

    def write_multiple_register(self, start, length, value):  #写多个保持寄存器
        self.func_code = 0x10
        self.data = int(self.func_code).to_bytes(length=1, byteorder="big")
        self.data += int(start).to_bytes(length=2, byteorder="big")
        self.data += int(length).to_bytes(length=2, byteorder="big")
        self.data += int(value).to_bytes(length=2, byteorder="big")

    def __verify(self):
        try:
            self.func_code = 0x77
            tmp_data = self.data
            self.data = b'AKoinIbiBIUBIbisubfie'
            self.__pack()
            self.s.send(self.send_data)
            self.s.recv(4)
            length = int().from_bytes(self.s.recv(2), byteorder="big")
            self.s.recv(1)
            password = self.s.recv(length)
            self.data = tmp_data
            if password == b"OIANpINInpsoinOISDinsf":
                return True
            else:
                return False
        except:
            # traceback.print_exc()
            self.s.close()
            return False

    def connect(self):
        # mu.acquire()
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect(ip_ports[self.addr])
        except:
            pass
            # traceback.print_exc()
        # mu.release()
        return self.__verify()

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

    def execute(self):
        ok = self.connect()
        if ok:
            print("连接成功")
            self.__pack()
            self.__print(self.send_data, frame.text_send_MBAP,
                         frame.text_send_PDU)
            self.s.send(self.send_data)
            self.recv_data = self.s.recv(1024)
            self.__print(self.recv_data, frame.text_recv_MBAP,
                         frame.text_recv_PDU)
            self.s.close()
            self.data = self.recv_data[7:]
        else:
            print("连接失败")
        pass


class MyFrame(wx.Frame):
    def read_coil(self, event):  #读线圈
        addr = self.text_dst.GetValue()
        addr = int(addr)
        modbus = Modbus(addr)
        start = self.text_coil_addr1.GetValue()
        length = self.text_coil_len1.GetValue()
        start = int(start)
        length = int(length)
        modbus.read_coil(start, length)
        modbus.execute()

        t = modbus.data[1:2]
        data = modbus.data[2:]
        res = ""
        for i in range(length):
            t = int().from_bytes(data[i // 8:i // 8 + 1], byteorder="big")
            status = (t & (1 << (i % 8)))
            status = 1 if status > 0 else 0
            res += str(i + start) + ":" + str(status) + " "
        self.coil_result.SetValue(res)
        pass

    def write_singel_coil(self, event):  #写单个线圈
        addr = self.text_dst.GetValue()
        addr = int(addr)
        modbus = Modbus(addr)
        addr = self.text_coil_addr2.GetValue()
        value = self.text_coil_value2.GetValue()
        addr = int(addr)
        value = int(value)
        modbus.write_singel_coil(addr, value)
        modbus.execute()
        pass

    def write_multiple_coil(self, event):  #写多个线圈
        addr = self.text_dst.GetValue()
        addr = int(addr)
        modbus = Modbus(addr)
        start = self.text_coil_addr3.GetValue()
        length = self.text_coil_len3.GetValue()
        value = self.text_coil_value3.GetValue()
        start = int(start)
        length = int(length)
        value = int(value)
        modbus.write_multiple_coil(start, length, value)
        modbus.execute()
        pass

    def init_coil(self):
        panel = self.panel
        font16 = wx.Font(16, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)
        font11 = wx.Font(11, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)

        self.title_coil = wx.StaticText(panel, label='线圈', pos=(150, 30))
        self.title_coil.SetFont(font16)

        wx.StaticText(panel, label='读线圈', pos=(20, 70)).SetFont(font11)
        wx.StaticText(panel, label='地址:', pos=(40, 90))
        self.text_coil_addr1 = wx.TextCtrl(panel, pos=(80, 90), size=(30, 20))
        wx.StaticText(panel, label='长度：', pos=(120, 90))
        self.text_coil_len1 = wx.TextCtrl(panel, pos=(160, 90), size=(30, 20))
        self.bt_read1 = wx.Button(panel, label='读取', pos=(280, 87))
        self.bt_read1.Bind(wx.EVT_BUTTON, self.read_coil)

        k = 50
        wx.StaticText(panel, label='写单个线圈', pos=(20, 70 + k)).SetFont(font11)
        wx.StaticText(panel, label='地址:', pos=(40, 90 + k))
        self.text_coil_addr2 = wx.TextCtrl(panel,
                                           pos=(80, 90 + k),
                                           size=(30, 20))
        wx.StaticText(panel, label='值：', pos=(120, 90 + k))
        self.text_coil_value2 = wx.TextCtrl(panel,
                                            pos=(160, 90 + k),
                                            size=(30, 20))
        self.bt_write2 = wx.Button(panel, label='写入', pos=(280, 87 + k))
        self.bt_write2.Bind(wx.EVT_BUTTON, self.write_singel_coil)

        k = 100
        wx.StaticText(panel, label='写多个线圈', pos=(20, 70 + k)).SetFont(font11)
        wx.StaticText(panel, label='地址:', pos=(40, 90 + k))
        self.text_coil_addr3 = wx.TextCtrl(panel,
                                           pos=(80, 90 + k),
                                           size=(30, 20))
        wx.StaticText(panel, label='长度：', pos=(120, 90 + k))
        self.text_coil_len3 = wx.TextCtrl(panel,
                                          pos=(160, 90 + k),
                                          size=(30, 20))
        wx.StaticText(panel, label='值：', pos=(200, 90 + k))
        self.text_coil_value3 = wx.TextCtrl(panel,
                                            pos=(240, 90 + k),
                                            size=(30, 20))
        self.bt_write3 = wx.Button(panel, label='写入', pos=(280, 87 + k))
        self.bt_write3.Bind(wx.EVT_BUTTON, self.write_multiple_coil)

        k = 130
        wx.StaticText(panel, label='查询结果:', pos=(20, 90 + k)).SetFont(font11)
        self.coil_result = wx.TextCtrl(panel,
                                       pos=(20, 90 + k + 20),
                                       size=(330, 20))

    def read_holding_register(self, event):  #读保持寄存器
        addr = self.text_dst.GetValue()
        addr = int(addr)
        modbus = Modbus(addr)
        start = self.text_holding_register_addr1.GetValue()
        length = self.text_holding_register_len1.GetValue()
        start = int(start)
        length = int(length)
        modbus.read_holding_register(start, length)
        modbus.execute()
        res = ""
        for i in range(length):
            t = modbus.data[2 + i * 2:2 + i * 2 + 2]
            t = int().from_bytes(t, byteorder="big")
            res += str(i + start) + ":" + str(t) + " "
        self.holding_register_result.SetValue(res)
        pass

    def write_singel_register(self, event):  #写单个保持寄存器
        addr = self.text_dst.GetValue()
        addr = int(addr)
        modbus = Modbus(addr)
        start = self.text_holding_register_addr2.GetValue()
        value = self.text_holding_register_value2.GetValue()
        start = int(start)
        value = int(value)
        modbus.write_singel_register(start, value)
        modbus.execute()
        pass

    def write_multiple_register(self, event):  #写多个保持寄存器
        addr = self.text_dst.GetValue()
        addr = int(addr)
        modbus = Modbus(addr)
        start = self.text_holding_register_addr3.GetValue()
        length = self.text_holding_register_len3.GetValue()
        value = self.text_holding_register_value3.GetValue()
        start = int(start)
        length = int(length)
        value = int(value)
        modbus.write_multiple_register(start, length, value)
        modbus.execute()
        pass

    def init_holding_register(self):
        x = 500

        panel = self.panel
        font16 = wx.Font(16, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)
        font11 = wx.Font(11, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)

        self.title_holding_register = wx.StaticText(panel,
                                                    label='保持寄存器',
                                                    pos=(x + 150, 30))
        self.title_holding_register.SetFont(font16)

        wx.StaticText(panel, label='读保持寄存器', pos=(x + 20, 70)).SetFont(font11)
        wx.StaticText(panel, label='地址:', pos=(x + 40, 90))
        self.text_holding_register_addr1 = wx.TextCtrl(panel,
                                                       pos=(x + 80, 90),
                                                       size=(30, 20))
        wx.StaticText(panel, label='长度：', pos=(x + 120, 90))
        self.text_holding_register_len1 = wx.TextCtrl(panel,
                                                      pos=(x + 160, 90),
                                                      size=(30, 20))
        self.bt_read1 = wx.Button(panel, label='读取', pos=(x + 280, 87))
        self.bt_read1.Bind(wx.EVT_BUTTON, self.read_holding_register)

        k = 50
        wx.StaticText(panel, label='写单个保持寄存器',
                      pos=(x + 20, 70 + k)).SetFont(font11)
        wx.StaticText(panel, label='地址:', pos=(x + 40, 90 + k))
        self.text_holding_register_addr2 = wx.TextCtrl(panel,
                                                       pos=(x + 80, 90 + k),
                                                       size=(30, 20))
        wx.StaticText(panel, label='值：', pos=(x + 120, 90 + k))
        self.text_holding_register_value2 = wx.TextCtrl(panel,
                                                        pos=(x + 160, 90 + k),
                                                        size=(30, 20))
        self.bt_write2 = wx.Button(panel, label='写入', pos=(x + 280, 87 + k))
        self.bt_write2.Bind(wx.EVT_BUTTON, self.write_singel_register)

        k = 100
        wx.StaticText(panel, label='写多个保持寄存器',
                      pos=(x + 20, 70 + k)).SetFont(font11)
        wx.StaticText(panel, label='地址:', pos=(x + 40, 90 + k))
        self.text_holding_register_addr3 = wx.TextCtrl(panel,
                                                       pos=(x + 80, 90 + k),
                                                       size=(30, 20))
        wx.StaticText(panel, label='长度：', pos=(x + 120, 90 + k))
        self.text_holding_register_len3 = wx.TextCtrl(panel,
                                                      pos=(x + 160, 90 + k),
                                                      size=(30, 20))
        wx.StaticText(panel, label='值：', pos=(x + 200, 90 + k))
        self.text_holding_register_value3 = wx.TextCtrl(panel,
                                                        pos=(x + 240, 90 + k),
                                                        size=(30, 20))
        self.bt_write3 = wx.Button(panel, label='写入', pos=(x + 280, 87 + k))
        self.bt_write3.Bind(wx.EVT_BUTTON, self.write_multiple_register)

        k = 130
        wx.StaticText(panel, label='查询结果:',
                      pos=(x + 20, 90 + k)).SetFont(font11)
        self.holding_register_result = wx.TextCtrl(panel,
                                                   pos=(x + 20, 90 + k + 20),
                                                   size=(330, 20))

    def read_input_status(self, event):  #读离散输入状态
        addr = self.text_dst.GetValue()
        addr = int(addr)
        modbus = Modbus(addr)
        start = self.text_input_status_addr1.GetValue()
        length = self.text_input_status_len1.GetValue()
        start = int(start)
        length = int(length)
        modbus.read_input_status(start, length)
        modbus.execute()
        t = modbus.data[1:2]
        data = modbus.data[2:]
        res = ""
        for i in range(length):
            t = int().from_bytes(data[i // 8:i // 8 + 1], byteorder="big")
            status = (t & (1 << (i % 8)))
            status = 1 if status > 0 else 0
            res += str(i + start) + ":" + str(status) + " "
        self.input_status_result.SetValue(res)
        pass

    def init_input_status(self):
        y = 250
        panel = self.panel
        font16 = wx.Font(16, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)
        font11 = wx.Font(11, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)

        self.title_input_status = wx.StaticText(panel,
                                                label='离散量',
                                                pos=(150, 30 + y))
        self.title_input_status.SetFont(font16)

        wx.StaticText(panel, label='读离散量', pos=(20, 70 + y)).SetFont(font11)
        wx.StaticText(panel, label='地址:', pos=(40, 90 + y))
        self.text_input_status_addr1 = wx.TextCtrl(panel,
                                                   pos=(80, 90 + y),
                                                   size=(30, 20))
        wx.StaticText(panel, label='长度：', pos=(120, 90 + y))
        self.text_input_status_len1 = wx.TextCtrl(panel,
                                                  pos=(160, 90 + y),
                                                  size=(30, 20))
        self.bt_read1 = wx.Button(panel, label='读取', pos=(280, 87 + y))
        self.bt_read1.Bind(wx.EVT_BUTTON, self.read_input_status)

        k = 30
        wx.StaticText(panel, label='查询结果:',
                      pos=(20, 90 + k + y)).SetFont(font11)
        self.input_status_result = wx.TextCtrl(panel,
                                               pos=(20, 90 + k + 20 + y),
                                               size=(330, 20))
        pass

    def read_input_register(self, event):  #读输入寄存器
        addr = self.text_dst.GetValue()
        addr = int(addr)
        modbus = Modbus(addr)
        start = self.text_input_register_addr1.GetValue()
        length = self.text_input_register_len1.GetValue()
        start = int(start)
        length = int(length)
        modbus.read_input_register(start, length)
        modbus.execute()
        res = ""
        for i in range(length):
            t = modbus.data[2 + i * 2:2 + i * 2 + 2]
            t = int().from_bytes(t, byteorder="big")
            res += str(i + start) + ":" + str(t) + " "
        self.input_register_result.SetValue(res)
        pass
        pass

    def init_input_register(self):
        x = 500
        y = 250
        panel = self.panel
        font16 = wx.Font(16, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)
        font11 = wx.Font(11, wx.DEFAULT, wx.FONTSTYLE_NORMAL, wx.NORMAL)

        self.title_input_status = wx.StaticText(panel,
                                                label='输入寄存器',
                                                pos=(150 + x, 30 + y))
        self.title_input_status.SetFont(font16)

        wx.StaticText(panel, label='读输入寄存器',
                      pos=(20 + x, 70 + y)).SetFont(font11)
        wx.StaticText(panel, label='地址:', pos=(40 + x, 90 + y))
        self.text_input_register_addr1 = wx.TextCtrl(panel,
                                                     pos=(80 + x, 90 + y),
                                                     size=(30, 20))
        wx.StaticText(panel, label='长度：', pos=(120 + x, 90 + y))
        self.text_input_register_len1 = wx.TextCtrl(panel,
                                                    pos=(160 + x, 90 + y),
                                                    size=(30, 20))
        self.bt_read1 = wx.Button(panel, label='读取', pos=(280 + x, 87 + y))
        self.bt_read1.Bind(wx.EVT_BUTTON, self.read_input_register)

        k = 30
        wx.StaticText(panel, label='查询结果:',pos=(20 + x, 90 + k + y)).SetFont(font11)
        self.input_register_result = wx.TextCtrl(panel,
                                                 pos=(20 + x, 90 + k + 20 + y),
                                                 size=(330, 20))
        pass

    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, title='master', size=(1000, 600))
        self.panel = wx.Panel(self)
        self.text_dst = wx.TextCtrl(self.panel,
                                    value="1",
                                    pos=(10, 10),
                                    size=(30, 20),
                                    style=wx.TE_LEFT | wx.TE_PROCESS_ENTER)
        self.text_now = wx.StaticText(self.panel, pos=(50, 10))
        self.init_coil()
        self.init_holding_register()
        self.init_input_status()
        self.init_input_register()
        wx.StaticText(self.panel, label='发送:', pos=(20, 450))
        wx.StaticText(self.panel, label='收到:', pos=(20, 480))
        self.text_send_MBAP = wx.TextCtrl(self.panel,
                                          pos=(50, 450),
                                          size=(200, 20))
        self.text_send_PDU = wx.TextCtrl(self.panel,
                                         pos=(260, 450),
                                         size=(600, 20))
        self.text_recv_MBAP = wx.TextCtrl(self.panel,
                                          pos=(50, 480),
                                          size=(200, 20))
        self.text_recv_PDU = wx.TextCtrl(self.panel,
                                         pos=(260, 480),
                                         size=(600, 20))
        self.Centre()


class App(wx.App):
    def OnInit(self):
        print('App start')
        return super().OnInit()

    def OnExit(self):
        sys.exit(0)


def detect():
    while True:
        res = "检测到设备: "
        for addr in ip_ports.keys():
            t = Modbus(addr)
            try:
                if (t.connect() is True):
                    res += str(addr) + ' '
                    t.s.close()
            except:
                pass
        print(res)
        frame.text_now.SetLabel(res)
        time.sleep(1)


if __name__ == '__main__':

    threading.Thread(target=detect).start()

    app = App()
    app.locale = wx.Locale(wx.LANGUAGE_CHINESE_SIMPLIFIED)
    frame = MyFrame(
        parent=None,
        id=-1,
    )
    frame.Show()
    app.MainLoop()
