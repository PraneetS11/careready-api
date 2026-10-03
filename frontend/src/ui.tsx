import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { animate, motion, useReducedMotion } from "motion/react";
import { X, ArrowUpRight, HeartHandshake } from "lucide-react";
export function Brand() {
  return (
    <span className="brand">
      <span className="brand-mark">
        <HeartHandshake size={21} />
      </span>
      care<span className="brand-light">ready</span>
      <span className="brand-dot">.</span>
    </span>
  );
}
export function Counter({ value }: { value: number }) {
  const [display, setDisplay] = useState(value);
  const previous = useRef(value);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) {
      setDisplay(value);
      return;
    }
    const controls = animate(previous.current, value, {
      duration: 0.6,
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
    previous.current = value;
    return () => controls.stop();
  }, [value, reduced]);
  return <span>{display}</span>;
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-symbol">↗</span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function ErrorNotice({ error }: { error: unknown }) {
  return error ? (
    <div role="alert" className="notice error">
      {error instanceof Error ? error.message : String(error)}
    </div>
  ) : null;
}
export function Status({ value }: { value: string }) {
  return (
    <span className={"status " + value}>
      <i />
      {value.replaceAll("_", " ")}
    </span>
  );
}
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const node = dialog.current;
    node?.showModal();
    return () => node?.close();
  }, []);
  return (
    <dialog
      ref={dialog}
      onCancel={onClose}
      aria-labelledby="dialog-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-head">
        <h2 id="dialog-title">{title}</h2>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function PageTitle({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <motion.div
      className="page-title"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
      </div>
      {children}
    </motion.div>
  );
}
export function Primary({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button className="button primary" onClick={onClick}>
      {children}
      <ArrowUpRight size={17} />
    </button>
  );
}
