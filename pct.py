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
    


class code:
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

    time = {
    '.'    : 1 ,
    '-'    : 3 ,
    'sub'  : 1 ,
    'char' : 3 ,
    'word' : 7 ,
    }
    
class communicate:
    q = None
    def __init__( self ):
        if type(self).q is None:
            self.q = queue.SimpleQueue()
            type(self).q = self.q
            

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
        
