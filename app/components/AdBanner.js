"use client";
import { useEffect, useRef } from 'react';
import { ADSENSE_CONFIG } from '../utils/ads';

export default function AdBanner({ 
  slotId, 
  format = "auto", 
  responsive = "true",
  layoutKey = null,
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

  if (!slotId || !ADSENSE_CONFIG.PUBLISHER_ID) {
    return null; 
  }

  return (
    <div 
      className={`ad-container ${className}`} 
      style={{ 
        margin: '20px 0', 
        textAlign: 'center', 
        minHeight: '100px', 
        width: '100%', 
        overflow: 'hidden',
        ...style 
      }}
    >
      <ins
        ref={adRef}
        className="adsbygoogle"
        style={{ display: 'block', width: '100%' }}
        data-ad-client={ADSENSE_CONFIG.PUBLISHER_ID}
        data-ad-slot={slotId}
        data-ad-format={format}
        data-full-width-responsive={responsive}
        {...(layoutKey && { "data-ad-layout-key": layoutKey })}
      />
    </div>
  );
}
