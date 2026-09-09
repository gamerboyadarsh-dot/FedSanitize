import { cn } from "../../lib/utils";
import { AnimatePresence, type Transition, motion } from "framer-motion";
import {
  Children,
  cloneElement,
  type ReactElement,
  useEffect,
  useState,
  useId,
} from "react";

export type AnimatedBackgroundProps = {
  children:
    | ReactElement<{ "data-id": string; className?: string; onClick?: (e: any) => void; children?: any }>[]
    | ReactElement<{ "data-id": string; className?: string; onClick?: (e: any) => void; children?: any }>;
  defaultValue?: string;
  onValueChange?: (newActiveId: string | null) => void;
  className?: string;
  transition?: Transition;
  enableHover?: boolean;
};

export function AnimatedBackground({
  children,
  defaultValue,
  onValueChange,
  className,
  transition,
  enableHover = false,
}: AnimatedBackgroundProps) {
  const [activeId, setActiveId] = useState<string | null>(defaultValue ?? null);
  const uniqueId = useId();

  const handleSetActiveId = (id: string | null) => {
    setActiveId(id);
    if (onValueChange) {
      onValueChange(id);
    }
  };

  useEffect(() => {
    if (defaultValue !== undefined) {
      setActiveId(defaultValue);
    }
  }, [defaultValue]);

  return (
    <>
      {Children.map(children, (child: any, index) => {
        if (!child) return null;
        const id = child.props["data-id"];
        const interactionProps = enableHover
          ? {
              onMouseEnter: () => handleSetActiveId(id),
              onMouseLeave: () => handleSetActiveId(null),
            }
          : {
              onClick: (e: any) => {
                handleSetActiveId(id);
                child.props.onClick?.(e);
              },
            };

        return cloneElement(
          child,
          {
            key: index,
            className: cn("relative inline-flex", child.props.className),
            "data-checked": activeId === id ? "true" : "false",
            ...interactionProps,
          },
          <>
            <AnimatePresence initial={false}>
              {activeId === id && (
                <motion.div
                  layoutId={`background-${uniqueId}`}
                  className={cn("absolute inset-0", className)}
                  transition={
                    transition ?? {
                      type: "spring",
                      bounce: 0.15,
                      duration: 0.35,
                    }
                  }
                  initial={{ opacity: defaultValue ? 1 : 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                />
              )}
            </AnimatePresence>
            <span className="z-10 relative flex items-center gap-3 w-full">
              {child.props.children}
            </span>
          </>
        );
      })}
    </>
  );
}
