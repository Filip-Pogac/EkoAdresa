import { useEffect, useRef, useState, type ReactNode } from 'react';

const INTENT_EVENTS = ['pointermove', 'pointerdown', 'keydown', 'scroll', 'touchstart'] as const;

interface LoadOnIntentProps {
  /** Rendered once the user interacts with the page while the placeholder is near the
   * viewport, or presses the placeholder's button (stays rendered after that). */
  children: ReactNode;
  /** Shown until then, with the same size, so nothing jumps; gets `load` for its button. */
  placeholder: (load: () => void) => ReactNode;
}

/**
 * Mounts heavy content (the home page map, MapLibre + WebGL) only when it is near the
 * viewport AND the user has moved, touched, scrolled or typed: the first screen and the
 * search box are never held up by it. The placeholder's button loads it at once.
 */
export function LoadOnIntent({ children, placeholder }: LoadOnIntentProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [near, setNear] = useState(false);
  const [interacted, setInteracted] = useState(false);
  const [forced, setForced] = useState(false);
  const show = forced || (near && interacted);

  useEffect(() => {
    const el = ref.current;
    if (!el || near) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) setNear(true);
      },
      { rootMargin: '200px' },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [near]);

  useEffect(() => {
    if (interacted) return;
    const onIntent = () => setInteracted(true);
    for (const type of INTENT_EVENTS)
      window.addEventListener(type, onIntent, { once: true, passive: true });
    return () => {
      for (const type of INTENT_EVENTS) window.removeEventListener(type, onIntent);
    };
  }, [interacted]);

  return (
    <div ref={ref} className="flex flex-1 flex-col">
      {show ? children : placeholder(() => setForced(true))}
    </div>
  );
}
