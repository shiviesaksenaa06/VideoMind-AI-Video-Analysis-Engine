export function Input({ className, ...props }) {
  return (
    <input
      className={`border rounded-md px-4 py-2 text-black w-full ${className}`}
      {...props}
    />
  );
}
