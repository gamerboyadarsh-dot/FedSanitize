import { cn } from "../../lib/utils";
import { AnimatePresence, type Transition, type Variant, motion } from "framer-motion";
import { type ReactNode } from "react";

export type TransitionPanelProps = {
  children: ReactNode[];
  activeIndex: number;
  className?: string;
  transition?: Transition;
  variants?: { enter: Variant; center: Variant; exit: Variant };
};

export function TransitionPanel({
  children,
  activeIndex,
  className,
  transition,
  variants,
}: TransitionPanelProps) {
  const defaultVariants = {
    enter: { opacity: 0, y: 8, filter: "blur(2px)" },
    center: { opacity: 1, y: 0, filter: "blur(0px)" },
    exit: { opacity: 0, y: -8, filter: "blur(2px)" },
  };

  return (
    <div className={cn("relative w-full", className)}>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={activeIndex}
          variants={variants ?? defaultVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={transition ?? { duration: 0.22, ease: "easeOut" }}
          className="w-full"
        >
          {children[activeIndex]}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
