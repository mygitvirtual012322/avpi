from database import SessionLocal, MetaPixelConfig
from datetime import datetime

def get_pixel_config():
    """Get Meta Pixel configuration from database"""
    db = SessionLocal()
    try:
        config = db.query(MetaPixelConfig).first()
        if not config:
            # Create default empty config
            config = MetaPixelConfig(
                pixel_id='',
                enabled=False
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return {
            'pixel_id': config.pixel_id or '',
            'enabled': config.enabled
        }
    finally:
        db.close()

def save_pixel_config(pixel_id, enabled=True):
    """Save Meta Pixel configuration to database"""
    db = SessionLocal()
    try:
        config = db.query(MetaPixelConfig).first()
        if config:
            config.pixel_id = pixel_id
            config.enabled = enabled
            config.updated_at = datetime.utcnow()
        else:
            config = MetaPixelConfig(
                pixel_id=pixel_id,
                enabled=enabled
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        
        return {
            'pixel_id': config.pixel_id,
            'enabled': config.enabled
        }
    except Exception as e:
        print(f"Error saving pixel config: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def get_pixel_code():
    """Get Meta Pixel base code snippet"""
    config = get_pixel_config()
    
    if not config['enabled'] or not config['pixel_id']:
        return ''
    
    pixel_id = config['pixel_id']
    
    return f"""
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '{pixel_id}');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id={pixel_id}&ev=PageView&noscript=1"
/></noscript>
<!-- End Meta Pixel Code -->
"""
