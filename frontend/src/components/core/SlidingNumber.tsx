import { cn } from "../../lib/utils";
import { motion, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";

interface DigitProps {
  digit: number;
}

function DigitWheel({ digit }: DigitProps) {
  const spring = useSpring(digit, { stiffness: 220, damping: 26 });

  useEffect(() => {
    spring.set(digit);
  }, [digit, spring]);

  return (
    <span className="relative inline-block h-[1.15em] w-[0.62em] overflow-hidden align-middle">
      <motion.span
        style={{
          y: useTransform(spring, (latest) => `${-latest * 1.15}em`),
        }}
        className="absolute top-0 left-0 flex flex-col items-center select-none font-mono"
      >
        {Array.from({ length: 10 }, (_, i) => (
          <span key={i} className="h-[1.15em] flex items-center justify-center">
            {i}
          </span>
        ))}
      </motion.span>
    </span>
  );
}

export interface SlidingNumberProps {
  value: number;
  decimalPlaces?: number;
  className?: string;
  prefix?: string;
  suffix?: string;
}

export function SlidingNumber({
  value,
  decimalPlaces = 0,
  className,
  prefix = "",
  suffix = "",
}: SlidingNumberProps) {
  const formatted = decimalPlaces > 0 ? value.toFixed(decimalPlaces) : Math.round(value).toString();
  const chars = formatted.split("");

  return (
    <span className={cn("inline-flex items-center font-mono", className)}>
      {prefix && <span className="mr-0.5">{prefix}</span>}
      {chars.map((ch, idx) => {
        const isDigit = !isNaN(Number(ch)) && ch !== " ";
        if (isDigit) {
          return <DigitWheel key={idx} digit={Number(ch)} />;
        }
        return (
          <span key={idx} className="inline-block">
            {ch}
          </span>
        );
      })}
      {suffix && <span className="ml-0.5">{suffix}</span>}
    </span>
  );
}
