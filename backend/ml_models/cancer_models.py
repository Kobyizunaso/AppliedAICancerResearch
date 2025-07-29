"""
Cancer-specific machine learning models for survival analysis, prediction, and classification
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import mean_squared_error, r2_score
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.utils import concordance_index
import joblib
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CancerMLPipeline:
    """
    Comprehensive ML pipeline for cancer data analysis
    """
    
    def __init__(self):
        self.models = {
            'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
            'random_forest': RandomForestClassifier(random_state=42, n_estimators=100),
            'svm': SVC(random_state=42, probability=True),
            'neural_network': MLPClassifier(random_state=42, max_iter=1000),
            'random_forest_regressor': RandomForestRegressor(random_state=42, n_estimators=100)
        }
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_importance = {}
        self.model_performance = {}
        
    def preprocess_data(self, df, target_column, test_size=0.2):
        """
        Preprocess cancer dataset for ML analysis
        """
        # Handle missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        categorical_columns = df.select_dtypes(include=['object']).columns
        
        # Fill missing values
        for col in numeric_columns:
            if col != target_column:
                df[col].fillna(df[col].median(), inplace=True)
        
        for col in categorical_columns:
            if col != target_column:
                df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown', inplace=True)
        
        # Encode categorical variables
        categorical_features = []
        for col in categorical_columns:
            if col != target_column:
                le = LabelEncoder()
                df[col + '_encoded'] = le.fit_transform(df[col].astype(str))
                categorical_features.append(col + '_encoded')
                df.drop(col, axis=1, inplace=True)
        
        # Separate features and target
        X = df.drop(target_column, axis=1)
        y = df[target_column]
        
        # Handle target variable encoding if needed
        if y.dtype == 'object':
            y = self.label_encoder.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test, X.columns.tolist()
    
    def train_classification_model(self, X_train, y_train, model_type='random_forest'):
        """
        Train classification model for cancer prediction
        """
        model = self.models[model_type]
        
        # Hyperparameter tuning for Random Forest
        if model_type == 'random_forest':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10]
            }
            grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy', n_jobs=-1)
            grid_search.fit(X_train, y_train)
            model = grid_search.best_estimator_
        else:
            model.fit(X_train, y_train)
        
        return model
    
    def evaluate_model(self, model, X_test, y_test):
        """
        Evaluate model performance with comprehensive metrics
        """
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted')
        }
        
        if y_pred_proba is not None:
            try:
                metrics['auc_score'] = roc_auc_score(y_test, y_pred_proba)
            except ValueError:
                metrics['auc_score'] = None
        
        return metrics
    
    def get_feature_importance(self, model, feature_names):
        """
        Extract feature importance from trained model
        """
        if hasattr(model, 'feature_importances_'):
            importance_data = list(zip(feature_names, model.feature_importances_))
            importance_data.sort(key=lambda x: x[1], reverse=True)
            return importance_data
        elif hasattr(model, 'coef_'):
            importance_data = list(zip(feature_names, abs(model.coef_[0])))
            importance_data.sort(key=lambda x: x[1], reverse=True)
            return importance_data
        return []
    
    def survival_analysis(self, df, duration_col, event_col):
        """
        Perform survival analysis using Kaplan-Meier estimation
        """
        kmf = KaplanMeierFitter()
        kmf.fit(df[duration_col], df[event_col])
        
        # Create survival data for plotting
        survival_data = {
            'timeline': kmf.timeline.tolist(),
            'survival_function': kmf.survival_function_.values.flatten().tolist(),
            'confidence_interval_lower': kmf.confidence_interval_.iloc[:, 0].tolist(),
            'confidence_interval_upper': kmf.confidence_interval_.iloc[:, 1].tolist(),
            'median_survival': kmf.median_survival_time_
        }
        
        return survival_data, kmf
    
    def cox_regression(self, df, duration_col, event_col, covariates):
        """
        Perform Cox proportional hazards regression
        """
        # Prepare data for Cox regression
        cox_data = df[[duration_col, event_col] + covariates].copy()
        cox_data = cox_data.dropna()
        
        # Fit Cox model
        cph = CoxPHFitter()
        cph.fit(cox_data, duration_col=duration_col, event_col=event_col)
        
        # Calculate concordance index
        c_index = concordance_index(cox_data[duration_col], 
                                  -cph.predict_partial_hazard(cox_data), 
                                  cox_data[event_col])
        
        return {
            'coefficients': cph.summary.to_dict(),
            'concordance_index': c_index,
            'model': cph
        }
    
    def predict_treatment_response(self, df, treatment_col, response_col, patient_features):
        """
        Predict treatment response based on patient characteristics
        """
        # Group by treatment type
        treatment_groups = df.groupby(treatment_col)
        
        predictions = {}
        for treatment, group_data in treatment_groups:
            if len(group_data) > 10:  # Minimum samples for reliable prediction
                X = group_data[patient_features]
                y = group_data[response_col]
                
                # Train model for this treatment
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                
                # Evaluate
                metrics = self.evaluate_model(model, X_test, y_test)
                
                predictions[treatment] = {
                    'model': model,
                    'metrics': metrics,
                    'feature_importance': self.get_feature_importance(model, patient_features)
                }
        
        return predictions
    
    def cross_validate_model(self, X, y, model_type='random_forest', cv_folds=5):
        """
        Perform cross-validation on the model
        """
        model = self.models[model_type]
        scores = cross_val_score(model, X, y, cv=cv_folds, scoring='accuracy')
        
        return {
            'cv_scores': scores.tolist(),
            'mean_score': scores.mean(),
            'std_score': scores.std()
        }
    
    def save_model(self, model, filepath):
        """
        Save trained model to file
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(model, filepath)
        return filepath
    
    def load_model(self, filepath):
        """
        Load trained model from file
        """
        return joblib.load(filepath)


