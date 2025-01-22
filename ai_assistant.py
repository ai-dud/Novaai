from gtts import gTTS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import requests
import json
import os
import subprocess
import psutil
import pyautogui
from datetime import datetime
from ollama_client import OllamaClient
import pygame
import sys
import platform
import shutil
import keyboard
import winsound
import logging
import speech_recognition as sr
import webbrowser

# Set up logging for debugging purposes
logging.basicConfig(level=logging.INFO)  # Changed from DEBUG to INFO
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('gtts').setLevel(logging.WARNING)

class AIAssistant:
    def __init__(self):
        pygame.mixer.init()
        self.max_retries = 3
        self.retry_delay = 1
        self.ollama = OllamaClient(base_url="http://localhost:11434")
        self.last_youtube_search = None
        self.running = False
        self.system = platform.system().lower()
        
        # Set console to use UTF-8 for Windows
        if self.system == 'windows':
            import subprocess
            subprocess.run(['chcp', '65001'], shell=True)
        
        # Website dictionary
        self.websites = {
            "Google": "https://www.google.com",
            "YouTube": "https://www.youtube.com",
            "Facebook": "https://www.facebook.com",
            "Twitter": "https://www.twitter.com",
            "Instagram": "https://www.instagram.com",
            "Amazon": "https://www.amazon.com",
            "Netflix": "https://www.netflix.com",
            "Gmail": "https://www.gmail.com",
            "Google Maps": "https://www.google.com/maps",
            "Wikipedia": "https://www.wikipedia.org",
            "GitHub": "https://www.github.com",
            "Netlify": "https://app.netlify.com"
        }
        
    def speak(self, text):
        """Speak the given text using Google TTS in Hindi"""
        try:
            self.play_notification_sound()  # Play sound before speaking
            print(f"Assistant: {text}", flush=True)
        except UnicodeEncodeError:
            print("Assistant: [Hindi Text]", flush=True)
        
        tts = gTTS(text=text, lang='hi')  # Changed language to Hindi
        temp_file = "response.mp3"
        tts.save(temp_file)
        try:
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            # Increased wait time for longer responses
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(5)  # Reduced tick rate for smoother playback
            time.sleep(0.5)  # Added small delay after speech
            pygame.mixer.music.unload()
            os.remove(temp_file)  # Clean up the file after playing
        except Exception as e:
            print(f"Error playing sound: {e}")
        
    def play_notification_sound(self):
        """Play a notification sound to indicate command recognition"""
        try:
            frequency = 1000  # Set frequency to 1000 Hz
            duration = 100    # Set duration to 100 milliseconds
            winsound.Beep(frequency, duration)
        except Exception as e:
            print(f"Error playing notification sound: {str(e)}")

    def listen(self):
        """Listen for speech input and convert to text using Google Speech Recognition"""
        try:
            recognizer = sr.Recognizer()
            recognizer.dynamic_energy_threshold = False
            recognizer.energy_threshold = 500
            recognizer.dynamic_energy_adjustment_damping = 0.8
            recognizer.dynamic_energy_ratio = 0.9
            recognizer.pause_threshold = 0.5
            recognizer.operation_timeout = None
            recognizer.non_speaking_duration = 0.5

            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
                print("\033[93mListening...\033[0m", flush=True)
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio, language="en-IN")
                print("\033[92mSir: \033[0m", text)
                return text
                
        except sr.UnknownValueError:
            print("\033[91mCould not understand the audio\033[0m")  # If speech is unintelligible
            return ""
        except sr.RequestError as e:
            print(f"\033[91mError with Google Speech API: {e}\033[0m")  # If API request fails
            return ""
        except Exception as e:
            print(f"\033[91mAn unexpected error occurred: {e}\033[0m")  # General error handling
            return ""
            
    # Web Browser Functions
    def open_website(self, website_name):
        """Open a website in the default browser"""
        try:
            import webbrowser
            
            # Handle case-insensitive matching for known websites
            website_key = next((key for key in self.websites.keys() if key.lower() == website_name.lower()), None)
            
            if website_key:
                url = self.websites[website_key]
                webbrowser.open_new_tab(url)
                return True
            else:
                # If not in our dictionary, construct the URL
                website_name = website_name.lower().replace(" ", "").replace(".com", "")
                url = f"https://www.{website_name}.com"
                webbrowser.open_new_tab(url)
                return True
                
        except Exception as e:
            print(f"Error opening website: {str(e)}")
            self.speak(f"माफ़ कीजिये, {website_name} नहीं खोल पाया")
            return False

    def open_multiple_websites(self, sites):
        """Open multiple websites in new tabs"""
        try:
            import webbrowser
            
            # Ensure sites is a list and not empty
            if not sites or not isinstance(sites, list):
                raise ValueError("No websites provided or invalid input")
                
            # Process each site name
            processed_sites = []
            for site in sites:
                site_name = site.lower().replace(".com", "").strip()
                if site_name in self.websites:
                    processed_sites.append(self.websites[site_name])
                else:
                    processed_sites.append(f'https://www.{site_name}.com')
            
            # Open first site
            try:
                webbrowser.open(processed_sites[0])
                time.sleep(1.5)  # Increased delay for first site
            except Exception as e:
                print(f"Error opening first site {processed_sites[0]}: {str(e)}")
                return
            
            # Open rest in new tabs
            for url in processed_sites[1:]:
                try:
                    webbrowser.open_new_tab(url)
                    time.sleep(1)  # Consistent delay between tabs
                except Exception as e:
                    print(f"Error opening site {url}: {str(e)}")
                    continue
            
            # Format names for speech
            if len(sites) == 1:
                self.speak(f"Opening {sites[0]}")
            elif len(sites) == 2:
                self.speak(f"Opening {sites[0]} और {sites[1]}")
            else:
                sites_text = ", ".join(sites[:-1]) + " और " + sites[-1]
                self.speak(f"Opening {sites_text}")
                
        except Exception as e:
            print(f"Error opening websites: {str(e)}")
            self.speak("Sorry, I had trouble opening some websites")

    def click_element(self, element, retries=0):
        """Try multiple methods to click an element"""
        try:
            # Scroll element into view
            self.browser.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)  # Wait for scroll to complete
            
            # Method 1: Regular click with JavaScript focus
            try:
                self.browser.execute_script("arguments[0].focus();", element)
                element.click()
                return True
            except:
                pass

            # Method 2: JavaScript click
            try:
                self.browser.execute_script("arguments[0].click();", element)
                return True
            except:
                pass

            # Method 3: Action chains with moves and clicks
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.browser)
                actions.move_to_element(element)
                actions.click()
                actions.perform()
                return True
            except:
                pass

            # Method 4: Send Enter key
            try:
                element.send_keys(Keys.RETURN)
                return True
            except:
                pass

            if retries < self.max_retries:
                time.sleep(self.retry_delay)
                return self.click_element(element, retries + 1)
            return False
        except Exception as e:
            print(f"Click error: {str(e)}")
            return False

    def wait_and_find_element(self, by, value, timeout=10):
        """Wait for element to be present and return it"""
        try:
            wait = WebDriverWait(self.browser, timeout)
            # First try to find clickable element
            try:
                return wait.until(EC.element_to_be_clickable((by, value)))
            except:
                # If not clickable, try to find visible element
                try:
                    return wait.until(EC.visibility_of_element_located((by, value)))
                except:
                    # If not visible, try to find any element
                    return wait.until(EC.presence_of_element_located((by, value)))
        except:
            return None

    def find_and_click_video(self, search_term):
        """Find and click video with multiple methods"""
        try:
            # List of possible selectors for videos
            selectors = [
                "ytd-video-renderer #video-title",
                "ytd-video-renderer .ytd-video-renderer",
                "#contents ytd-video-renderer",
                "a#video-title",
                "a.ytd-video-renderer",
                "ytd-video-renderer a"
            ]
            
            # Try each selector
            for selector in selectors:
                try:
                    # Wait for element
                    element = self.wait_and_find_element(By.CSS_SELECTOR, selector)
                    if element and self.click_element(element):
                        self.speak("Playing video")
                        return True
                except:
                    continue
            
            # If no selector worked, try finding by link text
            try:
                links = self.browser.find_elements(By.TAG_NAME, "a")
                for link in links:
                    if search_term.lower() in link.text.lower():
                        if self.click_element(link):
                            self.speak("Playing video")
                            return True
            except:
                pass
                
            return False
        except Exception as e:
            print(f"Video click error: {str(e)}")
            return False

    def search_google(self, query):
        """Search on Google"""
        try:
            if self.browser is None:
                self.start_browser()
            
            # Navigate to Google and perform search
            self.browser.get("https://www.google.com")
            time.sleep(1)  # Wait for page to load
            
            # Find and interact with search box
            search_box = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            
            self.speak(f"Searching for {query}")
            
        except Exception as e:
            print(f"Error searching Google: {str(e)}")
            # Fallback to opening in default Chrome
            try:
                search_url = f"https://www.google.com/search?q={query}"
                subprocess.Popen(['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', search_url])
                self.speak(f"Searching for {query}")
            except Exception as e:
                print(f"Final fallback failed: {str(e)}")
                self.speak("Sorry, I couldn't perform the search")

    # System Control Functions
    def open_application(self, app_name):
        """Open Windows applications"""
        app_paths = {
            # Basic Windows Apps
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "wordpad": "wordpad.exe",
            "snipping tool": "SnippingTool.exe",
            "file explorer": "explorer.exe",
            
            # System Tools
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "task manager": "taskmgr.exe",
            "control panel": "control.exe",
            "device manager": "devmgmt.msc",
            "disk cleanup": "cleanmgr.exe",
            "system settings": "ms-settings:",
            
            # Microsoft Office
            "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "powerpoint": "POWERPNT.EXE",
            "outlook": "OUTLOOK.EXE",
            "access": "MSACCESS.EXE",
            "teams": "C:\\Users\\Scorp\\AppData\\Local\\Microsoft\\Teams\\current\\Teams.exe",
            
            # Browsers
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "firefox": "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "edge": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "brave": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            
            # Gaming
            "tlauncher": "C:\\Users\\Scorp\\AppData\\Roaming\\.minecraft\\TLauncher.exe",
            "minecraft": "C:\\Users\\Scorp\\AppData\\Roaming\\.minecraft\\TLauncher.exe",
            "steam": "C:\\Program Files (x86)\\Steam\\Steam.exe",
            "epic games": "C:\\Program Files (x86)\\Epic Games\\Launcher\\Portal\\Binaries\\Win32\\EpicGamesLauncher.exe",
            
            # Media
            "vlc": "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            "windows media player": "wmplayer.exe",
            "spotify": "C:\\Users\\Scorp\\AppData\\Roaming\\Spotify\\Spotify.exe",
            "obs": "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
            
            # Development
            "visual studio code": "C:\\Users\\Scorp\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
            "vscode": "C:\\Users\\Scorp\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
            "github desktop": "C:\\Users\\Scorp\\AppData\\Local\\GitHubDesktop\\GitHubDesktop.exe",
            "python": "python.exe",
            "jupyter": "jupyter-notebook.exe",
            
            # Communication
            "discord": "C:\\Users\\Scorp\\AppData\\Local\\Discord\\Update.exe --processStart Discord.exe",
            "whatsapp": "C:\\Users\\Scorp\\AppData\\Local\\WhatsApp\\WhatsApp.exe",
            "telegram": "C:\\Users\\Scorp\\AppData\\Roaming\\Telegram Desktop\\Telegram.exe",
            "zoom": "C:\\Users\\Scorp\\AppData\\Roaming\\Zoom\\bin\\Zoom.exe",
            
            # Utilities
            "winrar": "C:\\Program Files\\WinRAR\\WinRAR.exe",
            "7zip": "C:\\Program Files\\7-Zip\\7zFM.exe",
            "ccleaner": "C:\\Program Files\\CCleaner\\CCleaner64.exe",
            "anydesk": "C:\\Program Files (x86)\\AnyDesk\\AnyDesk.exe",
            "teamviewer": "C:\\Program Files\\TeamViewer\\TeamViewer.exe"
        }

        try:
            app_name = app_name.lower()
            
            # Try to find the app in our dictionary
            app_path = None
            for key, path in app_paths.items():
                if key in app_name:
                    app_path = path
                    break
            
            if app_path:
                try:
                    subprocess.Popen(app_path)
                    self.speak(f"{app_name} खोल रहा हूं")
                    return True
                except FileNotFoundError:
                    self.speak(f"माफ़ कीजिये, {app_name} नहीं मिला")
                    return False
            else:
                # If app not in our list, try to open directly
                try:
                    subprocess.Popen(app_name)
                    self.speak(f"{app_name} खोल रहा हूं")
                    return True
                except:
                    self.speak(f"माफ़ कीजिये, {app_name} नहीं खोल पाया")
                    return False
                        
        except Exception as e:
            print(f"Error handling application: {str(e)}")
            self.speak(f"माफ़ कीजिये, {app_name} को खोलने में समस्या आई")
            return False

    def get_system_info(self):
        """Get system information"""
        try:
            # Get CPU usage
            cpu = psutil.cpu_percent(interval=1)
            
            # Get memory info
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = round(memory.used / (1024 * 1024 * 1024), 2)  # Convert to GB
            memory_total = round(memory.total / (1024 * 1024 * 1024), 2)  # Convert to GB
            
            # Get battery info
            battery = psutil.sensors_battery()
            
            # Prepare response in Hindi
            self.speak(f"सीपीयू का उपयोग {cpu} प्रतिशत है")
            self.speak(f"मेमोरी का उपयोग {memory_percent} प्रतिशत है, कुल {memory_total} जीबी में से {memory_used} जीबी इस्तेमाल हो रहा है")
            
            if battery:
                if battery.power_plugged:
                    status = "चार्जिंग पर है"
                else:
                    status = "बैटरी पर चल रहा है"
                self.speak(f"बैटरी {battery.percent} प्रतिशत है और सिस्टम {status}")
            
            return True
        except Exception as e:
            print(f"Error getting system info: {str(e)}")
            self.speak("सिस्टम की जानकारी प्राप्त करने में समस्या आई है")
            return False

    def system_control(self, command):
        """Control system functions"""
        if "volume" in command or "वॉल्यूम" in command or "आवाज" in command or "mute" in command or "म्यूट" in command or "चुप" in command or "unmute" in command or "अनम्यूट" in command or "आवाज चालू" in command:
            try:
                import keyboard
                if "up" in command or "increase" in command or "बढ़ाओ" in command:
                    for _ in range(5):
                        keyboard.press_and_release('volume up')
                        time.sleep(0.1)
                    self.speak("वॉल्यूम बढ़ा दिया है")
                elif "down" in command or "decrease" in command or "कम" in command:
                    for _ in range(5):
                        keyboard.press_and_release('volume down')
                        time.sleep(0.1)
                    self.speak("वॉल्यूम कम कर दिया है")
                elif "unmute" in command or "अनम्यूट" in command or "आवाज चालू" in command:
                    keyboard.press_and_release('volume mute')
                    self.speak("वॉल्यूम अनम्यूट कर दिया है")
                elif "mute" in command or "silent" in command or "चुप" in command:
                    keyboard.press_and_release('volume mute')
                    self.speak("वॉल्यूम म्यूट कर दिया है")
                return True
            except Exception as e:
                # Try alternate method using pyautogui if keyboard module fails
                try:
                    if "up" in command or "increase" in command or "बढ़ाओ" in command:
                        for _ in range(5):
                            pyautogui.press('volumeup')
                            time.sleep(0.1)
                        self.speak("वॉल्यूम बढ़ा दिया है")
                    elif "down" in command or "decrease" in command or "कम" in command:
                        for _ in range(5):
                            pyautogui.press('volumedown')
                            time.sleep(0.1)
                        self.speak("वॉल्यूम कम कर दिया है")
                    elif "unmute" in command or "अनम्यूट" in command or "आवाज चालू" in command:
                        pyautogui.press('volumemute')
                        self.speak("वॉल्यूम अनम्यूट कर दिया है")
                    elif "mute" in command or "silent" in command or "चुप" in command:
                        pyautogui.press('volumemute')
                        self.speak("वॉल्यूम म्यूट कर दिया है")
                    return True
                except Exception as inner_e:
                    print(f"Error controlling volume: {str(e)}\nSecond attempt error: {str(inner_e)}")
                    self.speak("वॉल्यूम कंट्रोल में समस्या आई है")
                    return False

    def get_information(self, query):
        """Get information using Ollama"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Enhanced prompt with better structure and guidelines
                prompt = f"""Question: {query}

                Instructions:
                1. Answer in clear and simple Hindi
                2. Keep the answer concise and accurate
                3. Focus on the most important information
                4. Use proper formatting and punctuation
                5. Avoid unnecessary details

                Format:
                - Start with a direct answer
                - Add necessary details
                - End with a conclusion if needed"""

                response = self.ollama.generate(prompt)
                
                if response and len(response.strip()) > 0:
                    # Format and clean the response
                    cleaned_response = self._format_response(response)
                    print("\033[94mAssistant: \033[0m" + cleaned_response)  # Print in blue color
                    self.speak(cleaned_response)
                    return
                    
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                
                self.speak("क्षमा करें, मैं आपके प्रश्न का उचित उत्तर नहीं दे पा रही हूं।")
                
            except Exception as e:
                print(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    self.speak("क्षमा करें, तकनीकी समस्या के कारण मैं आपका प्रश्न नहीं समझ पा रही हूं।")

    def _format_response(self, response):
        """Format and clean Ollama response"""
        try:
            # Remove extra whitespace and normalize line endings
            response = response.strip().replace('\r\n', '\n')
            
            # Split into lines and remove empty lines
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            # Join lines with proper spacing
            formatted_response = ' '.join(lines)
            
            # Remove any markdown formatting
            formatted_response = formatted_response.replace('*', '').replace('_', '').replace('#', '')
            
            # Remove any remaining special characters
            formatted_response = ''.join(char for char in formatted_response if char.isprintable())
            
            return formatted_response
            
        except Exception as e:
            print(f"Error formatting response: {str(e)}")
            return response  # Return original response if formatting fails

    def answer_question(self, question):
        """Use Ollama to answer questions with improved handling"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Enhanced prompt for better question answering
                prompt = f"""निम्नलिखित प्रश्न का विस्तृत उत्तर दें: {question}

                निर्देश:
                1. उत्तर स्पष्ट और सटीक होना चाहिए
                2. जटिल विषयों को सरल तरीके से समझाएं
                3. यथासंभव व्यावहारिक उदाहरण दें
                4. महत्वपूर्ण तथ्यों और आंकड़ों को शामिल करें
                5. विश्वसनीय स्रोतों पर आधारित जानकारी दें
                
                उत्तर का प्रारूप:
                - प्रश्न का सीधा उत्तर
                - आवश्यक विवरण और व्याख्या
                - प्रासंगिक उदाहरण
                - निष्कर्ष या अतिरिक्त जानकारी"""

                response = self.ollama.generate(prompt)
                
                if response and len(response.strip()) > 0:
                    cleaned_response = self._format_response(response)
                    self.speak(cleaned_response)
                    return
                    
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                
                self.speak("क्षमा करें, मैं आपके प्रश्न का उचित उत्तर नहीं दे पा रही हूं। कृपया प्रश्न को दूसरे तरीके से पूछें।")
                
            except Exception as e:
                print(f"Error in attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    self.speak("क्षमा करें, तकनीकी समस्या के कारण मैं आपका प्रश्न नहीं समझ पा रही हूं।")

    def process_command(self, command):
        """Process voice commands"""
        command = command.lower().strip()
        
        # Handle "go home" command
        if command in ["go home", "home", "go to home", "homepage", "home page"]:
            self.go_home()
            return
            
        # Handle website opening with specific "open website" command
        if command.startswith("open website"):
            # Extract website names after "open website"
            websites = command.replace("open website", "", 1).strip().split()
            if websites:
                opened_sites = []
                for website in websites:
                    # Try to match each website name with our known websites
                    for known_site in self.websites:
                        if website.lower() in known_site.lower():
                            if self.open_website(known_site):
                                opened_sites.append(known_site)
                            break
                
                if opened_sites:
                    if len(opened_sites) == 1:
                        self.speak(f"{opened_sites[0]} खोल रहा हूं")
                    else:
                        sites_text = ", ".join(opened_sites[:-1]) + " और " + opened_sites[-1]
                        self.speak(f"{sites_text} खोल रहा हूं")
                else:
                    self.speak("कोई भी वेबसाइट नहीं मिली")
            else:
                self.speak("कौन सी वेबसाइट खोलनी है?")
            return

        # Handle YouTube video playback with "play" command
        elif command.startswith("play"):
            query = command.replace("play", "", 1).strip()
            if query:
                self.play_youtube_video(query)
            else:
                self.speak("क्या प्ले करना चाहेंगे?")
            return
            
        # Handle Google search with "search" command
        elif command.startswith("search"):
            query = command.replace("search", "", 1).strip()
            if query:
                self.search_google(query)
            else:
                self.speak("क्या सर्च करना चाहेंगे?")
            return

       

        # Handle system info commands with more variations
        if any(phrase in command for phrase in [
            "system status", "system info", "system information", 
            "सिस्टम", "system", "जानकारी दो", "स्टेटस", 
            "system ki jankar", "system ki jankari"
        ]):
            self.get_system_info()
            return
            
        # Handle volume control commands with simpler variations
        if any(word in command for word in ["volume", "वॉल्यूम", "आवाज", "mute", "म्यूट", "चुप", "unmute", "अनम्यूट", "आवाज चालू"]):
            # For direct mute/unmute commands
            if command in ["mute", "म्यूट", "चुप"]:
                command = "volume mute"
            elif command in ["unmute", "अनम्यूट", "आवाज चालू"]:
                command = "volume unmute"
            self.system_control(command)
            return

        # Handle questions with Ollama
        elif any(command.startswith(keyword) for keyword in ["question", "questions", "ek sawal"]):
            # Remove the trigger word and get the actual question
            for keyword in ["question", "questions", "ek sawal"]:
                if command.startswith(keyword):
                    question = command.replace(keyword, "", 1).strip()
                    break
            
            if question:
                self.answer_question(question)
            else:
                self.speak("कृपया अपना प्रश्न बताएं")
            return

        # Handle greetings and identity questions
        elif command == "nova" or command == "नोवा":
            self.speak("जी सर, बताइये मैं आपके लिए क्या कर सकती हूं")
            return
            
        elif command == "who are you " or command == "आप कौन हैं"  or command == "h r u" or command == "how are you":
            self.speak("मेरा नाम नोवा है।")
            return
            
        elif "tum kya ho" in command or "what are you" in command:
            self.speak("मैं असिस्टेंट हूं जो की आपके काम को आसान करती हूं")
            return

        # Add system app opening command
        elif "open" in command and any(app in command for app in ["calculator", "notepad", "paint", "control panel", "task manager", 
            "file explorer", "command prompt", "powershell", "settings", "media player", "terminal", "system monitor"]):
            app_name = command.replace("open", "").strip()
            self.open_system_app(app_name)
            return

        # Handle identity and introduction questions
        identity_responses = {
            # What are you/What do you do responses
            "what are you": "I am an AI assistant designed to help you with various tasks and make your life easier.",
            "what do you do": "I am an AI assistant that helps you with various tasks like controlling your computer, playing music, searching information, and much more.",
            "तुम क्या हो": "मैं एक एआई असिस्टेंट हूं जो आपकी हर प्रकार से मदद करती हूं।",
            "आप क्या हो": "मैं एक एआई असिस्टेंट हूं जो आपकी हर प्रकार से मदद करती हूं।",
            "तुम क्या करती हो": "मैं एक एआई असिस्टेंट हूं जो आपकी हर प्रकार की मदद करती हूं, जैसे कंप्यूटर कंट्रोल, म्यूजिक प्ले करना, जानकारी खोजना, और बहुत कुछ।",
            
            # Name responses
            "what is your name": "My name is Nova.",
            "who are you": "My name is Nova, I am an AI assistant created by Raj Jaiswal.",
            "तुम्हारा नाम क्या है": "मेरा नाम नोवा है।",
            "आपका नाम क्या है": "मेरा नाम नोवा है।",
            "तुम कौन हो": "मेरा नाम नोवा है, मैं राज जायसवाल द्वारा बनाई गई एक एआई असिस्टेंट हूं।",
            
            # Developer responses
            "who created you": "I was created by Raj Jaiswal.",
            "who made you": "I was created by Raj Jaiswal.",
            "who developed you": "I was developed by Raj Jaiswal.",
            "तुम्हें किसने बनाया": "मुझे राज जायसवाल ने बनाया है।",
            "तुम्हारा डेवलपमेंट किसने किया": "मेरा डेवलपमेंट राज जायसवाल ने किया है।",
            "तुम्हें किसने डेवलप किया": "मुझे राज जायसवाल ने डेवलप किया है।"
        }
        
        # Check for identity questions
        for question, response in identity_responses.items():
            if question in command:
                self.speak(response)
                return
                
        # Check for partial matches in identity questions
        if any(word in command for word in ["who", "what", "कौन", "क्या", "किसने"]):
            if any(word in command for word in ["you", "your", "तुम", "तुम्हारा", "आप"]):
                if "name" in command or "नाम" in command:
                    self.speak("मेरा नाम नोवा है।")
                elif "creat" in command or "develop" in command or "made" in command or "बनाया" in command or "डेवलप" in command:
                    self.speak("मुझे राज जायसवाल ने बनाया है।")
                elif "do" in command or "करती" in command or "करते" in command:
                    self.speak("मैं एक एआई असिस्टेंट हूं जो आपकी हर प्रकार से मदद करती हूं।")
                else:
                    self.speak("मैं नोवा हूं, एक एआई असिस्टेंट जो आपकी मदद के लिए हमेशा तैयार रहती है।")
                return
        
        # Handle other commands
        if "exit" in command or "quit" in command or "goodbye" in command:
            if self.browser:
                self.browser.quit()
            self.speak("Goodbye")
            return False

        if "close website" in command or "close chrome" in command or "close window" in command or "close tab" in command:
            self.close_chrome_tabs()
            return True

    def close_chrome_tabs(self):
        """Close all open Chrome tabs."""
        try:
            os.system("taskkill /f /im chrome.exe")
            self.speak("All Chrome tabs have been closed.")
        except Exception as e:
            self.speak("Sorry, I couldn't close Chrome tabs.")
            logging.error(f"Error closing Chrome tabs: {str(e)}")

    def play_youtube_video(self, query):
        """Search and play a YouTube video"""
        try:
            # Close existing browser instance if any
            try:
                if self.browser:
                    self.browser.quit()
            except:
                pass
            
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            
            # Add arguments to use default profile
            options.add_argument('--user-data-dir=C:/Users/' + os.getenv('USERNAME') + '/AppData/Local/Google/Chrome/User Data')
            options.add_argument('--profile-directory=Default')
            
            # Disable automation flags
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.browser = webdriver.Chrome(options=options)

            # Navigate to YouTube
            self.browser.get("https://www.youtube.com")
            time.sleep(2)  # Wait for page to load

            # Find and interact with search box
            search_box = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.NAME, "search_query"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)  # Wait for search results

            # Try to find and click the first video
            video_found = False
            selectors = [
                "ytd-video-renderer #video-title",
                "#contents ytd-video-renderer",
                "a#video-title",
                ".ytd-video-renderer h3",
                "#dismissible"
            ]
            
            for selector in selectors:
                try:
                    # Wait for element
                    element = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        self.browser.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(1)
                        try:
                            element.click()
                            video_found = True
                            break
                        except:
                            try:
                                self.browser.execute_script("arguments[0].click();", element)
                                video_found = True
                                break
                            except:
                                continue
                except:
                    continue

            if not video_found:
                self.speak("माफ़ कीजिये, वीडियो नहीं मिला")
                try:
                    self.browser.quit()
                except:
                    pass
                self.browser = None
                return False

            # Wait for video player to load
            time.sleep(3)
            
            # Ensure video is playing
            try:
                self.browser.execute_script("if(document.getElementsByTagName('video')[0].paused) document.getElementsByTagName('video')[0].play();")
                self.speak("वीडियो प्ले हो रहा है")
                return True
            except Exception as e:
                print(f"Error ensuring video playback: {str(e)}")
                return False
        except Exception as e:
            print(f"Error playing YouTube video: {str(e)}")
            self.speak("माफ़ कीजिये, वीडियो प्ले करने में समस्या आई")
            try:
                self.browser.quit()
            except:
                pass
            self.browser = None
            return False
        
        try:
            if self.system == 'windows':
                if app_name in windows_apps:
                    subprocess.Popen(windows_apps[app_name])
                    self.speak(f"{app_name} खोल दिया गया है")
                else:
                    self.speak(f"माफ़ कीजिये, {app_name} एप्लिकेशन नहीं मिला")
        
                
        except Exception as e:
            print(f"Error opening application: {e}")
            self.speak("माफ़ कीजिये, एप्लिकेशन खोलने में कोई समस्या आई है")

    def go_home(self):
        """Navigate to default homepage"""
        try:
            webbrowser.open("https://www.google.com")
            self.speak("Opening home page")
        except Exception as e:
            print(f"Error going home: {str(e)}")
            self.speak("होम पेज पर जाने में समस्या आई")

    def run(self):
        """Main loop to run the assistant"""
        self.running = True  # Add this line
        self.speak("welcome sir. i am नोवा ")
       
        
        while self.running:  # Modify the main loop condition
            try:
                command = self.listen()
                if command:
                    if "exit" in command or "quit" in command or "goodbye" in command:
                        if self.browser:
                            self.browser.quit()
                        self.speak("Goodbye")
                        break
                    
                    self.process_command(command)
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                self.speak("Sorry, an error occurred. Please try again.")

    def stop(self):  # Add this new method
        """Stop the assistant"""
        self.running = False
        if self.browser:
            self.browser.quit()

    def open_system_app(self, app_name):
        app_name = app_name.lower()
        # Common paths for popular apps
        app_paths = {
            'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            'chrome86': r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            'whatsapp': os.path.join(os.getenv('LOCALAPPDATA'), 'WhatsApp', 'WhatsApp.exe'),
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'paint': 'mspaint.exe',
            'word': r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE',
            'excel': r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE',
            'powerpoint': r'C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE'
        }

        # Check if app exists in predefined paths
        if app_name in app_paths:
            path = app_paths[app_name]
            if os.path.exists(path):
                try:
                    subprocess.Popen(path)
                    return f"Opening {app_name}..."
                except Exception as e:
                    return f"Error opening {app_name}: {str(e)}"
            else:
                # For system apps that don't need full path
                if app_name in ['notepad', 'calculator', 'paint']:
                    try:
                        subprocess.Popen(path)
                        return f"Opening {app_name}..."
                    except Exception as e:
                        return f"Error opening {app_name}: {str(e)}"
                return f"Sorry, {app_name} is not installed on your system."
        else:
            return f"Sorry, I don't know how to open {app_name}. Please make sure it's a supported application."

if __name__ == "__main__":
    assistant = AIAssistant()
    assistant.run()