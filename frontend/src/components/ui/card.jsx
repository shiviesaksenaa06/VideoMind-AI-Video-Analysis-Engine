export function Card({ className, ...props }) {
  return <div className={`rounded-2xl bg-zinc-900 p-6 shadow-md ${className}`} {...props} />;
}

export function CardContent({ className, ...props }) {
  return <div className={`mt-4 ${className}`} {...props} />;
}
