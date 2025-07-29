"""
Dataset model for storing uploaded cancer datasets
"""

from datetime import datetime
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import db

class Dataset(db.Model):
    """Dataset model for storing uploaded cancer datasets"""
    
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    cancer_type = db.Column(db.String(50), nullable=False)  # breast, lung, colorectal, etc.
    data_type = db.Column(db.String(50), nullable=False)  # clinical, genetic, imaging
    file_path = db.Column(db.String(500), nullable=False)
    processed_file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    file_format = db.Column(db.String(10), nullable=False)  # csv, json, xlsx
    
    # Data characteristics
    num_rows = db.Column(db.Integer)
    num_columns = db.Column(db.Integer)
    column_info = db.Column(db.Text)  # JSON string containing column metadata
    data_quality_score = db.Column(db.Float)  # 0-1 score for data quality
    missing_data_percentage = db.Column(db.Float)
    
    # Privacy and security
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    is_processed = db.Column(db.Boolean, default=False, nullable=False)
    is_validated = db.Column(db.Boolean, default=False, nullable=False)
    
    # Metadata
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    analyses = db.relationship('Analysis', backref='dataset', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, cancer_type, data_type, file_path, file_size, file_format, user_id, description=None):
        self.name = name
        self.cancer_type = cancer_type
        self.data_type = data_type
        self.file_path = file_path
        self.file_size = file_size
        self.file_format = file_format
        self.user_id = user_id
        self.description = description
    
    def set_column_info(self, column_data):
        """Set column information as JSON"""
        self.column_info = json.dumps(column_data)
    
    def get_column_info(self):
        """Get column information from JSON"""
        if self.column_info:
            return json.loads(self.column_info)
        return {}
    
    def update_data_stats(self, num_rows, num_columns, missing_percentage, quality_score=None):
        """Update dataset statistics after processing"""
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.missing_data_percentage = missing_percentage
        if quality_score is not None:
            self.data_quality_score = quality_score
        self.last_modified = datetime.utcnow()
    
    def mark_as_processed(self, processed_file_path):
        """Mark dataset as processed and set processed file path"""
        self.is_processed = True
        self.processed_file_path = processed_file_path
        self.last_modified = datetime.utcnow()
    
    def validate_dataset(self):
        """Mark dataset as validated"""
        self.is_validated = True
        self.last_modified = datetime.utcnow()
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    def to_dict(self):
        """Convert dataset object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cancer_type': self.cancer_type,
            'data_type': self.data_type,
            'file_path': self.file_path,
            'processed_file_path': self.processed_file_path,
            'file_size': self.file_size,
            'file_size_mb': self.file_size_mb,
            'file_format': self.file_format,
            'num_rows': self.num_rows,
            'num_columns': self.num_columns,
            'column_info': self.get_column_info(),
            'data_quality_score': self.data_quality_score,
            'missing_data_percentage': self.missing_data_percentage,
            'is_public': self.is_public,
            'is_processed': self.is_processed,
            'is_validated': self.is_validated,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'user_id': self.user_id,
            'owner': self.owner.username if self.owner else None
        }
    
    def __repr__(self):
        return f'<Dataset {self.name} ({self.cancer_type})>'