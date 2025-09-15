from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from contextlib import contextmanager
import logging
from typing import Dict, List, Any, Optional, Tuple
import os
from config import Config

# Import models - חשוב!
from models import Base, User, AreaOfInterest, AnalysisHistory, UserActivity

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: str, engine_options: Dict = None):
        self.engine = create_engine(
            database_url,
            **(engine_options or {})
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        logger.info(f"Database initialized: {database_url.split('@')[0]}@[HIDDEN]")
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_or_create_user(self, clerk_user_id: str, email: str = None, 
                          first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """Get or create user"""
        with self.get_session() as session:
            logger.info(f"Looking for user with clerk_user_id: {clerk_user_id}")
            
            user = session.query(User).filter_by(clerk_user_id=clerk_user_id).first()
            
            if user:
                logger.info(f"Found existing user: ID={user.id}, tokens_remaining={user.tokens_remaining}")
                
                # Update user info if provided
                updated = False
                if email and user.email != email:
                    user.email = email
                    updated = True
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    updated = True
                
                if updated:
                    user.updated_at = func.now()
                    session.commit()  # FIX: Commit the updates to database
                    logger.info("✅ Updated and committed user information to database")
                
                return user.to_dict()
            
            # Create new user
            logger.info("Creating new user with 5 tokens")
            user = User(
                clerk_user_id=clerk_user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='user',  # Default role
                is_admin=False,  # Default admin status
                tokens_remaining=5,
                total_tokens_used=0
            )
            session.add(user)
            session.flush()  # Get the ID
            
            # Log user creation activity
            activity = UserActivity(
                user_id=user.id,
                activity_type='user_created',
                activity_data={'clerk_user_id': clerk_user_id, 'email': email, 'initial_tokens': 5}
            )
            session.add(activity)
            
            logger.info(f"Created user with ID: {user.id}, tokens: 5")
            return user.to_dict()
    
    def use_token(self, user_id: int, tokens_to_use: int = 1, reference_id: str = None) -> Tuple[bool, str]:
        """Use tokens for analysis with transaction tracking"""
        result = self.update_token_usage_with_transaction(user_id, tokens_to_use, reference_id)
        return result['success'], result['message']
    
    def use_tokens(self, user_id: int, tokens_to_use: int = 1, reference_id: str = None) -> Tuple[bool, str]:
        """Use tokens for analysis with transaction tracking (alias for use_token)"""
        result = self.update_token_usage_with_transaction(user_id, tokens_to_use, reference_id)
        return result['success'], result['message']
    
    def create_aoi(self, user_id: int, aoi_data: Dict) -> int:
        """Create Area of Interest"""
        with self.get_session() as session:
            logger.info(f"Creating AOI for user {user_id}: {aoi_data['name']}")
            
            aoi = AreaOfInterest(
                user_id=user_id,
                name=aoi_data['name'],
                description=aoi_data.get('description', ''),
                location_name=aoi_data.get('location_name', ''),
                bbox_coordinates=aoi_data['bbox_coordinates'],
                classification=aoi_data.get('classification', 'CONFIDENTIAL'),
                priority=aoi_data.get('priority', 'MEDIUM'),
                color_code=aoi_data.get('color_code', '#3B82F6'),
                monitoring_frequency=aoi_data.get('monitoring_frequency', 'WEEKLY')
            )
            session.add(aoi)
            session.flush()  # Get the ID
            
            # Log activity
            activity = UserActivity(
                user_id=user_id,
                activity_type='aoi_created',
                activity_data={'aoi_id': aoi.id, 'aoi_name': aoi.name}
            )
            session.add(activity)
            
            logger.info(f"AOI created with ID: {aoi.id}")
            return aoi.id
    
    def get_user_aois(self, user_id: int) -> List[Dict]:
        """Get all active AOIs for a user"""
        with self.get_session() as session:
            aois = session.query(AreaOfInterest).filter_by(
                user_id=user_id, 
                is_active=True
            ).order_by(AreaOfInterest.created_at.desc()).all()
            
            return [aoi.to_dict() for aoi in aois]
    
    def delete_aoi(self, user_id: int, aoi_id: int) -> Tuple[bool, str]:
        """Soft delete an AOI"""
        with self.get_session() as session:
            aoi = session.query(AreaOfInterest).filter_by(
                id=aoi_id, 
                user_id=user_id
            ).first()
            
            if not aoi:
                return False, "AOI not found or access denied"
            
            aoi_name = aoi.name
            aoi.is_active = False
            aoi.updated_at = func.now()
            
            # Log activity
            activity = UserActivity(
                user_id=user_id,
                activity_type='aoi_deleted',
                activity_data={'aoi_id': aoi_id, 'aoi_name': aoi_name}
            )
            session.add(activity)
            
            logger.info(f"AOI {aoi_id} ({aoi_name}) marked as inactive")
            return True, "AOI deleted successfully"
    
    # Update the save_analysis method signature
    def save_analysis(self, user_id: int, aoi_id: Optional[int], process_id: str, 
                 operation_name: str, location_description: str, bbox_coordinates: List,
                 image_filenames: Dict, meta: Dict, change_percentage: float = None, 
                 tokens_used: int = 1, s3_keys: Dict = None) -> int:
        """Save analysis results to database"""
        with self.get_session() as session:
            # Extract S3 keys if provided
            s3_keys = s3_keys or {}
            
            analysis = AnalysisHistory(
                user_id=user_id,
                aoi_id=aoi_id,
                process_id=process_id,
                operation_name=operation_name,
                location_description=location_description,
                bbox_coordinates=bbox_coordinates,
                image1_filename=image_filenames.get('image1'),
                image2_filename=image_filenames.get('image2'),
                heatmap_filename=image_filenames.get('heatmap'),
                # S3 keys
                image1_s3_key=s3_keys.get('image1'),
                image2_s3_key=s3_keys.get('image2'),
                heatmap_s3_key=s3_keys.get('heatmap'),
                tokens_used=tokens_used,
                change_percentage=change_percentage,
                meta=meta
            )
            session.add(analysis)
            session.flush()
            
            # Log activity
            activity = UserActivity(
                user_id=user_id,
                activity_type='analysis_completed',
                activity_data={
                    'analysis_id': analysis.id,
                    'process_id': process_id,
                    'aoi_id': aoi_id,
                    'location': location_description,
                    'tokens_used': tokens_used,
                    'change_percentage': change_percentage
                }
            )
            session.add(activity)
            
            logger.info(f"Analysis saved with ID: {analysis.id}")
            return analysis.id

    def create_baseline_image(self, aoi_id: int, satellite_processor):
        """Create baseline image for AOI"""
        with self.get_session() as session:
            aoi = session.query(AreaOfInterest).filter_by(id=aoi_id).first()
            if not aoi:
                logger.error(f"AOI {aoi_id} not found for baseline creation")
                return False
            
            # Update status to processing
            aoi.baseline_status = 'processing'
            session.commit()
            
            try:
                # Use new date strategy for baseline creation
                from utils.date_strategy import SatelliteDateStrategy
                baseline_dates = SatelliteDateStrategy.get_aoi_creation_dates()
                date_from = baseline_dates['baseline_from']
                date_to = baseline_dates['baseline_to']
                baseline_date = datetime.strptime(baseline_dates['baseline_center'], "%Y-%m-%d")
                
                # Download baseline image
                baseline_image = satellite_processor.download_image(
                    bbox=aoi.bbox_coordinates,
                    date_from=date_from,
                    date_to=date_to
                )
                
                if baseline_image:
                    # Save baseline image
                    baseline_filename = f"baseline_aoi_{aoi_id}_{int(baseline_date.timestamp())}.jpg"
                    baseline_path = os.path.join(Config.IMAGES_DIR, baseline_filename)
                    baseline_image.save(baseline_path, 'JPEG', quality=95)
                    
                    # Update AOI with baseline info
                    aoi.baseline_status = 'completed'
                    aoi.baseline_date = baseline_date
                    aoi.baseline_image_filename = baseline_filename
                    
                    logger.info(f"Baseline created successfully for AOI {aoi_id}")
                    
                    # Log activity
                    activity = UserActivity(
                        user_id=aoi.user_id,
                        activity_type='baseline_created',
                        activity_data={'aoi_id': aoi_id, 'baseline_filename': baseline_filename}
                    )
                    session.add(activity)
                    
                    return True
                else:
                    aoi.baseline_status = 'failed'
                    logger.error(f"Failed to download baseline image for AOI {aoi_id}")
                    return False
                    
            except Exception as e:
                aoi.baseline_status = 'failed'
                logger.error(f"Error creating baseline for AOI {aoi_id}: {str(e)}")
                return False

    def get_aoi_dashboard(self, aoi_id: int, user_id: int) -> Optional[Dict]:
        """Get comprehensive AOI dashboard data"""
        with self.get_session() as session:
            aoi = session.query(AreaOfInterest).filter_by(
                id=aoi_id, 
                user_id=user_id
            ).first()
            
            if not aoi:
                return None
            
            # Get recent analyses
            recent_analyses = session.query(AnalysisHistory).filter_by(
                aoi_id=aoi_id
            ).order_by(AnalysisHistory.analysis_timestamp.desc()).limit(5).all()
            
            # Calculate statistics
            total_analyses = session.query(AnalysisHistory).filter_by(aoi_id=aoi_id).count()
            total_tokens_used = session.query(func.sum(AnalysisHistory.tokens_used)).filter_by(aoi_id=aoi_id).scalar() or 0
            
            return {
                'aoi': aoi.to_dict(),
                'recent_analyses': [analysis.to_dict() for analysis in recent_analyses],
                'statistics': {
                    'total_analyses': total_analyses,
                    'total_tokens_used': total_tokens_used,
                    'monitoring_status': 'active' if aoi.monitoring_frequency and aoi.is_active else 'inactive',
                    'baseline_status': aoi.baseline_status,
                    'baseline_date': aoi.baseline_date.isoformat() if aoi.baseline_date else None
                },
                'baseline': {
                    'status': aoi.baseline_status,
                    'date': aoi.baseline_date.isoformat() if aoi.baseline_date else None,
                    'image_url': f'/api/image/{aoi.baseline_image_filename}' if aoi.baseline_image_filename else None
                }
            }
    
    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's analysis history"""
        with self.get_session() as session:
            analyses = session.query(AnalysisHistory).filter_by(
                user_id=user_id
            ).order_by(AnalysisHistory.analysis_timestamp.desc()).limit(limit).all()
            
            result = []
            for analysis in analyses:
                analysis_dict = analysis.to_dict()
                # Add AOI info if exists
                if analysis.aoi:
                    analysis_dict['aoi'] = {
                        'name': analysis.aoi.name,
                        'location_name': analysis.aoi.location_name
                    }
                result.append(analysis_dict)
            
            return result
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            return user.to_dict() if user else None
    
    def log_activity(self, user_id: int, activity_type: str, activity_data: Dict, description: str = None):
        """Log user activity"""
        with self.get_session() as session:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data,
                description=description
            )
            session.add(activity)
            logger.debug(f"Logged activity: {activity_type} for user {user_id}")
    
    def get_aois_for_analysis(self) -> List[Dict]:
        """Get AOIs that need automatic analysis"""
        from datetime import datetime, timedelta
        
        with self.get_session() as session:
            # Get AOIs with monitoring enabled that are due for analysis
            current_time = datetime.utcnow()
            
            aois = session.query(AreaOfInterest).filter(
                AreaOfInterest.monitoring_frequency.isnot(None),
                AreaOfInterest.is_active == True,
                AreaOfInterest.baseline_status == 'completed',  # Only analyze AOIs with completed baselines
                # Check if it's time for analysis - respect monitoring frequency
                func.coalesce(AreaOfInterest.next_run_at, current_time - timedelta(days=1)) <= current_time
            ).all()
            
            result = []
            for aoi in aois:
                # Get user info for token checking
                user = session.query(User).filter_by(id=aoi.user_id).first()
                if user and user.tokens_remaining > 0:
                    result.append({
                        'aoi_id': aoi.id,
                        'user_db_id': aoi.user_id,
                        'name': aoi.name,
                        'location_name': aoi.location_name,
                        'bbox_coordinates': aoi.bbox_coordinates,
                        'monitoring_frequency': aoi.monitoring_frequency,
                        'analysis_type': 'baseline_comparison',
                        'user_tokens': user.tokens_remaining
                    })
            
            return result
    
    def update_aoi_analysis_date(self, aoi_id: int, increment_total: bool = False):
        """Update AOI analysis date and optionally increment analysis count"""
        from datetime import datetime, timedelta
        
        with self.get_session() as session:
            aoi = session.query(AreaOfInterest).filter_by(id=aoi_id).first()
            if aoi:
                # Set next analysis date based on frequency with minimum intervals
                if aoi.monitoring_frequency == 'daily':
                    aoi.next_run_at = datetime.utcnow() + timedelta(days=1)
                elif aoi.monitoring_frequency == 'weekly' or aoi.monitoring_frequency == 'WEEKLY':
                    aoi.next_run_at = datetime.utcnow() + timedelta(days=7)
                elif aoi.monitoring_frequency == 'monthly' or aoi.monitoring_frequency == 'MONTHLY':
                    aoi.next_run_at = datetime.utcnow() + timedelta(days=30)
                else:
                    # Default to weekly if frequency is unknown
                    aoi.next_run_at = datetime.utcnow() + timedelta(days=7)
                
                # Optionally increment analysis count (could add a field if needed)
                if increment_total:
                    logger.info(f"Analysis completed for AOI {aoi.name}")
                
                session.commit()
                logger.debug(f"Updated next analysis date for AOI {aoi_id} to {aoi.next_run_at}")
                
    def add_tokens_to_user(self, user_id: int, amount: int, transaction_type: str = 'admin_grant', 
                          admin_user_id: int = None, admin_note: str = None, 
                          payment_intent_id: str = None, price_per_token: float = None) -> Dict:
        """Add tokens to user account with full transaction tracking"""
        with self.get_session() as session:
            from models import User, TokenTransaction
            
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            balance_before = user.tokens_remaining
            user.tokens_remaining += amount
            balance_after = user.tokens_remaining
            
            # Create transaction record
            transaction = TokenTransaction(
                user_id=user_id,
                transaction_type=transaction_type,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                admin_user_id=admin_user_id,
                admin_note=admin_note,
                payment_intent_id=payment_intent_id,
                price_per_token=price_per_token,
                total_amount_usd=price_per_token * amount if price_per_token else None,
                status='completed'
            )
            session.add(transaction)
            session.flush()
            
            logger.info(f"Added {amount} tokens to user {user_id}: {balance_before} -> {balance_after}")
            
            return {
                'success': True,
                'message': f'Successfully added {amount} tokens',
                'user_id': user_id,
                'tokens_added': amount,
                'balance_before': balance_before,
                'balance_after': balance_after,
                'transaction_id': transaction.id
            }
    
    def get_user_token_transactions(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's token transaction history"""
        with self.get_session() as session:
            from models import TokenTransaction
            
            transactions = session.query(TokenTransaction)\
                .filter_by(user_id=user_id)\
                .order_by(TokenTransaction.created_at.desc())\
                .limit(limit).all()
            
            return [tx.to_dict() for tx in transactions]
    
    def get_all_token_transactions(self, limit: int = 100) -> List[Dict]:
        """Get all token transactions (admin view)"""
        with self.get_session() as session:
            from models import TokenTransaction, User
            
            transactions = session.query(TokenTransaction)\
                .join(User, TokenTransaction.user_id == User.id)\
                .order_by(TokenTransaction.created_at.desc())\
                .limit(limit).all()
            
            result = []
            for tx in transactions:
                tx_dict = tx.to_dict()
                tx_dict['user_email'] = tx.user.email
                result.append(tx_dict)
            
            return result
            
    def update_token_usage_with_transaction(self, user_id: int, tokens_used: int, reference_id: str = None) -> Dict:
        """Record token usage with transaction tracking (for AOI creation, etc.)"""
        with self.get_session() as session:
            from models import User, TokenTransaction
            
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            if user.tokens_remaining < tokens_used:
                return {'success': False, 'message': 'Insufficient tokens'}
            
            balance_before = user.tokens_remaining
            user.tokens_remaining -= tokens_used
            user.total_tokens_used += tokens_used
            balance_after = user.tokens_remaining
            
            # Create usage transaction record
            transaction = TokenTransaction(
                user_id=user_id,
                transaction_type='usage',
                amount=-tokens_used,  # negative for usage
                balance_before=balance_before,
                balance_after=balance_after,
                reference_id=reference_id,
                status='completed'
            )
            session.add(transaction)
            session.flush()
            
            logger.info(f"Recorded {tokens_used} token usage for user {user_id}: {balance_before} -> {balance_after}")
            
            return {
                'success': True,
                'message': f'Used {tokens_used} tokens',
                'user_id': user_id,
                'tokens_used': tokens_used,
                'balance_before': balance_before,
                'balance_after': balance_after,
                'transaction_id': transaction.id
            }
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        with self.get_session() as session:
            user = session.query(User).filter_by(email=email).first()
            return user.to_dict() if user else None
    
    def list_all_users(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all users with pagination"""
        with self.get_session() as session:
            users = session.query(User)\
                .order_by(User.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return [user.to_dict() for user in users]
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        with self.get_session() as session:
            return session.query(User).count()
    
    def get_admin_stats(self) -> Dict[str, Any]:
        """Get comprehensive admin statistics"""
        with self.get_session() as session:
            from datetime import datetime, timedelta
            
            # Basic counts
            total_users = session.query(User).count()
            admin_users = session.query(User).filter(
                (User.is_admin == True) | (User.role.in_(['admin', 'super_admin']))
            ).count()
            
            total_aois = session.query(AreaOfInterest).count()
            active_aois = session.query(AreaOfInterest).filter_by(is_active=True).count()
            
            total_analyses = session.query(AnalysisHistory).count()
            
            # Token usage statistics
            total_tokens_used = session.query(func.sum(User.total_tokens_used)).scalar() or 0
            total_tokens_remaining = session.query(func.sum(User.tokens_remaining)).scalar() or 0
            
            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_users = session.query(User).filter(User.created_at >= week_ago).count()
            recent_analyses = session.query(AnalysisHistory).filter(
                AnalysisHistory.created_at >= week_ago
            ).count()
            recent_aois = session.query(AreaOfInterest).filter(
                AreaOfInterest.created_at >= week_ago
            ).count()
            
            return {
                'users': {
                    'total': total_users,
                    'admins': admin_users,
                    'recent_7_days': recent_users
                },
                'aois': {
                    'total': total_aois,
                    'active': active_aois,
                    'recent_7_days': recent_aois
                },
                'analyses': {
                    'total': total_analyses,
                    'recent_7_days': recent_analyses
                },
                'tokens': {
                    'total_used': total_tokens_used,
                    'total_remaining': total_tokens_remaining
                },
                'system': {
                    'timestamp': datetime.now().isoformat(),
                    'status': 'operational'
                }
            }
    
    def get_all_users_paginated(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get paginated list of all users for admin panel"""
        with self.get_session() as session:
            offset = (page - 1) * per_page
            
            users_query = session.query(User).order_by(User.created_at.desc())
            total_users = users_query.count()
            users = users_query.offset(offset).limit(per_page).all()
            
            return {
                'users': [user.to_dict() for user in users],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_users,
                    'pages': (total_users + per_page - 1) // per_page,
                    'has_next': offset + per_page < total_users,
                    'has_prev': page > 1
                }
            }