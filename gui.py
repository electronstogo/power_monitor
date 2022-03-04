from ili9488 import ILI9488
from font import *





class GUI:
    # Maximum number of measured values in the graph lists.
    MAX_VALUE_NUMBER = 200
    
    # Graph height in pixel.
    Y_HEIGHT = 125
    
    # Zero-point offset of y axis. 
    Y_OFFSET = 135
    
    # Zero-point offset of x axis. 
    X_OFFSET = 40
    
    
    
    def __init__(self, frames_sec):
        self.height = ILI9488.HEIGHT - (ILI9488.HEIGHT - self.Y_OFFSET) - 1
        
        self.current_values = []
        self.power = 0
        self.voltage = 0
        self.work = 0
        self.current_max = 0
        self.time_offset = 0
        self.frames_sec = 1 / frames_sec
        self.process_active = False
        
        self.lcd = ILI9488()
    

    def draw_point(self, x, y, color):
        ''' Draws one pixel at given position.
        '''
        self.lcd.hline(x, y, 1, color)
    
    
    def get_letter_index(self, letter):
        ''' Returns the data table index of given letter.
        '''   
        if letter.isdigit():
            return ord(letter) - ord('0') + 1
        elif letter.isupper():
            return ord(letter) - ord('A') + 11
        elif letter.islower():
            return ord(letter) - ord('a') + 37
        elif letter == '.':
            return 0
        elif letter == '=':
            return 63
    
    
    def draw_letter(self, letter, x, y, color):
        ''' Draws the letter and returns its width in pixel.
        '''
        index = self.get_letter_index(letter)
        
        # Get the letter byte width, height and table offset.
        width = int(FONT_META[index][0] / 8) + (1 if FONT_META[index][0] % 8 else 0)
        offset = FONT_META[index][1]
        height = int((FONT_META[index + 1][1] - FONT_META[index][1]) / width)
        
        # Correction of y to set same text line.
        y = y + (MAX_FONT_HEIGHT - height) if MAX_FONT_HEIGHT > height else height
        
        # Bit width as return value for spaces when string is drawn.
        bit_width = 0
        
        # Draw the letter.
        for i in range(width * height):
            for j in range(8):
                if(FONT_DATA[offset + i] >> j) & 0x1:
                    self.draw_point(x + (7 - j) + (i % width) * 8, y + int(i / width), color)
                    bit_width = 7 - j if 7 - j > bit_width and i % width == width - 1 else bit_width
                            
        # Return bit width.
        bit_width += (width - 1) * 8

        return bit_width
    
    
    def draw_string(self, string, x, y, color):
        offset = 0
        for letter in string:
            if letter == ' ':
                offset += 5
                continue
            
            offset += self.draw_letter(letter, x + offset, y, color) + 4
    
    
    def get_string_width(self, string):
        ''' Returns the width of string in pixels.
        '''
        width = 0
        
        for letter in string:
            width += FONT_META[self.get_letter_index(letter)][0] + 4
            
        return width - 4
    
    
    def draw_string_right_adjusted(self, string, x, y, color):
        ''' Draws a string right aligned at position.
        '''
        offset = 0
        width = self.get_string_width(string)
        for letter in string:
            offset += self.draw_letter(letter, x + offset - width, y, color) + 4
    
    
    def set_bus_voltage(self, value):
        ''' Updates the voltage currently applied at load.
        '''
        self.voltage = value if self.process_active else 0
    
    
    def update_power(self, value):
        ''' Updates the power currently needed by load.
        '''
        self.power = value if self.process_active else 0
    
    
    def update_work(self, value):
        ''' Adds the measured bus power for the last time slot to the work value. 
        '''
        if not self.process_active:
            return
        
        self.work = self.work + value / self.frames_sec
    
    
    def add_current_value(self, value):
        ''' Adds the current value to list.
        '''
        
        if not self.process_active:
            return
        
        # If maximum of current values is reached.
        if len(self.current_values) >= self.MAX_VALUE_NUMBER:
            # Shift current values.
            self.current_values.pop(0)
            # Increment time offset
            self.time_offset += 1 / self.frames_sec
        
        self.current_values.append(value)
        
        # Update maximum current.
        self.current_max = value if value > self.current_max else self.current_max
    
    
    def reset_data(self):
        ''' Resets process data if user stops. 
        '''
        self.current_values.clear()
        self.time_offset = 0
        self.work = 0
        self.current_max = 0
    
    
    def handle_touch(self):
        ''' Checks touch inputs for button activation.
        '''
        touch = self.lcd.get_touch()
        
        if not touch:
            return
    
        x = int((touch[1] - 430) * 480 / 3270)
        x = x if x < 480 else 480
        x = x if x > 0 else 0
        
        y = 320 - int((touch[0] - 430) * 320 / 3270)
        y = y if y > 0 else 0
        
        # Check if buttons range is touched.
        if ILI9488.WIDTH * 2 - 70 > x > ILI9488.WIDTH * 2 - 170:
            if 15 < y < 65:
                if self.process_active:
                    self.reset_data()
                
                self.process_active = not self.process_active
    
    
    def update(self):
        ''' Updates graph, numerical data views and buttons.
        '''
        self.draw_graph_part_1()
        self.draw_graph_part_2()
        self.draw_numeric_values()
        self.draw_buttons()
        
        
    def draw_buttons(self):
        self.lcd.fill(ILI9488.BLACK)
        
        # Top button.
        color = ILI9488.RED if self.process_active else ILI9488.GREEN
        for i in range(2):
            self.lcd.hline(70, 15 + i, 100, color)
            self.lcd.hline(70, 65 + i, 100, color)
            self.lcd.vline(70 + i, 15, 50, color)
            self.lcd.vline(170 + i, 15, 50, color)
            
        # Button text depends on process state.
        if not self.process_active:
            self.draw_string('START', 79, 24, color)
        else:
            self.draw_string('STOP', 85, 24, color)
        
        
        self.lcd.update_rectangle(ILI9488.RIGHT, ILI9488.TOP)
        

    def draw_graph_part_1(self):
        ''' Draws the left part of the graph.
        '''
        self.lcd.fill(0xFDDE)
        
        ## Draw graph frame.
        length = ILI9488.WIDTH - self.X_OFFSET
        
        # Draw graph frame.
        self.lcd.hline(self.X_OFFSET, self.Y_OFFSET, length, ILI9488.BLACK)
        self.lcd.hline(self.X_OFFSET, self.Y_OFFSET + 1, length, ILI9488.BLACK)
        self.lcd.vline(self.X_OFFSET, self.Y_OFFSET - self.height, self.height, ILI9488.BLACK)
        self.lcd.vline(self.X_OFFSET - 1, self.Y_OFFSET - self.height, self.height, ILI9488.BLACK)
        
        # X dotted lines.
        for x in [1, 2, 3]:
            for y in range(int(self.Y_OFFSET / 4) + 1):
                self.lcd.vline(int(length / 4) * x + self.X_OFFSET, self.Y_OFFSET - y * 4, 2, ILI9488.BLACK)   
        
        # Y coordinate lines.
        self.lcd.hline(self.X_OFFSET - 6, 1, 12, ILI9488.BLACK)
        self.lcd.hline(self.X_OFFSET - 6, 2, 12, ILI9488.BLACK)
        
        # Y dotted lines.
        for y in [1, 2, 3]:
            for x in range(int(length / 4) + 1):
                self.lcd.vline(self.X_OFFSET + x * 4, self.Y_OFFSET - int(self.height / 4) * y, 2, ILI9488.BLACK)
            
        self.lcd.hline(self.X_OFFSET - 6, self.Y_OFFSET - int(self.height / 2), 12, ILI9488.BLACK)
        self.lcd.hline(self.X_OFFSET - 6, self.Y_OFFSET - int(self.height / 2) - 1, 12, ILI9488.BLACK)
        
        
        # Draw time with unit, and x-coordinate lines.
        self.lcd.vline(self.X_OFFSET + 120, self.Y_OFFSET - 5, 12, ILI9488.BLACK)
        self.lcd.vline(self.X_OFFSET + 121, self.Y_OFFSET - 5, 12, ILI9488.BLACK)
        string = str(int((self.frames_sec * 60 + self.time_offset) / 60)) + ' min'
        self.lcd.text(string, self.X_OFFSET + 110, ILI9488.HEIGHT - 15, ILI9488.BLACK)
        
    
        # Get maximum current to scale graph. 
        if self.process_active:
            current_max = int(max(self.current_values) + 1)
        else:
            current_max = 1
    
        # Draw current values and unit for axis.
        self.lcd.text(str(current_max), 16, 3, ILI9488.BLACK)
        self.lcd.text(str(current_max / 2), 7, int(self.height / 2) - 2, ILI9488.BLACK)
        self.lcd.text('mA', 16, 12, ILI9488.BLACK)
        
            
        # Leave if no measurements have been made already.
        if not len(self.current_values):
            self.lcd.update_rectangle(ILI9488.LEFT, ILI9488.BOTTOM)
            return
    
        
        # Calculate and scale the first y value.
        y_old = self.current_values[0]
        y_old = int((y_old / current_max) * self.Y_HEIGHT)
        
        
        # Draw current data into diagram.
        for i, value in enumerate(self.current_values[:100]):
            y = int((value / current_max) * self.Y_HEIGHT)
            self.lcd.line(self.X_OFFSET + i * 2, self.Y_OFFSET - y_old, self.X_OFFSET + (i + 1) * 2, self.Y_OFFSET - y, ILI9488.RED)
            self.lcd.line(self.X_OFFSET - 1 + i * 2, self.Y_OFFSET - y_old, self.X_OFFSET - 1 + (i + 1) * 2, self.Y_OFFSET - y, ILI9488.RED)
            y_old = y
            
            
        self.lcd.update_rectangle(ILI9488.LEFT, ILI9488.BOTTOM)
    
    
    def draw_graph_part_2(self):
        ''' Draws the right part of the graph.
        '''
        self.lcd.fill(0xFDDE)
        
        length = ILI9488.WIDTH - self.X_OFFSET
        self.lcd.hline(0, self.Y_OFFSET, length, ILI9488.BLACK)
        self.lcd.hline(0, self.Y_OFFSET + 1, length, ILI9488.BLACK)
        
            
        # X dotted lines.
        for x in range(5):
            for y in range(int(self.Y_OFFSET / 4) + 1):
                self.lcd.vline(int(length / 4) * x, self.Y_OFFSET - y * 4, 2, ILI9488.BLACK)    
            
        
        # Y dotted lines.        
        for y in [1, 2, 3]:
            for x in range(int(length / 4) + 1):
                self.lcd.vline(x * 4, self.Y_OFFSET - int(self.height / 4) * y, 2, ILI9488.BLACK)
        
        # Draw time with unit, and x-coordinate lines.
        self.lcd.vline(40, self.Y_OFFSET - 5, 12, ILI9488.BLACK)
        self.lcd.vline(41, self.Y_OFFSET - 5, 12, ILI9488.BLACK)
        string = str(int((self.frames_sec * 120 + self.time_offset) / 60)) + ' min'
        self.lcd.text(string, 30, ILI9488.HEIGHT - 15, ILI9488.BLACK)
        
        self.lcd.vline(160, self.Y_OFFSET - 5, 12, ILI9488.BLACK)
        self.lcd.vline(161, self.Y_OFFSET - 5, 12, ILI9488.BLACK)
        string = str(int((self.frames_sec * 180 + self.time_offset) / 60)) + ' min'
        self.lcd.text(string, 150, ILI9488.HEIGHT - 15, ILI9488.BLACK)
        

        # Draw second graph lines if more than 100 current measurements where done.
        if len(self.current_values) > 100:
            # Get maximum current to scale graph. 
            current_max = int(max(self.current_values) + 1)
            
            # Calculate and scale the first y value.
            y_old = int((self.current_values[99] / current_max) * self.Y_HEIGHT)
            
            
            # Draw current data into diagram.
            for i, value in enumerate(self.current_values[100:]):
                y = int((value / current_max) * self.Y_HEIGHT)
                self.lcd.line(i * 2, self.Y_OFFSET - y_old, (i + 1) * 2, self.Y_OFFSET - y, ILI9488.RED)
                self.lcd.line(i * 2, self.Y_OFFSET - y_old, 1 + (i + 1) * 2, self.Y_OFFSET - y, ILI9488.RED)
                y_old = y
            
            
            
        self.lcd.update_rectangle(ILI9488.RIGHT, ILI9488.BOTTOM)

        
    def draw_numeric_values(self):
        ''' Draws the numerical data.
        '''
        self.lcd.fill(ILI9488.BLACK)
        
        # X position offsets of the different string parts.
        x_character = 65
        x_equals = 80
        x_value = 180
        x_unit = 185
        
        y_pos = 2
        
        # Current.
        self.draw_string_right_adjusted('I', x_character, y_pos, ILI9488.WHITE)
        self.draw_string('=', x_equals, y_pos, ILI9488.WHITE)
        
        if self.process_active:
            string = str('%1.1f' %self.current_values[-1]) if self.current_values[-1] < 1000 else '%1.1f' %(self.current_values[-1] / 1000)
            self.draw_string('mA' if self.current_values[-1] < 1000 else 'A', x_unit, y_pos, ILI9488.WHITE)
        else:
            string = '0'
            self.draw_string('mA', x_unit, y_pos, ILI9488.WHITE)
        
        self.draw_string_right_adjusted(string, x_value, y_pos, ILI9488.WHITE)
        
        
        y_pos += 30
        
        # Maximum current.
        self.draw_string_right_adjusted('Imax', x_character, y_pos, ILI9488.WHITE)
        self.draw_string('=', x_equals, y_pos, ILI9488.WHITE)
        
        string = '%1.1f' %self.current_max if self.current_max < 1000 else '%1.1f' %(self.current_max / 1000)
        self.draw_string('mA' if self.current_max < 1000 else 'A', x_unit, y_pos, ILI9488.WHITE)
        self.draw_string_right_adjusted(string, x_value, y_pos, ILI9488.WHITE)
        
        
        y_pos += 30
        
        # Voltage.
        self.draw_string_right_adjusted('U', x_character, y_pos, ILI9488.WHITE)
        self.draw_string('=', x_equals, y_pos, ILI9488.WHITE)
        string = '%1.1f' %self.voltage
        self.draw_string_right_adjusted(string, x_value, y_pos, ILI9488.WHITE)
        self.draw_string('V', x_unit, y_pos, ILI9488.WHITE)
        
        y_pos += 30
        
        # Power
        self.draw_string_right_adjusted('P', x_character, y_pos, ILI9488.WHITE)
        self.draw_string('=', x_equals, y_pos, ILI9488.WHITE)
        string = '%1.1f' %self.power if self.power < 1000 else '%1.1f' %(self.power / 1000)
        self.draw_string_right_adjusted(string, x_value, y_pos, ILI9488.WHITE)
        self.draw_string('mW' if self.power < 1000 else 'W', x_unit, y_pos, ILI9488.WHITE)
        
        y_pos += 30
        
        # Work.
        self.draw_string_right_adjusted('W', x_character, y_pos, ILI9488.WHITE)
        self.draw_string('=', x_equals, y_pos, ILI9488.WHITE)
        string = '%1.2f' %(self.work / 3600)
        self.draw_string_right_adjusted(string, x_value, y_pos, ILI9488.WHITE)
        self.draw_string('Wh', x_unit, y_pos, ILI9488.WHITE)
        

        self.lcd.update_rectangle(ILI9488.LEFT, ILI9488.TOP)




