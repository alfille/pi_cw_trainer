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

# Note: tkinter only likes being the primary thread, so will just use it for control
# alternatively could poll repidly.

configuration = {
    'Graphics'  : True  ,
    'Keyboard'  : True  ,
    'Audio'     : True  ,
    'Buzzer'    : False ,
    'LEDflash'  : False ,
    'LEDscreen' : False ,
    'Knob'      : False ,
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
        import numpy as np
    except:
        print('Numpy module could not be loaded.\n Perhaps it needs to be installed by "pip3 install numpy"\n')
        raise
    try:
        import pyaudio
    except:
        print('pyaudio module could not be loaded.\n Perhaps it needs to be installed by "pip3 install pyaudio"\n')
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
    
gPiHardware = None
if configuration['Buzzer'] or configuration['Knob'] or configuration['LEDscreen'] or configuration['LEDflash']:
    class PiHardware:
        """
        PiHardware connection -- i.e. Raspberry Pi GPIO pins
        """

        # PiHardware PWM (for buzzer)
        # GPIO Header
        #  g12    p32
        #  g13    p33
        #  g18    p12
        #  g19    p35

        # I2C
        #      BUS 1 (prefered)
        #  g02     p3 (Data)
        #  g03     p5 (CLK)
        #      BUS 0
        #  g00    p27 (Data)
        #  g01    p28 (CLK)

        # Pure GPIO Pins
        #  g05    p29
        #  g06    p31
        #      and more
        
        
        # Choices
        LED = 5 # PIO 5, Pi header pin 29
        PWM = 32
        I2Cbus = 1
        
        def __init__( self ):
            global configuration, gLEDflash, gBuzzer
            self.pi = pigpio.pi()
            if not self.pi.connected:
                print("Could not connect to pigpiod, was it started?\n")
                exit()
            
            try:
                gLEDflash = LEDflash( self.pi, type(self).LED )
            except:
                gLEDflash = None

            try:
                gBuzzer = Buzzer( self.pi, type(self).PWM )
            except:
                gBuzzer = None
                            
class Source(threading.Thread):
    """
    Change dits/dahs/gaps to timed events
    """
    def __init__( self, Q ):
        super().__init__()
        global configuration
        self.outQ = Q
        self.source_function = self.random
        self.choices = Pulses.Volcabulary() + list(' '*10)

    def random( self ):
        return random.choice( self.choices )

    def  run( self ):
        # called in a separate thred by "start()"
        global running
        while running:
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

    def __init__( self, inQ, outQ, WPM=5  ):
        super().__init__()
        global gAudio, gBuzzer, gLEDflash, gGraphics
        self.wpm = WPM
        self.inQ = inQ
        self.outQ = outQ
        self.clients = [ gBuzzer, gLEDflash, gGraphics ]

        self.cw = type(self).cw
        

    @classmethod
    def Volcabulary( cls ):
        return list(cls.cw.keys())

    @property
    def wpm( self ):
        return self._wpm

    @wpm.setter
    def wpm( self, Wpm ):
        global gAudio
        self._wpm = Wpm
        self.DIT  = self._dittime()
        self.DAH  = self.DIT * 3
        self.GAP  = self.DIT * 1
        self.LGAP = self.DIT * 3 - self.GAP
        self.WGAP = self.DIT * 7 - self.LGAP - self.GAP
        if gAudio:
            gAudio.settimes( self.DIT, self.DAH )

    def _dittime( self ):
        return 60. / (50 * self._wpm)
        
    def on( self ):
        for c in self.clients:
            if c is not None:
                c.on()

    def off( self ):
        for c in self.clients:
            if c is not None:
                c.off()

    def run( self ):
        # called in a separate thred by "start()"
        global running, gAudio
        while running:
            letter = self.inQ.get()
            if letter not in self.cw:
                continue
            if letter == " ":
                time.sleep( self.WGAP )
                self.outQ.put(letter)
                continue
            for d in self.cw[letter]:
                if d == '.':
                    if gAudio:
                        gAudio.play(".")
                    self.on()
                    time.sleep( self.DIT )
                    self.off()
                    time.sleep( self.GAP )
                elif d == '-':
                    if gAudio:
                        gAudio.play("-")
                    self.on()
                    time.sleep( self.DAH )
                    self.off()
                    time.sleep( self.GAP )

            time.sleep( self.LGAP )
            self.outQ.put(letter)
            self.inQ.task_done()

class LettersOut(threading.Thread):
    """
    Change dits/dahs/gaps to timed events
    """
    def __init__( self, Q ):
        super().__init__()
        global configuration, gTerminal, gGraphics
        self.Q = Q
        self.clients = [ gTerminal, gGraphics ]

    def run( self ):
        # called in a separate thred by "start()"
        global running
        while running:
            letter = self.Q.get()
            for c in self.clients:
                if c is not None:
                    c.write(letter)
            self.Q.task_done()

gTerminal = None
if configuration['Terminal']:
    class Terminal:
        """
        Letters out to terminal
        """
        def __init__( self ):
            print()

        def write( self, letter ):
            print( letter, end = '' )
            
gAudio = None
if configuration['Audio']:
    class Audio(threading.Thread):
        """
        Computer audio beeps using pyaudio
        Code from pysine
        https://github.com/lneuhaus/pysine/blob/master/pysine/pysine.py
        """
        def __init__( self ):
            print("Audio 1")
            self.stream = None
            self.freq = 512.
            self.Q = queue.Queue( maxsize=2 )
            print(pyaudio.get_portaudio_version_text())
            print("Audio 2")
            self.pa = pyaudio.PyAudio()
            print("Audio 3")
            print(pyaudio.get_default_output_device_info() )
            print("Audio 4")
            try:
                self.stream = self.pa.open(
                    format=self.pa.get_format_from_width(1),
                    channels=1,
                    rate=96000,
                    output=True)
                print(self.stream)
            except:
                print("pyaudio open error")
                raise
            super().__init__()

        def play( self, d ):
            self.Q.put( d )

        def __del__(self):
            print("Audio delete")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.pa.terminate()

        def makewave( self, duration ):
            points = int(96000 * duration)
            times = np.linspace(0, duration, points, endpoint=False)
            return np.array((np.sin(times*self.freq*2*np.pi) + 1.0)*127.5, dtype=np.int8).tobytes()
            
        def run( self ) :
            # called in a separate thread by "start()"
            global running
            while running:
                if self.Q.get() == ".":
                    self.dit()
                else:
                    self.dah()
                self.Q.task_done()

        def settimes( self, DIT, DAH ):

            self.DIT = DIT
            self.ditwave = self.makewave( DIT )

            self.DAH = DAH
            self.dahwave = self.makewave( DAH )

        def dit( self ):
            self.stream.write( self.ditwave )

        def dah( self ):
            self.stream.write( self.dahwave )

        def louder( self ):
            self.volume += 3
            self.settimes( self.DIT, self.DAH )

        def softer( self ):
            self.volume -= 3
            self.settimes( self.DIT, self.DAH )

        def higher( self ):
            self.freq *= np.sqrt(2)
            self.settimes( self.DIT, self.DAH )

        def lower( self ):
            self.freq *= np.sqrt(.5)
            self.settimes( self.DIT, self.DAH )

gBuzzer = None
if configuration['Buzzer']:
    class Buzzer:
        """
        Piezo beep using PWM pin amplified with transistor
        """
        def __init__( self, handle, pin ):
            self._pitch_ = 0
            self.calc()
            self.volume = 0
            self.pin = pin
            self.handle = handle

        def on( self ):
            self.handle.hardware_PWM( self.pin , self.freq , 500000 )

        def off( self ):
            self.handle.hardware_PWM( self.pin , self.freq , 0 )

        def louder( self ):
            pass

        def softer( self ):
            pass

        def higher( self ):
            self._pitch_ += 6
            self.set_pitch( self._pitch_ )
            self.calc()

        def lower( self ):
            self._pitch_ -= 6
            self.set_pitch( self._pitch_ )
            self.calc()

        def calc( self ):
            self.freq = 256. * pow(2,self._pitch_/12.)

gLEDflash = None
if configuration['LEDflash']:
    class LEDflash:
        """
        Flash singleLED connected to a gpio pin (with 10K resistor)
        """
        def __init__( self, handle, pin ):
            self.pin = pin
            self.handle = handle
            self.handle.set_mode( self.pin, pigpio.OUTPUT )

        def on( self ):
            self.handle.write( self.pin , 1 )

        def off( self ):
            self.handle.write( self.pin , 0 )

gGraphics = None
if configuration['Graphics']:
    class Graphics():
        """
        Computer audio beeps using pysinewave
        Single instance
        """
        root = None

        def __init__( self ):
            # set root window
            self.root = tk.Tk()
            # Set geometry
            self.root.geometry("400x400")

            self.flash = tk.Frame( self.root, width=50, height=50 )
            self.off()
            self.flash.pack()

            self.text = tk.Text( self.root)
            self.text.config( font=("Courier",20) )
            self.text.pack()

        def Mainloop( self ):
            return self.root.mainloop()

        def on( self ):
            self.root.after_idle( self._on)

        def off( self ):
            self.root.after_idle( self._off)

        def _on( self ):
            self.flash['background']='red'

        def _off( self ):
            self.flash['background']='grey'

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

        def write( self, letter ):
            self.text.insert( tk.END, letter )

def signal_handler(signal, frame):
    global running
    running = False
    sys.exit(0)

def main(args):
    global configuration, gPiHardware, gAudio, gGraphics, gTerminal, running
    
    # keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    try:
        gPiHardware = PiHardware()
    except:
        gPiHardware = None

    try:
        gAudio = Audio()
        gAudio.start()
    except:
        gAudio = None

    try:
        gGraphics = Graphics()
    except:
        gGraphics = None

    try:
        gTerminal = Terminal()
    except:
        gTerminal = None

    sourceQ = queue.Queue( maxsize=50 )
    resultQ = queue.Queue( maxsize=0 )

    running = True

    LettersOut(resultQ).start()
    Pulses(sourceQ,resultQ).start()
    Source(sourceQ).start()

    if gGraphics is not None:
        gGraphics.Mainloop()
    running = False
    
if __name__ == "__main__":
    # execute only if run as a script
    sys.exit(main(sys.argv))
