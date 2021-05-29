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
        import tkinter
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
    

class communicate:
    q = None
    def __init__( self ):
        if type(self).q is None:
            self.q = queue.SimpleQueue()
            type(self).q = self.q

    @property
    def Q( self ):
        return self.q
            
class hardware(communicate):
    LED = 5 # PIO 5, Pi header pin 29
    def __init__( self ):
        self.pi = pigpio.pi()
        if not self.pi.connected():
            print("Could not connect to pigpiod, was it started?\n")
            exit()
        self.led = self.pi.set_mode( type(self).LED, pigpio.OUTPUT )
        
    def pulse_led( self ):
        self.led.write
        
class LED(communicate):
    def __init__( self, pin ):
        self.pin = pin
        self.led = self.pi.set_mode( pin, pigpio.OUTPUT )

    def put( self, x ):
        for q in self.outputQs:
            q.put(x)

class Queued:
    """
    Class that handles input source and translates to
    multiple output sources
    with a trigger to indicate progress
    """
    def __init__( self, inputQ, outputQ2, triggerF ):
        self.inputQ = inputQ
        self.outputQs = outputQs
        self.triggerF = triggerF
        self.start()

class Ditter( Queued ):
    # From https://morsecode.world/international/morse2.html
    cw = {
    'a' : '.-'    ,
    'b' : '-...'  ,
    'c' : '-.-.'  ,
    'd' : '-..'   ,
    'e' : '.'     ,
    'f' : '..-.'  ,
    'g' : '--.'   ,
    'h' : '....'  ,
    'i' : '..'    ,
    'j' : '.---'  ,
    'k' : '-.-'   ,
    'l' : '.-..'  ,
    'm' : '--'    ,
    'n' : '-.'    ,
    'o' : '---'   ,
    'p' : '.--.'  ,
    'q' : '--.-'  ,
    'r' : '.-.'   ,
    's' : '...'   ,
    't' : '-'     ,
    'u' : '..-'   ,
    'v' : '...-'  ,
    'w' : '.--'   ,
    'x' : '-..-'  ,
    'y' : '-.--'  ,
    'z' : '--..'  ,
    
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
    }

    def start( self ):
        while True:
            letter = self.inputQ.get()
            if letter == ' ':
                self.put('WGAP' )
            else:    
                for d in type(self).cw[d]:
                    self.put(d)
                self.put('LGAP')


class Pulses:
    """
    Change dits/dahs/gaps to timed events
    """

    DIT = 1
    DAH = 3
    GAP = 1
    LGAP = 3 - GAP
    WGAP = 7 - GAP - LGAP

    def __init__( self, Q, WPM=5  ):
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
        
    @property
    def wpm( self ):
        return self._wpm

    @wpm.setter
    def wpm( self, Wpm ):
        self._wpm = Wpm
        self.dt = self._dittime

    def _dittime( self ):
        return 60. / (50 * self._wpm)
        
    def on( self ):
        for c in self.clients:
            c.on()

    def off( self ):
        for c in self.clients:
            c.off()

    def start( self ):
        while True:
            d = self.Q.get()
            if d == '.':
                self.on()
                time.sleep( self._dt * type(self).DIT )
                self.off()
                time.sleep( self._dt*type(self).GAP )
            elif d == '-':
                self.on()
                time.sleep( self._dt * type(self).DAH )
                self.off()
                time.sleep( self._dt*type(self).GAP )
            elif d == 'LGAP':
                time.sleep( self._dt*type(self).LGAP )
            elif d == 'WGAP':
                time.sleep( self._dt*type(self).WGAP )

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
            
