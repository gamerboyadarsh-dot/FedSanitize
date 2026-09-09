import { cn } from "../../lib/utils";
import { motion, type Variants } from "framer-motion";

export interface TextEffectProps {
  children: string;
  per?: "word" | "char";
  className?: string;
  delay?: number;
}

export function TextEffect({
  children,
  per = "word",
  className,
  delay = 0,
}: TextEffectProps) {
  const segments = per === "word" ? children.split(" ") : children.split("");

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: per === "word" ? 0.05 : 0.02,
        delayChildren: delay,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 5, filter: "blur(2px)" },
    visible: {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: { duration: 0.22, ease: "easeOut" },
    },
  };

  return (
    <motion.span
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className={cn("inline-block", className)}
    >
      {segments.map((seg, idx) => (
        <motion.span key={idx} variants={itemVariants} className="inline-block">
          {seg}
          {per === "word" && idx < segments.length - 1 && "\u00A0"}
        </motion.span>
      ))}
    </motion.span>
  );
}
