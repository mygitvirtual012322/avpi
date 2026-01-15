import json
import os

CONFIG_FILE = 'admin_data/meta_pixel_config.json'

def get_pixel_config():
    """Get Meta Pixel configuration"""
    os.makedirs('admin_data', exist_ok=True)
    
    if not os.path.exists(CONFIG_FILE):
        # Default empty config
        default_config = {
            'pixel_id': '',
            'enabled': False
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_pixel_config(pixel_id, enabled=True):
    """Save Meta Pixel configuration"""
    os.makedirs('admin_data', exist_ok=True)
    
    config = {
        'pixel_id': pixel_id,
        'enabled': enabled
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config

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
