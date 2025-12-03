import { useMutation } from '@tanstack/react-query';
import { LogIn as LogInIcon } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api.ts';
import useAuthStore from '../store/authStore.ts';


// Local SVG icon to avoid dependency on 'lucide-react'
// const LogInIcon = (props: SVGProps<SVGSVGElement>) => (
//   <svg
//     {...props}
//     viewBox="0 0 24 24"
//     fill="none"
//     xmlns="http://www.w3.org/2000/svg"
//   >
//     <path
//       d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"
//       stroke="currentColor"
//       strokeWidth="2"
//       strokeLinecap="round"
//       strokeLinejoin="round"
//     />
//     <path
//       d="M10 17l5-5-5-5"
//       stroke="currentColor"
//       strokeWidth="2"
//       strokeLinecap="round"
//       strokeLinejoin="round"
//     />
//     <path
//       d="M15 12H3"
//       stroke="currentColor"
//       strokeWidth="2"
//       strokeLinecap="round"
//       strokeLinejoin="round"
//     />
//   </svg>
// );

interface FormData { email: string; password: string; }
interface LoginResponse {
  access: string;
  firstName: string;
  refresh: string;
}

const Login = () => {
  const { register, handleSubmit } = useForm<FormData>();
  const navigate = useNavigate();
  // Using the stubbed useAuthStore
  const { setAuth } = useAuthStore();

  // State for displaying user-friendly errors
  const [errorMessage, setErrorMessage] = useState('');

  const mutation = useMutation({
    mutationFn: (data: FormData) => api.post('/core/login', data),


    onSuccess: (response: { access: string; refresh: string; firstName: string }) => {
      setAuth(response.access, response.refresh, response.firstName);
      navigate('/overview');
    },

    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : 'An unknown error occurred during login.';

      // Set the error message to display in the UI
      setErrorMessage(message);
    }
  });

  const onSubmit = (data: FormData) => {
    // Clear the error message before starting a new mutation
    setErrorMessage('');
    mutation.mutate(data);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900 text-slate-300 font-sans p-4">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="p-8 bg-slate-800/70 rounded-xl shadow-2xl border border-slate-700 w-full max-w-sm backdrop-blur-sm"
      >
        <div className="flex justify-center mb-6">
          <LogInIcon className="w-8 h-8 text-cyan-500" />
        </div>

        <div className="space-y-4">
          <input
            {...register('email', { required: true })}
            type="email"
            placeholder="Email Address"
            className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500 transition duration-300"
          />

          <input
            {...register('password', { required: true })}
            type="password"
            placeholder="Password"
            className="w-full p-3 bg-slate-700/50 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500 transition duration-300"
          />
        </div>

        {/* Dynamic Error Display */}
        {(mutation.isError || errorMessage) && (
          <div className="mt-6 p-3 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm text-center shadow-inner">
            {/* <p className="font-medium">Error:</p> */}
            <p>{errorMessage || 'Login failed. Please check your credentials.'}</p>
          </div>
        )}

        <button
          type="submit"
          className="w-full mt-8 bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 rounded-lg transition duration-300 shadow-md shadow-cyan-900/50 hover:shadow-lg hover:shadow-cyan-900/80 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Authenticating...
            </>
          ) : (
            'Secure Login'
          )}
        </button>

        <p className="mt-8 text-center text-slate-400 text-sm">
          Forgot password? <Link to="#" className="text-cyan-500 hover:text-cyan-400 font-medium transition-colors">Reset</Link>
        </p>
        <p className="mt-2 text-center text-slate-400 text-sm">
          Don't have an account? <Link to="/register" className="text-cyan-500 hover:text-cyan-400 font-medium transition-colors">Register here</Link>
        </p>
      </form>
    </div>
  );
};

export default Login;
