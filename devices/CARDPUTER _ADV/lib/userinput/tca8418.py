from machine import I2C, Pin
import time

# TCA8418 Register Addresses
REG_CFG = 0x01
REG_INT_STAT = 0x02
REG_KEY_STAT = 0x04
REG_KEY_LCK_EC = 0x03
REG_KP_ML_SM = 0x0E
REG_KP_SL_CFG = 0x0F
REG_KP_GPIO1 = 0x1D # KP_GPIO1 for COL0-COL7 / ROW0-ROW7
REG_KP_GPIO2 = 0x1E # KP_GPIO2 for COL8-COL10 / ROW8-ROW9
REG_KP_GPIO3 = 0x1F # KP_GPIO3 for ROW10-ROW11

# Default I2C address for the TCA8418
TCA8418_ADDR = 0x34

class TCA8418:
    """MicroPython driver for the TCA8418 I2C Keypad/GPIO expander."""

    def __init__(self, i2c, address=TCA8418_ADDR):
        self.i2c = i2c
        self.address = address
        if self.address not in self.i2c.scan():
            raise OSError(f"TCA8418 not found at address {hex(self.address)}")
        self.init_device()

    def _write_register(self, register, value):
        """Writes a byte value to a specific register using writeto_mem."""
        self.i2c.writeto_mem(self.address, register, bytes([value]))

    def _read_register(self, register):
        """Reads a byte value from a specific register using readfrom_mem."""
        data = self.i2c.readfrom_mem(self.address, register, 1)
        return data[0] # Return the single byte value

    def init_device(self):
        """Initializes the TCA8418 for keypad scanning mode and clears interrupts."""
        
        # 1. Clear any pending interrupts by writing to the status register
        self._write_register(REG_INT_STAT, 0xFF)

        # 2. Configure the chip:
        # Enable keypad interrupt (KE_IEN) and set interrupt config (INT_CFG)
        # 0x11: INT_EN=1, INT_CFG=1 (cleared by writing 1), KE_IEN=1
        self._write_register(REG_CFG, 0x11) 

        # 3. Define which pins are part of the keypad matrix (example for an 8x2 matrix)
        # You MUST configure these registers based on your physical wiring.
        # This example assumes R0-R7 and C0-C1 are used.
        
        # To configure ALL rows (R0-R11) and columns (C0-C10) to be part of the keypad matrix:
        self._write_register(REG_KP_GPIO1, 0xFF) # Enable all pins in this register for keypad use
        self._write_register(REG_KP_GPIO2, 0xFF) 
        self._write_register(REG_KP_GPIO3, 0x0F) # Adjust this mask based on actual rows used
        
        # 4. Enable Keypad Matrix Scan Mode
        # Write 0x01 to KP_ML_SM to enable scanning
        self._write_register(REG_KP_ML_SM, 0x01)
        
    def read_event_count(self):
        # Check the number of events in the FIFO - including press and release
        event_count = self._read_register(REG_KEY_LCK_EC) & 0x0F
        return event_count

    def read_key_event(self):
        """Reads the next key event from the FIFO queue."""
        
        # Read register to determin what asserted the interrupt
        interrupt = self._read_register(REG_INT_STAT)
        
        # Check if bit 0 is set
        if (interrupt & 0x00) != 0:
            return 0, 0
            
        if (interrupt & 0x01) != 0:            
            # Check the number of events in the FIFO - including press and release
            event_count = self._read_register(REG_KEY_LCK_EC) & 0x0F
            
            if event_count > 0:
                # Reading REG_KEY_STAT pops the oldest event from the FIFO
                key_event = self._read_register(REG_KEY_STAT)
                
                # Key event format:
                # Bit 7: Key Event type (1=Press, 0=Release)
                # Bits 6:0: Keypad representation code (Row/Column combination)
                is_press = bool(key_event & 0x80)
                key_code = key_event & 0x7F
                
                # After processing all events, the interrupt line should go high
                # You might need to clear the interrupt status bit manually if using interrupt pin
                if event_count == 1:
                     self.clear_interrupt()

                return key_code, is_press
        
        return 0, 0

    def clear_interrupt(self):
        """Clears the interrupt status by reading/writing to the INT_STAT register."""
        # Reading the register clears it if INT_CFG bit is 0. 
        # If INT_CFG bit is 1 (as set in init_device), you must write 1 to clear the specific KE_INT bit.
        # Writing 0xFF ensures all bits are cleared for safety.
        self._write_register(REG_INT_STAT, 0xFF)
