import { useEffect } from 'react';

export default function usePageTitle(title) {
  useEffect(() => {
    const prevTitle = document.title;
    if (title) {
      document.title = `${title} | BUSify`;
    }
    return () => {
      document.title = prevTitle;
    };
  }, [title]);
}
