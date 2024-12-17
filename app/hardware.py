import os
import time
import logging
import threading
import pygame
from rpi_ws281x import PixelStrip, Color

logger = logging.getLogger(__name__)

# LED strip configuration
LED_COUNT = 8        # Number of LED pixels
LED_PIN = 18        # GPIO pin connected to the pixels
LED_FREQ_HZ = 800000  # LED signal frequency in hertz
LED_DMA = 10        # DMA channel to use for generating signal
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False   # True to invert the signal
LED_CHANNEL = 0      # Set to '1' for GPIOs 13, 19, 41, 45 or 53

class HardwareController:
    def __init__(self):
        """Initialize hardware components."""
        self.sound_thread = None
        self.light_thread = None
        self.running = False
        
        # Initialize LED strip
        try:
            self.strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                                  LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
            self.strip.begin()
            logger.info("LED strip initialized")
        except Exception as e:
            logger.error(f"Error initializing LED strip: {str(e)}")
            self.strip = None

        # Initialize audio
        try:
            pygame.mixer.init()
            logger.info("Audio system initialized")
        except Exception as e:
            logger.error(f"Error initializing audio: {str(e)}")

    def play_alarm_sound(self, sound_file):
        """Play alarm sound in a separate thread."""
        if self.sound_thread and self.sound_thread.is_alive():
            return  # Already playing

        try:
            # Construct full path to sound file
            sound_path = os.path.join('sounds', sound_file)
            if not os.path.exists(sound_path):
                logger.error(f"Sound file not found: {sound_path}")
                return

            self.sound_thread = threading.Thread(
                target=self._play_sound_loop,
                args=(sound_path,)
            )
            self.sound_thread.start()
            
        except Exception as e:
            logger.error(f"Error playing alarm sound: {str(e)}")

    def _play_sound_loop(self, sound_path):
        """Internal method to play sound in a loop."""
        try:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
        except Exception as e:
            logger.error(f"Error in sound loop: {str(e)}")

    def stop_alarm_sound(self):
        """Stop playing alarm sound."""
        try:
            pygame.mixer.music.stop()
            if self.sound_thread:
                self.sound_thread.join()
        except Exception as e:
            logger.error(f"Error stopping alarm sound: {str(e)}")

    def start_light_sequence(self, pattern='default'):
        """Start LED light sequence in a separate thread."""
        if not self.strip:
            logger.error("LED strip not initialized")
            return

        if self.light_thread and self.light_thread.is_alive():
            return  # Already running

        self.running = True
        self.light_thread = threading.Thread(
            target=self._run_light_pattern,
            args=(pattern,)
        )
        self.light_thread.start()

    def _run_light_pattern(self, pattern):
        """Internal method to run LED patterns."""
        try:
            while self.running:
                if pattern == 'default':
                    self._pattern_rainbow_cycle()
                elif pattern == 'pulse':
                    self._pattern_pulse()
                elif pattern == 'chase':
                    self._pattern_color_chase()
                else:
                    self._pattern_solid_color()
        except Exception as e:
            logger.error(f"Error in light pattern: {str(e)}")
        finally:
            self._clear_lights()

    def _pattern_rainbow_cycle(self):
        """Rainbow cycle pattern."""
        for j in range(256):
            for i in range(self.strip.numPixels()):
                if not self.running:
                    return
                pixel_index = (i * 256 // self.strip.numPixels()) + j
                self.strip.setPixelColor(i, self._wheel(pixel_index & 255))
            self.strip.show()
            time.sleep(0.02)

    def _pattern_pulse(self):
        """Pulsing light pattern."""
        for brightness in range(0, 255, 5) + range(255, 0, -5):
            if not self.running:
                return
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, Color(brightness, 0, 0))
            self.strip.show()
            time.sleep(0.02)

    def _pattern_color_chase(self):
        """Color chase pattern."""
        colors = [Color(255, 0, 0), Color(0, 255, 0), Color(0, 0, 255)]
        for color in colors:
            for i in range(self.strip.numPixels()):
                if not self.running:
                    return
                self.strip.setPixelColor(i, color)
                self.strip.show()
                time.sleep(0.05)

    def _pattern_solid_color(self, color=Color(255, 0, 0)):
        """Solid color pattern."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
        self.strip.show()
        time.sleep(0.5)

    def _wheel(self, pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    def _clear_lights(self):
        """Turn off all LEDs."""
        if self.strip:
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, Color(0, 0, 0))
            self.strip.show()

    def stop_light_sequence(self):
        """Stop LED light sequence."""
        self.running = False
        if self.light_thread:
            self.light_thread.join()
        self._clear_lights()

    def cleanup(self):
        """Clean up hardware resources."""
        self.stop_alarm_sound()
        self.stop_light_sequence()
        pygame.mixer.quit()
        logger.info("Hardware resources cleaned up") 