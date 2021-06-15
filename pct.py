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
        import simpleaudio as sa
    except:
        print('simpleaudio module could not be loaded.\n Perhaps it needs to be installed by "pip3 install simpleaudio".\n It may also need libasound2-dev\n')
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

running = True
    
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

gPulses = None
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
        self.Fwpm = WPM
        self.Cwpm = WPM
        self.inQ = inQ
        self.outQ = outQ
        self.clients = [ gBuzzer, gLEDflash, gGraphics ]
        self.farnsworth( WPM, WPM )

        self.cw = type(self).cw
        

    @classmethod
    def Volcabulary( cls ):
        return list(cls.cw.keys())

    def farnsworth( self, Fwpm=5, Cwpm=18 ):
        # total words per minute Wpm
        # Characters sent as Cwpm
        # see https://morsecode.world/international/timing.html
        global gAudio
        self.Fwpm = Fwpm
        self.Cwpm = Cwpm
        self.DIT  = 60. / (50. * Cwpm )
        self.DAH  = self.DIT * 3
        self.GAP  = self.DIT * 1
        fdit = ( 300. * Cwpm - 186. * Fwpm ) / ( 95. * Cwpm * Fwpm ) 
        self.LGAP = fdit * 3 - self.GAP
        self.WGAP = fdit * 7 - self.LGAP - self.GAP
        if gAudio:
            gAudio.settimes( self.DIT, self.DAH )

    def on( self ):
        for c in self.clients:
            if c is not None:
                c.on()

    def off( self ):
        for c in self.clients:
            if c is not None:
                c.off()

    def run( self ):
        # called in a separate thread by "start()"
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
    class Audio:
        """
        Computer audio beeps using pyaudio
        Code from pysine
        https://github.com/lneuhaus/pysine/blob/master/pysine/pysine.py
        """
        def __init__( self ):
            self.freq = 1024.
            self.sample_rate = 44100
            self.volume = 20000 # in range 4000 to 32700
            
            # Use rounding of 1ms as in https://brats-qth.org/training/advanced/trandrec8.htm
            # Will use formula: y = (x/T)^2*(3-2*x/T) --- a smoothing function with rotational symmetry at x=0, x=T
            self.shoulder_length = int( .001 * self.sample_rate )
            self.smooth = np.linspace(0,1,self.shoulder_length)
            self.smooth = self.smooth**2 * (3-2*self.smooth)

        def __del__(self):
            sa.stop_all()

        def makewave( self, duration ):
            times = np.linspace(0, duration, int(duration*self.sample_rate), endpoint=False)
            wave = np.sin(times*self.freq*2*np.pi)*self.volume # Raw sine wave
            wave[0:self.shoulder_length] *= self.smooth # Start smooth
            wave[-self.shoulder_length:] *= 1-self.smooth # End smooth
            return sa.WaveObject( wave.astype('int16'), 1, 2, self.sample_rate )

        def play( self, d ):
            if d == ".":
                self.dit()
            else:
                self.dah()

        def settimes( self, DIT, DAH ):

            self.DIT = DIT
            self.ditwave = self.makewave( DIT )

            self.DAH = DAH
            self.dahwave = self.makewave( DAH )

        def dit( self ):
            self.ditwave.play()

        def dah( self ):
            self.dahwave.play()

        def louder( self ):
            self.volume = max( 32700, int( self.volume * 1.3 ) )
            self.settimes( self.DIT, self.DAH )

        def softer( self ):
            self.volume = min( 4000, int( self.volume * .7 ) )
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
            self.main = tk.Frame(self.root)
            # Set geometry
            self.root.geometry("400x400")

            
            self.flash = tk.Frame( self.main, width=100, height=50 )
            self.off()
            self.flash.pack()

            self.text = tk.Text( self.main, height=1 )
            self.text.config( font=("Courier",24) )
            self.text.pack()

            self.Speed( self.main )

            self.Menu( self.root )

            self.main.pack()

        def Mainloop( self ):
            return self.root.mainloop()

        def Menu( self, frame ):
            menubar = tk.Menu( frame )

            filemenu = tk.Menu( menubar, tearoff=0 )
            filemenu.add_command(label="Exit", command=self.root.quit)
            menubar.add_cascade(label="File", menu=filemenu)

            soundmenu = tk.Menu( menubar, tearoff=0 )
            soundmenu.add_command(label="Higher", command=self.higher)
            soundmenu.add_command(label="Lower", command=self.lower)
            soundmenu.add_separator()
            soundmenu.add_command(label="Louder", command=self.louder)
            soundmenu.add_command(label="Softer", command=self.softer)
            menubar.add_cascade(label="Sound", menu=soundmenu)

            frame.config( menu=menubar )

        def Speed( self, frame ):
            self.fspeed = tk.Frame(frame)
            
            tk.Label( self.fspeed, text="Timing" ).grid(row=0,column=0 )
            #tk.Label( self.fspeed, text="Timing" ).pack()

            self.farnsvar = tk.BooleanVar( value=True )
            tk.Checkbutton( self.fspeed, text="Farnsworth", variable=self.farnsvar, command=self.set_fvar ).grid( row=0,column=1 )


            # assert Cwpm >= Fwpm
            self.cwpmcontrol=tk.LabelFrame( self.fspeed, text="Character speed in words per minute", relief=tk.RIDGE )
            self.cwpmvar = tk.IntVar( value=13 )
            tk.Scale( self.cwpmcontrol, from_=5, to=60, resolution=1, orient=tk.HORIZONTAL, variable=self.cwpmvar, command=self.set_cwpm ).pack() 
            self.cwpmcontrol.grid(columnspan=2, sticky="nesw" )

            fwpmcontrol=tk.LabelFrame( self.fspeed, text="Total words per minute", relief=tk.RIDGE )
            self.fwpmvar = tk.IntVar( value=5  )
            tk.Scale( fwpmcontrol, from_=5, to=60, resolution=1, orient=tk.HORIZONTAL, variable=self.fwpmvar, command=self.set_fwpm ).pack()
            fwpmcontrol.grid(columnspan=2, sticky="nesw")
            
            self.farnsvar.set(True) # To trigger a change and set proper timing
            
            self.fspeed.pack()

        def set_fvar( self ):
            global gPulses
            # Farnsworth Checkbox
            if self.farnsvar.get():
                # Yes Farnsworth now
                self.cwpmcontrol.grid()
                gPulses.farnsworth( self.fwpmvar.get(), self.cwpmvar.get() )
            else:
                # No Farnsworth
                self.cwpmcontrol.grid_remove()
                gPulses.farnsworth( self.fwpmvar.get(), self.fwpmvar.get() )
            
        def set_cwpm( self, val ):
            global gPulses
            # Change char wpm
            f = self.fwpmvar.get()
            c = self.cwpmvar.get()
            if c < f:
                self.fwpmvar.set(c)
                gPulses.farnsworth( f, f )
            elif self.farnsvar.get():
                gPulses.farnsworth( f, c )
            else:
                gPulses.farnsworth( f, f )
                
        def set_fwpm( self, val ):
            global gPulses
            # Change farnsworth wpm
            f = self.fwpmvar.get()
            c = self.cwpmvar.get()
            if c < f:
                self.cwpmvar.set(f)
                gPulses.farnsworth( f, f )
            elif self.farnsvar.get():
                gPulses.farnsworth( f, c )
            else:
                gPulses.farnsworth( f, f )
                
        def louder( self ):
            global gAudio, gBuzzer
            if gAudio:
                gAudio.louder()
            if gBuzzer:
                gBuzzer.louder()

        def softer( self ):
            global gAudio, gBuzzer
            if gAudio:
                gAudio.softer()
            if gBuzzer:
                gBuzzer.softer()

        def higher( self ):
            global gAudio, gBuzzer
            if gAudio:
                gAudio.higher()
            if gBuzzer:
                gBuzzer.higher()

        def lower( self ):
            global gAudio, gBuzzer
            if gAudio:
                gAudio.lower()
            if gBuzzer:
                gBuzzer.lower()

        def on( self ):
            self.root.after_idle( self._on)

        def off( self ):
            self.root.after_idle( self._off)

        def _on( self ):
            self.flash['background']='red'

        def _off( self ):
            self.flash['background']='grey'

        def write( self, letter ):
            self.text.insert( tk.END, letter )
            self.text.see( tk.END )

def signal_handler(signal, frame):
    global running
    running = False
    sys.exit(0)

def main(args):
    global configuration, gPiHardware, gAudio, gGraphics, gTerminal, running, gPulses
    
    # keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)

    try:
        gPiHardware = PiHardware()
    except:
        gPiHardware = None

    try:
        gAudio = Audio()
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
    gPulses = Pulses(sourceQ,resultQ)
    gPulses.start()
    Source(sourceQ).start()

    if gGraphics is not None:
        gGraphics.Mainloop()
    
if __name__ == "__main__":
    # execute only if run as a script
    sys.exit(main(sys.argv))
