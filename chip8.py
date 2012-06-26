import os
import itertools
import random

class graphics(object):
  # draws objects on screen
  def initialize(self):
    print "Initializing graphics..."
    print "...done."
 
  def draw(self):
    pass
    
  def clear(self):
    pass
 
class sound(object):
  # plays sounds
  def initialize(self):
    print "Initializing sound..."
    print "...done."
    
  def buzz(self):
    print "Playing a sound!"
  
class cpu (object):
  memory = [0]*4096 # max 4096
  gpio = [0]*16 # max 16
  display_buffer = [0]*32 # 64*32
  stack = []
  key_inputs = [0]*16
  fonts = [0]*80 #fonts
  
  opcode = 0
  index = 0
  pc = 0
  
  delay_timer = 0
  sound_timer = 0
  
  graphics = graphics()
  sound = sound()
  
  should_draw = False
  
  def load_rom(self, rom_path):
    binary = open("pong", "rb").read()
    i = 0
    while i < len(binary):
      self.memory[i+0x200] = ord(binary[i])
      i += 1
  
  def initialize(self):
    self.memory = [0]*4096 # max 4096
    self.gpio = [0]*16 # max 16
    self.display_buffer = [0]*32 # 64*32
    self.stack = []
    self.key_inputs = [0]*16  
    self.opcode = 0
    self.index = 0

    self.delay_timer = 0
    self.sound_timer = 0
    self.should_draw = False
    
    self.pc = 0x200
    
    i = 0
    while i < 80:
      # load 80-char font set
      self.memory[i] = self.fonts[i]
      i += 1
  
  def cycle(self):
    # Opcodes taken from http://en.wikipedia.org/wiki/CHIP-8#Opcode_table
    # 1. get op (op code plus operand)
    self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
    
    # 2. check ops
    extracted_op = self.opcode & 0xf000
    if extracted_op == 0:
      extracted_op = self.opcode & 0x000f
      if extracted_op == 0: # Clears the screen
        self.graphics.clear()
        self.pc += 2
      elif extracted_op == 0x000e: # Returns from subroutine 
        self.pc = selt.stack.pop()
    elif extracted_op == 0x1000: # Jumps to address NNN.
      jumpto = self.opcode & 0x0fff
      self.pc = jumpto
    elif extracted_op == 0x2000: # Calls subroutine at NNN.
      sub_address = self.opcode & 0x0fff
      self.stack.append(self.pc)
      self.pc = sub_address
    elif extracted_op == 0x3000: # Skips the next instruction if VX equals NN.
      if self.gpio[(self.opcode & 0x0f00) >> 8] == (self.opcode & 0x00ff):
        self.pc += 2
      self.pc += 2
    elif extracted_op == 0x4000: # Skips the next instruction if VX doesn't equal NN.
      if self.gpio[(self.opcode & 0x0f00) >> 8] != (self.opcode & 0x00ff):
        self.pc += 2
      self.pc += 2
    elif extracted_op == 0x5000: # Skips the next instruction if VX equals VY.
      if self.gpio[(self.opcode & 0x0f00) >> 8] == self.gpio[(self.opcode & 0x00f0) >> 4]:
        self.pc += 2
      self.pc += 2
    elif extracted_op == 0x6000: # Sets VX to NN.
      self.gpio[(self.opcode & 0x0f00) >> 8] = self.opcode & 0x00ff
      self.pc += 2
    elif extracted_op == 0x7000: # Adds NN to VX.
      self.gpio[(self.opcode & 0x0f00) >> 8] += self.opcode & 0x00ff
      self.pc += 2
    elif extracted_op == 0x8000:
      extracted_op = extracted_op & 0x000f
      if self.extracted_op == 0x0000: # Sets VX to the value of VY.
        self.gpio[(self.opcode & 0x0f00) >> 8] = self.gpio[(self.opcode & 0x00f0) >> 4]
        self.pc += 2
      elif extracted_op == 0x0001: # Sets VX to VX or VY.
        self.gpio[(self.opcode & 0x0f00) >> 8] |= self.gpio[(self.opcode & 0x00f0) >> 4]
        self.pc += 2
      elif extracted_op == 0x0002: # Sets VX to VX and VY.
        self.gpio[(self.opcode & 0x0f00) >> 8] &= self.gpio[(self.opcode & 0x00f0) >> 4]
        self.pc += 2
      elif extracted_op == 0x0003: # Sets VX to VX xor VY.
        self.gpio[(self.opcode & 0x0f00) >> 8] ^= self.gpio[(self.opcode & 0x00f0) >> 4]
        self.pc += 2
      elif extracted_op == 0x0004: # Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't.
        self.gpio[(self.opcode & 0x0f00) >> 8] += self.gpio[(self.opcode & 0x00f0) >> 4]
        if self.gpio[(self.opcode & 0x0f00) >> 8] > 0xff:
          self.gpio[0xf] = 1
        else:
          self.gpio[0xf] = 0
        self.gpio[(self.opcode & 0x0f00) >> 8] &= 0xff
        self.pc += 2
      elif extracted_op == 0x0005: # VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't
        self.gpio[(self.opcode & 0x0f00) >> 8] -= self.gpio[(self.opcode & 0x00f0) >> 4]
        if self.gpio[(self.opcode & 0x00f0) >> 4] > 0xff:
          self.gpio[0xf] = 1
        else:
          self.gpio[0xf] = 0
        self.gpio[(self.opcode & 0x0f00) >> 8] &= 0xff
        self.pc += 2
      elif extracted_op == 0x0006: # Shifts VX right by one. VF is set to the value of the least significant bit of VX before the shift.
        self.gpio[0xf] = self.gpio[(self.opcode & 0x0f00) >> 8] & 0x000f
        self.gpio[(self.opcode & 0x0f00) >> 8] = self.gpio[(self.opcode & 0x0f00) >> 8] >> 1
        self.pc += 2
      elif extracted_op == 0x0007: # Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't.
        if self.gpio[(self.opcode & 0x0f00) >> 8] > 0xff:
          self.gpio[0xf] = 1
        else:
          self.gpio[0xf] = 0
        self.gpio[(self.opcode & 0x0f00) >> 8] = self.gpio[(self.opcode & 0x00f0) >> 4] - self.gpio[(self.opcode & 0x0f00) >> 8]
        self.gpio[(self.opcode & 0x0f00) >> 8] &= 0xff
        self.pc += 2
      elif extracted_op == 0x000e: # Shifts VX left by one. VF is set to the value of the most significant bit of VX before the shift.[2]
        self.gpio[0xf] = self.gpio[(self.opcode & 0x0f00) >> 8] & 0x00f0
        self.gpio[(self.opcode & 0x0f00) >> 8] = self.gpio[(self.opcode & 0x0f00) >> 8] << 1
        self.pc += 2
    elif extracted_op == 0x9000: # Skips the next instruction if VX doesn't equal VY.
      if self.gpio[(self.opcode & 0x0f00) >> 8]!= self.gpio[(self.opcode & 0x00f0) >> 4]:
        self.pc += 2
      self.pc += 2
    elif extracted_op == 0xa000: # Sets I to the address NNN.
      self.index = self.opcode & 0x0fff
      self.pc += 2
    elif extracted_op == 0xb000: # Jumps to the address NNN plus V0.
      self.pc = (self.opcode & 0x0fff) + self.gpio[0]
    elif extracted_op == 0xc000: # Sets VX to a random number and NN.
      r = int(random.random() * 0xff)
      self.gpio[(self.opcode & 0x0f00) >> 8] = r & (self.opcode & 0x00ff)
      self.pc += 2
    elif extracted_op == 0xd000:
      # Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels
      # and a height of N pixels. Each row of 8 pixels is read as bit-coded
      # (with the most significant bit of each byte displayed on the left)
      # starting from memory location I; I value doesn't change after the
      # execution of this instruction. As described above, VF is set to 1
      # if any screen pixels are flipped from set to unset when the sprite
      # is drawn, and to 0 if that doesn't happen.
      print "Draw a pixel!!!"
      self.pc += 2
    elif extracted_op == 0xe000:
      extracted_op == self.extracted_op & 0x000f
      if extracted_op == 0x000e: # Skips the next instruction if the key stored in VX is pressed.
        if self.key_inputs[self.gpio[(self.opcode & 0x0f00) >> 8]] == 1:
          self.pc += 2
        self.pc += 2
      elif extracted_op == 0x0001: # Skips the next instruction if the key stored in VX isn't pressed.
        if self.key_inputs[self.gpio[(self.opcode & 0x0f00) >> 8]] == 0:
          self.pc += 2
        self.pc += 2
    elif extracted_op == 0xf000:
      extracted_op == self.opcode & 0x00ff
      if extracted_op == 0x0007: # Sets VX to the value of the delay timer.
        self.gpio[(self.opcode & 0x0f00) >> 8] = self.delay_timer
      elif extracted_op == 0x000a: # A key press is awaited, and then stored in VX.
        p = 0
        print "Wait for a keypress..."
        #self.gpio[
        self.pc += 2
      elif extracted_op == 0x0015: # Sets the delay timer to VX.
        self.delay_timer = self.gpio[(self.opcode & 0x0f00) >> 8]
        self.pc += 2
      elif extracted_op == 0x0018: # Sets the sound timer to VX.
        self.sound_timer = self.gpio[(self.opcode & 0x0f00) >> 8]
        self.pc += 2
      elif extracted_op == 0x001e: # Adds VX to I. if overflow, vf = 1
        self.index += self.gpio[(self.opcode & 0x0f00) >> 8]
        if self.index > 0xfff:
          self.gpio[0xf] = 1
          self.index &= 0xfff
        else:
          self.gpio[0xf] = 0
        self.pc += 2
      elif extracted_op == 0x0029:
        # Sets I to the location of the sprite for the character in VX.
        # Characters 0-F (in hexadecimal) are represented by a 4x5 font.
        print "character location"
        self.pc += 2
      elif extracted_op == 0x0033:
        # Stores the Binary-coded decimal representation of VX, with the
        # most significant of three digits at the address in I, the middle
        # digit at I plus 1, and the least significant digit at I plus 2.
        self.memory[i]   = (self.gpio[(self.opcode & 0x0f00) >> 8] & 0xf00) >> 8
        self.memory[i+1] = (self.gpio[(self.opcode & 0x0f00) >> 8] & 0x0f0) >> 4
        self.memory[i+2] = (self.gpio[(self.opcode & 0x0f00) >> 8] & 0x00f)
        self.pc += 2
      elif extracted_op == 0x0055: # Stores V0 to VX in memory starting at address I.
        i = 0
        while i < 0xf:
          self.memory[self.index + i] = self.gpio[i]
          i += 1
        self.index += ((self.opcode & 0x0f00) >> 8) + 1
        self.pc += 2
      elif extracted_op == 0x0065: # Fills V0 to VX with values from memory starting at address I.
        i = 0
        while i < 0xf:
          self.gpio[i] = self.memory[self.index + i]
          i += 1
        self.index += ((self.opcode & 0x0f00) >> 8) + 1
        self.pc += 2
    
    # 3. time it
    if self.delay_timer > 0:
      self.delay_timer -= 1
    if self.sound_timer > 0:
      self.sound_timer -= 1
      if sound_timer == 0:
        self.sound.buzz()
    
  def draw(self):
    if self.should_draw:
      self.graphics.draw()
    pass
    
  def keystate(self):
    pass
  
  def main(self):
    if len(sys.argv) < 1:
      print "Usage: python chip8.py <path to chip8 rom>"
      return
    self.initialize()
    self.graphics.initialize()
    self.sound.initialize()
    self.load_rom("pong")
    while True:
      self.cycle()
      self.draw()
      self.keystate()
      

# begin emulating!    
chip8emu = cpu()
chip8emu.main()
