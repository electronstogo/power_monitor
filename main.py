from gui import GUI
from ina219 import INA219
from ili9488 import ILI9488
import time



# GUI frames per sec. 
FRAMES_SEC = 1



if __name__=='__main__':
    gui = GUI(FRAMES_SEC)
    ina219 = INA219()
    
    
    timestamp = time.ticks_ms()
    debounce = True
    
    
    while True:
        if(time.ticks_diff(time.ticks_ms(), timestamp) < 1000 * FRAMES_SEC):
            time.sleep_ms(10)
            if debounce:
                gui.handle_touch()
                debounce = False
                
            continue
        
        debounce = True
        timestamp = time.ticks_ms()
        
        
        # Add current, power, work and bus voltage to digram data.
        gui.add_current_value(ina219.get_current())
        power = ina219.get_power()
        gui.update_power(power)       
        gui.update_work(power)
        gui.set_bus_voltage(ina219.get_bus_voltage())

        gui.update()