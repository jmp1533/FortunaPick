import './globals.css';

export const metadata = {
  title: 'FortunaPick | Premium Lotto Combination Engine',
  description: '고급 알고리즘 기반 로또 번호 조합 추천 서비스. AC값, 홀짝비율, 번호대분포 등 다양한 필터링으로 최적의 조합을 찾아드립니다.',
  keywords: '로또, 번호추천, 조합, AC값, 필터링, 알고리즘',
  authors: [{ name: 'FortunaPick' }],
  viewport: 'width=device-width, initial-scale=1, maximum-scale=1',
  themeColor: '#0A0B0E',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
