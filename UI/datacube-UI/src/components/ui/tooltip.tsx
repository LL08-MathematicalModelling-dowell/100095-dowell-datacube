import * as React from "react";

export const TooltipProvider = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const Tooltip = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const TooltipTrigger = React.forwardRef<HTMLButtonElement, React.HTMLAttributes<HTMLButtonElement>>(
  ({ children, ...props }, ref) => <button ref={ref} {...props}>{children}</button>
);
export const TooltipContent = ({ children, side = "top", className = "" }: any) => (
  <div className={`absolute z-50 px-3 py-2 text-sm rounded-lg shadow-lg ${className}`} style={{ [side]: "100%", marginTop: side === "bottom" ? "8px" : side === "top" ? "-8px" : "0" }}>
    {children}
  </div>
);