class CancerDataAnalyzer:
    """
    High-level analyzer for cancer datasets
    """
    
    def __init__(self):
        self.pipeline = CancerMLPipeline()
    
    def analyze_breast_cancer(self, df):
        """
        Specialized analysis for breast cancer data
        """
        results = {}
        
        # Common breast cancer features
        clinical_features = ['age', 'tumor_size', 'lymph_nodes', 'grade']
        genetic_features = ['er_status', 'pr_status', 'her2_status']
        
        # Survival analysis if data available
        if 'survival_time' in df.columns and 'death_event' in df.columns:
            survival_data, kmf = self.pipeline.survival_analysis(df, 'survival_time', 'death_event')
            results['survival_analysis'] = survival_data
        
        # Treatment response prediction
        if 'treatment' in df.columns and 'response' in df.columns:
            available_features = [f for f in clinical_features + genetic_features if f in df.columns]
            treatment_predictions = self.pipeline.predict_treatment_response(
                df, 'treatment', 'response', available_features
            )
            results['treatment_response'] = treatment_predictions
        
        return results
    
    def analyze_lung_cancer(self, df):
        """
        Specialized analysis for lung cancer data
        """
        results = {}
        
        # Lung cancer specific features
        clinical_features = ['age', 'smoking_history', 'stage', 'histology']
        molecular_features = ['egfr_mutation', 'kras_mutation', 'alk_fusion']
        
        # Staging prediction
        if 'stage' in df.columns:
            available_features = [f for f in df.columns if f != 'stage']
            X_train, X_test, y_train, y_test, feature_names = self.pipeline.preprocess_data(
                df, 'stage'
            )
            
            model = self.pipeline.train_classification_model(X_train, y_train, 'random_forest')
            metrics = self.pipeline.evaluate_model(model, X_test, y_test)
            
            results['stage_prediction'] = {
                'metrics': metrics,
                'feature_importance': self.pipeline.get_feature_importance(model, feature_names)
            }
        
        return results
    
    def generate_insights(self, analysis_results):
        """
        Generate clinical insights from analysis results
        """
        insights = []
        
        # Survival analysis insights
        if 'survival_analysis' in analysis_results:
            survival_data = analysis_results['survival_analysis']
            median_survival = survival_data.get('median_survival')
            if median_survival:
                insights.append(f"Median survival time is {median_survival:.1f} months")
        
        # Feature importance insights
        for analysis_type, result in analysis_results.items():
            if 'feature_importance' in result:
                top_features = result['feature_importance'][:3]
                feature_text = ", ".join([f[0] for f in top_features])
                insights.append(f"Most important features for {analysis_type}: {feature_text}")
        
        return insights