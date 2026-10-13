import { useEffect } from "react";

export default function useOutsideClose(ref) {
  useEffect(() => {
    function close(event) {
      if (ref.current && !ref.current.contains(event.target))
        ref.current.open = false;
    }
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [ref]);
}
