import customtkinter as ctk
import requests
import json
import os
import csv
from datetime import datetime
import threading
from tkinter import filedialog, messagebox
import pandas as pd

# --- Theme Setup ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- Configuration Loading ---
def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default configuration if file doesn't exist
        return {
            "api": {
                "base_url": "https://your-api-url.com/api/v1",
                "auth_type": "U"
            },
            "ui": {
                "window_title": "RedCat Stamp Card Reporting",
                "default_width": 900,
                "default_height": 700
            },
            "reports": {
                "default_limit": 1000,
                "auto_export": False
            }
        }

# Load configuration
CONFIG = load_config()
BASE_URL = CONFIG["api"]["base_url"]

# --- API Helpers ---
def login(username, password):
    """Authenticate with the API and return token"""
    url = f"{BASE_URL}/login"
    payload = {"username": username, "psw": password, "auth_type": CONFIG["api"]["auth_type"]}
    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
        response_data = r.json()
        if "token" not in response_data:
            raise ValueError(f"Login response missing token. Response: {response_data}")
        return response_data["token"]
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Login request failed: {e}")
    except KeyError as e:
        raise ValueError(f"Login response missing expected field: {e}. Response: {response_data}")

def get_stampcard_summary(token, start=0, limit=1000, order_by="MemberNo", order_direction="desc"):
    """Get stampcard summary report"""
    url = f"{BASE_URL}/reports/loyalty/stampcards_summary"
    headers = {
        "X-Redcat-Authtoken": token,
        "Content-Type": "application/json"
    }
    payload = {
        "Fields": ["MemberNo", "CurrentStamps", "CardsFilled", "RewardsEarned"],
        "Order": [[order_by, order_direction]],
        "Start": start,
        "Limit": limit
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def get_stampcard_transactions(token, start=0, limit=1000, order_by="MemberSalesHeaderRecid", order_direction="desc"):
    """Get stampcard transactions report"""
    url = f"{BASE_URL}/reports/loyalty/stampcards_transactions"
    headers = {
        "X-Redcat-Authtoken": token,
        "Content-Type": "application/json"
    }
    payload = {
        "Fields": ["MemberSalesHeaderRecid", "MemberNo", "SaleStampsEarned", "RewardsEarned", "StoreName", "Amount", "TxnDate"],
        "Order": [[order_by, order_direction]],
        "Start": start,
        "Limit": limit
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def export_to_csv(data, filename, report_type):
    """Export report data to CSV file"""
    if not data:
        raise ValueError("No data to export")
    
    # Handle both response formats
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict) and 'data' in data:
        records = data['data']
    else:
        raise ValueError("Unexpected data format for export")
    
    if not records:
        raise ValueError("No records to export")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = records[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def export_to_json(data, filename, report_type):
    """Export report data to JSON file"""
    if not data:
        raise ValueError("No data to export")
    
    # Handle both response formats
    if isinstance(data, list):
        records = data
        record_count = len(data)
    elif isinstance(data, dict) and 'data' in data:
        records = data['data']
        record_count = len(data['data'])
    else:
        records = []
        record_count = 0
    
    export_data = {
        'report_type': report_type,
        'generated_at': datetime.now().isoformat(),
        'total_records': record_count,
        'data': data
    }
    
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)

# --- GUI App ---
class StampReportingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(CONFIG["ui"]["window_title"])
        self.geometry(f"{CONFIG['ui']['default_width']}x{CONFIG['ui']['default_height']}")
        self.configure(fg_color="#1E1E1E")
        self.resizable(True, True)
        self.minsize(700, 600)

        self.token = None
        self.is_processing = False
        self.current_report_data = None
        self.current_report_type = None

        # Create main scrollable container
        main_container = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E")
        main_container.pack(expand=True, padx=10, pady=10, fill="both")
        
        # Main content frame
        frame = ctk.CTkFrame(main_container, fg_color="#1E1E1E")
        frame.pack(expand=True, padx=10, pady=10, fill="both")

        # -- Configuration Info --
        config_frame = ctk.CTkFrame(frame, fg_color="#404040", corner_radius=10)
        config_frame.pack(pady=(10, 15), padx=20, fill="x")
        
        config_title = ctk.CTkLabel(config_frame, text="⚙️ Configuration", font=("Arial", 12, "bold"))
        config_title.pack(pady=(8, 5))
        
        config_info = ctk.CTkLabel(config_frame, 
            text=f"API: {BASE_URL}\nDefault Limit: {CONFIG['reports']['default_limit']} records", 
            font=("Arial", 10), justify="left", text_color="#CCCCCC")
        config_info.pack(pady=(0, 8))

        # -- Credentials Section --
        creds_frame = ctk.CTkFrame(frame, fg_color="#2B2B2B", corner_radius=10)
        creds_frame.pack(pady=10, padx=20, fill="x")
        
        creds_title = ctk.CTkLabel(creds_frame, text="🔐 Authentication", font=("Arial", 14, "bold"))
        creds_title.pack(pady=(10, 5))
        
        self.username_entry = ctk.CTkEntry(creds_frame, placeholder_text="API Username", width=300, height=35)
        self.username_entry.pack(pady=5)
        
        self.password_entry = ctk.CTkEntry(creds_frame, placeholder_text="Password", show="*", width=300, height=35)
        self.password_entry.pack(pady=(5, 15))

        # -- Report Selection Section --
        report_frame = ctk.CTkFrame(frame, fg_color="#2B2B2B", corner_radius=10)
        report_frame.pack(pady=10, padx=20, fill="x")
        
        report_title = ctk.CTkLabel(report_frame, text="📊 Report Selection", font=("Arial", 14, "bold"))
        report_title.pack(pady=(10, 5))

        # Report type selection
        self.report_type_var = ctk.StringVar(value="summary")
        
        report_type_frame = ctk.CTkFrame(report_frame, fg_color="transparent")
        report_type_frame.pack(pady=10, fill="x")
        
        self.summary_radio = ctk.CTkRadioButton(
            report_type_frame, 
            text="📋 Stampcard Summary", 
            variable=self.report_type_var, 
            value="summary",
            font=("Arial", 12)
        )
        self.summary_radio.pack(side="left", padx=(20, 40))
        
        self.transactions_radio = ctk.CTkRadioButton(
            report_type_frame, 
            text="💳 Stampcard Transactions", 
            variable=self.report_type_var, 
            value="transactions",
            font=("Arial", 12)
        )
        self.transactions_radio.pack(side="left")

        # Report parameters
        params_frame = ctk.CTkFrame(report_frame, fg_color="transparent")
        params_frame.pack(pady=10, fill="x")

        # Limit input
        limit_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        limit_frame.pack(side="left", padx=(20, 20))
        
        limit_label = ctk.CTkLabel(limit_frame, text="Record Limit:", font=("Arial", 11))
        limit_label.pack()
        self.limit_entry = ctk.CTkEntry(limit_frame, placeholder_text="1000", width=100, height=30)
        self.limit_entry.pack()
        self.limit_entry.insert(0, str(CONFIG['reports']['default_limit']))

        # Order by selection
        order_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        order_frame.pack(side="left", padx=(20, 20))
        
        order_label = ctk.CTkLabel(order_frame, text="Order By:", font=("Arial", 11))
        order_label.pack()
        self.order_var = ctk.StringVar(value="MemberNo")
        self.order_combo = ctk.CTkComboBox(
            order_frame, 
            values=["MemberNo", "CurrentStamps", "CardsFilled", "RewardsEarned"],
            variable=self.order_var,
            width=140,
            height=30
        )
        self.order_combo.pack()

        # Order direction
        direction_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        direction_frame.pack(side="left", padx=(20, 20))
        
        direction_label = ctk.CTkLabel(direction_frame, text="Direction:", font=("Arial", 11))
        direction_label.pack()
        self.direction_var = ctk.StringVar(value="desc")
        self.direction_combo = ctk.CTkComboBox(
            direction_frame, 
            values=["desc", "asc"],
            variable=self.direction_var,
            width=80,
            height=30
        )
        self.direction_combo.pack()

        # Action buttons
        button_frame = ctk.CTkFrame(report_frame, fg_color="transparent")
        button_frame.pack(pady=15)

        self.generate_button = ctk.CTkButton(
            button_frame, 
            text="📊 Generate Report", 
            command=self.handle_generate_report_threaded, 
            width=180, 
            height=40,
            font=("Arial", 12, "bold")
        )
        self.generate_button.pack(side="left", padx=(0, 10))

        self.export_csv_button = ctk.CTkButton(
            button_frame, 
            text="📄 Export CSV", 
            command=self.export_csv, 
            width=120, 
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049",
            state="disabled"
        )
        self.export_csv_button.pack(side="left", padx=(5, 5))

        self.export_json_button = ctk.CTkButton(
            button_frame, 
            text="📋 Export JSON", 
            command=self.export_json, 
            width=120, 
            height=40,
            fg_color="#2196F3",
            hover_color="#1976D2",
            state="disabled"
        )
        self.export_json_button.pack(side="left", padx=(5, 0))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(report_frame, width=600)
        self.progress_bar.pack(pady=(10, 15))
        self.progress_bar.set(0)

        # -- Results Section --
        results_frame = ctk.CTkFrame(frame, fg_color="#2B2B2B", corner_radius=10)
        results_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        results_title = ctk.CTkLabel(results_frame, text="📈 Report Results", font=("Arial", 14, "bold"))
        results_title.pack(pady=(10, 5))
        
        # Results display with scrollable textbox
        self.results_display = ctk.CTkTextbox(results_frame, height=300, width=800, wrap="none", state="disabled")
        self.results_display.pack(pady=(0, 15), fill="both", expand=True, padx=15)
        self.results_display.configure(fg_color="#0D1117", text_color="#E6EDF3", font=("Consolas", 10))

        # -- Activity Log --
        log_frame = ctk.CTkFrame(frame, fg_color="#2B2B2B", corner_radius=10)
        log_frame.pack(pady=10, padx=20, fill="x")
        
        log_title = ctk.CTkLabel(log_frame, text="📋 Activity Log", font=("Arial", 14, "bold"))
        log_title.pack(pady=(10, 5))
        
        self.output_box = ctk.CTkTextbox(log_frame, height=120, width=800, wrap="word", state="disabled")
        self.output_box.pack(pady=(0, 15), fill="x", padx=15)
        self.output_box.configure(fg_color="#0D1117", text_color="#E6EDF3", font=("Consolas", 11))

    def log(self, message):
        """Add message to the activity log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.output_box.configure(state="normal")
        self.output_box.insert("end", formatted_message + "\n")
        self.output_box.see("end")
        self.output_box.configure(state="disabled")

    def update_progress(self, message, progress=None):
        """Update progress bar and log message"""
        self.log(message)
        if progress is not None:
            self.progress_bar.set(progress)

    def safe_get_record_value(self, record, key, default='N/A'):
        """Safely get a value from a record regardless of format (dict or list)"""
        try:
            if isinstance(record, dict):
                return record.get(key, default)
            elif isinstance(record, list):
                # Map field names to list indices based on API response format
                # Summary fields: ["MemberNo", "CurrentStamps", "CardsFilled", "RewardsEarned"]
                summary_field_map = {
                    'MemberNo': 0,
                    'CurrentStamps': 1, 
                    'CardsFilled': 2,
                    'RewardsEarned': 3
                }
                
                # Transaction fields: ["MemberSalesHeaderRecid", "MemberNo", "SaleStampsEarned", "RewardsEarned", "StoreName", "Amount", "TxnDate"]
                transaction_field_map = {
                    'MemberSalesHeaderRecid': 0,
                    'MemberNo': 1,
                    'SaleStampsEarned': 2,
                    'RewardsEarned': 3,
                    'StoreName': 4,
                    'Amount': 5,
                    'TxnDate': 6
                }
                
                # Try transaction fields first, then summary fields
                if key in transaction_field_map:
                    field_index = transaction_field_map[key]
                elif key in summary_field_map:
                    field_index = summary_field_map[key]
                else:
                    field_index = None
                
                if field_index is not None and field_index < len(record):
                    return record[field_index]
                else:
                    return default
            else:
                return default
        except Exception as e:
            self.log(f"⚠️ Error getting '{key}' from record: {e}")
            return default

    def display_results(self, data, report_type):
        """Display report results in the results textbox"""
        self.results_display.configure(state="normal")
        self.results_display.delete("1.0", "end")
        
        if not data:
            self.results_display.insert("end", "No data returned from API")
            self.results_display.configure(state="disabled")
            return
        
        # Debug logging to understand data structure
        self.log(f"🔍 Debug: Data type = {type(data)}")
        if isinstance(data, list) and len(data) > 0:
            self.log(f"🔍 Debug: First record type = {type(data[0])}")
        elif isinstance(data, dict):
            self.log(f"🔍 Debug: Dict keys = {list(data.keys())}")
        
        # Handle both response formats: direct list or dict with 'data' key
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict) and 'data' in data:
            records = data['data']
        else:
            self.results_display.insert("end", f"Unexpected API response format: {type(data)}")
            self.results_display.configure(state="disabled")
            return
            
        if not records:
            self.results_display.insert("end", "No records found")
            self.results_display.configure(state="disabled")
            return
            
        # Debug first record structure
        if len(records) > 0:
            self.log(f"🔍 Debug: First record = {records[0]}")
        
        # Format results as a table
        if report_type == "summary":
            header = f"{'Member#':<10} {'Stamps':<8} {'Filled':<6} {'Rewards':<8}\n"
            header += "-" * 40 + "\n"
            self.results_display.insert("end", header)
            
            for record in records:
                member_no = self.safe_get_record_value(record, 'MemberNo')
                current_stamps = self.safe_get_record_value(record, 'CurrentStamps')
                cards_filled = self.safe_get_record_value(record, 'CardsFilled')
                rewards_earned = self.safe_get_record_value(record, 'RewardsEarned')
                
                line = f"{str(member_no):<10} {str(current_stamps):<8} {str(cards_filled):<6} {str(rewards_earned):<8}\n"
                self.results_display.insert("end", line)
                
        elif report_type == "transactions":
            header = f"{'TxnID':<12} {'Member#':<10} {'Stamps':<7} {'Rewards':<8} {'Store':<15} {'Amount':<10} {'Date':<12}\n"
            header += "-" * 80 + "\n"
            self.results_display.insert("end", header)
            
            for record in records:
                txn_id = self.safe_get_record_value(record, 'MemberSalesHeaderRecid')
                member_no = self.safe_get_record_value(record, 'MemberNo')
                stamps_earned = self.safe_get_record_value(record, 'SaleStampsEarned')
                rewards_earned = self.safe_get_record_value(record, 'RewardsEarned')
                store_name = self.safe_get_record_value(record, 'StoreName')
                amount = self.safe_get_record_value(record, 'Amount')
                txn_date = self.safe_get_record_value(record, 'TxnDate')
                
                line = f"{str(txn_id):<12} {str(member_no):<10} {str(stamps_earned):<7} {str(rewards_earned):<8} {str(store_name)[:14]:<15} {str(amount):<10} {str(txn_date)[:10]:<12}\n"
                self.results_display.insert("end", line)
        
        self.results_display.configure(state="disabled")

    def validate_inputs(self):
        """Validate all input fields"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        limit_str = self.limit_entry.get().strip()

        if not username or not password:
            raise ValueError("Username and password are required")
        
        if not limit_str or not limit_str.isdigit() or int(limit_str) < 1:
            raise ValueError("Record limit must be a positive integer")

        return {
            'username': username,
            'password': password,
            'report_type': self.report_type_var.get(),
            'limit': int(limit_str),
            'order_by': self.order_var.get(),
            'order_direction': self.direction_var.get()
        }

    def handle_generate_report_threaded(self):
        """Handle report generation in a separate thread"""
        if self.is_processing:
            return
        
        # Run report generation in thread to prevent UI freezing
        thread = threading.Thread(target=self.handle_generate_report)
        thread.daemon = True
        thread.start()

    def handle_generate_report(self):
        """Handle the report generation process"""
        self.is_processing = True
        original_text = self.generate_button.cget("text")
        
        try:
            # Update UI to show processing state
            self.generate_button.configure(text="⏳ Processing...", state="disabled")
            self.export_csv_button.configure(state="disabled")
            self.export_json_button.configure(state="disabled")
            self.progress_bar.set(0)
            
            # Clear previous results
            self.results_display.configure(state="normal")
            self.results_display.delete("1.0", "end")
            self.results_display.configure(state="disabled")
            
            # Clear previous log
            self.output_box.configure(state="normal")
            self.output_box.delete("1.0", "end")
            self.output_box.configure(state="disabled")
            
            # Validate inputs
            self.update_progress("🔍 Validating inputs...", 0.1)
            inputs = self.validate_inputs()
            
            # Login
            self.update_progress("🔐 Authenticating...", 0.2)
            token = login(inputs['username'], inputs['password'])
            self.update_progress("✅ Authentication successful", 0.3)
            
            # Generate report
            report_type = inputs['report_type']
            self.update_progress(f"📊 Generating {report_type} report...", 0.5)
            
            if report_type == "summary":
                # Update order combo for summary fields
                if inputs['order_by'] not in ["MemberNo", "CurrentStamps", "CardsFilled", "RewardsEarned"]:
                    inputs['order_by'] = "MemberNo"
                
                data = get_stampcard_summary(
                    token,
                    start=0,
                    limit=inputs['limit'],
                    order_by=inputs['order_by'],
                    order_direction=inputs['order_direction']
                )
            else:  # transactions
                # Update order combo for transaction fields
                if inputs['order_by'] not in ["MemberSalesHeaderRecid", "MemberNo", "SaleStampsEarned", "RewardsEarned", "StoreName", "Amount", "TxnDate"]:
                    inputs['order_by'] = "MemberSalesHeaderRecid"
                
                data = get_stampcard_transactions(
                    token,
                    start=0,
                    limit=inputs['limit'],
                    order_by=inputs['order_by'],
                    order_direction=inputs['order_direction']
                )
            
            self.update_progress("✅ Report generated successfully", 0.8)
            
            # Store data for export
            self.current_report_data = data
            self.current_report_type = report_type
            
            # Display results
            self.update_progress("📈 Displaying results...", 0.9)
            self.display_results(data, report_type)
            
            # Success
            self.progress_bar.set(1.0)
            # Calculate record count based on response format
            if isinstance(data, list):
                record_count = len(data)
            elif isinstance(data, dict) and 'data' in data:
                record_count = len(data['data'])
            else:
                record_count = 0
            self.log(f"🎉 Report completed! {record_count} records retrieved")
            
            # Enable export buttons
            self.export_csv_button.configure(state="normal")
            self.export_json_button.configure(state="normal")
                    
        except Exception as e:
            self.progress_bar.set(0)
            self.log(f"❌ Error: {str(e)}")
        finally:
            # Restore button state
            self.generate_button.configure(text=original_text, state="normal")
            self.is_processing = False

    def export_csv(self):
        """Export current report data to CSV"""
        if not self.current_report_data:
            messagebox.showwarning("No Data", "Please generate a report first")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"stampcard_{self.current_report_type}_{timestamp}.csv"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if filename:
                export_to_csv(self.current_report_data, filename, self.current_report_type)
                self.log(f"📄 CSV exported successfully: {filename}")
                messagebox.showinfo("Export Successful", f"Report exported to:\n{filename}")
        except Exception as e:
            self.log(f"❌ CSV export failed: {str(e)}")
            messagebox.showerror("Export Failed", f"Failed to export CSV:\n{str(e)}")

    def export_json(self):
        """Export current report data to JSON"""
        if not self.current_report_data:
            messagebox.showwarning("No Data", "Please generate a report first")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"stampcard_{self.current_report_type}_{timestamp}.json"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if filename:
                export_to_json(self.current_report_data, filename, self.current_report_type)
                self.log(f"📋 JSON exported successfully: {filename}")
                messagebox.showinfo("Export Successful", f"Report exported to:\n{filename}")
        except Exception as e:
            self.log(f"❌ JSON export failed: {str(e)}")
            messagebox.showerror("Export Failed", f"Failed to export JSON:\n{str(e)}")

# --- Main ---
if __name__ == "__main__":
    app = StampReportingApp()
    app.mainloop()