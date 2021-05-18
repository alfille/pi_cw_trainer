# pi_cw_trainer
HArdware and software for a CW (Morse Code) trainer ... Audio and visual.

The design goal is to make a stand-alone CW trainer.

Parts:
* Raspberry Pi -- any generation
  * SD card 4 GB or larger
  * Power supply
* Freenove Super Starter Kit for Raspberry Pi
  * About $22 on Amazon
  * Includes breakout board
  * LED and resistor
  * LCD screen with I2C controller
  * Potentiometer * 2
  * ADC chip via I2C
  * Speaker (passive buzzer with transistor driver)
  * LED matrix screen
  * Pushbuttons 

Software:
* Raspbian OS https://www.raspbian.com
* pigpio library http://abyz.me.uk/pigpio/ or https://github.com/joan2937/pigpio

Installation
* Install raspbian OS
* Install pigpio
  * Need cmake
    sudo apt install cmake
  * From Github:
```
git clone https://github.com/joan2937/pigio
cd pigpio
mkdir build
cd build
cmake ../
make -j4
sudo make install
sudo systemctl start pigpiod.service
sudo systemctl enable pigpiod.service
sudo systemctl status pigpiod.service
cd ~
````
  * Python module
  ```
  pip3 install pigpio
  ```
  
* Enable I2c control
  * sudo raspi-config




