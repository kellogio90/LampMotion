'''
Libreria per gestione lampada a 4 motori
Data Creazione 11.03.2020

#example
    
if __name__ == '__main__':
install_and_import(['math','copy','opcua','random','configparser'])#installo lib necessarie
plc = PLC(
    "opc.tcp://localhost:4840",
    "ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.")
l = Lamp()
l.lamp_read_config(os.path.dirname(__file__)+"\\config.ini")
l.get_CableLenght(0,0,0,45) 
for i in range(0,3):
    ang = random.randint(0,90)
    l.move_to_point(random.randint(-4,4),random.randint(-4,4),random.randint(-3,0),ang)   
    plc.Seq_Motor(l.sequence,l.CableLenght,"Lamp.ACK","Lamp.Motor") 

l.lamp_on()
plc.comand_ack("Lamp.ACK","Lamp.light",l.light)
l.Home_reset()
plc.Seq_Motor(l.sequence,l.CableLenght,"Lamp.ACK","Lamp.Motor")

'''

#from threading import Thread 
#import time
import operator
import os
import serial


def install_and_import(package):
    import importlib
    for pk in package:
        try:
            importlib.import_module(pk)
            print(pk+ " Installed")
        except ImportError:
            import pip
            pip.main(['install', pk])
        finally:
            globals()[pk] = importlib.import_module(pk)

class Point():
    def __init__(self,x,y,z):
        self.x = x
        self.y = y
        self.z = z
    
    def __str__(self):
        return "X {0},Y {1},Z {2}".format(self.x,self.y,self.z)

class Lamp():
    '''
    Costrututtore Lampada tramite Pos Motori e Pos Su Muro
    def __init__(self,LampPos = [],Wall = [])
    '''
    def __init__(self,LampPos = [],Wall = []):
        self.L = LampPos
        self.W = Wall
        self.Ganc = []
        self.CableLenght = {}
        self.Coord = []


    def __str__(self):
        #return "Lamp of Radius {0} in Pos {1}".format(self.R,self.P)
        return str(self.CableLenght)
    
    def lamp_read_config(self,Path):
        '''
        def lamp_read_config(self,Path)
        '''
        ini = configparser.ConfigParser()
        ini.read(Path)
        n =int(ini.get('gen', 'n'))
        self.L = []
        self.W = []
        for i in range(0,n):
            LampPt = ini.get('LampPt', str(i))
            LampPt = LampPt.split(',')
            Wl = ini.get('Wall', str(i))
            Wl = Wl.split(',')
            for i in range(0,3):
                LampPt[i] = int(LampPt[i])
                Wl[i] = int(Wl[i])
            self.L.append(LampPt)
            self.W.append(Point(Wl[0],Wl[1],Wl[2]))

    def get_motor_position(self,Int):
        pass

    def comparePoint(self,PointA,PointB):
        '''
        comparePoint(self,PointA,PointB):
        return Distance
        '''
        Deltx = (PointA.x - PointB.x)
        Delty = (PointA.y - PointB.y)
        Deltz = (PointA.z - PointB.z)
        Distance = math.sqrt((Deltx)**2 + (Delty)**2 +(Deltz)**2)
        Distance = round(Distance, 2)
        return Distance

    def get_CableLenght(self,x,y,z,alpha):
        '''
        get_CableLenght(self,x,y,z,alpha):
        no return
        '''
        self.Ganc.clear()
        self.Orig = Point(x,y,z)
        rad = math.radians(alpha)
        for i in self.L:
            ix =  math.cos(rad) * (i[0]) + math.sin(rad) * (i[1])
            iy =  math.sin(rad) * (i[0]) - math.cos(rad) * (i[1])
            print(ix,iy)
            P = Point(x + ix,y + iy ,z+i[2])
            self.Ganc.append(P)

        self.CableLenght = {}
        for i in range(0,len(self.Ganc)):
            self.CableLenght[str(i)] = self.comparePoint(self.Ganc[i],self.W[i])
        #return(Dist)
    
    def myFunc(self,e):
        return e[1]

    def move_to_point(self,x,y,z,alpha):
        '''
        move_to_point(self,x,y,z,alpha):
        return self.CableLenght
        '''
        self.Coord = [x,y,z,alpha]
        if self.CableLenght != {}:
            self.OldCable = self.CableLenght
            self.get_CableLenght(x,y,z,alpha)
            print("_____")
            print("New Pos = "+ str(self.CableLenght))
            ## CalcDelta
            for i in range(0,len(self.OldCable)):
                self.OldCable[i]: self.OldCable[i]-self.CableLenght[i]
            self.sequence = sorted(self.OldCable, key=self.OldCable.__getitem__,reverse= True)
            return self.CableLenght
            
    def lamp_on(self):
        self.light = True
    
    def lamp_off(self):
        self.light = False
    
    def change_color(self,Color):
        # TODO
        # Da definire chi comanda il colore, se il plc di impianto o il raspberry
        pass
    
    def save_point(self,Name):
        # todo
        # Non più valido lo gestisce direttamente l'UI
        pass

    def Home_reset(self):
        self.move_to_point(self.W[0].x,self.W[0].y,self.W[0].z,0)

