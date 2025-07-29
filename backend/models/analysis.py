"""
Analysis and AnalysisResult models for storing ML analysis data
"""

from datetime import datetime
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import db

class Analysis(db.Model):
    """Analysis model for storing cancer data analysis sessions"""
    
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    analysis_type = db.Column(db.String(50), nullable=False)  # survival, prediction, classification
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, running, completed, failed
    
    # Analysis parameters
    target_variable = db.Column(db.String(100))  # What we're trying to predict
    features = db.Column(db.Text)  # JSON list of features used
    model_type = db.Column(db.String(50))  # logistic_regression, random_forest, neural_network, etc.
    hyperparameters = db.Column(db.Text)  # JSON string of model hyperparameters
    
    # Results summary
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    auc_score = db.Column(db.Float)
    
    # Execution details
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime)
    execution_time = db.Column(db.Integer)  # in seconds
    error_message = db.Column(db.Text)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('ml_models.id'))
    
    # Relationships
    results = db.relationship('AnalysisResult', backref='analysis', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, analysis_type, target_variable, user_id, dataset_id, description=None):
        self.name = name
        self.analysis_type = analysis_type
        self.target_variable = target_variable
        self.user_id = user_id
        self.dataset_id = dataset_id
        self.description = description
    
    def set_features(self, features_list):
        """Set features as JSON"""
        self.features = json.dumps(features_list)
    
    def get_features(self):
        """Get features from JSON"""
        if self.features:
            return json.loads(self.features)
        return []
    
    def set_hyperparameters(self, params_dict):
        """Set hyperparameters as JSON"""
        self.hyperparameters = json.dumps(params_dict)
    
    def get_hyperparameters(self):
        """Get hyperparameters from JSON"""
        if self.hyperparameters:
            return json.loads(self.hyperparameters)
        return {}
    
    def start_analysis(self):
        """Mark analysis as started"""
        self.status = 'running'
        self.start_time = datetime.utcnow()
        db.session.commit()
    
    def complete_analysis(self, metrics):
        """Mark analysis as completed with results"""
        self.status = 'completed'
        self.end_time = datetime.utcnow()
        self.execution_time = int((self.end_time - self.start_time).total_seconds())
        
        # Update metrics
        self.accuracy = metrics.get('accuracy')
        self.precision = metrics.get('precision')
        self.recall = metrics.get('recall')
        self.f1_score = metrics.get('f1_score')
        self.auc_score = metrics.get('auc_score')
        
        db.session.commit()
    
    def fail_analysis(self, error_message):
        """Mark analysis as failed"""
        self.status = 'failed'
        self.end_time = datetime.utcnow()
        self.error_message = error_message
        db.session.commit()
    
    @property
    def duration_minutes(self):
        """Return execution time in minutes"""
        if self.execution_time:
            return round(self.execution_time / 60, 2)
        return None
    
    def to_dict(self):
        """Convert analysis object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'analysis_type': self.analysis_type,
            'status': self.status,
            'target_variable': self.target_variable,
            'features': self.get_features(),
            'model_type': self.model_type,
            'hyperparameters': self.get_hyperparameters(),
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'auc_score': self.auc_score,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time': self.execution_time,
            'duration_minutes': self.duration_minutes,
            'error_message': self.error_message,
            'user_id': self.user_id,
            'dataset_id': self.dataset_id,
            'model_id': self.model_id
        }
    
    def __repr__(self):
        return f'<Analysis {self.name} ({self.analysis_type})>'


class AnalysisResult(db.Model):
    """Detailed results from analysis including predictions and visualizations"""
    
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.Integer, primary_key=True)
    result_type = db.Column(db.String(50), nullable=False)  # prediction, visualization, report
    result_data = db.Column(db.Text, nullable=False)  # JSON data
    file_path = db.Column(db.String(500))  # Path to saved files (plots, reports)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Foreign key
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'), nullable=False)
    
    def __init__(self, result_type, result_data, analysis_id, file_path=None):
        self.result_type = result_type
        self.result_data = result_data if isinstance(result_data, str) else json.dumps(result_data)
        self.analysis_id = analysis_id
        self.file_path = file_path
    
    def get_result_data(self):
        """Get result data from JSON"""
        if self.result_data:
            return json.loads(self.result_data)
        return {}
    
    def set_result_data(self, data):
        """Set result data as JSON"""
        self.result_data = json.dumps(data)
    
    def to_dict(self):
        """Convert result object to dictionary"""
        return {
            'id': self.id,
            'result_type': self.result_type,
            'result_data': self.get_result_data(),
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'analysis_id': self.analysis_id
        }
    
    def __repr__(self):
        return f'<AnalysisResult {self.result_type} for Analysis {self.analysis_id}>'