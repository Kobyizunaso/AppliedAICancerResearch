# Medical Data Visualization Platform

A comprehensive web application for uploading and analyzing patient data related to cancer and anemia. This platform provides interactive charts and visualizations to help identify patterns in medical data, particularly focusing on hemoglobin levels and treatment effectiveness.

## Features

### 📊 **Data Upload & Validation**
- Drag & drop CSV file upload interface
- Real-time data validation and error handling
- Support for patient datasets with medical information

### 📈 **Interactive Visualizations**
- **Hemoglobin Distribution**: Bar chart showing hemoglobin level ranges
- **Treatment Types**: Doughnut chart displaying treatment distribution
- **Age vs Hemoglobin**: Scatter plot revealing age-related trends
- **Cancer Types**: Pie chart showing cancer type distribution
- **Treatment Effectiveness**: Bar chart comparing average hemoglobin by treatment
- **Age Demographics**: Line chart showing patient age distribution

### 📋 **Data Management**
- Comprehensive data summary with key metrics
- Interactive data table with all patient records
- Responsive design for mobile and desktop devices

## Expected Data Format

The application expects a CSV file with the following columns:

| Column | Description | Type |
|--------|-------------|------|
| `patient_id` | Unique patient identifier | String |
| `age` | Patient age in years | Number |
| `hemoglobin_level` | Hemoglobin level in g/dL | Number |
| `treatment_type` | Type of treatment | String |
| `diagnosis_date` | Date of diagnosis | String |
| `cancer_type` | Type of cancer | String |

### Sample Data Structure
```csv
patient_id,age,hemoglobin_level,treatment_type,diagnosis_date,cancer_type
P001,45,8.2,Chemotherapy,2024-01-15,Breast Cancer
P002,62,11.5,Radiation Therapy,2024-02-03,Lung Cancer
...
```

## Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- No additional software installation required

### Usage
1. **Open the Application**
   - Open `index.html` in your web browser
   - The application loads with a clean, modern interface

2. **Upload Patient Data**
   - Click the upload area or drag & drop a CSV file
   - The system validates the file format and required columns
   - Success/error messages guide you through the process

3. **View Visualizations**
   - After successful upload, the platform displays:
     - Data summary with key statistics
     - Six interactive charts showing different data perspectives
     - Complete data table with all patient records

4. **Analyze Patterns**
   - Use charts to identify trends in hemoglobin levels
   - Compare treatment effectiveness across different approaches
   - Analyze age-related patterns in cancer and anemia data

## File Structure

```
medical-data-platform/
├── index.html          # Main application interface
├── styles.css          # Modern, responsive styling
├── script.js           # Application logic and chart generation
├── sample_data.csv     # Example dataset for testing
└── README.md          # This documentation
```

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charting**: Chart.js for interactive visualizations
- **Data Processing**: Papa Parse for CSV handling
- **Design**: Modern gradient backgrounds, glassmorphism effects
- **Responsive**: Mobile-first design approach

## Key Insights Provided

### 🩺 **Medical Analytics**
- Hemoglobin level distributions across patient populations
- Treatment type effectiveness comparisons
- Age-related health pattern identification
- Cancer type prevalence analysis

### 📊 **Visual Intelligence**
- Color-coded charts for easy pattern recognition
- Interactive elements for detailed data exploration
- Professional medical-grade visualizations
- Responsive charts that work on all devices

## Browser Compatibility

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## Sample Data

The included `sample_data.csv` contains 50 realistic patient records with:
- Various cancer types (Breast, Lung, Leukemia, etc.)
- Different treatment approaches (Chemotherapy, Radiation, Surgery, etc.)
- Range of hemoglobin levels (6.9 - 14.9 g/dL)
- Patient ages (32 - 76 years)
- Recent diagnosis dates (January-February 2024)

## Privacy & Security

- **Client-Side Processing**: All data remains in your browser
- **No Server Upload**: Files are processed locally for privacy
- **No Data Storage**: Information is not saved or transmitted
- **HIPAA Consideration**: Designed with medical data privacy in mind

## Future Enhancements

- Export functionality for charts and reports
- Advanced filtering and search capabilities
- Time-series analysis for longitudinal studies
- Additional chart types and statistical analysis
- Multi-file data comparison features

## Support

For questions or issues:
1. Check that your CSV file matches the expected format
2. Ensure all required columns are present
3. Verify that numerical data is properly formatted
4. Use the provided sample data to test functionality

---

**Built for medical professionals, researchers, and data analysts working with cancer and anemia patient data.**
