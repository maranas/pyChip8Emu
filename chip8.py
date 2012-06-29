# pyChip8Emu: Simple Chip8 interpreter/emulator.
# See README.md for more info
# Requires pyglet

import itertools
import os
import pyglet
import random
import sys
import time

from pyglet.sprite import Sprite

KEY_MAP = {pyglet.window.key._1: 0x1,
           pyglet.window.key._2: 0x2,
           pyglet.window.key._3: 0x3,
           pyglet.window.key._4: 0xc,
           pyglet.window.key.Q: 0x4,
           pyglet.window.key.W: 0x5,
           pyglet.window.key.E: 0x6,
           pyglet.window.key.R: 0xd,
           pyglet.window.key.A: 0x7,
           pyglet.window.key.S: 0x8,
           pyglet.window.key.D: 0x9,
           pyglet.window.key.F: 0xe,
           pyglet.window.key.Z: 0xa,
           pyglet.window.key.X: 0,
           pyglet.window.key.C: 0xb,
           pyglet.window.key.V: 0xf
          }
          
LOGGING = False
          
def log(msg):
  if LOGGING:
    print msg
  
class cpu (pyglet.window.Window):
  memory = [0]*4096 # max 4096
  gpio = [0]*16 # max 16
  display_buffer = [0]*32*64 # 64*32
  stack = []
  key_inputs = [0]*16
  fonts = [0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
           0x20, 0x60, 0x20, 0x20, 0x70, # 1
           0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
           0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
           0x90, 0x90, 0xF0, 0x10, 0x10, # 4
           0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
           0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
           0xF0, 0x10, 0x20, 0x40, 0x40, # 7
           0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
           0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
           0xF0, 0x90, 0xF0, 0x90, 0x90, # A
           0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
           0xF0, 0x80, 0x80, 0x80, 0xF0, # C
           0xE0, 0x90, 0x90, 0x90, 0xE0, # D
           0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
           0xF0, 0x80, 0xF0, 0x80, 0x80  # F
           ]
  
  opcode = 0
  index = 0
  pc = 0
  
  delay_timer = 0
  sound_timer = 0
    
  should_draw = False
  key_wait = False
  
  pixel = pyglet.image.load('pixel.png') # pseudo-pixelwise drawing with 10x10 boxes
  buzz = pyglet.resource.media('buzz.wav', streaming=False)
  
  # instruction functions
  funcmap = None # store op <-> method mappings here
  vx = 0 # store register numbers here for op method access
  vy = 0
  
  def _0ZZZ(self):
    extracted_op = self.opcode & 0xf0ff
    try:
      self.funcmap[extracted_op]()
    except:
      print "Unknown instruction: %X" % self.opcode
    
  def _0ZZ0(self):
    log("Clears the screen")
    self.display_buffer = [0]*64*32 # 64*32
    self.should_draw = True
    
  def _0ZZE(self):
    log("Returns from subroutine")
    self.pc = self.stack.pop()
      
  def _1ZZZ(self):
    log("Jumps to address NNN.")
    self.pc = self.opcode & 0x0fff
    
  def _2ZZZ(self):
    log("Calls subroutine at NNN.")
    self.stack.append(self.pc)
    self.pc = self.opcode & 0x0fff
      
  def _3ZZZ(self):
    log("Skips the next instruction if VX equals NN.")
    if self.gpio[self.vx] == (self.opcode & 0x00ff):
      self.pc += 2
      
  def _4ZZZ(self):
    log("Skips the next instruction if VX doesn't equal NN.")
    if self.gpio[self.vx] != (self.opcode & 0x00ff):
      self.pc += 2
      
  def _5ZZZ(self):
    log("Skips the next instruction if VX equals VY.")
    if self.gpio[self.vx] == self.gpio[self.vy]:
      self.pc += 2
      
  def _6ZZZ(self):
    log("Sets VX to NN.")
    self.gpio[self.vx] = self.opcode & 0x00ff
    
  def _7ZZZ(self):
    log("Adds NN to VX.")
    self.gpio[self.vx] += (self.opcode & 0xff)
    
  def _8ZZZ(self):
    extracted_op = self.opcode & 0xf00f
    extracted_op += 0xff0
    try:
      self.funcmap[extracted_op]()
    except:
      print "Unknown instruction: %X" % self.opcode
    
  def _8ZZ0(self):
    log("Sets VX to the value of VY.")
    self.gpio[self.vx] = self.gpio[self.vy]
    self.gpio[self.vx] &= 0xff
  
  def _8ZZ1(self):  
    log("Sets VX to VX or VY.")
    self.gpio[self.vx] |= self.gpio[self.vy]
    self.gpio[self.vx] &= 0xff
    
  def _8ZZ2(self):
    log("Sets VX to VX and VY.")
    self.gpio[self.vx] &= self.gpio[self.vy]
    self.gpio[self.vx] &= 0xff
    
  def _8ZZ3(self):
    log("Sets VX to VX xor VY.")
    self.gpio[self.vx] ^= self.gpio[self.vy]
    self.gpio[self.vx] &= 0xff
    
  def _8ZZ4(self):
    log("Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't.")
    if self.gpio[self.vx] + self.gpio[self.vy] > 0xff:
      self.gpio[0xf] = 1
    else:
      self.gpio[0xf] = 0
    self.gpio[self.vx] += self.gpio[self.vy]
    self.gpio[self.vx] &= 0xff
    
  def _8ZZ5(self):
    log("VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't")
    if self.gpio[self.vy] > self.gpio[self.vx]:
      self.gpio[0xf] = 0
    else:
      self.gpio[0xf] = 1
    self.gpio[self.vx] = self.gpio[self.vx] - self.gpio[self.vy]
    self.gpio[self.vx] &= 0xff
    
  def _8ZZ6(self):
    log("Shifts VX right by one. VF is set to the value of the least significant bit of VX before the shift.")
    self.gpio[0xf] = self.gpio[self.vx] & 0x0001
    self.gpio[self.vx] = self.gpio[self.vx] >> 1
    
  def _8ZZ7(self):
    log("Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't.")
    if self.gpio[self.vx] > self.gpio[self.vy]:
      self.gpio[0xf] = 0
    else:
      self.gpio[0xf] = 1
    self.gpio[self.vx] = self.gpio[self.vy] - self.gpio[self.vx]
    self.gpio[self.vx] &= 0xff
    
  def _8ZZE(self):
    log("Shifts VX left by one. VF is set to the value of the most significant bit of VX before the shift.")
    self.gpio[0xf] = (self.gpio[self.vx] & 0x00f0) >> 7
    self.gpio[self.vx] = self.gpio[self.vx] << 1
    self.gpio[self.vx] &= 0xff
      
  def _9ZZZ(self):
    log("Skips the next instruction if VX doesn't equal VY.")
    if self.gpio[self.vx] != self.gpio[self.vy]:
      self.pc += 2
      
  def _AZZZ(self):
    log("Sets I to the address NNN.")
    self.index = self.opcode & 0x0fff
    
  def _BZZZ(self):
    log("Jumps to the address NNN plus V0.")
    self.pc = (self.opcode & 0x0fff) + self.gpio[0]
    
  def _CZZZ(self):
    log("Sets VX to a random number and NN.")
    r = int(random.random() * 0xff)
    self.gpio[self.vx] = r & (self.opcode & 0x00ff)
    self.gpio[self.vx] &= 0xff
    
  def _DZZZ(self):
    log("Draw a sprite")
    # Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels
    # and a height of N pixels. Each row of 8 pixels is read as bit-coded
    # (with the most significant bit of each byte displayed on the left)
    # starting from memory location I; I value doesn't change after the
    # execution of this instruction. As described above, VF is set to 1
    # if any screen pixels are flipped from set to unset when the sprite
    # is drawn, and to 0 if that doesn't happen.
    self.gpio[0xf] = 0
    x = self.gpio[self.vx] & 0xff
    y = self.gpio[self.vy] & 0xff
    height = self.opcode & 0x000f
    row = 0
    while row < height:
      curr_row = self.memory[row + self.index]
      pixel_offset = 0
      while pixel_offset < 8:
        loc = x + pixel_offset + ((y + row) * 64)
        pixel_offset += 1
        if (y + row) >= 32 or (x + pixel_offset - 1) >= 64:
          # ignore pixels outside the screen
          continue
        mask = 1 << 8-pixel_offset
        curr_pixel = (curr_row & mask) >> (8-pixel_offset)
        self.display_buffer[loc] ^= curr_pixel
        if self.display_buffer[loc] == 0:
          self.gpio[0xf] = 1
        else:
          self.gpio[0xf] = 0
      row += 1
    self.should_draw = True
    
  def _EZZZ(self):
    extracted_op = self.opcode & 0xf00f
    try:
      self.funcmap[extracted_op]()
    except:
      print "Unknown instruction: %X" % self.opcode
    
  def _EZZE(self):
    log("Skips the next instruction if the key stored in VX is pressed.")
    key = self.gpio[self.vx] & 0xf
    if self.key_inputs[key] == 1:
      self.pc += 2
      
  def _EZZ1(self):
    log("Skips the next instruction if the key stored in VX isn't pressed.")
    key = self.gpio[self.vx] & 0xf
    if self.key_inputs[key] == 0:
      self.pc += 2
        
  def _FZZZ(self):
    extracted_op = self.opcode & 0xf0ff
    try:
      self.funcmap[extracted_op]()
    except:
      print "Unknown instruction: %X" % self.opcode
    
  def _FZ07(self):
    log("Sets VX to the value of the delay timer.")
    self.gpio[self.vx] = self.delay_timer
    
  def _FZ0A(self):
    log("A key press is awaited, and then stored in VX.")
    ret = self.get_key()
    if ret >= 0:
      self.gpio[self.vx] = ret
    else:
      self.pc -= 2
      
  def _FZ15(self):
    log("Sets the delay timer to VX.")
    self.delay_timer = self.gpio[self.vx]
    
  def _FZ18(self):
    log("Sets the sound timer to VX.")
    self.sound_timer = self.gpio[self.vx]
    
  def _FZ1E(self):
    log("Adds VX to I. if overflow, vf = 1")
    self.index += self.gpio[self.vx]
    if self.index > 0xfff:
      self.gpio[0xf] = 1
      self.index &= 0xfff
    else:
      self.gpio[0xf] = 0
      
  def _FZ29(self):
    log("Set index to point to a character")
    # Sets I to the location of the sprite for the character in VX.
    # Characters 0-F (in hexadecimal) are represented by a 4x5 font.
    self.index = (5*(self.gpio[self.vx])) & 0xfff
    
  def _FZ33(self):
    log("Store a number as BCD")
    # Stores the Binary-coded decimal representation of VX, with the
    # most significant of three digits at the address in I, the middle
    # digit at I plus 1, and the least significant digit at I plus 2.
    self.memory[self.index]   = self.gpio[self.vx] / 100
    self.memory[self.index+1] = (self.gpio[self.vx] % 100) / 10
    self.memory[self.index+2] = self.gpio[self.vx] % 10
    
  def _FZ55(self):
    log("Stores V0 to VX in memory starting at address I.")
    i = 0
    while i <= self.vx:
      self.memory[self.index + i] = self.gpio[i]
      i += 1
    self.index += (self.vx) + 1
    
  def _FZ65(self):
    log("Fills V0 to VX with values from memory starting at address I.")
    i = 0
    while i <= self.vx:
      self.gpio[i] = self.memory[self.index + i]
      i += 1
    self.index += (self.vx) + 1
  # end instructions
  
  def __init__(self, *args, **kwargs):
    super(cpu, self).__init__(*args, **kwargs)
    self.funcmap = {0x0000: self._0ZZZ,
                    0x00e0: self._0ZZ0,
                    0x00ee: self._0ZZE,
                    0x1000: self._1ZZZ,
                    0x2000: self._2ZZZ,
                    0x3000: self._3ZZZ,
                    0x4000: self._4ZZZ,
                    0x5000: self._5ZZZ,
                    0x6000: self._6ZZZ,
                    0x7000: self._7ZZZ,
                    0x8000: self._8ZZZ,
                    0x8FF0: self._8ZZ0,
                    0x8FF1: self._8ZZ1,
                    0x8FF2: self._8ZZ2,
                    0x8FF3: self._8ZZ3,
                    0x8FF4: self._8ZZ4,
                    0x8FF5: self._8ZZ5,
                    0x8FF6: self._8ZZ6,
                    0x8FF7: self._8ZZ7,
                    0x8FFE: self._8ZZE,
                    0x9000: self._9ZZZ,
                    0xA000: self._AZZZ,
                    0xB000: self._BZZZ,
                    0xC000: self._CZZZ,
                    0xD000: self._DZZZ,
                    0xE000: self._EZZZ,
                    0xE00E: self._EZZE,
                    0xE001: self._EZZ1,
                    0xF000: self._FZZZ,
                    0xF007: self._FZ07,
                    0xF00A: self._FZ0A,
                    0xF015: self._FZ15,
                    0xF018: self._FZ18,
                    0xF01E: self._FZ1E,
                    0xF029: self._FZ29,
                    0xF033: self._FZ33,
                    0xF055: self._FZ55,
                    0xF065: self._FZ65
                    }
  
  def load_rom(self, rom_path):
    log("Loading %s..." % rom_path)
    binary = open(rom_path, "rb").read()
    i = 0
    while i < len(binary):
      self.memory[i+0x200] = ord(binary[i])
      i += 1
  
  def initialize(self):
    self.clear()
    self.memory = [0]*4096 # max 4096
    self.gpio = [0]*16 # max 16
    self.display_buffer = [0]*64*32 # 64*32
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
    # 1. get op (op code plus operand)
    self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
    log("Current opcode: %X" % self.opcode)
    self.pc += 2
    self.vx = (self.opcode & 0x0f00) >> 8
    self.vy = (self.opcode & 0x00f0) >> 4

    # 2. check ops, lookup and execute
    extracted_op = self.opcode & 0xf000
    try:
      self.funcmap[extracted_op]()
    except:
      print "Unknown instruction: %X" % self.opcode
    
    if self.delay_timer > 0:
      self.delay_timer -= 1
    if self.sound_timer > 0:
      self.sound_timer -= 1
      if self.sound_timer == 0:
        self.buzz.play()

  def draw(self):
    if self.should_draw:
      # draw
      self.clear()
      line_counter = 0
      i = 0
      while i < 2048:
        if self.display_buffer[i] == 1:
          # draw a square pixel
          self.pixel.blit((i%64)*10, 310 - ((i/64)*10))
        i += 1
      self.flip()
      self.should_draw = False

  def get_key(self):
    i = 0
    while i < 16:
      if self.key_inputs[i] == 1:
        return i
      i += 1
    return -1
    
  def on_key_press(self, symbol, modifiers):
    log("Key pressed: %r" % symbol)
    if symbol in KEY_MAP.keys():
      self.key_inputs[KEY_MAP[symbol]] = 1
      if self.key_wait:
        self.key_wait = False
    else:
      super(cpu, self).on_key_press(symbol, modifiers)

  def on_key_release(self, symbol, modifiers):
    log("Key released: %r" % symbol)
    if symbol in KEY_MAP.keys():
      self.key_inputs[KEY_MAP[symbol]] = 0
      
  def main(self):
    if len(sys.argv) <= 1:
      print "Usage: python chip8.py <path to chip8 rom> <log>"
      print "where: <path to chip8 rom> - path to Chip8 rom"
      print "     : <log> - if present, prints log messages to console"
      return
    self.initialize()
    self.load_rom(sys.argv[1])
    while not self.has_exit:
      self.dispatch_events()    
      self.cycle()
      self.draw()


# begin emulating!
if len(sys.argv) == 3:
  if sys.argv[2] == "log":
    LOGGING = True
      
chip8emu = cpu(640, 320)
chip8emu.main()
log("... done.")

