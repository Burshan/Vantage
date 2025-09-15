# models.py - מתוקן
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50), default='user', nullable=False)  # 'user', 'admin', 'super_admin'
    is_admin = Column(Boolean, default=False, nullable=False)
    tokens_remaining = Column(Integer, default=5)
    total_tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships - תוקן לטבלאות הקיימות
    areas_of_interest = relationship("AreaOfInterest", back_populates="user", cascade="all, delete-orphan")
    analysis_history = relationship("AnalysisHistory", back_populates="user", cascade="all, delete-orphan") 
    user_activity = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    token_transactions = relationship("TokenTransaction", back_populates="user", foreign_keys="[TokenTransaction.user_id]", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'clerk_user_id': self.clerk_user_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_admin': self.is_admin,
            'tokens_remaining': self.tokens_remaining,
            'total_tokens_used': self.total_tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = {
            'user': ['view_own_data', 'create_aoi', 'run_analysis'],
            'admin': ['view_own_data', 'create_aoi', 'run_analysis', 'view_all_users', 'manage_tokens', 'view_analytics'],
            'super_admin': ['*']  # All permissions
        }
        
        user_permissions = permissions.get(self.role, [])
        return permission in user_permissions or '*' in user_permissions

class AreaOfInterest(Base):
    __tablename__ = 'areas_of_interest'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    location_name = Column(String(255))
    bbox_coordinates = Column(JSON, nullable=False)
    classification = Column(String(50), default='CONFIDENTIAL')
    priority = Column(String(20), default='MEDIUM')
    color_code = Column(String(7), default='#3B82F6')
    monitoring_frequency = Column(String(20), default='WEEKLY')
    is_active = Column(Boolean, default=True, index=True)
    next_run_at = Column(DateTime, nullable=True, index=True)  # For scheduled monitoring
    
    # Add baseline-related fields
    baseline_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    baseline_date = Column(DateTime, nullable=True)
    baseline_image_filename = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="areas_of_interest")
    analysis_history = relationship("AnalysisHistory", back_populates="aoi", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'location_name': self.location_name,
            'bbox_coordinates': self.bbox_coordinates,
            'classification': self.classification,
            'priority': self.priority,
            'color_code': self.color_code,
            'monitoring_frequency': self.monitoring_frequency,
            'is_active': self.is_active,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'baseline_status': self.baseline_status,
            'baseline_date': self.baseline_date.isoformat() if self.baseline_date else None,
            'baseline_image_filename': self.baseline_image_filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
# תוקן - שימוש בטבלה הקיימת
class AnalysisHistory(Base):
    __tablename__ = 'analysis_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    aoi_id = Column(Integer, ForeignKey('areas_of_interest.id'), nullable=True, index=True)
    process_id = Column(String(50), nullable=False, unique=True)
    operation_name = Column(String(255))
    location_description = Column(Text)
    bbox_coordinates = Column(JSON)
    analysis_timestamp = Column(DateTime, default=func.now(), index=True)
    image1_filename = Column(String(255))
    image2_filename = Column(String(255))
    heatmap_filename = Column(String(255))
    
    # S3 storage keys for satellite images
    image1_s3_key = Column(String(512))
    image2_s3_key = Column(String(512))
    heatmap_s3_key = Column(String(512))
    status = Column(String(50), default='completed')
    tokens_used = Column(Integer, default=1)
    change_percentage = Column(Float, nullable=True)  # Add this field
    meta = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="analysis_history")
    aoi = relationship("AreaOfInterest", back_populates="analysis_history")
    
    def get_image_url(self, image_type: str) -> str:
        """
        Get the appropriate image URL (S3 signed URL or local file URL)
        
        Args:
            image_type: 'image1', 'image2', or 'heatmap'
        """
        s3_key = getattr(self, f"{image_type}_s3_key", None)
        filename = getattr(self, f"{image_type}_filename", None)
        
        # Prefer S3 if available
        if s3_key:
            try:
                from services.s3_service import s3_service
                if s3_service and s3_service.enabled:
                    signed_url = s3_service.generate_signed_url(s3_key)
                    if signed_url:
                        return signed_url
            except ImportError:
                pass
        
        # Fall back to local file API endpoint
        if filename:
            return f"/api/image/{filename}"
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'aoi_id': self.aoi_id,
            'process_id': self.process_id,
            'operation_name': self.operation_name,
            'location_description': self.location_description,
            'bbox_coordinates': self.bbox_coordinates,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            'change_percentage': self.change_percentage,
            
            # Legacy filename fields (kept for backward compatibility)
            'image1_filename': self.image1_filename,
            'image2_filename': self.image2_filename,
            'heatmap_filename': self.heatmap_filename,
            
            # S3 keys
            'image1_s3_key': self.image1_s3_key,
            'image2_s3_key': self.image2_s3_key,
            'heatmap_s3_key': self.heatmap_s3_key,
            
            # Generated URLs (prefer S3 signed URLs)
            'image1_url': self.get_image_url('image1'),
            'image2_url': self.get_image_url('image2'),
            'heatmap_url': self.get_image_url('heatmap'),
            
            'status': self.status,
            'tokens_used': self.tokens_used,
            'meta': self.meta,
            'aoi': self.aoi.to_dict() if self.aoi else None
        }

class UserActivity(Base):
    __tablename__ = 'user_activity'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False)
    activity_data = Column(JSON)
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="user_activity")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_type': self.activity_type,
            'activity_data': self.activity_data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class TokenTransaction(Base):
    __tablename__ = 'token_transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # 'purchase', 'admin_grant', 'usage', 'refund'
    amount = Column(Integer, nullable=False)  # positive for credits, negative for debits
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    
    # Payment/Source tracking (ready for Stripe)
    payment_intent_id = Column(String(255), nullable=True, index=True)  # Stripe payment intent
    stripe_charge_id = Column(String(255), nullable=True, index=True)   # Stripe charge
    stripe_invoice_id = Column(String(255), nullable=True, index=True)  # For subscriptions
    
    # Admin/Manual tracking
    admin_user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    admin_note = Column(Text, nullable=True)
    
    # Transaction metadata
    price_per_token = Column(Float, nullable=True)  # USD per token (for purchases)
    total_amount_usd = Column(Float, nullable=True)  # Total transaction amount in USD
    currency = Column(String(3), default='USD')
    
    # Status and metadata
    status = Column(String(50), default='completed')  # 'pending', 'completed', 'failed', 'refunded'
    reference_id = Column(String(255), nullable=True, index=True)  # External reference
    metad = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="token_transactions", foreign_keys=[user_id])
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'balance_before': self.balance_before,
            'balance_after': self.balance_after,
            'payment_intent_id': self.payment_intent_id,
            'stripe_charge_id': self.stripe_charge_id,
            'admin_user_id': self.admin_user_id,
            'admin_note': self.admin_note,
            'price_per_token': self.price_per_token,
            'total_amount_usd': self.total_amount_usd,
            'currency': self.currency,
            'status': self.status,
            'reference_id': self.reference_id,
            'metadata': self.metad,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
