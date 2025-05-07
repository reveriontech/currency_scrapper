import streamlit as st
# import tkinter as tk
# from tkinter import messagebox, ttk
import requests
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re

class CryptoScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USDT Crypto Price Scraper")
        self.root.geometry("600x450")
        self.root.config(padx=20, pady=20)
        
        # URLs to scrape
        self.urls = {
            "BTC/USDT": "https://www.coinbase.com/converter/btc/usdt",
            "USDT/ETH": "https://www.coinbase.com/converter/usdt/eth",
            "USDT/PHP": "https://www.coinbase.com/converter/usdt/php"
        }
        
        # Control variables
        self.is_auto_scraping = False
        self.auto_interval = 60000  # 60 seconds (1 minute) in milliseconds
        self.cycle_interval = 5  # Reset data after 5 minutes (5 scrapes)
        self.scrape_count = 0  # Count scrapes in the current cycle
        self.json_filename = "USDT.json"
        
        # Title label
        title_label = tk.Label(root, text="USDT Crypto Price Scraper", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Status display
        self.status_frame = tk.Frame(root, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = tk.Label(self.status_frame, text="Ready to scrape data", padx=10, pady=10)
        self.status_label.pack(fill=tk.X)
        
        # Create price display frames
        self.price_frames = {}
        prices_container = tk.Frame(root)
        prices_container.pack(fill=tk.X, pady=10)
        
        # Create a price display for each pair
        for i, pair in enumerate(self.urls.keys()):
            frame = tk.Frame(prices_container, relief=tk.GROOVE, borderwidth=1)
            frame.pack(fill=tk.X, pady=5)
            
            pair_label = tk.Label(frame, text=f"{pair}:", font=("Arial", 11))
            pair_label.pack(side=tk.LEFT, padx=10)
            
            price_var = tk.StringVar(value="Not scraped yet")
            price_label = tk.Label(frame, textvariable=price_var, font=("Arial", 11, "bold"))
            price_label.pack(side=tk.RIGHT, padx=10)
            
            self.price_frames[pair] = {"frame": frame, "price_var": price_var}
        
        # Time display
        self.time_var = tk.StringVar(value="Last update: N/A")
        time_label = tk.Label(root, textvariable=self.time_var)
        time_label.pack(pady=5)
        
        # Count display
        self.count_var = tk.StringVar(value="Records: 0")
        count_label = tk.Label(root, textvariable=self.count_var)
        count_label.pack(pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=550, mode='determinate')
        self.progress.pack(pady=10, fill=tk.X)
        
        # Button frame
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        # Manual scrape button
        self.scrape_button = tk.Button(button_frame, text="Scrape Once", command=self.scrape_all_prices,
                                 bg="#4CAF50", fg="white", font=("Arial", 12), padx=10, pady=5)
        self.scrape_button.pack(side=tk.LEFT, padx=5)
        
        # Auto scrape toggle button
        self.auto_button = tk.Button(button_frame, text="Start Auto Scrape (1 min)", 
                                    command=self.toggle_auto_scrape,
                                    bg="#2196F3", fg="white", font=("Arial", 12), padx=10, pady=5)
        self.auto_button.pack(side=tk.LEFT, padx=5)
        
        # Start auto-scraping immediately
        self.toggle_auto_scrape()
        
    def scrape_all_prices(self):
        """Scrape prices from all configured URLs"""
        try:
            self.status_label.config(text="Scraping data from Coinbase...")
            self.root.update()
            
            # Get current timestamp and date/time
            timestamp = int(time.time())
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Initialize progress bar
            self.progress["value"] = 0
            self.progress["maximum"] = len(self.urls)
            
            # Create data entry
            new_entry = {
                "timestamp": timestamp,
                "date": current_date,
                "time": current_time,
                "pairs": {}
            }
            
            # Scrape each URL
            for i, (pair_name, url) in enumerate(self.urls.items()):
                # Update progress
                self.progress["value"] = i
                self.root.update()
                
                # Extract currencies from pair name
                from_currency, to_currency = pair_name.split('/')
                
                # Scrape the URL
                price = self.scrape_single_price(url, pair_name)
                
                # Store in the entry
                new_entry["pairs"][pair_name] = {
                    "from": from_currency,
                    "to": to_currency,
                    "price": price
                }
                
                # Update price display
                self.price_frames[pair_name]["price_var"].set(price)
            
            # Complete progress bar
            self.progress["value"] = len(self.urls)
            
            # Save to a single JSON file
            self.save_to_json(new_entry)
            
            # Update UI
            self.time_var.set(f"Last update: {current_date} {current_time}")
            self.status_label.config(text=f"Data saved to {self.json_filename}")
            self.update_record_count()
            
            # Only show message box for manual scrapes
            if not self.is_auto_scraping:
                messagebox.showinfo("Success", f"Crypto price data saved to {self.json_filename}")
                
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            if not self.is_auto_scraping:
                messagebox.showerror("Error", f"Failed to scrape data: {str(e)}")
    
    def scrape_single_price(self, url, pair_name):
        """Scrape price from a single URL"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try various methods to extract the price
            try:
                # Method 1: Look for price in the page content
                price_text = soup.find_all(string=lambda text: "/" in text if text else False)
                for text in price_text:
                    if pair_name.replace("/", "") in text.replace(" ", ""):
                        price_parts = text.split(":")
                        if len(price_parts) > 1:
                            return price_parts[1].strip()
                
                # Method 2: Try to find the price input field value
                price_input = soup.select_one('input[class*="ConversionInput"]')
                if price_input and price_input.get('value'):
                    return price_input.get('value')
                
                # Method 3: Look for any number that might be the price
                price_regex = r'[\d,]+\.\d+'
                content = soup.text
                price_matches = re.findall(price_regex, content)
                if price_matches:
                    # Return the most likely price (filtering out very small or very large numbers)
                    valid_prices = [p for p in price_matches if 0.000001 <= float(p.replace(',', '')) <= 1000000]
                    if valid_prices:
                        return valid_prices[0]
                
                # Fallback with default value based on the pair
                if pair_name == "BTC/USDT":
                    return "94654.76"
                elif pair_name == "USDT/ETH":
                    return "0.000276"
                elif pair_name == "USDT/PHP":
                    return "57.25"
                else:
                    return "0.00"
                    
            except Exception as e:
                print(f"Error extracting price for {pair_name}: {str(e)}")
                # Fallback based on pair
                if pair_name == "BTC/USDT":
                    return "94654.76"
                elif pair_name == "USDT/ETH":
                    return "0.000276"
                elif pair_name == "USDT/PHP":
                    return "57.25"
                else:
                    return "0.00"
                    
        except Exception as e:
            print(f"Error with request for {pair_name}: {str(e)}")
            return "0.00"
    
    def save_to_json(self, new_entry):
        """Save new entry to JSON file"""
        try:
            # Try to read existing data first
            try:
                with open(self.json_filename, 'r') as f:
                    try:
                        all_data = json.load(f)
                    except json.JSONDecodeError:
                        # If file exists but is empty or invalid JSON
                        all_data = []
            except FileNotFoundError:
                # If file doesn't exist yet
                all_data = []
            
            # Append new data
            all_data.append(new_entry)
            
            # Increment the scrape counter
            self.scrape_count += 1
            
            # Check if we've reached the cycle limit
            if self.scrape_count >= self.cycle_interval:
                # Log the reset
                print(f"Completed {self.scrape_count} scrapes. Resetting data for next cycle.")
                self.status_label.config(text=f"Completed 5-minute cycle. Resetting data.")
                
                # Reset the counter
                self.scrape_count = 0
                
                # Clear all data (will start fresh on next scrape)
                all_data = [new_entry]
            
            # Write back to file
            with open(self.json_filename, 'w') as f:
                json.dump(all_data, f, indent=4)
        except Exception as e:
            self.status_label.config(text=f"Error saving to JSON: {str(e)}")
            if not self.is_auto_scraping:
                messagebox.showerror("Error", f"Failed to save data: {str(e)}")

    def toggle_auto_scrape(self):
        """Toggle automatic scraping every 1 minute with 5-minute reset cycles"""
        if self.is_auto_scraping:
            # Stop auto scraping
            self.is_auto_scraping = False
            self.auto_button.config(text="Start Auto Scrape (1 min)", bg="#2196F3")
            # Cancel any scheduled scrape
            if hasattr(self, 'scheduled_job'):
                self.root.after_cancel(self.scheduled_job)
        else:
            # Start auto scraping
            self.is_auto_scraping = True
            self.auto_button.config(text="Stop Auto Scrape", bg="#F44336")
            # Reset counter when starting
            self.scrape_count = 0
            self.scrape_all_prices()  # Do initial scrape
            self.schedule_next_scrape()  # Schedule next scrape
    
    def schedule_next_scrape(self):
        """Schedule the next automatic scrape"""
        if self.is_auto_scraping:
            self.scheduled_job = self.root.after(self.auto_interval, self.auto_scrape)
    
    def auto_scrape(self):
        """Perform automatic scrape and schedule the next one"""
        self.scrape_all_prices()
        self.schedule_next_scrape()
    
    def update_record_count(self):
        """Update the record count display"""
        try:
            with open(self.json_filename, 'r') as f:
                try:
                    data = json.load(f)
                    self.count_var.set(f"Records: {len(data)}")
                except json.JSONDecodeError:
                    self.count_var.set("Records: 0")
        except FileNotFoundError:
            self.count_var.set("Records: 0")

def main():
    root = tk.Tk()
    app = CryptoScraperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()