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

# asyncio version

# 2021 Paul H Alffille

configuration = {
    'Graphics'  : True  ,
    'Audio'     : False ,
    'Keyboard'  : True  ,
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
    import asyncio
except:
    print('asyncio module could not be loaded.\n It should be part of the standard configuration\n')
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
    
try:
    import re
except:
    print('re module (regular expression search) could not be loaded.\n It should be part of the standard configuration\n')
    raise
    
gHardware = None
if configuration['Buzzer'] or configuration['Knob'] or configuration['LEDscreen'] or configuration['LEDflash']:
    class Hardware:
        """
        Hardware connection -- i.e. Raspberry Pi GPIO pins
        """

        # Hardware PWM (for buzzer)
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
            self.led = self.pi.set_mode( type(self).LED, pigpio.OUTPUT )
            self.BCM = self.board() # Type of Pi

            if configuration['LEDflash']:
                gLEDflash = LEDflash( self.pi, type(self).LEDpin )

            if configuration['Buzzer']:
                gBuzzer = Buzzer( self.pi, type(self).PWMpin )

class Source:
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

    async def  run( self ):
        while True:
            await self.outQ.put( self.source_function() )

class Pulses:
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
        global gLEDflash, gAudio, gBuzzer, gGraphics
        self.wpm = WPM
        self.Q = inQ
        self.outQ = outQ

        self.clients = []
        if gAudio is not None:
            self.clients.append( gAudio )
        if gBuzzer is not None:
            self.clients.append( gBuzzer )
        if gLEDflash is not None:
            self.clients.append( gLEDflash )
        if gGraphics is not None:
            self.clients.append( gGraphics )

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

    async def run( self ):
        while True:
            letter = await self.Q.get()
            if letter not in self.cw:
                continue
            if letter == " ":
                time.sleep( self.WGAP )
                await self.outQ.put(letter)
                continue
            for d in self.cw[letter]:
                if d == '.':
                    self.on()
                    await asyncio.sleep( self.DIT )
                    self.off()
                    await asyncio.sleep( self.GAP )
                elif d == '-':
                    self.on()
                    await asyncio.sleep( self.DAH )
                    self.off()
                    await asyncio.sleep( self.GAP )

            await asyncio.sleep( self.LGAP )
            await self.outQ.put(letter)

class LettersOut:
    """
    Change dits/dahs/gaps to timed events
    """
    def __init__( self, Q ):
        super().__init__()
        global configuration, gTerminal
        self.Q = Q
        self.clients = []
        if gTerminal is not None:
            self.clients.append( gTerminal )

    async def run( self ):
        while True:
            letter = await self.Q.get()
            for c in self.clients:
                c.write(letter)

gTerminal = None
if configuration['Terminal']:
    class Terminal:
        """
        Letters out to terminal
        Single instance
        """
        def __init__( self ):
            print()

        def write( self, letter ):
            print( letter, end = '' )
            
gAudio = None
if configuration['Audio']:
    class Audio(pysinewave.SineWave):
        """
        Computer audio beeps using pysinewave
        """
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
        """
        def __init__( self ):
            # set root window
            self.root = tk.Tk()
            # Set geometry
            self.root.geometry("400x400")
            self.flash = tk.Frame( self.root, width=50, height=50 )
            self.off()
            self.flash.grid()

        @property
        def Root( self ):
            return self.root

        def on( self ):
            self.flash['background']='red'

        def off( self ):
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
    
def signal_handler(signal, frame):
    sys.exit(0)

async def run_tk(root, interval=0.05):
    try:
        while True:
            root.update()
            await asyncio.sleep(interval)
            print(".",end='')
    except tkinter.TclError as e:
        if "application has been destroyed" not in e.args[0]:
            raise

async def main(args):
    global configuration, gHardware, gGraphics, gTerminal, gAudio
    
    # keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    sourceQ = asyncio.Queue( maxsize = 50 )
    letterQ = asyncio.Queue()
    
    if configuration['Buzzer'] or configuration['Knob'] or configuration['LEDscreen'] or configuration['LEDflash']:
        gHardware = Hardware()

    if configuration['Terminal']:
        gTerminal = Terminal()

    if configuration['Audio']:
        gAudio = Audio()

    asyncio.ensure_future( Source( sourceQ ).run() )
    asyncio.ensure_future( Pulses( sourceQ, letterQ ).run() )
    asyncio.ensure_future( LettersOut( letterQ ).run() )

    if configuration['Graphics']:
        gGraphics = Graphics()
        await run_tk( gGraphics.Root )

if __name__ == "__main__":
    # execute only if run as a script
    asyncio.get_event_loop().run_until_complete(main(sys.argv))
    sys.exit()
