# Cancer Research Data Analytics Platform

A comprehensive web application for cancer dataset analysis, visualization, and machine learning. This platform enables researchers to explore cancer datasets, generate insights through interactive visualizations, and run predictive models using machine learning algorithms.

## Features

### 🔬 Data Management
- **File Upload**: Support for CSV and Excel files
- **Sample Datasets**: Pre-loaded cancer datasets for testing
- **Data Validation**: Automatic data type detection and quality assessment

### 📊 Interactive Visualizations
- **Correlation Heatmaps**: Identify relationships between variables
- **Survival Curves**: Kaplan-Meier survival analysis with confidence intervals
- **Outcome Distribution**: Treatment outcome analysis by groups

### 🤖 Machine Learning Models
- **Logistic Regression**: For binary classification problems
- **Decision Trees**: Interpretable models with feature importance
- **Random Forest**: Ensemble methods for improved accuracy
- **Feature Importance**: Automatic identification of key predictive features

### 📈 Analysis & Reporting
- **Data Quality Assessment**: Missing data, duplicates, and outlier detection
- **Statistical Summaries**: Comprehensive dataset overview
- **Plain Language Reports**: Automated insights generation

## Technology Stack

### Backend
- **Flask**: Python web framework
- **pandas**: Data manipulation and analysis
- **scikit-learn**: Machine learning algorithms
- **lifelines**: Survival analysis
- **Plotly**: Interactive visualizations

### Frontend
- **HTML5/CSS3**: Modern responsive design
- **JavaScript**: Interactive user interface
- **Plotly.js**: Client-side data visualization
- **Font Awesome**: Professional icons

### Styling
- **Hospital/Lab Theme**: Blue and yellow color scheme
- **Responsive Design**: Mobile-friendly interface
- **Professional UI**: Clean, medical-grade appearance

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd cancer-research-platform
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the platform**:
   Open your browser and navigate to `http://localhost:5000`

## Usage

### Getting Started
1. **Load Data**: Upload your own CSV/Excel file or select a sample dataset
2. **Explore**: View dataset information and statistics
3. **Visualize**: Generate correlation heatmaps, survival curves, and outcome distributions
4. **Analyze**: Run machine learning models to predict outcomes
5. **Report**: Generate comprehensive analysis summaries

### Sample Datasets
The platform includes two sample datasets:

#### Breast Cancer Survival Dataset
- Patient demographics and tumor characteristics
- Treatment types and outcomes
- Survival time and status data
- 40 patients with 11 features

#### Lung Cancer Treatment Dataset
- Staging and histology information
- Treatment modalities and responses
- Progression-free survival data
- 40 patients with 10 features

### API Endpoints

#### Data Management
- `POST /api/upload` - Upload dataset file
- `GET /api/load_sample/<dataset_name>` - Load sample dataset
- `GET /api/dataset_info` - Get current dataset information
- `GET /api/available_datasets` - List available sample datasets

#### Visualizations
- `GET /api/visualizations/correlation_heatmap` - Generate correlation heatmap
- `GET /api/visualizations/survival_curve` - Generate Kaplan-Meier survival curve
- `GET /api/visualizations/outcome_distribution` - Generate outcome distribution chart

#### Machine Learning
- `POST /api/ml/predict` - Train and evaluate ML models

#### Analysis
- `GET /api/analysis/summary` - Generate dataset analysis summary

## Data Requirements

### For Survival Analysis
Your dataset should include:
- **Time column**: Contains keywords like 'time', 'duration', 'survival', 'days', 'months'
- **Event column**: Contains keywords like 'event', 'death', 'censored', 'status', 'outcome'

### For Treatment Analysis
Your dataset should include:
- **Treatment column**: Contains keywords like 'treatment', 'therapy', 'drug', 'intervention'
- **Outcome column**: Contains keywords like 'outcome', 'response', 'result', 'status'

### For Machine Learning
- At least 10 rows of data (more is better)
- Numeric features for model training
- A target variable for prediction

## File Structure

```
cancer-research-platform/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main web interface
├── sample_data/
│   ├── breast_cancer_survival.csv
│   └── lung_cancer_treatment.csv
└── uploads/              # User uploaded files (created automatically)
```

## Customization

### Adding New Sample Datasets
1. Add your CSV file to the `sample_data/` directory
2. Update the `get_available_datasets()` function in `app.py`
3. Follow the naming convention for automatic column detection

### Extending Visualizations
1. Add new visualization functions to `app.py`
2. Create corresponding API endpoints
3. Update the frontend JavaScript to call the new endpoints

### Adding ML Models
1. Import the model from scikit-learn
2. Add it to the model selection in the `run_ml_model()` function
3. Update the frontend dropdown options

## Security Considerations

- File uploads are limited to 16MB
- Only CSV and Excel files are accepted
- Data is stored in memory (not persisted)
- Input validation for all API endpoints

## Browser Compatibility

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please open an issue on the repository or contact the development team.

## Acknowledgments

- Built with Flask and modern web technologies
- Inspired by the need for accessible cancer research tools
- Designed with input from medical researchers and data scientists
