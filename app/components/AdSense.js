"use client";
import { useEffect } from 'react';

export default function AdSense({ pId }) {
  useEffect(() => {
    // This component is only for loading the script.
    // The actual ad push happens in AdBanner components.
  }, []);

  if (!pId) return null;

  return (
    <script
      async
      src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${pId}`}
      crossOrigin="anonymous"
    />
  );
}
