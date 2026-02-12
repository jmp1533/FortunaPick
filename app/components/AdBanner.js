"use client";
import { useEffect, useRef } from 'react';
import { ADSENSE_CONFIG } from '../utils/ads';

export default function AdBanner({ 
  slotId, 
  format = "auto", 
  responsive = "true",
  style = { display: 'block' },
  className = ""
}) {
  const adRef = useRef(null);

  useEffect(() => {
    try {
      const adsbygoogle = window.adsbygoogle || [];
      if (adRef.current && adRef.current.innerHTML === "") {
          adsbygoogle.push({});
      }
    } catch (err) {
      console.error('AdBanner error:', err);
    }
  }, []);

  if (!slotId || !ADSENSE_CONFIG.PUBLISHER_ID || ADSENSE_CONFIG.PUBLISHER_ID === "ca-pub-XXXXXXXXXXXXXXXX") {
    return null; 
  }

  return (
    <div className={`ad-container ${className}`} style={{ margin: '20px 0', textAlign: 'center', minHeight: '100px', ...style }}>
      <ins
        ref={adRef}
        className="adsbygoogle"
        style={style}
        data-ad-client={ADSENSE_CONFIG.PUBLISHER_ID}
        data-ad-slot={slotId}
        data-ad-format={format}
        data-full-width-responsive={responsive}
      />
      <span style={{ fontSize: '10px', color: '#ccc', display: 'block', marginTop: '4px' }}>Advertisement</span>
    </div>
  );
}
