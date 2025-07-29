"""
Data processing utilities for medical datasets
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import os
import hashlib
from pathlib import Path

class MedicalDataProcessor:
    """
    Processor for medical and cancer datasets with security and validation
    """
    
    def __init__(self, upload_folder, processed_folder):
        self.upload_folder = Path(upload_folder)
        self.processed_folder = Path(processed_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.processed_folder.mkdir(parents=True, exist_ok=True)
        
        # Medical data standards
        self.required_cancer_fields = {
            'breast': ['patient_id', 'age', 'diagnosis_date'],
            'lung': ['patient_id', 'age', 'smoking_history'],
            'colorectal': ['patient_id', 'age', 'stage'],
            'general': ['patient_id', 'age']
        }
        
        self.sensitive_fields = [
            'patient_id', 'mrn', 'ssn', 'name', 'address', 'phone', 'email',
            'date_of_birth', 'diagnosis_date', 'admission_date'
        ]
    
    def validate_file_format(self, file_path):
        """
        Validate file format and structure
        """
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_extension == '.json':
                df = pd.read_json(file_path)
            else:
                return False, f"Unsupported file format: {file_extension}"
            
            # Basic validation
            if df.empty:
                return False, "File contains no data"
            
            if df.shape[0] < 10:
                return False, "Dataset too small (minimum 10 rows required)"
            
            return True, f"Valid dataset with {df.shape[0]} rows and {df.shape[1]} columns"
            
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    def detect_cancer_type(self, df):
        """
        Automatically detect cancer type from column names and data
        """
        columns_lower = [col.lower() for col in df.columns]
        
        # Breast cancer indicators
        breast_indicators = ['er_status', 'pr_status', 'her2', 'breast', 'mammogram', 'brca']
        if any(indicator in ' '.join(columns_lower) for indicator in breast_indicators):
            return 'breast'
        
        # Lung cancer indicators
        lung_indicators = ['smoking', 'lung', 'egfr', 'kras', 'alk', 'chest_xray']
        if any(indicator in ' '.join(columns_lower) for indicator in lung_indicators):
            return 'lung'
        
        # Colorectal cancer indicators
        colorectal_indicators = ['colorectal', 'colon', 'rectal', 'cea', 'colonoscopy']
        if any(indicator in ' '.join(columns_lower) for indicator in colorectal_indicators):
            return 'colorectal'
        
        return 'general'
    
    def detect_data_type(self, df):
        """
        Detect if data is clinical, genetic, or imaging
        """
        columns_lower = [col.lower() for col in df.columns]
        
        # Genetic data indicators
        genetic_indicators = ['gene', 'mutation', 'expression', 'variant', 'allele', 'chromosome']
        genetic_score = sum(1 for col in columns_lower if any(ind in col for ind in genetic_indicators))
        
        # Imaging data indicators
        imaging_indicators = ['pixel', 'image', 'scan', 'dicom', 'mri', 'ct', 'pet']
        imaging_score = sum(1 for col in columns_lower if any(ind in col for ind in imaging_indicators))
        
        # Clinical data indicators
        clinical_indicators = ['age', 'stage', 'grade', 'treatment', 'diagnosis', 'survival']
        clinical_score = sum(1 for col in columns_lower if any(ind in col for ind in clinical_indicators))
        
        scores = {'clinical': clinical_score, 'genetic': genetic_score, 'imaging': imaging_score}
        return max(scores, key=scores.get)
    
    def anonymize_data(self, df):
        """
        Anonymize sensitive medical data
        """
        df_anonymized = df.copy()
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Hash patient IDs
            if 'patient_id' in col_lower or 'mrn' in col_lower:
                df_anonymized[col] = df_anonymized[col].apply(
                    lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:10]
                )
            
            # Remove direct identifiers
            elif any(sensitive in col_lower for sensitive in ['name', 'address', 'phone', 'email', 'ssn']):
                df_anonymized = df_anonymized.drop(col, axis=1)
            
            # Generalize dates to year only
            elif 'date' in col_lower:
                try:
                    df_anonymized[col] = pd.to_datetime(df_anonymized[col]).dt.year
                except:
                    pass
        
        return df_anonymized
    
    def clean_data(self, df):
        """
        Clean and preprocess medical data
        """
        df_cleaned = df.copy()
        
        # Remove duplicate rows
        df_cleaned = df_cleaned.drop_duplicates()
        
        # Handle missing values based on column type
        for col in df_cleaned.columns:
            if df_cleaned[col].dtype in ['int64', 'float64']:
                # For numeric columns, flag extreme outliers
                if df_cleaned[col].notna().sum() > 0:
                    Q1 = df_cleaned[col].quantile(0.25)
                    Q3 = df_cleaned[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 3 * IQR
                    upper_bound = Q3 + 3 * IQR
                    
                    # Replace extreme outliers with NaN
                    outliers = (df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)
                    df_cleaned.loc[outliers, col] = np.nan
        
        return df_cleaned
    
    def calculate_data_quality_score(self, df):
        """
        Calculate overall data quality score (0-1)
        """
        scores = []
        
        # Completeness score
        completeness = (df.notna().sum().sum()) / (df.shape[0] * df.shape[1])
        scores.append(completeness)
        
        # Consistency score (no duplicate rows)
        consistency = (df.shape[0] - df.duplicated().sum()) / df.shape[0]
        scores.append(consistency)
        
        # Valid data types score
        valid_types = 0
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64', 'object', 'datetime64[ns]']:
                valid_types += 1
        type_score = valid_types / df.shape[1]
        scores.append(type_score)
        
        return np.mean(scores)
    
    def extract_column_metadata(self, df):
        """
        Extract detailed metadata about each column
        """
        metadata = {}
        
        for col in df.columns:
            col_data = df[col]
            col_meta = {
                'name': col,
                'dtype': str(col_data.dtype),
                'null_count': col_data.isnull().sum(),
                'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
                'unique_count': col_data.nunique(),
                'is_categorical': col_data.dtype == 'object' or col_data.nunique() < 10
            }
            
            if col_data.dtype in ['int64', 'float64']:
                col_meta.update({
                    'min': float(col_data.min()) if not col_data.isnull().all() else None,
                    'max': float(col_data.max()) if not col_data.isnull().all() else None,
                    'mean': float(col_data.mean()) if not col_data.isnull().all() else None,
                    'std': float(col_data.std()) if not col_data.isnull().all() else None
                })
            
            if col_meta['is_categorical']:
                value_counts = col_data.value_counts().head(10).to_dict()
                col_meta['top_values'] = {str(k): int(v) for k, v in value_counts.items()}
            
            metadata[col] = col_meta
        
        return metadata
    
    def process_dataset(self, file_path, user_id, dataset_name, description=None):
        """
        Complete processing pipeline for uploaded dataset
        """
        # Validate file
        is_valid, validation_message = self.validate_file_format(file_path)
        if not is_valid:
            return {'success': False, 'error': validation_message}
        
        # Load data
        file_extension = Path(file_path).suffix.lower()
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_extension == '.json':
            df = pd.read_json(file_path)
        
        # Detect dataset characteristics
        cancer_type = self.detect_cancer_type(df)
        data_type = self.detect_data_type(df)
        
        # Clean and anonymize data
        df_processed = self.clean_data(df)
        df_processed = self.anonymize_data(df_processed)
        
        # Calculate quality metrics
        data_quality_score = self.calculate_data_quality_score(df_processed)
        missing_percentage = (df_processed.isnull().sum().sum() / 
                            (df_processed.shape[0] * df_processed.shape[1])) * 100
        
        # Extract metadata
        column_metadata = self.extract_column_metadata(df_processed)
        
        # Save processed data
        processed_filename = f"processed_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processed_path = self.processed_folder / processed_filename
        df_processed.to_csv(processed_path, index=False)
        
        return {
            'success': True,
            'processed_file_path': str(processed_path),
            'cancer_type': cancer_type,
            'data_type': data_type,
            'num_rows': df_processed.shape[0],
            'num_columns': df_processed.shape[1],
            'data_quality_score': data_quality_score,
            'missing_data_percentage': missing_percentage,
            'column_metadata': column_metadata,
            'validation_message': validation_message
        }
    
    def load_processed_dataset(self, file_path):
        """
        Load a processed dataset for analysis
        """
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise Exception(f"Error loading processed dataset: {str(e)}")
    
    def get_dataset_summary(self, file_path):
        """
        Get quick summary of dataset
        """
        df = self.load_processed_dataset(file_path)
        
        return {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'sample_data': df.head().to_dict('records')
        }