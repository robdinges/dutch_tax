# Dutch Tax Calculator - Web GUI

A modern, user-friendly web-based interface for calculating Dutch income (Box1) and wealth (Box3) taxes for 2025.

## Features

✨ **Modern Web Interface**
- Beautiful, responsive design with Bootstrap 5
- Works on desktop, tablet, and mobile devices
- Real-time form validation
- Intuitive user experience

💰 **Tax Calculation**
- Box1 (Income Tax) with progressive brackets
- Box3 (Wealth Tax) calculation
- Support for multiple household members
- Multiple income sources per person
- Deductions and tax credits
- Asset tracking and allocation

📊 **Results Display**
- Detailed tax breakdown by member
- Box1 and Box3 summary
- Effective tax rate calculation
- Color-coded financial summaries
- Easy to understand presentation

🎯 **Flexible Allocation**
- Equal split (50-50)
- Proportional allocation (by income)
- Custom percentage allocation

## Running the Application

### Prerequisites

- Python 3.9+
- Flask
- All project files (object_model.py, tax_brackets.py, etc.)

### Installation

```bash
# Install Flask (if not already installed)
pip install flask

# Navigate to the project directory
cd "/path/to/Copilot_test TAX"

# Run the Flask app
python3 app.py
```

### Access the Application

Open your web browser and go to:
```
http://localhost:5000
```

The application will start on port 5000 by default.

## How to Use

### 1. Enter Household Information
- Set a household ID (optional)
- Select the number of household members
- Fill in basic information for each member:
  - Full name
  - BSN (tax identification number)
  - Residency status

### 2. Add Income Sources
For each household member:
- Click "+ Add Income Source"
- Select the type (Employment, Self-Employment, Rental, etc.)
- Enter the annual amount in euros

### 3. Add Deductions
For each household member:
- Click "+ Add Deduction"
- Enter description (e.g., "Mortgage Interest")
- Enter the deduction amount in euros

### 4. Add Withheld Tax
- Enter any taxes already withheld by employers or banks

### 5. Add Assets (Box3)
For each household member:
- Click "+ Add Asset"
- Select asset type (Savings, Investment, Real Estate, etc.)
- Enter the asset value in euros

### 6. Choose Box3 Allocation Strategy
Select how household assets should be allocated:
- **Equal**: 50-50 split between partners
- **Proportional**: Split based on income ratios
- **Custom**: Manual percentage entry

### 7. Calculate Taxes
- Click the "Calculate Taxes" button
- View detailed results including:
  - Individual member tax calculations
  - Box1 (income tax) totals
  - Box3 (wealth tax) calculations
  - Total tax due
  - Effective tax rate

## Tax Year Information

**Tax Year 2025:**
- General Tax Credit: €2,917.00
- Box3 Rate: 36%
- Progressive tax brackets for Box1

## Project Structure

```
Copilot_test TAX/
├── app.py                 # Flask application with API routes
├── object_model.py        # Core domain models
├── tax_brackets.py        # Tax configurations for 2023-2025
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── style.css         # Styling and layout
    └── app.js            # Frontend JavaScript and interactivity
```

## API Endpoints

The application provides REST API endpoints for use by the frontend:

- `GET /` - Main page
- `GET /api/income-types` - Available income source types
- `GET /api/asset-types` - Available asset types
- `GET /api/allocation-strategies` - Box3 allocation strategies
- `POST /api/calculate` - Calculate taxes (accepts JSON form data)

## Technical Stack

- **Backend**: Python 3 with Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Bootstrap 5
- **Domain Logic**: Custom Python classes (Person, Household, TaxBracket, etc.)
- **Financial Calculations**: Python Decimal for precision

## Calculation Details

### Box1 (Income Tax)
1. Calculate total gross income from all sources
2. Subtract deductions
3. Apply progressive tax brackets (4 tiers for 2025)
4. Apply general tax credit (€2,917)
5. Subtract any withheld taxes
6. Show net tax liability (or refund if negative)

### Box3 (Wealth Tax)
1. Sum all household member assets
2. Apply 36% tax rate
3. Allocate between members based on selected strategy
4. Display per-member allocation

### Total Tax Due
- Box1 tax + Box3 tax
- Effective tax rate = (Total Tax / Total Income) × 100

## Important Disclaimer

⚠️ **For informational purposes only**

This calculator is provided for educational and informational purposes. It does not constitute professional tax advice. 

For official tax purposes and accurate calculations, always consult the Dutch Tax Authority (Belastingdienst) or a qualified tax professional.

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify the Flask app:
```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change to different port
```

### Module Not Found
Ensure all required Python files are in the same directory:
- object_model.py
- tax_brackets.py
- app.py

### Styling Issues
Clear your browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete) and reload the page.

## Future Enhancements

Potential features for future versions:
- Save calculations to file (PDF/Excel export)
- Multi-language support (Dutch/English)
- Tax history and comparison tools
- Advanced household scenarios
- Database storage of calculations
- Mobile app versions
- API-only deployment

## License & Attribution

This calculator uses realistic Dutch tax brackets from the Belastingdienst (Dutch Tax Authority).

---

**Built with ❤️ for Dutch tax calculations**
