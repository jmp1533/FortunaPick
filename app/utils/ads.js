// Google AdSense Configuration

export const ADSENSE_CONFIG = {
  // 1. 게시자 ID
  PUBLISHER_ID: "ca-pub-5715472916498822",
  
  // 2. 광고 단위 슬롯 ID
  SLOTS: {
    /** 디스플레이 광고 (반응형) - 상단 배너 */
    BANNER_TOP: "8035275094",
    
    /** 디스플레이 광고 (반응형) - 중간 배너 */
    BANNER_MIDDLE: "3363093412",
    
    /** 인피드 광고 - 리스트 내 삽입 */
    IN_FEED_LIST: "9154051110",
    
    /** 멀티플렉스 광고 - 사이드바 하단 */
    SIDEBAR_BOTTOM: "4069670429",
  },

  // 3. 인피드 광고 레이아웃 키 (IN_FEED_LIST 전용)
  LAYOUT_KEYS: {
    IN_FEED_LIST: "-f5+5t+4z-d1+5q"
  }
};
