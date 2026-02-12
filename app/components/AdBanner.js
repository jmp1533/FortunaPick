"use client";
import { useEffect, useRef } from 'react';
import { ADSENSE_CONFIG } from '../utils/ads';

export default function AdBanner({ 
  slotId, 
  format = "auto", 
  responsive = "true",
  layoutKey = null, // 인피드 광고용 레이아웃 키 추가
  style = { display: 'block' },
  className = ""
}) {
  const adRef = useRef(null);

  useEffect(() => {
    try {
      const adsbygoogle = window.adsbygoogle || [];
      // 광고가 이미 로드되었는지 확인하여 중복 푸시 방지
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
    <div className={`ad-container ${className}`} style={{ margin: '20px 0', textAlign: 'center', minHeight: '100px', ...style }}>
      <ins
        ref={adRef}
        className="adsbygoogle"
        style={style}
        data-ad-client={ADSENSE_CONFIG.PUBLISHER_ID}
        data-ad-slot={slotId}
        data-ad-format={format}
        data-full-width-responsive={responsive}
        {...(layoutKey && { "data-ad-layout-key": layoutKey })} // layoutKey가 있을 때만 속성 추가
      />
    </div>
  );
}
