import { cn } from "../../lib/utils";
import { motion, type Transition } from "framer-motion";

export interface BorderTrailProps {
  className?: string;
  size?: number;
  transition?: Transition;
  trailColor?: string;
}

export function BorderTrail({
  className,
  size = 70,
  transition,
  trailColor = "#e11d2e",
}: BorderTrailProps) {
  return (
    <div className="pointer-events-none absolute inset-0 rounded-[inherit] overflow-hidden z-20">
      <motion.div
        className={cn("absolute aspect-square rounded-full blur-[1px]", className)}
        style={{
          width: size,
          height: size,
          background: `radial-gradient(circle, ${trailColor} 10%, rgba(225,29,46,0.5) 40%, transparent 75%)`,
          offsetPath: `rect(0 100% 100% 0 round 12px)`,
        }}
        animate={{
          offsetDistance: ["0%", "100%"],
        }}
        transition={
          transition ?? {
            repeat: Infinity,
            ease: "linear",
            duration: 2.2,
          }
        }
      />
    </div>
  );
}
