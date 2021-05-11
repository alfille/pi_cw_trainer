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
    
    
    
    
