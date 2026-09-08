import { cn } from "../../lib/utils";
import { type ReactNode } from "react";

export interface GlowEffectProps {
  children: ReactNode;
  className?: string;
  glowColor?: string;
}

export function GlowEffect({
  children,
  className,
  glowColor = "rgba(225, 29, 46, 0.35)",
}: GlowEffectProps) {
  return (
    <div className={cn("relative group/glow w-full h-full", className)}>
      <div
        className="absolute -inset-[1px] rounded-xl opacity-0 group-hover/glow:opacity-100 transition-opacity duration-300 pointer-events-none blur-[6px] -z-10"
        style={{
          background: `radial-gradient(circle at center, ${glowColor} 10%, rgba(225,29,46,0.1) 60%, transparent 80%)`,
        }}
      />
      <div className="relative w-full h-full z-0">
        {children}
      </div>
    </div>
  );
}
