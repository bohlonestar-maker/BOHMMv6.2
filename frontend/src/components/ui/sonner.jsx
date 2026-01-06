import { Toaster as Sonner, toast } from "sonner"

const Toaster = ({
  ...props
}) => {
  return (
    <Sonner
      theme="dark"
      position="top-center"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast bg-slate-800 text-white border border-slate-600 shadow-lg",
          description: "text-slate-300",
          actionButton:
            "bg-blue-600 text-white",
          cancelButton:
            "bg-slate-700 text-slate-300",
          success: "bg-green-900 border-green-700 text-green-100",
          error: "bg-red-900 border-red-700 text-red-100",
          warning: "bg-yellow-900 border-yellow-700 text-yellow-100",
          info: "bg-blue-900 border-blue-700 text-blue-100",
        },
      }}
      {...props} />
  );
}

export { Toaster, toast }
