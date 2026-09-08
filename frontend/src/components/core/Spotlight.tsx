import React, { useRef, useState, useCallback } from "react";
import { motion, useSpring, useTransform } from "framer-motion";

interface SpotlightProps {
  className?: string;
  fill?: string;
  size?: number;
  children: React.ReactNode;
}

export const Spotlight: React.FC<SpotlightProps> = ({
  className = "",
  fill = "rgba(225, 29, 46, 0.08)",
  size = 350,
  children,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  const mouseX = useSpring(0, { damping: 25, stiffness: 200 });
  const mouseY = useSpring(0, { damping: 25, stiffness: 200 });

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      mouseX.set(e.clientX - rect.left);
      mouseY.set(e.clientY - rect.top);
    },
    [mouseX, mouseY]
  );

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`relative overflow-hidden ${className}`}
    >
      <motion.div
        className="pointer-events-none absolute -inset-px transition-opacity duration-300"
        style={{
          opacity: isHovered ? 1 : 0,
          background: useTransform(
            [mouseX, mouseY],
            ([x, y]) =>
              `radial-gradient(${size}px circle at ${x}px ${y}px, ${fill}, transparent 80%)`
          ),
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
};
