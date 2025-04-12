from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from datetime import datetime, timedelta
import time
import sys
import os
import platform

def wait_for_element(driver, selector, timeout=20, by=By.CSS_SELECTOR):
    """Helper function to wait for an element with better error handling"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return element
    except TimeoutException:
        return None

def wait_for_elements(driver, selector, timeout=20, by=By.CSS_SELECTOR):
    """Helper function to wait for multiple elements with better error handling"""
    try:
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, selector))
        )
        return elements
    except TimeoutException:
        return []

def scroll_to_top(driver):
    """Scroll the chat list to the top"""
    chat_list = wait_for_element(driver, 'div#pane-side')
    if chat_list:
        driver.execute_script("arguments[0].scrollTop = 0;", chat_list)
        time.sleep(1)

def get_chat_title(driver, chat_element):
    """Helper function to get chat title using multiple methods"""
    # First try to get title from the chat list item itself
    try:
        # Try to get the title directly from the chat element
        title_span = chat_element.find_element(By.CSS_SELECTOR, "span[title]")
        if title_span and title_span.get_attribute("title"):
            return title_span.get_attribute("title")
    except:
        pass

    # If not found, try getting it from the chat header after clicking
    title_selectors = [
        'div[data-testid="conversation-info-header-chat-title"]',
        'div[data-testid="chat-title"]',
        'span[data-testid="conversation-info-header-chat-title"]',
        'header span[title]',
        'header span[dir="auto"]',
        '//header//span[@title]',
        '//header//div[@title]'
    ]
    
    for selector in title_selectors:
        try:
            if selector.startswith('//'):
                element = wait_for_element(driver, selector, timeout=5, by=By.XPATH)
            else:
                element = wait_for_element(driver, selector, timeout=5)
            if element:
                # Try both text and title attribute
                title = element.text or element.get_attribute("title")
                if title:
                    return title
        except:
            continue
    
    # If still not found, try JavaScript
    try:
        title = driver.execute_script("""
            // Try multiple methods to find the chat title
            let titleElement = document.querySelector('header span[title]') || 
                             document.querySelector('header div[title]') ||
                             document.querySelector('[data-testid="conversation-info-header-chat-title"]');
            return titleElement ? (titleElement.title || titleElement.textContent) : null;
        """)
        if title:
            return title
    except:
        pass
    
    return None

def parse_whatsapp_timestamp(timestamp_text):
    """Helper function to parse WhatsApp timestamp in various formats"""
    try:
        # If it's already a datetime object, return it
        if isinstance(timestamp_text, datetime):
            return timestamp_text
            
        # Remove brackets if present
        timestamp_text = timestamp_text.strip('[]')
        
        # Try different date formats
        formats = [
            "%I:%M %p, %m/%d/%Y",    # 12:34 PM, 03/21/2024
            "%I:%M %p, %d/%m/%Y",    # 12:34 PM, 21/03/2024
            "%d/%m/%Y %I:%M %p",     # 21/03/2024 12:34 PM
            "%m/%d/%Y %I:%M %p",     # 03/21/2024 12:34 PM
            "%d/%m/%Y, %H:%M",       # 21/03/2024, 12:34
            "%Y-%m-%d %H:%M:%S",     # 2024-03-21 12:34:56
            "%I:%M %p",              # 12:34 PM (today)
            "%H:%M"                  # 12:34 (today)
        ]
        
        for date_format in formats:
            try:
                parsed_time = datetime.strptime(timestamp_text, date_format)
                
                # If format doesn't include date, use today's date
                if "%Y" not in date_format:
                    today = datetime.now()
                    parsed_time = parsed_time.replace(
                        year=today.year,
                        month=today.month,
                        day=today.day
                    )
                    
                    # If the time is in the future, it's from yesterday
                    if parsed_time > today:
                        parsed_time -= timedelta(days=1)
                
                return parsed_time
            except ValueError:
                continue
                
        return None
    except Exception as e:
        print(f"Error parsing timestamp: {str(e)}")
        return None

def get_message_content(message_elem):
    """Helper function to extract message content using multiple methods"""
    try:
        # First try the most reliable selectors for text content
        text_selectors = [
            'span.selectable-text.copyable-text',
            'span[data-testid="msg-container"] span.selectable-text',
            'div.copyable-text span.selectable-text',
            'div._21Ahp',  # Direct message container class
            'div[data-pre-plain-text] span.selectable-text',
            'div[class*="message-text"] span.selectable-text',
            'div[class*="text-message"] span.selectable-text'
        ]
        
        # Try each selector
        for selector in text_selectors:
            try:
                elements = message_elem.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Get text from all matching elements
                    texts = []
                    for elem in elements:
                        text = elem.text.strip()
                        if text:  # Accept any non-empty text
                            texts.append(text)
                    
                    if texts:
                        return ' '.join(texts)
            except:
                continue
        
        # If no text found with selectors, try direct JavaScript approach
        try:
            text = message_elem.parent.execute_script("""
                function getPlainText(element) {
                    // Get all text nodes within the element
                    const walker = document.createTreeWalker(
                        element,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let text = '';
                    let node;
                    
                    while (node = walker.nextNode()) {
                        // Skip if parent is a script or style element
                        if (!['SCRIPT', 'STYLE'].includes(node.parentElement.tagName)) {
                            text += node.textContent.trim() + ' ';
                        }
                    }
                    
                    return text.trim();
                }
                return getPlainText(arguments[0]);
            """, message_elem)
            
            if text:  # Accept any non-empty text
                return text.strip()
        except:
            pass
            
        return None
    except Exception as e:
        print(f"Error getting message content: {str(e)}")
        return None

def get_message_timestamp(message_elem):
    """Helper function to extract message timestamp using multiple methods"""
    try:
        # Try different selectors for timestamp
        timestamp_selectors = [
            'span[data-testid="msg-time"]',
            'div[data-pre-plain-text]',
            'div.copyable-text[data-pre-plain-text]',
            'div.message-info span.message-time'
        ]
        
        for selector in timestamp_selectors:
            try:
                timestamp_elem = message_elem.find_element(By.CSS_SELECTOR, selector)
                if timestamp_elem:
                    # Try data-pre-plain-text attribute first
                    timestamp_text = timestamp_elem.get_attribute("data-pre-plain-text")
                    if timestamp_text:
                        return timestamp_text
                    
                    # Try getting the time text directly
                    time_text = timestamp_elem.text
                    if time_text and ":" in time_text:
                        # Convert time to full timestamp
                        today = datetime.now()
                        try:
                            # Handle both 12-hour and 24-hour formats
                            if "PM" in time_text or "AM" in time_text:
                                time_obj = datetime.strptime(time_text.strip(), "%I:%M %p")
                            else:
                                time_obj = datetime.strptime(time_text.strip(), "%H:%M")
                            
                            # Combine with today's date
                            full_time = today.replace(
                                hour=time_obj.hour,
                                minute=time_obj.minute,
                                second=0,
                                microsecond=0
                            )
                            
                            # If the time is in the future, it's from yesterday
                            if full_time > today:
                                full_time -= timedelta(days=1)
                            
                            return full_time.strftime("%I:%M %p, %m/%d/%Y")
                        except ValueError as e:
                            print(f"Error parsing time {time_text}: {str(e)}")
                            continue
            except:
                continue
        
        # Try JavaScript fallback for timestamp
        try:
            timestamp = message_elem.get_attribute('data-timestamp')
            if timestamp:
                timestamp_dt = datetime.fromtimestamp(int(timestamp)/1000)
                return timestamp_dt.strftime("%I:%M %p, %m/%d/%Y")
        except:
            pass
                
        return None
    except Exception as e:
        print(f"Error getting timestamp: {str(e)}")
        return None

def wait_for_chat_list(driver, timeout=30):
    """Helper function to wait for chat list to load with multiple selectors"""
    chat_list_selectors = [
        'div[data-testid="chat-list"]',
        'div#pane-side',
        'div#side div[role="grid"]',
        '[data-testid="cell-frame-container"]',
        'div#pane-side div[role="gridcell"]',
        'div[data-testid="default-user"]',  # Single chat indicator
        'div[data-testid="default-group"]'  # Group chat indicator
    ]
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        for selector in chat_list_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.is_displayed():
                    # Try to find actual chat elements
                    chat_items = driver.find_elements(By.CSS_SELECTOR, 
                        f'{selector} [role="row"], {selector} [data-testid="cell-frame-container"]')
                    if chat_items:
                        return True
            except:
                continue
        time.sleep(2)
    return False

def wait_for_login_complete(driver, timeout=60):
    """Helper function to wait for login to complete after QR scan"""
    login_indicators = [
        'div[data-testid="chat-list"]',
        'div#side div[role="grid"]',
        '[data-testid="default-user"]',
        'div#pane-side',
        'div[data-testid="cell-frame-container"]'
    ]
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Check if any login indicator is present
        for selector in login_indicators:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.is_displayed():
                    return True
            except:
                pass
        time.sleep(2)
    return False

def find_messages_in_chat(driver, num_messages):
    """Helper function to find messages in the current chat"""
    try:
        # Wait longer for messages to load after clicking chat
        time.sleep(5)
        
        # First ensure we're in the message view and wait for messages to load
        message_view_selectors = [
            'div[data-testid="conversation-panel-messages"]',
            'div.message-list',
            'div[role="region"][aria-label*="Message list"]',
            'div[data-testid="msg-container"]'
        ]
        
        message_view = None
        for selector in message_view_selectors:
            try:
                message_view = wait_for_element(driver, selector, timeout=15)
                if message_view:
                    print(f"Found message view with selector: {selector}")
                    break
            except:
                continue
        
        if message_view:
            # Scroll to bottom and then back up to ensure messages are loaded
            driver.execute_script("""
                const view = arguments[0];
                // Scroll to bottom
                view.scrollTop = view.scrollHeight;
                // Wait a bit and scroll up
                setTimeout(() => {
                    view.scrollTop = 0;
                }, 500);
            """, message_view)
            time.sleep(3)  # Wait for scroll and load
        
        # Try multiple approaches to find messages
        message_selectors = [
            'div[data-testid="msg-container"]',
            'div.message-in, div.message-out',
            'div[role="row"]',
            'div.focusable-list-item',
            'div[data-pre-plain-text]',
            'div.copyable-text',
            'div[class*="message"]',
            # Add more specific selectors
            'div[data-id]',
            'div._21Ahp',
            'div[tabindex="-1"]'
        ]
        
        all_messages = []
        print("Searching for messages with multiple selectors...")
        
        for selector in message_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Found {len(elements)} potential messages with selector '{selector}'")
                    # Add unique elements to all_messages
                    for elem in elements:
                        if elem not in all_messages:
                            text = get_message_content(elem)
                            if text:
                                all_messages.append(elem)
            except Exception as e:
                print(f"Error with selector '{selector}': {str(e)}")
                continue
        
        if all_messages:
            print(f"Found total of {len(all_messages)} valid messages across all selectors")
            # Get the last N messages
            messages = all_messages[-num_messages:] if len(all_messages) > num_messages else all_messages
            return messages
        
        # If no messages found, try JavaScript approach
        print("No messages found with selectors, trying JavaScript approach...")
        try:
            messages = driver.execute_script("""
                function findValidMessages() {
                    const messages = new Set();
                    
                    // Try specific selectors first
                    const selectors = [
                        'div[data-testid="msg-container"]',
                        '.message-in, .message-out',
                        'div[data-pre-plain-text]',
                        'div.copyable-text'
                    ];
                    
                    for (const selector of selectors) {
                        document.querySelectorAll(selector).forEach(el => messages.add(el));
                    }
                    
                    // If no messages found, try finding elements with message characteristics
                    if (messages.size === 0) {
                        document.querySelectorAll('div').forEach(el => {
                            const hasText = el.querySelector('span.selectable-text, span[dir="ltr"], span[dir="auto"]');
                            const hasTime = el.querySelector('span[data-testid="msg-time"]');
                            const hasMetadata = el.getAttribute('data-pre-plain-text');
                            
                            if ((hasText && hasTime) || hasMetadata) {
                                const text = hasText ? hasText.textContent.trim() : '';
                                if (text) {
                                    messages.add(el);
                                }
                            }
                        });
                    }
                    
                    return Array.from(messages);
                }
                return findValidMessages();
            """)
            
            if messages:
                print(f"Found {len(messages)} messages using JavaScript")
                # Get the last N messages
                messages = messages[-num_messages:] if len(messages) > num_messages else messages
                return messages
        except Exception as e:
            print(f"JavaScript approach failed: {str(e)}")
        
        # One final attempt with a more aggressive approach
        print("Trying final aggressive message search...")
        try:
            messages = driver.execute_script("""
                function findAnyPossibleMessage() {
                    const messages = new Set();
                    
                    // Look for any element that might be a message
                    document.querySelectorAll('div').forEach(el => {
                        // Check for any text content
                        const hasText = el.querySelector('span') && el.textContent.trim();
                        // Check for typical message attributes
                        const hasMessageAttr = el.getAttribute('data-id') || 
                                            el.getAttribute('data-pre-plain-text') ||
                                            el.querySelector('span[data-testid="msg-time"]');
                        
                        if (hasText && hasMessageAttr) {
                            messages.add(el);
                        }
                    });
                    
                    return Array.from(messages);
                }
                return findAnyPossibleMessage();
            """)
            
            if messages:
                print(f"Found {len(messages)} messages in final attempt")
                messages = messages[-num_messages:] if len(messages) > num_messages else messages
                return messages
        except Exception as e:
            print(f"Final attempt failed: {str(e)}")
        
        print("No messages found after all attempts")
        return None
    except Exception as e:
        print(f"Error finding messages: {str(e)}")
        return None

def read_whatsapp_messages(num_messages=10):
    """
    Read the last N WhatsApp messages from web.whatsapp.com for each chat.
    
    Args:
        num_messages (int): Number of most recent messages to collect from each chat (default: 10)
    
    Returns:
        str: Concatenated string of all group and individual chat messages
    """
    driver = None
    try:
        print("Setting up Chrome WebDriver...")
        
        # Set up Chrome options
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        
        # Initialize undetected-chromedriver
        try:
            driver = uc.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
        except Exception as e:
            print(f"Error during WebDriver setup: {str(e)}")
            print("Please make sure Chrome browser is installed and up to date.")
            return "Failed to initialize Chrome WebDriver. Please check if Chrome is installed and up to date."
        
        # Navigate to WhatsApp Web
        print("Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        # Wait for initial page load
        time.sleep(5)
        
        # Check for various possible elements that indicate the page has loaded
        print("Waiting for WhatsApp Web to load...")
        
        # Update the QR code selectors and detection logic
        qr_selectors = [
            'div[data-testid="qrcode"]',
            'canvas[aria-label*="Scan me"]',
            'div[data-ref]',
            'div[class*="landing-wrapper"] canvas',
            'div._19vUU canvas',  # WhatsApp's internal class for QR container
            'div[class*="landing-window"] canvas',
            'div[class*="qr-container"] canvas'
        ]
        
        # First check if already logged in
        print("Checking if already logged in...")
        if wait_for_chat_list(driver, timeout=15):
            print("Already logged in!")
            time.sleep(2)  # Wait for chat list to fully load
        else:
            # Not logged in, look for QR code
            print("Looking for QR code...")
            qr_found = False
            qr_element = None
            
            # Try direct selectors first
            for selector in qr_selectors:
                try:
                    qr_element = wait_for_element(driver, selector, timeout=5)
                    if qr_element and qr_element.is_displayed():
                        print(f"Found QR code with selector: {selector}")
                        qr_found = True
                        break
                except:
                    continue
            
            # If not found, try JavaScript approach
            if not qr_found:
                try:
                    print("Trying JavaScript approach to find QR code...")
                    qr_element = driver.execute_script("""
                        function findQRCode() {
                            // Try various methods to find QR code
                            const selectors = [
                                'div[data-testid="qrcode"]',
                                'canvas[aria-label*="Scan me"]',
                                'div[data-ref]',
                                'div[class*="landing-wrapper"] canvas',
                                'div._19vUU canvas',
                                'div[class*="qr-container"] canvas'
                            ];
                            
                            for (const selector of selectors) {
                                const element = document.querySelector(selector);
                                if (element && element.offsetParent !== null) {
                                    return element;
                                }
                            }
                            
                            // Try finding any canvas in the landing page
                            const canvas = document.querySelector('div[class*="landing"] canvas');
                            if (canvas && canvas.offsetParent !== null) {
                                return canvas;
                            }
                            
                            return null;
                        }
                        return findQRCode();
                    """)
                    
                    if qr_element:
                        print("Found QR code using JavaScript")
                        qr_found = True
                except Exception as e:
                    print(f"JavaScript QR detection failed: {str(e)}")
            
            if qr_found:
                print("\nPlease scan the QR code displayed in the browser window...")
                
                # Wait for login to complete
                print("Waiting for QR code scan...")
                login_successful = False
                max_wait = 120  # 2 minutes
                start_wait = time.time()
                
                while time.time() - start_wait < max_wait:
                    try:
                        # Check if QR code is gone and chat list is present
                        if not driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="qrcode"], canvas[aria-label*="Scan me"]'):
                            print("QR code no longer visible, checking for successful login...")
                            if wait_for_login_complete(driver, timeout=30):
                                print("Successfully logged in!")
                                login_successful = True
                                time.sleep(5)  # Wait for everything to load
                                break
                    except:
                        # Check if we're logged in
                        if wait_for_login_complete(driver, timeout=30):
                            print("Successfully logged in!")
                            login_successful = True
                            time.sleep(5)  # Wait for everything to load
                            break
                    time.sleep(2)
                
                if not login_successful:
                    return "Login timeout. Please try again."
            else:
                # One final check for existing login
                if wait_for_login_complete(driver, timeout=10):
                    print("Already logged in!")
                else:
                    print("Could not detect QR code. Refreshing page...")
                    driver.refresh()
                    time.sleep(5)
                    
                    # Try one more time after refresh
                    for selector in qr_selectors:
                        try:
                            qr_element = wait_for_element(driver, selector, timeout=5)
                            if qr_element and qr_element.is_displayed():
                                print(f"Found QR code after refresh with selector: {selector}")
                                print("\nPlease scan the QR code displayed in the browser window...")
                                qr_found = True
                                break
                        except:
                            continue
                    
                    if not qr_found:
                        return "Could not detect QR code even after refresh. Please try again."
        
        # Final verification of login status
        print("Verifying login status...")
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            if wait_for_login_complete(driver, timeout=20):
                print("Login verified successfully!")
                time.sleep(5)  # Wait for everything to stabilize
                break
            else:
                retry_count += 1
                print(f"Retrying login verification... ({retry_count}/{max_retries})")
                if retry_count >= 3:
                    print("Refreshing page...")
                    driver.refresh()
                    time.sleep(10)
        else:
            return "Could not verify login status. Please try again."
            
        print("Successfully connected to WhatsApp Web!")
        time.sleep(5)  # Increased final wait for stability
        
        # Initialize result strings
        group_messages = []  # string1 collection
        individual_messages = []  # string2 collection
        
        # Get all chat elements
        print("Looking for chats...")
        print(f"Will collect last {num_messages} messages from each chat")
        
        # Scroll to top of chat list first
        scroll_to_top(driver)
        
        # Updated chat selectors
        chat_selectors = [
            'div[data-testid="cell-frame-container"]',
            'div#pane-side div[role="row"]',
            'div#pane-side div[role="gridcell"]',
            'div#pane-side div[data-testid="chat-list-item"]',
            '//div[@id="pane-side"]//div[@role="row"]',
            '//div[@id="pane-side"]//div[contains(@class, "focusable-list-item")]'
        ]
        
        # Try to find chats with each selector
        chats = []
        for selector in chat_selectors:
            try:
                if selector.startswith('//'):
                    elements = wait_for_elements(driver, selector, timeout=10, by=By.XPATH)
                else:
                    elements = wait_for_elements(driver, selector, timeout=10)
                
                if elements:
                    print(f"Found {len(elements)} chats with selector: {selector}")
                    chats = elements
                    break
            except Exception as e:
                print(f"Error with selector {selector}: {str(e)}")
                continue
        
        if not chats:
            # Try one more time with direct JavaScript
            try:
                chats = driver.execute_script("""
                    return Array.from(document.querySelectorAll('#pane-side [role="row"], #pane-side [role="gridcell"]'));
                """)
                print(f"Found {len(chats)} chats using JavaScript")
            except Exception as e:
                print(f"JavaScript fallback failed: {str(e)}")
        
        if not chats:
            return "No chats found. Please try again."
        
        total_chats = len(chats)
        print(f"Found {total_chats} chats to process...")
        
        processed_chats = 0
        for index, chat in enumerate(chats, 1):
            try:
                print(f"\nProcessing chat {index}/{total_chats}")
                if index == 2:
                    print("Stopping at chat 2 as requested")
                    break
                
                # First try to get the title before clicking
                chat_title = get_chat_title(driver, chat)
                
                # Scroll chat into view and click
                driver.execute_script("arguments[0].scrollIntoView(true);", chat)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", chat)
                time.sleep(3)  # Increased wait time after clicking
                
                # Find messages in this chat
                messages = find_messages_in_chat(driver, num_messages)
                
                if not messages:
                    print(f"No messages found in chat {index}")
                    continue
                
                # Process messages
                chat_messages = []
                processed_messages = 0
                
                for message in messages:
                    try:
                        # Get message text
                        message_text = get_message_content(message)
                        if not message_text:
                            print("No text content found in message")
                            continue
                        
                        # Get sender information
                        try:
                            metadata_container = message.find_element(By.CSS_SELECTOR, 'div[data-pre-plain-text]')
                            metadata = metadata_container.get_attribute('data-pre-plain-text')
                            if metadata and ']' in metadata:
                                sender = metadata.split(']')[1].strip().strip(':')
                            else:
                                sender = "Unknown"
                        except:
                            sender = "Unknown"
                        
                        # Add the message
                        chat_messages.append(f"{sender}: {message_text}")
                        processed_messages += 1
                        
                    except Exception as e:
                        print(f"Error processing message: {str(e)}")
                        continue
                
                print(f"\nChat {index} summary:")
                print(f"- Total messages found: {len(messages)}")
                print(f"- Messages successfully processed: {processed_messages}")
                print(f"- Messages after filtering (no links/attachments): {len(chat_messages)}")
                
                if chat_messages:
                    processed_chats += 1
                    # Determine if it's a group or individual chat
                    is_group = False
                    try:
                        # Check for group indicators
                        group_indicators = driver.find_elements(By.CSS_SELECTOR, 
                            'span[data-testid="group-info-drawer-subject-input"], ' + 
                            'div[data-testid="group-info-drawer"], ' +
                            'span[data-icon="groups"]'
                        )
                        is_group = len(group_indicators) > 0
                    except:
                        # If we can't determine, assume individual chat
                        pass
                    
                    # Format and add messages to appropriate list
                    formatted_messages = f"{chat_title}:\n" + "\n".join(chat_messages) + "\n\n"
                    if is_group:
                        group_messages.append(formatted_messages)
                        print(f"Added {len(chat_messages)} messages to group chat")
                    else:
                        individual_messages.append(formatted_messages)
                        print(f"Added {len(chat_messages)} messages to individual chat")
                else:
                    print(f"No valid messages found in chat {index}")
                    
            except Exception as e:
                print(f"Error processing chat {index}: {str(e)}")
                continue
        
        print("\nProcessing Summary:")
        print(f"Total chats processed: {processed_chats}")
        print(f"Group chats with messages: {len(group_messages)}")
        print(f"Individual chats with messages: {len(individual_messages)}")
        
        # Combine all messages in the required format
        final_string = "".join(group_messages) + "".join(individual_messages)
        if not final_string:
            return "No messages found in the specified time range. This could be because:\n" + \
                   "1. No messages were sent during this time period\n" + \
                   "2. The messages were filtered out (links/attachments)\n" + \
                   "3. There were issues reading the message timestamps"
        return final_string
        
    except TimeoutException as e:
        return "Timeout waiting for WhatsApp Web to load. Please check your internet connection and try again."
    
    except WebDriverException as e:
        if "Chrome failed to start" in str(e):
            return "Failed to start Chrome. Please make sure Chrome browser is installed on your system."
        return f"WebDriver error: {str(e)}"
    
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}\nPlease make sure Chrome browser is installed and up to date."
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# Example usage:
if __name__ == "__main__":
    # Get the last 10 messages from each chat
    num_messages = 10
    print(f"Getting last {num_messages} messages from each chat")
    messages = read_whatsapp_messages(num_messages)
    print(messages) 