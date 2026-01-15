from database import SessionLocal, UserSession
from datetime import datetime, timedelta
from sqlalchemy import func

class SessionTracker:
    """Track user sessions and journey stages using PostgreSQL"""
    
    STAGE_INITIAL = 'initial_form'
    STAGE_RESULTS = 'viewing_results'
    STAGE_PIX_MODAL = 'pix_modal'
    
    def create_or_update_session(self, session_id, stage, utm_source=None, ip_address=None, plate=None):
        """Create or update user session in database"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
            now = datetime.utcnow()
            
            if not session:
                # New session
                session = UserSession(
                    session_id=session_id,
                    created_at=now,
                    utm_source=utm_source or 'direct',
                    ip_address=ip_address,
                    current_stage=stage,
                    stages=[{'stage': stage, 'timestamp': now.isoformat()}]
                )
                db.add(session)
            else:
                # Update existing session
                session.last_active = now
                session.current_stage = stage
                
                if plate:
                    session.plate = plate
                
                # Add stage to history if not already there
                stages = session.stages or []
                if not stages or stages[-1]['stage'] != stage:
                    stages.append({
                        'stage': stage,
                        'timestamp': now.isoformat()
                    })
                    session.stages = stages
            
            db.commit()
        except Exception as e:
            print(f"Error updating session: {e}")
            db.rollback()
        finally:
            db.close()
    
    def mark_pix_copied(self, session_id):
        """Mark that user copied PIX code"""
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
            if session:
                session.pix_copied = True
                session.pix_copied_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            print(f"Error marking PIX copied: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_online_users(self, minutes=5):
        """Get users active in last N minutes"""
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)
            sessions = db.query(UserSession)\
                .filter(UserSession.last_active >= cutoff)\
                .all()
            
            return [{
                'session_id': s.session_id,
                'ip': s.ip_address or 'Unknown',
                'current_stage': s.current_stage or 'unknown',
                'utm_source': s.utm_source or 'direct',
                'last_active': s.last_active.isoformat() if s.last_active else '',
                'plate': s.plate or '-',
                'pix_copied': s.pix_copied or False
            } for s in sessions]
        finally:
            db.close()
    
    def get_stats(self):
        """Get session statistics"""
        db = SessionLocal()
        try:
            total_sessions = db.query(UserSession).count()
            online_count = len(self.get_online_users())
            
            # Count by stage
            stage_counts = {
                self.STAGE_INITIAL: db.query(UserSession).filter(UserSession.current_stage == self.STAGE_INITIAL).count(),
                self.STAGE_RESULTS: db.query(UserSession).filter(UserSession.current_stage == self.STAGE_RESULTS).count(),
                self.STAGE_PIX_MODAL: db.query(UserSession).filter(UserSession.current_stage == self.STAGE_PIX_MODAL).count()
            }
            
            pix_copied_count = db.query(UserSession).filter(UserSession.pix_copied == True).count()
            
            # Count by UTM source
            utm_results = db.query(UserSession.utm_source, func.count(UserSession.id))\
                .group_by(UserSession.utm_source)\
                .all()
            utm_sources = {utm: count for utm, count in utm_results}
            
            return {
                'total_sessions': total_sessions,
                'online_now': online_count,
                'stage_counts': stage_counts,
                'pix_copied_count': pix_copied_count,
                'utm_sources': utm_sources
            }
        finally:
            db.close()
    
    def cleanup_old_sessions(self, days=7):
        """Remove sessions older than N days"""
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = db.query(UserSession)\
                .filter(UserSession.last_active < cutoff)\
                .delete()
            db.commit()
            return deleted
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            db.rollback()
            return 0
        finally:
            db.close()

# Global tracker instance
tracker = SessionTracker()
