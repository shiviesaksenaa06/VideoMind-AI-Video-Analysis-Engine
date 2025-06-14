import React, { useState } from "react";

// Parent container to hold state
export function Tabs({ defaultValue, children, className }) {
  const [activeTab, setActiveTab] = useState(defaultValue);

  return (
    <div className={`mt-6 ${className}`}>
      {React.Children.map(children, (child) => {
        // Inject props like onValueChange into children
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            activeTab,
            onValueChange: setActiveTab,
          });
        }
        return child;
      })}
    </div>
  );
}

export function TabsList({ children }) {
  return <div className="flex gap-2 border-b border-zinc-700 pb-2">{children}</div>;
}

export function TabsTrigger({ value, children, onValueChange, activeTab }) {
  const isActive = activeTab === value;

  return (
    <button
      onClick={() => onValueChange(value)}
      className={`px-4 py-2 rounded-t font-medium transition ${
        isActive ? "bg-zinc-800 text-white border-b-2 border-blue-500" : "text-gray-400"
      }`}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, activeTab, children }) {
  if (value !== activeTab) return null;
  return <div className="mt-4">{children}</div>;
}
