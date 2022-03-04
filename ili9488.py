from machine import Pin,SPI,PWM
import framebuf
import time



class ILI9488(framebuf.FrameBuffer):
    WIDTH = 240
    HEIGHT = 160
    
    RIGHT  = 1
    LEFT   = 2
    TOP    = 1
    BOTTOM = 2

    LCD_DC   = 8
    LCD_CS   = 9
    LCD_SCK  = 10
    LCD_MOSI = 11
    LCD_MISO = 12
    LCD_BL   = 13
    LCD_RST  = 15
    TOUCH_CS    = 16
    TOUCH_IRQ   = 17
    
    RED   =  0x07E0
    GREEN =  0x001f
    BLUE  =  0xf800
    WHITE =  0xffff
    BLACK =  0x0000
    
    
    def __init__(self):
        self.cs = Pin(self.LCD_CS, Pin.OUT)
        self.rst = Pin(self.LCD_RST, Pin.OUT)
        self.dc = Pin(self.LCD_DC, Pin.OUT)
        
        self.cs.on()
        self.dc.on()
        self.rst.on()
        self.spi = SPI(1, 60_000_000, sck=Pin(self.LCD_SCK), mosi=Pin(self.LCD_MOSI), miso=Pin(self.LCD_MISO))
        
        self.irq = Pin(self.TOUCH_IRQ, Pin.IN)
        self.tp_cs = Pin(self.TOUCH_CS, Pin.OUT)
        self.tp_cs.on()
        
        self.buffer = bytearray(self.WIDTH * self.HEIGHT * 2)
        super().__init__(self.buffer, self.WIDTH, self.HEIGHT, framebuf.RGB565)
        
        self.init_display()
    

    def _write_cmd(self, cmd):
        ''' Writes command to display controller.
        '''
        cmd = cmd if isinstance(cmd, list) else [cmd] 

        for value in cmd:
            self.cs.on()
            self.dc.off()
            self.cs.off()
            self.spi.write(bytearray([value]))
            self.cs.on()


    def _write_data(self, data):
        ''' Writes data to display controller.
        '''
        data = data if isinstance(data, list) else [data] 

        for value in data:
            self.cs.on()
            self.dc.on()
            self.cs.off()
            self.spi.write(bytearray([value]))
            self.cs.on()
    
    
    def init_display(self):
        self.rst.on()
        time.sleep_ms(5)
        self.rst.off()
        time.sleep_ms(10)
        self.rst.on()
        time.sleep_ms(5)
        
        self._write_cmd([0x21, 0xC2])
        self._write_data(0x33)
        
        self._write_cmd(0XC5)
        self._write_data([0x0, 0x1E, 0x80])
        
        self._write_cmd(0xB1)
        self._write_data(0xB0)
        
        self._write_cmd(0x36)
        self._write_data(0x28)
        
        self._write_cmd(0XE0)
        self._write_data([0x0, 0x13, 0x18, 0x04, 0x0F, 0x06, 0x3A, 0x56])
        self._write_data([0x4D, 0x03, 0x0A, 0x06, 0x30, 0x3E, 0x0F])
        
        self._write_cmd(0XE1)
        self._write_data([0x0, 0x13, 0x18, 0x01, 0x11, 0x06, 0x38, 0x34])
        self._write_data([0x4D, 0x06, 0x0D, 0x0B, 0x31, 0x37, 0x0F])

        self._write_cmd(0X3A)
        self._write_data(0x55)

        self._write_cmd(0x11)
        time.sleep_ms(120)
        self._write_cmd([0x29, 0xB6])
        self._write_data([0x00, 0x62])
        
        self._write_cmd(0x36)
        self._write_data(0x28)
    
    
    def update_rectangle(self, side, height):
        """ Updates one of the 4 screen rectangles.
        """
        self._write_cmd(0x2A)
        self._write_data(0x00)
        self._write_data(0x00 if side == self.LEFT else 0xF0)
        self._write_data(0x00 if side == self.LEFT else 0x1)
        self._write_data(0xEF if side == self.LEFT else 0xDF)
        
        self._write_cmd(0x2B)
        self._write_data(0x00)
        self._write_data(0x00 if height == self.TOP else 0xA0)
        self._write_data(0x00 if height == self.TOP else 0x1)
        self._write_data(0x9f if height == self.TOP else 0x3F)
        
        self._write_cmd(0x2C)
        
        self.cs.on()
        self.dc.on()
        self.cs.off()
        self.spi.write(self.buffer)
        self.cs.on()
        

    def set_backlight(self, duty):
        ''' Sets backlight brightness.
        '''
        pwm = PWM(Pin(self.LCD_BL))
        pwm.freq(1000)
        pwm.duty_u16(655 * duty if duty < 100 else 65535)


    def get_touch(self):
        if not self.irq():
            self.tp_cs.off()
            touch_x = 0
            touch_y = 0
            
            self.spi = SPI(1, 5_000_000, sck=Pin(self.LCD_SCK), mosi=Pin(self.LCD_MOSI), miso=Pin(self.LCD_MISO))
            
            for i in range(0,3):
                self.spi.write(bytearray([0XD0]))
                touch_data = self.spi.read(2)
                time.sleep_us(10)
                touch_x = touch_x + (((touch_data[0] << 8) + touch_data[1]) >> 3)
                
                self.spi.write(bytearray([0X90]))
                touch_data = self.spi.read(2)
                touch_y = touch_y + (((touch_data[0] << 8) + touch_data[1]) >> 3)

            touch_x = touch_x / 3
            touch_y = touch_y / 3
            
            self.tp_cs.on()
            self.spi = SPI(1, 60_000_000, sck=Pin(self.LCD_SCK), mosi=Pin(self.LCD_MOSI), miso=Pin(self.LCD_MISO))
            
            return touch_x, touch_y