import json
import os
from datetime import datetime, timedelta

USER_SESSIONS_FILE = 'admin_data/user_sessions.json'

class SessionTracker:
    """Track user sessions and journey stages"""
    
    STAGE_INITIAL = 'initial_form'
    STAGE_RESULTS = 'viewing_results'
    STAGE_PIX_MODAL = 'pix_modal'
    
    def __init__(self):
        os.makedirs('admin_data', exist_ok=True)
        self.sessions = self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from file"""
        if os.path.exists(USER_SESSIONS_FILE):
            with open(USER_SESSIONS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        with open(USER_SESSIONS_FILE, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    def create_or_update_session(self, session_id, stage, utm_source=None, ip_address=None, plate=None, city=None, state=None):
        """Create or update user session"""
        now = datetime.now().isoformat()
        
        if session_id not in self.sessions:
            # New session
            self.sessions[session_id] = {
                'created_at': now,
                'utm_source': utm_source or 'direct',
                'ip_address': ip_address,
                'city': city,
                'state': state,
                'stages': []
            }
        
        # Update session
        session = self.sessions[session_id]
        session['last_active'] = now
        session['current_stage'] = stage
        
        # Update location if provided
        if city:
            session['city'] = city
        if state:
            session['state'] = state
        
        if plate:
            session['plate'] = plate
        
        # Add stage to history if not already there
        if not session['stages'] or session['stages'][-1]['stage'] != stage:
            session['stages'].append({
                'stage': stage,
                'timestamp': now
            })
        
        self._save_sessions()
    
    def mark_pix_copied(self, session_id):
        """Mark that user copied PIX code"""
        if session_id in self.sessions:
            self.sessions[session_id]['pix_copied'] = True
            self.sessions[session_id]['pix_copied_at'] = datetime.now().isoformat()
            self._save_sessions()
    
    def get_online_users(self, minutes=5):
        """Get users active in last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        online = []
        
        for session_id, session in self.sessions.items():
            if 'last_active' in session:
                last_active = datetime.fromisoformat(session['last_active'])
                if last_active > cutoff:
                    online.append({
                        'session_id': session_id,
                        'ip': session.get('ip_address', 'Unknown'),
                        'current_stage': session.get('current_stage', 'unknown'),
                        'utm_source': session.get('utm_source', 'direct'),
                        'last_active': session['last_active'],
                        'plate': session.get('plate', '-'),
                        'pix_copied': session.get('pix_copied', False)
                    })
        
        return online
    
    def get_stats(self):
        """Get session statistics"""
        total_sessions = len(self.sessions)
        online_count = len(self.get_online_users())
        
        # Count by stage
        stage_counts = {
            self.STAGE_INITIAL: 0,
            self.STAGE_RESULTS: 0,
            self.STAGE_PIX_MODAL: 0
        }
        
        pix_copied_count = 0
        utm_sources = {}
        
        for session in self.sessions.values():
            current_stage = session.get('current_stage')
            if current_stage in stage_counts:
                stage_counts[current_stage] += 1
            
            if session.get('pix_copied'):
                pix_copied_count += 1
            
            utm = session.get('utm_source', 'direct')
            utm_sources[utm] = utm_sources.get(utm, 0) + 1
        
        return {
            'total_sessions': total_sessions,
            'online_now': online_count,
            'stage_counts': stage_counts,
            'pix_copied_count': pix_copied_count,
            'utm_sources': utm_sources
        }
    
    def cleanup_old_sessions(self, days=7):
        """Remove sessions older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for session_id, session in self.sessions.items():
            if 'last_active' in session:
                last_active = datetime.fromisoformat(session['last_active'])
                if last_active < cutoff:
                    to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        if to_remove:
            self._save_sessions()
        
        return len(to_remove)

# Global tracker instance
tracker = SessionTracker()
