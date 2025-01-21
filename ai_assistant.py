import speech_recognition as sr
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

class AIAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        pygame.mixer.init()
        self.browser = None
        self.max_retries = 3
        self.retry_delay = 1
        self.ollama = OllamaClient(base_url="http://localhost:11434")
        self.last_youtube_search = None
        self.chrome_driver_path = None
        self.setup_chrome_driver()  # Set up ChromeDriver on init
        self.running = False  # Add this line
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
        
    def listen(self):
        """Listen to user's voice input"""
        with sr.Microphone() as source:
            print("Listening...")
            # Adjust for ambient noise and increase timeout
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            try:
                # Increased timeout and phrase_time_limit for better recognition
                audio = self.recognizer.listen(source, timeout=20, phrase_time_limit=10)
                
                command = self.recognizer.recognize_google(audio)
                print(f"You: {command}")
                return command.lower()
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                self.speak("माफ़ कीजिये, स्पीच रिकग्निशन सर्विस में कुछ समस्या है")
                return None
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except Exception as e:
                print(f"Error in speech recognition: {e}")
                return None

    # Web Browser Functions
    def open_website(self, website_name):
        """Open a website in the default browser"""
        try:
            import webbrowser
            
            # Handle case-insensitive matching for known websites
            website_key = next((key for key in self.websites.keys() if key.lower() == website_name.lower()), None)
            
            if website_key:
                url = self.websites[website_key]
            else:
                # If not in our dictionary, construct the URL
                website_name = website_name.lower().replace(" ", "").replace(".com", "")
                url = f"https://www.{website_name}.com"
            
            # Try to open with system's default browser
            webbrowser.open(url)
            self.speak(f"{website_name} खोल रहा हूं")
            
        except Exception as e:
            print(f"Error opening website: {str(e)}")
            self.speak(f"माफ़ कीजिये, {website_name} नहीं खोल पाया")
            
    def open_multiple_websites(self, sites):
        """Open multiple websites in new tabs"""
        try:
            import webbrowser
            # Open first site
            first_site = sites[0].replace(".com", "")
            if first_site in self.websites:
                webbrowser.open(self.websites[first_site])
            else:
                webbrowser.open(f'https://www.{first_site}.com')
            
            time.sleep(1)
            
            # Open rest in new tabs
            for site in sites[1:]:
                site = site.replace(".com", "")
                if site in self.websites:
                    webbrowser.open_new_tab(self.websites[site])
                else:
                    webbrowser.open_new_tab(f'https://www.{site}.com')
                time.sleep(0.5)
            
            # Format names for Hindi speech
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

    def github_search(self, query):
        """Search GitHub repositories"""
        try:
            self.browser.get(f"https://github.com/search?q={query}&type=repositories")
            self.speak(f"Searching GitHub for {query}")
            
            results = self.wait_and_find_element(By.CSS_SELECTOR, ".repo-list-item")
            if results:
                self.speak("Found repositories. You can say 'click first' to open the first result")
        except:
            self.speak("Sorry, couldn't search GitHub")

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

    def system_control(self, command):
        """Control system functions"""
        if "volume" in command:
            if "up" in command:
                pyautogui.press("volumeup", presses=5)
                self.speak("Volume increased")
            elif "down" in command:
                pyautogui.press("volumedown", presses=5)
                self.speak("Volume decreased")
            elif "mute" in command:
                pyautogui.press("volumemute")
                self.speak("Volume muted")

    def get_system_info(self):
        """Get system information"""
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        
        self.speak(f"CPU usage is {cpu}%")
        self.speak(f"Memory usage is {memory}%")
        if battery:
            self.speak(f"Battery is at {battery.percent}%")

    def get_information(self, query):
        """Get information using Ollama"""
        try:
            prompt = f"""कृपया इस प्रश्न का उत्तर हिंदी में दें: {query}
            आवश्यकताएं:
            1. संक्षिप्त लेकिन जानकारीपूर्ण उत्तर दें
            2. सरल भाषा का प्रयोग करें
            3. मुख्य बिंदुओं पर ध्यान दें
            4. अधिकतम 2-3 वाक्य
            5. प्रश्न में दी गई जानकारी को न दोहराएं"""
        
            response = self.ollama.generate(prompt)
            if response:
                self.speak(response)
            else:
                # Fallback responses for common questions
                if "what is your name" in query.lower() or "who are you" in query.lower():
                    self.speak("नमस्ते। मेरा नाम इको है। मैं एक एआई असिस्टेंट हूं। मुझे राज जायसवाल ने बनाया है।")
                
        except Exception as e:
            print(f"Error getting information: {str(e)}")
            self.speak("माफ़ कीजिये, मैं आपके प्रश्न का उत्तर नहीं दे पा रही हूं। क्या मैं कुछ और मदद कर सकती हूं?")

    def answer_question(self, question):
        """Use Ollama to answer questions"""
        try:
            # Generate response using Ollama with Hindi instruction
            prompt = f"""कृपया इस प्रश्न का उत्तर हिंदी में दें: {question}
            आवश्यकताएं:
            1. सरल और स्पष्ट भाषा का प्रयोग करें
            2. जहां संभव हो, उदाहरण दें
            3. तकनीकी शब्दों को समझाएं
            4. उत्तर को 2-3 वाक्यों में सीमित रखें"""
            
            response = self.ollama.generate(prompt)
            if response:
                self.speak(response)
            else:
                self.speak("माफ़ कीजिये, मैं इस प्रश्न का उत्तर नहीं दे पा रही हूं")
        except Exception as e:
            print(f"Error in answer_question: {str(e)}")
            self.speak("माफ़ कीजिये, कुछ तकनीकी समस्या आ गई है")

    def scroll_page(self, direction="down"):
        """Scroll the page up or down"""
        if not self.browser:
            self.speak("No browser window is open")
            return False
        
        try:
            if direction == "up":
                self.browser.execute_script("window.scrollBy(0, -500);")
                self.speak("Scrolling up")
            else:
                self.browser.execute_script("window.scrollBy(0, 500);")
                self.speak("Scrolling down")
            return True
        except Exception as e:
            print(f"Error scrolling: {str(e)}")
            return False

    def click_search_result(self, index=1):
        """Click on a search result by index"""
        if not self.browser:
            self.speak("No browser window is open")
            return False

        try:
            # Different selectors for different sites
            selectors = [
                # Google search results
                f"(//div[@class='g'])[{index}]//a",
                f"(//div[@class='yuRUbf'])[{index}]//a",
                # YouTube results
                f"(//ytd-video-renderer)[{index}]//a[@id='thumbnail']",
                # Wikipedia results
                f"(//ul[@class='mw-search-results']//a)[{index}]",
                # Generic links
                f"(//a)[{index}]"
            ]

            for selector in selectors:
                try:
                    # Wait for element and scroll into view
                    element = WebDriverWait(self.browser, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    self.browser.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)  # Wait for scroll to complete
                    
                    # Try multiple click methods
                    try:
                        element.click()
                    except:
                        self.browser.execute_script("arguments[0].click();", element)
                    
                    self.speak(f"Clicked on result {index}")
                    return True
                except:
                    continue

            self.speak("Sorry, couldn't find anything to click")
            return False
        except Exception as e:
            print(f"Error clicking: {str(e)}")
            self.speak("Sorry, I had trouble clicking on that")
            return False

    def process_command(self, command):
        """Process voice commands"""
        command = command.lower().strip()
        
        # Handle website opening with specific "open website" command
        if command.startswith("open website"):
            website_name = command.replace("open website", "", 1).strip()
            if website_name:
                for site in self.websites:
                    if site.lower() in website_name:
                        self.open_website(site)
                        return
                self.speak("वह वेबसाइट मेरी लिस्ट में नहीं है")
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
        elif command == "echo" or command == "":
            self.speak("जी सर, बताइये मैं आपके लिए क्या कर सकती हूं")
            return
            
        elif command == "who are you " or command == "आप कौन हैं" or command == "hey" or command == "h r u" or command == "how are you":
            self.speak("मैं एक असिस्टेंट हूं और मैं आपकी मदद कर सकती हूं। मुझे राज जायसवाल ने बनाया है")
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

    def open_new_tab(self):
        """Open a new tab in Chrome"""
        try:
            subprocess.Popen(['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', '--new-tab'])
            self.speak("Opening a new tab in Chrome")
        except Exception as e:
            print(f"Error opening new tab: {str(e)}")
            self.speak("Sorry, I couldn't open a new tab")

    def open_multiple_tabs(self, num_tabs):
        """Open specified number of tabs in Chrome"""
        try:
            for _ in range(num_tabs):
                subprocess.Popen(['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', '--new-tab'])
                time.sleep(0.5)  # Small delay between tabs
            self.speak(f"Opening {num_tabs} new tabs in Chrome")
        except Exception as e:
            print(f"Error opening tabs: {str(e)}")
            self.speak("Sorry, I couldn't open the tabs")

    
    def setup_chrome_driver(self):
        """Set up the Chrome driver path"""
        # Try to find chrome driver in common locations
        possible_paths = [
            "chromedriver.exe",
            "C:/Program Files/Google/Chrome/Application/chromedriver.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chromedriver.exe",
            "./chromedriver.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.chrome_driver_path = path
                break

    def play_youtube_video(self, query):
        """Search and play a YouTube video"""
        try:
            # Always create a new browser instance
            try:
                if self.browser:
                    self.browser.quit()
            except:
                pass
                
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
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
                self.speak("Sorry, I couldn't find the video")
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
                self.speak("Playing your video")
                return True
            except Exception as e:
                print(f"Error ensuring video playback: {str(e)}")
                return False
        except Exception as e:
            print(f"Error playing YouTube video: {str(e)}")
            self.speak("Sorry, I had trouble playing the video")
            try:
                self.browser.quit()
            except:
                pass
            self.browser = None
            return False

    def open_system_app(self, app_name):
        """Open system applications based on the operating system"""
        app_name = app_name.lower()
        
        # Dictionary of common apps for different operating systems
        windows_apps = {
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
            "paint": "mspaint.exe",
            "control panel": "control.exe",
            "task manager": "taskmgr.exe",
            "file explorer": "explorer.exe",
            "command prompt": "cmd.exe",
            "powershell": "powershell.exe",
            "settings": "ms-settings:",
            "media player": "wmplayer.exe"
        }
        
        linux_apps = {
            "calculator": "gnome-calculator",
            "notepad": "gedit",
            "terminal": "gnome-terminal",
            "settings": "gnome-control-center",
            "file explorer": "nautilus",
            "system monitor": "gnome-system-monitor",
            "text editor": "nano",
            "media player": "vlc"
        }
        
        raspberry_apps = {
            "calculator": "galculator",
            "notepad": "leafpad",
            "terminal": "lxterminal",
            "settings": "raspi-config",
            "file explorer": "pcmanfm",
            "text editor": "nano",
            "media player": "vlc",
            "task manager": "lxtask"
        }
        
        try:
            if self.system == 'windows':
                if app_name in windows_apps:
                    subprocess.Popen(windows_apps[app_name])
                    self.speak(f"{app_name} खोल दिया गया है")
                else:
                    self.speak(f"माफ़ कीजिये, {app_name} एप्लिकेशन नहीं मिला")
                    
            elif self.system == 'linux':
                if app_name in linux_apps:
                    subprocess.Popen([linux_apps[app_name]])
                    self.speak(f"{app_name} खोल दिया गया है")
                else:
                    self.speak(f"माफ़ कीजिये, {app_name} एप्लिकेशन नहीं मिला")
                    
            elif self.system == 'darwin':  # For Raspberry Pi
                if app_name in raspberry_apps:
                    subprocess.Popen([raspberry_apps[app_name]])
                    self.speak(f"{app_name} खोल दिया गया है")
                else:
                    self.speak(f"माफ़ कीजिये, {app_name} एप्लिकेशन नहीं मिला")
            else:
                self.speak("माफ़ कीजिये, आपका ऑपरेटिंग सिस्टम सपोर्टेड नहीं है")
                
        except Exception as e:
            print(f"Error opening application: {e}")
            self.speak("माफ़ कीजिये, एप्लिकेशन खोलने में कोई समस्या आई है")

    def run(self):
        """Main loop to run the assistant"""
        self.running = True  # Add this line
        self.speak("Hello sir ")
       
        
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

if __name__ == "__main__":
    assistant = AIAssistant()
    assistant.run()
