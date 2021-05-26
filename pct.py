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

try:
    import pigpio
except:
    print('pigpio module could not be loaded.\n Perhaps it needs to be installed by "pip3 install pigpio"\n')
    raise

try:
    import threading
except:
    print('threading module could not be loaded.\n')
    raise
    
try:
    import queue
except:
    print('queue module could not be loaded.\n')
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
        for q in self.outputQs
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


class Pulses( Queued ):
    """
    Change dits/dahs/gaps to timed events
    """

    DIT = 1
    DAH = 3
    GAP = 1
    LGAP = 3 - GAP
    WGAP = 7 - GAP - WGAP

    def __init__( self, WPM=5, *args ):
        self.wpm = WPM
        super().__init__( *args )

    @property
    def wpm( self ):
        return self._wpm

    @wpm.setter
    def wpm( self, Wpm ):
        self._wpm = Wpm
        self.dt = self._dittime

    def _dittime( self ):
        return 60. / (50 * self._wpm)
        
    def start( self ):
        while True:
            d = self.inputQ.get()
            if d == '.':
                self.put((1,self._dt*type(self).DIT))
                self.put((0,self._dt*type(self).GAP))
            elif d == '-':
                self.put((1,self._dt*type(self).DAH))
                self.put((0,self._dt*type(self).GAP))
            elif d == 'LGAP':
                self.put((0,self._dt*type(self).LGAP))
            elif d == 'WGAP':
                self.put((0,self._dt*type(self).WGAP))
