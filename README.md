# RedCat Stamp Card Reporting

**A desktop application for generating and exporting stamp card reports from the RedCat API.**

Generate comprehensive reports on member stamp cards including summaries and detailed transaction histories with export capabilities.

## Quick Start

1. **Install Python 3.8+** and dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your API endpoint** in `config.json`:
   ```json
   {
       "api": {
           "base_url": "https://your-redcat-api.com/api/v1"
       }
   }
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Features

### **Report Types**
- **📋 Stampcard Summary**: Overview of all member stampcards showing current stamps, cards filled, and rewards earned
- **💳 Stampcard Transactions**: Detailed transaction history with stamps earned, rewards, store info, and transaction amounts

### **Core Functionality**
- Generate reports with customizable parameters (limit, sorting)
- Real-time progress tracking during report generation
- Export reports to CSV or JSON format
- Modern dark-themed, resizable interface
- Comprehensive error handling and validation

### **Export Options**
- **CSV Export**: Spreadsheet-compatible format for analysis
- **JSON Export**: Structured data with metadata and timestamps
- **Auto-naming**: Files automatically named with report type and timestamp

## Usage

### **Generate Reports**

1. **Authentication**: Enter your API username and password
2. **Select Report Type**: Choose between Summary or Transactions
3. **Set Parameters**:
   - **Record Limit**: Number of records to retrieve (default: 1000)
   - **Order By**: Field to sort results by
   - **Direction**: Ascending or descending order
4. **Generate**: Click "Generate Report" to fetch data
5. **View Results**: Report displays in formatted table view
6. **Export**: Use CSV or JSON export buttons to save data

### **Report Details**

#### **Stampcard Summary Report**
Shows overview data for all member stampcards:
- **Member Number**: Unique member identifier
- **Current Stamps**: Number of stamps on current card
- **Cards Filled**: Total completed stamp cards
- **Rewards Earned**: Total rewards received

#### **Stampcard Transactions Report**
Shows detailed transaction history:
- **Transaction ID**: Unique transaction identifier  
- **Member Number**: Member who made purchase
- **Sale Stamps Earned**: Stamps earned from transaction
- **Rewards Earned**: Rewards earned from transaction
- **Store Name**: Location of purchase
- **Amount**: Transaction total
- **Transaction Date**: Date of purchase

### **Sorting Options**

**Summary Report Sorting:**
- Member Number, Current Stamps, Cards Filled, Rewards Earned

**Transactions Report Sorting:**
- Transaction ID, Member Number, Sale Stamps Earned, Rewards Earned, Store Name, Amount, Transaction Date

## Configuration

Edit `config.json` to customize:

```json
{
    "api": {
        "base_url": "https://your-redcat-api.com/api/v1",
        "auth_type": "U"
    },
    "ui": {
        "window_title": "RedCat Stamp Card Reporting",
        "default_width": 900,
        "default_height": 700
    },
    "reports": {
        "default_limit": 1000,
        "auto_export": false
    }
}
```

### **Configuration Options**
- `api.base_url`: Your RedCat API endpoint
- `api.auth_type`: Authentication type (default: "U")
- `ui.window_title`: Application window title
- `ui.default_width/height`: Default window dimensions
- `reports.default_limit`: Default number of records to retrieve
- `reports.auto_export`: Enable automatic export after report generation

## API Integration

### **Authentication**
```http
POST /api/v1/login
{
    "username": "your_username",
    "psw": "your_password", 
    "auth_type": "U"
}
```

### **Stampcard Summary Endpoint**
```http
POST /api/v1/reports/loyalty/stampcards_summary
Headers: {"X-Redcat-Authtoken": "your_token"}
{
    "Fields": ["MemberNo", "CurrentStamps", "CardsFilled", "RewardsEarned"],
    "Order": [["MemberNo", "desc"]],
    "Start": 0,
    "Limit": 1000
}
```

### **Stampcard Transactions Endpoint**
```http
POST /api/v1/reports/loyalty/stampcards_transactions
Headers: {"X-Redcat-Authtoken": "your_token"}
{
    "Fields": ["MemberSalesHeaderRecid", "MemberNo", "SaleStampsEarned", "RewardsEarned", "StoreName", "Amount", "TxnDate"],
    "Order": [["MemberSalesHeaderRecid", "desc"]],
    "Start": 0,
    "Limit": 1000
}
```

## Export Formats

### **CSV Export**
- Standard comma-separated values format
- Headers included for easy import into spreadsheet applications
- Filename format: `stampcard_{type}_{timestamp}.csv`

### **JSON Export**
- Structured data with metadata
- Includes report type, generation timestamp, and record count
- Filename format: `stampcard_{type}_{timestamp}.json`

**JSON Structure:**
```json
{
    "report_type": "summary",
    "generated_at": "2024-07-25T10:30:00",
    "total_records": 150,
    "data": {
        "data": [...]
    }
}
```

## Perfect For

- **Store Managers**: Analyzing customer loyalty program performance
- **Marketing Teams**: Understanding stamp card usage patterns
- **Data Analysts**: Exporting loyalty data for further analysis
- **Customer Service**: Investigating member stamp card history
- **Business Intelligence**: Integrating loyalty data into reporting systems

## Files

- `main.py` - Main application with GUI and report generation
- `config.json` - Configuration settings
- `requirements.txt` - Python dependencies

## Dependencies

- **CustomTkinter 5.2.0+**: Modern GUI framework
- **Requests 2.31.0+**: HTTP client for API calls
- **Pandas 1.5.0+**: Data manipulation for export functionality
- **Python 3.8+**: Minimum Python version

## Troubleshooting

**"Login failed" Error**
- Verify username/password are correct
- Check API URL in config.json
- Ensure account has report access permissions

**"No data returned" Error**
- Check if there are stamp card records in the system
- Verify API endpoint is accessible
- Try reducing the record limit

**Export Issues**
- Ensure you have write permissions to the export directory
- Check available disk space
- Verify the report was generated successfully before exporting