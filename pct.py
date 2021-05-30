#!/usr/bin/env python3
#
# pi_cw_trainer
# http://github.com/alfille/pi_cw_trainer
# Combined hardware and software project
# Use a Pi to generate random CW
# audio output: buzzer
# screen output on LCD screen
# potentometer to adjust speed
#
# 2021 Paul H Alffille

configuration = {
    'Graphics'  : True  ,
    'Audio'     : False ,
    'Keyboard'  : True  ,
    'Buzzer'    : True  ,
    'LEDflash'  : True  ,
    'LEDscreen' : True  ,
    'Knob'      : True  ,
    'Terminal'  : True  ,
    }


if configuration['Buzzer'] or configuration['LEDflash'] or configuration['LEDscreen'] or configuration['Knob']:
    try:
        import pigpio
    except:
        print('pigpio module could not be loaded.\n Perhaps it needs to be installed by "pip3 install pigpio"\n')
        raise

if configuration['Audio']:
    try:
        import pysinewave
    except:
        print('pysinewave module could not be loaded.\n Perhaps it needs to be installed by "pip3 install pysinewave"\n')
        raise

if configuration['Graphics']:
    try:
        import tkinter as tk
    except:
        print('tkinter module could not be loaded.\n It should be part of the standard configuration\n')
        raise

try:
    import threading
except:
    print('threading module could not be loaded.\n It should be part of the standard configuration\n')
    raise
    
try:
    import queue
except:
    print('queue module could not be loaded.\n It should be part of the standard configuration\n')
    raise
    
try:
    import time
except:
    print('time module could not be loaded.\n It should be part of the standard configuration\n')
    raise
    
try:
    import signal
except:
    print('signal module could not be loaded.\n It should be part of the standard configuration\n')
    raise
    
try:
    import sys
except:
    print('sys module could not be loaded.\n It should be part of the standard configuration\n')
    raise
    
try:
    import random
except:
    print('random module could not be loaded.\n It should be part of the standard configuration\n')
    raise
    
class hardware:
    LED = 5 # PIO 5, Pi header pin 29
    def __init__( self ):
        self.pi = pigpio.pi()
        if not self.pi.connected():
            print("Could not connect to pigpiod, was it started?\n")
            exit()
        self.led = self.pi.set_mode( type(self).LED, pigpio.OUTPUT )
                
class Source(threading.Thread):
    """
    Change dits/dahs/gaps to timed events
    """
    def __init__( self ):
        super().__init__()
        global configuration
        self.outQ = queue.Queue( maxsize=50 )
        Pulses( self.outQ ).start()
        self.source_function = self.random
        self.choices = Pulses.Volcabulary() + list(' '*10)

    def random( self ):
        return random.choice( self.choices )

    def  run( self ):
        while True:
            self.outQ.put( self.source_function() )

class Pulses(threading.Thread):
    """
    Change letters to dits/dahs/gaps as timed events and play
    Send on to LettersOut after each is played
    """
    # From https://morsecode.world/international/morse2.html
    cw = {
    'A' : '.-'    ,
    'B' : '-...'  ,
    'C' : '-.-.'  ,
    'D' : '-..'   ,
    'E' : '.'     ,
    'F' : '..-.'  ,
    'G' : '--.'   ,
    'H' : '....'  ,
    'I' : '..'    ,
    'J' : '.---'  ,
    'K' : '-.-'   ,
    'L' : '.-..'  ,
    'M' : '--'    ,
    'N' : '-.'    ,
    'O' : '---'   ,
    'P' : '.--.'  ,
    'Q' : '--.-'  ,
    'R' : '.-.'   ,
    'S' : '...'   ,
    'T' : '-'     ,
    'U' : '..-'   ,
    'V' : '...-'  ,
    'W' : '.--'   ,
    'X' : '-..-'  ,
    'Y' : '-.--'  ,
    'Z' : '--..'  ,
    
    '0' : '-----' ,
    '1' : '.----' ,
    '2' : '..---' ,
    '3' : '...--' ,
    '4' : '....-' ,
    '5' : '.....' ,
    '6' : '-....' ,
    '7' : '--...' , 
    '8' : '---..' ,
    '9' : '----.' ,
    
    '.' : '.-.-.-',
    ',' : '--..--',
    '?' : '..--..',
    '/' : '-..-.' ,
    '=' : '-...-' ,
    '@' : '.--.-.',
    ':' : '---...',

    '<bk>' : '-...-',
    '<sk>' : '...-.-',
    '<ar>' : '.-.-.',
    }

    def __init__( self, Q, WPM=5  ):
        super().__init__()
        global configuration
        self.wpm = WPM
        self.Q = Q
        self.clients = []
        if configuration['Audio']:
            self.clients.append( Audio() )
        if configuration['Buzzer']:
            self.clients.append( Buzzer() )
        if configuration['LEDflash']:
            self.clients.append( LEDflash() )

        self.outQ = queue.SimpleQueue()
        LettersOut( self.outQ ).start()
        self.cw = type(self).cw
        

    @classmethod
    def Volcabulary( cls ):
        return list(cls.cw.keys())

    @property
    def wpm( self ):
        return self._wpm

    @wpm.setter
    def wpm( self, Wpm ):
        self._wpm = Wpm
        self.DIT  = self._dittime()
        self.DAH  = self.DIT * 3
        self.GAP  = self.DIT * 1
        self.LGAP = self.DIT * 3 - self.GAP
        self.WGAP = self.DIT * 7 - self.LGAP - self.GAP

    def _dittime( self ):
        return 60. / (50 * self._wpm)
        
    def on( self ):
        for c in self.clients:
            c.on()

    def off( self ):
        for c in self.clients:
            c.off()

    def run( self ):
        while True:
            letter = self.Q.get()
            if letter not in self.cw:
                continue
            if letter == " ":
                time.sleep( self.WGAP )
                self.outQ.put(letter)
                continue
            for d in self.cw(letter):
                if d == '.':
                    self.on()
                    time.sleep( self.DIT )
                    self.off()
                    time.sleep( self.GAP )
                elif d == '-':
                    self.on()
                    time.sleep( self.DAH )
                    self.off()
                    time.sleep( self.GAP )

            time.sleep( self.LGAP )
            self.outQ.put(letter)