class PLC():
    def __init__(self,url,Path):
        self.url = url
        self.type = opcua.ua.VariantType
        if Path.endswith("."):
            self.Path = Path
        else:
            self.Path = Path+"."
        self.Connect()

    def Connect(self):
        self.client = opcua.Client(self.url)
        try:
            self.client.connect()
            self.con = True
            print("Connection Success")
        except:
            self.con = False
            print("Fail Connection")
        
    def read_variable(self,NamePath):
        '''
        read_variable(self,NamePath):
        return val
        '''
        if self.con:
            strin = self.Path + NamePath
            var = self.client.get_node(self.Path + NamePath)
            val = var.get_value()
            return val
        return None

    def set_variable(self,NamePath,val):
        '''
        set_variable(self,NamePath,val):
        return bool
        '''
        if self.con:
            var = self.client.get_node(self.Path +NamePath)
            hint = var.get_data_type_as_variant_type()
            try:
                var.set_value(val,hint)
            except Exception as e: 
                print(e)
                return False
            return True
        return False

    def comand_ack(self,varRd,varWr,value):
        '''
        comand_ack(self,varRd,varWr,value):
        return bool
        '''
        if self.con:
            tp = False
            while tp == False:
                tp = self.read_variable(varRd)
            while not self.set_variable(varWr,value):
                pass
            while not self.set_variable(varRd,False):
                pass
            return True
        return False
  
    def Seq_Motor(self,ListSeq,Dict,bl,Nm):
        for i in ListSeq:
            if plc.comand_ack(bl,Nm+i,Dict[i]):
                print (Nm+i+"  DONE")

# Example

if __name__ == '__main__':
    install_and_import(['math','copy','opcua','random','configparser'])#installo lib necessarie
    plc = PLC(
        "opc.tcp://localhost:4840",
        "ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.")
    l = Lamp()
    l.lamp_read_config(os.path.dirname(__file__)+"\\config.ini")
    l.get_CableLenght(0,0,0,45) # TODO Da integrare con setup home
    for i in range(0,3):
        ang = random.randint(0,90)
        l.move_to_point(random.randint(-4,4),random.randint(-4,4),random.randint(-3,0),ang)   # Muovo pos
        plc.Seq_Motor(l.sequence,l.CableLenght,"Lamp.ACK","Lamp.Motor") # TODO spostato da move_point

    l.lamp_on()
    plc.comand_ack("Lamp.ACK","Lamp.light",l.light)
    l.Home_reset()
    plc.Seq_Motor(l.sequence,l.CableLenght,"Lamp.ACK","Lamp.Motor")# TODO se viene decisa la gestione con il plc bisogna passare il plc nella classe lamp e nelle seguenti definizioni
