from machine import Pin, I2C



class INA219:
    I2C_ADDRESS = 0x40
    CONFIG_REG = 0x0
    SHUNT_VOLTAGE_REG = 0x1
    BUS_VOLTAGE_REG = 0x2
    POWER_REG = 0x3
    CURRENT_REG = 0x4
    CALIBRATION_REG = 0x5
    
    # Maximum current in mA.
    MAX_CURRENT = 3200
    
    
    def __init__(self):
        self.i2c = I2C(1, scl=Pin(27), sda=Pin(26), freq=400000)
        self.i2c.scan()
        
        # Set configuration for max current and least reading frequency.
        self.i2c.writeto_mem(self.I2C_ADDRESS, self.CONFIG_REG, b'\x1F\xFF')
        self.i2c.writeto_mem(self.I2C_ADDRESS, self.CONFIG_REG, b'\x80\x00')
        self.i2c.writeto_mem(self.I2C_ADDRESS, self.CALIBRATION_REG, b'\x10\x00')
    
    
    def get_bus_voltage(self) -> float:
        ''' Returns the INA219 bus voltage in V.
        '''
        voltage = self.i2c.readfrom_mem(self.I2C_ADDRESS, self.BUS_VOLTAGE_REG, 2)
        voltage = float((int.from_bytes(voltage, 'big') >> 3) * 4 / 1000)
        return voltage
        
        
    def get_power(self) -> int:
        ''' Returns the power measured by INA219 in mW.
        '''
        power = self.i2c.readfrom_mem(self.I2C_ADDRESS, self.POWER_REG, 2)
        power = int.from_bytes(power, 'big') * 2
        return power
    
    
    def get_current(self) -> float:
        ''' Returns the INA219 current in mA.
        '''
        current = self.i2c.readfrom_mem(self.I2C_ADDRESS, self.CURRENT_REG, 2)
        current = int.from_bytes(current, 'big') / 10
        current = 0 if current > self.MAX_CURRENT else current
        
        # Filter noise.
        current = 0 if current <= 1 else current
        
        return current