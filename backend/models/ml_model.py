"""
MLModel model for storing trained machine learning models
"""

from datetime import datetime
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import db

class MLModel(db.Model):
    """Model for storing trained machine learning models"""
    
    __tablename__ = 'ml_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    model_type = db.Column(db.String(50), nullable=False)  # logistic_regression, random_forest, neural_network, etc.
    cancer_type = db.Column(db.String(50), nullable=False)  # breast, lung, colorectal, etc.
    target_variable = db.Column(db.String(100), nullable=False)  # What the model predicts
    
    # Model performance metrics
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    auc_score = db.Column(db.Float)
    
    # Training details
    training_samples = db.Column(db.Integer)
    features_used = db.Column(db.Text)  # JSON list of features
    hyperparameters = db.Column(db.Text)  # JSON string of hyperparameters
    cross_validation_scores = db.Column(db.Text)  # JSON array of CV scores
    
    # File storage
    model_file_path = db.Column(db.String(500), nullable=False)  # Path to saved model file
    feature_importance_path = db.Column(db.String(500))  # Path to feature importance plot
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_validated = db.Column(db.Boolean, default=False, nullable=False)
    version = db.Column(db.String(20), default='1.0', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    
    # Relationships
    analyses = db.relationship('Analysis', backref='ml_model', lazy=True)
    
    def __init__(self, name, model_type, cancer_type, target_variable, model_file_path, user_id, dataset_id, description=None):
        self.name = name
        self.model_type = model_type
        self.cancer_type = cancer_type
        self.target_variable = target_variable
        self.model_file_path = model_file_path
        self.user_id = user_id
        self.dataset_id = dataset_id
        self.description = description
    
    def set_features_used(self, features_list):
        """Set features used as JSON"""
        self.features_used = json.dumps(features_list)
    
    def get_features_used(self):
        """Get features used from JSON"""
        if self.features_used:
            return json.loads(self.features_used)
        return []
    
    def set_hyperparameters(self, params_dict):
        """Set hyperparameters as JSON"""
        self.hyperparameters = json.dumps(params_dict)
    
    def get_hyperparameters(self):
        """Get hyperparameters from JSON"""
        if self.hyperparameters:
            return json.loads(self.hyperparameters)
        return {}
    
    def set_cv_scores(self, scores_list):
        """Set cross-validation scores as JSON"""
        self.cross_validation_scores = json.dumps(scores_list)
    
    def get_cv_scores(self):
        """Get cross-validation scores from JSON"""
        if self.cross_validation_scores:
            return json.loads(self.cross_validation_scores)
        return []
    
    def update_performance_metrics(self, metrics):
        """Update model performance metrics"""
        self.accuracy = metrics.get('accuracy')
        self.precision = metrics.get('precision')
        self.recall = metrics.get('recall')
        self.f1_score = metrics.get('f1_score')
        self.auc_score = metrics.get('auc_score')
        db.session.commit()
    
    def update_last_used(self):
        """Update the last used timestamp"""
        self.last_used = datetime.utcnow()
        db.session.commit()
    
    def validate_model(self):
        """Mark model as validated"""
        self.is_validated = True
        db.session.commit()
    
    def deactivate(self):
        """Deactivate the model"""
        self.is_active = False
        db.session.commit()
    
    @property
    def mean_cv_score(self):
        """Return mean cross-validation score"""
        cv_scores = self.get_cv_scores()
        if cv_scores:
            return sum(cv_scores) / len(cv_scores)
        return None
    
    @property
    def days_since_created(self):
        """Return days since model was created"""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return None
    
    def to_dict(self):
        """Convert model object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'model_type': self.model_type,
            'cancer_type': self.cancer_type,
            'target_variable': self.target_variable,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'auc_score': self.auc_score,
            'training_samples': self.training_samples,
            'features_used': self.get_features_used(),
            'hyperparameters': self.get_hyperparameters(),
            'cross_validation_scores': self.get_cv_scores(),
            'mean_cv_score': self.mean_cv_score,
            'model_file_path': self.model_file_path,
            'feature_importance_path': self.feature_importance_path,
            'is_active': self.is_active,
            'is_validated': self.is_validated,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'days_since_created': self.days_since_created,
            'user_id': self.user_id,
            'dataset_id': self.dataset_id
        }
    
    def __repr__(self):
        return f'<MLModel {self.name} ({self.model_type})>'