class LettersOut(threading.Thread):
    """
    Change dits/dahs/gaps to timed events
    """
    def __init__( self, Q ):
        super().__init__()
        global configuration
        self.Q = Q
        self.clients = []
        if configuration['Terminal']:
            self.clients.append( Terminal )

    def run( self ):
        while True:
            letter = self.Q.get()
            for c in self.clients:
                c.write(letter)

if configuration['Terminal']:
    class Terminal:
        """
        Letters out to terminal
        Single instance
        """
        _instance = None

        def __new__( cls ):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
        
        def __init__( self ):
            print()

        def write( self, letter ):
            print( letter, end = '' )
            
if configuration['Audio']:
    class Audio(pysinewave.SineWave):
        """
        Computer audio beeps using pysinewave
        Single instance
        """
        _instance = None

        def __new__( cls ):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
        
        def __init__( self ):
            self._pitch_ = 0
            self.volume = 0
            super().__init__( pitch = self._pitch_, decibels = self.volume )

        def on( self ):
            self.play()

        def off( self ):
            self.stop()

        def louder( self ):
            self.volume += 3
            self.set_volume( self.volume )

        def softer( self ):
            self.volume -= 3
            self.set_volume( self.volume )

        def higher( self ):
            self._pitch_ += 6
            self.set_pitch( self._pitch_ )

        def lower( self ):
            self._pitch_ -= 6
            self.set_pitch( self._pitch_ )

if configuration['Buzzer']:
    class Buzzer:
        """
        Computer audio beeps using pysinewave
        Single instance
        """
        _instance = None

        def __new__( cls ):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
        
        def __init__( self ):
            self._pitch_ = 0
            self.volume = 0

        def on( self ):
            self.play()

        def off( self ):
            self.stop()

        def louder( self ):
            self.volume += 3
            self.set_volume( self.volume )

        def softer( self ):
            self.volume -= 3
            self.set_volume( self.volume )

        def higher( self ):
            self._pitch_ += 6
            self.set_pitch( self._pitch_ )

        def lower( self ):
            self._pitch_ -= 6
            self.set_pitch( self._pitch_ )

if configuration['Graphics']:
    class Graphics():
        """
        Computer audio beeps using pysinewave
        Single instance
        """
        _instance = None

        def __new__( cls ):
            if cls._instance is None:
                cls._instance = super().__new__(cls)                
            return cls._instance
        
        def __init__( self ):
            # set root window
            self.root = tk.Tk()
            # Set geometry
            self.root.geometry("400x400")
            self.flash = tk.Frame( self.root, width=50, height=50, bg="Gray" )
            self.flash.grid()

        @property
        def Root( self ):
            return self.root

        def on( self ):
            self.play()

        def off( self ):
            self.stop()

        def louder( self ):
            self.volume += 3
            self.set_volume( self.volume )

        def softer( self ):
            self.volume -= 3
            self.set_volume( self.volume )

        def higher( self ):
            self._pitch_ += 6
            self.set_pitch( self._pitch_ )

        def lower( self ):
            self._pitch_ -= 6
            self.set_pitch( self._pitch_ )

def BCM():
    infofile = "/proc/cpuinfo"
    try:
        with open(infofile) as f:
            lines = f.readlines()
            for l in lines:
                s = re,search(r'BCM\d\d\d\d',l)
                if s is not None:
                    return s.group()
            return None
    except:
        print( "Could not open <{}> for hardware information".format(infofile) )
        return None
            
def signal_handler(signal, frame):
    sys.exit(0)

def main(args):
    global configuration
    
    # keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    if configuration['Graphics']:
        Graphics()

    Source().start()

    if configuration['Graphics']:
        Graphics().Root.mainloop()
    
    

    # load library

if __name__ == "__main__":
    # execute only if run as a script
    sys.exit(main(sys.argv))
