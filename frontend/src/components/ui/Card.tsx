import { type HTMLAttributes, forwardRef } from "react";
import { cn } from "@/utils/cn";

type Variant = "default" | "elevated" | "outlined";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: Variant;
}

const variants: Record<Variant, string> = {
  default: "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm",
  elevated: "bg-white dark:bg-slate-800 shadow-md dark:shadow-slate-900/50",
  outlined: "bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = "default", className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("rounded-xl transition-shadow duration-200", variants[variant], className)}
      {...props}
    >
      {children}
    </div>
  )
);
Card.displayName = "Card";
