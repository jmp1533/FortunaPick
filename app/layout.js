import './globals.css';

export const metadata = {
    title: '로또 분석기',
    description: '파이썬 기반 로또 번호 추출',
};

export default function RootLayout({ children }) {
    return (
        <html lang="ko">
        <body>{children}</body>
        </html>
    );
}